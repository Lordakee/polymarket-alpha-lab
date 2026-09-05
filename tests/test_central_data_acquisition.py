from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab.central_data_acquisition import (
    AcquisitionOutcome,
    RETRY_AFTER_CAP_SECONDS,
    acquire_once,
    acquire_paginated,
)
from polymarket_alpha_lab.central_data_contracts import (
    CentralDataRequest,
    FailureStatus,
    RawResponse,
    RequestParamSpec,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_db_row import NormalizedObservationRow, RawEventRow
from polymarket_alpha_lab.central_data_registry import GAMMA_MARKETS_PAGINATION
from polymarket_alpha_lab.central_data_request_params import PaginationPolicy
from polymarket_alpha_lab.central_data_source_adapters import parse_gamma_markets
from polymarket_alpha_lab.central_data_transport import CentralTransportError


GAMMA = SourceDefinition(
    source_id="polymarket_gamma_markets",
    source_family="polymarket_gamma",
    url_template="https://gamma-api.polymarket.com/markets",
    content_type="application/json",
    freshness_policy_seconds=300,
    is_official=True,
    query_params=(
        RequestParamSpec("limit", "int_range", min_value=1, max_value=100),
        RequestParamSpec("offset", "int_range", min_value=0, max_value=100000),
    ),
)


def _market_page(count: int) -> bytes:
    import json

    markets = [
        {
            "conditionId": f"0x{i:04x}",
            "question": f"Q{i}?",
            "slug": f"q-{i}",
            "outcomePrices": '["0.5", "0.5"]',
            "outcomes": '["Yes", "No"]',
        }
        for i in range(count)
    ]
    return json.dumps(markets).encode()


class RecordingStore:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.raw_rows: list[RawEventRow] = []
        self.normalized_rows: list[NormalizedObservationRow] = []

    def insert_raw_event(self, row: RawEventRow):
        from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

        self.calls.append("raw")
        self.raw_rows.append(row)
        return CentralDataInsertResult(row.raw_event_id, "inserted")

    def insert_normalized_observation(self, row: NormalizedObservationRow):
        from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

        self.calls.append("normalized")
        self.normalized_rows.append(row)
        return CentralDataInsertResult(row.normalized_observation_id, "inserted")


class ScriptedTransport:
    """Fake transport returning scripted raw responses or raising."""

    def __init__(self, script) -> None:
        self.script = list(script)
        self.requests: list[CentralDataRequest] = []
        self.user_agent = "fake/1.0"

    def fetch(self, source_def, request):
        self.requests.append(request)
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def _ok_response(body: bytes) -> RawResponse:
    return RawResponse(
        200,
        {"content-type": "application/json"},
        body,
        GAMMA.url_template,
        retrieval_time=datetime.now(UTC),
        request_url=GAMMA.url_template,
        content_type="application/json",
    )


def _error_response(status_code: int, headers=None) -> RawResponse:
    return RawResponse(
        status_code,
        {"content-type": "application/json", **(headers or {})},
        b"",
        GAMMA.url_template,
        retrieval_time=datetime.now(UTC),
        request_url=GAMMA.url_template,
        failure_status=FailureStatus.HTTP_ERROR,
        content_type="application/json",
    )


def test_acquire_once_persists_raw_before_normalized() -> None:
    transport = ScriptedTransport([_ok_response(_market_page(2))])
    store = RecordingStore()
    outcome = acquire_once(
        GAMMA,
        transport=transport,
        store=store,
        params={"limit": 2, "offset": 0},
        parser=parse_gamma_markets,
    )
    assert outcome.failure_status is FailureStatus.NONE
    assert outcome.raw_result is not None and outcome.raw_result.inserted
    assert len(outcome.normalized_rows) == 2
    assert store.calls == ["raw", "normalized", "normalized"]
    assert store.normalized_rows[0].raw_event_id == store.raw_rows[0].raw_event_id


def test_acquire_once_is_deterministic_on_replay() -> None:
    body = _market_page(1)
    fixed = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)

    def _frozen(body: bytes) -> RawResponse:
        return RawResponse(
            200,
            {"content-type": "application/json"},
            body,
            GAMMA.url_template,
            retrieval_time=fixed,
            request_url=GAMMA.url_template,
            content_type="application/json",
        )

    first_transport = ScriptedTransport([_frozen(body)])
    second_transport = ScriptedTransport([_frozen(body)])
    first_store, second_store = RecordingStore(), RecordingStore()
    first = acquire_once(GAMMA, transport=first_transport, store=first_store, params={"limit": 1})
    second = acquire_once(GAMMA, transport=second_transport, store=second_store, params={"limit": 1})
    assert first.request_identity == second.request_identity
    assert first.normalized_rows[0].normalized_observation_id == (
        second.normalized_rows[0].normalized_observation_id
    )


def test_acquire_once_rejects_policy_refused_responses_before_any_store_call() -> None:
    sensitive_body = b'{"api_key": "should-not-persist"}'
    transport = ScriptedTransport([_ok_response(sensitive_body)])
    store = RecordingStore()
    outcome = acquire_once(GAMMA, transport=transport, store=store, params={"limit": 1})
    assert store.calls == []
    assert outcome.failure_status is FailureStatus.INVALID_REQUEST
    assert outcome.reason_codes == ("policy_refused",)


def test_acquire_once_retries_then_succeeds_with_backoff_sleeps() -> None:
    sleeps: list[float] = []
    transport = ScriptedTransport(
        [
            CentralTransportError(FailureStatus.TIMEOUT, "timed out"),
            _ok_response(_market_page(1)),
        ]
    )
    store = RecordingStore()
    outcome = acquire_once(
        GAMMA,
        transport=transport,
        store=store,
        params={"limit": 1},
        sleep=sleeps.append,
    )
    assert outcome.failure_status is FailureStatus.NONE
    assert outcome.attempts == 2
    assert sleeps == [1.0]


def test_acquire_once_rate_limit_outcomes() -> None:
    sleeps: list[float] = []
    transport = ScriptedTransport(
        [
            _error_response(429, {"retry-after": "60"}),
            _ok_response(_market_page(1)),
        ]
    )
    outcome = acquire_once(
        GAMMA, transport=transport, store=RecordingStore(), params={"limit": 1}, sleep=sleeps.append
    )
    assert outcome.failure_status is FailureStatus.NONE
    assert sleeps == [60.0]

    exhausted = acquire_once(
        GAMMA,
        transport=ScriptedTransport([_error_response(429, {"retry-after": "301"})]),
        store=RecordingStore(),
        params={"limit": 1},
        sleep=sleeps.append,
    )
    assert exhausted.failure_status is FailureStatus.HTTP_ERROR
    assert exhausted.reason_codes == ("rate_limit_exceeded",)
    assert exhausted.retry_after_seconds == RETRY_AFTER_CAP_SECONDS

    unparseable = acquire_once(
        GAMMA,
        transport=ScriptedTransport([_error_response(429, {"retry-after": "Wed, 21 Oct 2015"})]),
        store=RecordingStore(),
        params={"limit": 1},
    )
    assert unparseable.reason_codes == ("rate_limit_exceeded",)
    assert unparseable.retry_after_seconds is None

    huge = acquire_once(
        GAMMA,
        transport=ScriptedTransport([_error_response(429, {"retry-after": "999999"})]),
        store=RecordingStore(),
        params={"limit": 1},
    )
    assert huge.reason_codes == ("rate_limit_exceeded",)
    assert huge.retry_after_seconds == RETRY_AFTER_CAP_SECONDS
    assert 60.0 in sleeps


def test_acquire_once_surfaces_plain_http_errors_without_store_calls() -> None:
    transport = ScriptedTransport([_error_response(404)])
    store = RecordingStore()
    outcome = acquire_once(GAMMA, transport=transport, store=store, params={"limit": 1})
    assert store.calls == []
    assert outcome.failure_status is FailureStatus.HTTP_ERROR
    assert outcome.reason_codes == ("http_error_404",)


def test_acquire_once_non_retryable_transport_error_fails_fast() -> None:
    sleeps: list[float] = []
    transport = ScriptedTransport(
        [CentralTransportError(FailureStatus.RESOLVER_ERROR, "bad resolve")]
    )
    outcome = acquire_once(
        GAMMA,
        transport=transport,
        store=RecordingStore(),
        params={"limit": 1},
        sleep=sleeps.append,
    )
    assert outcome.failure_status is FailureStatus.RESOLVER_ERROR
    assert outcome.attempts == 1
    assert sleeps == []


def test_acquire_paginated_stops_on_underfull_page() -> None:
    transport = ScriptedTransport(
        [_ok_response(_market_page(3)), _ok_response(_market_page(1))]
    )
    store = RecordingStore()
    outcome = acquire_paginated(
        GAMMA,
        transport=transport,
        store=store,
        items_per_page=3,
        policy=GAMMA_MARKETS_PAGINATION,
        parser=parse_gamma_markets,
    )
    assert outcome.failure_status is FailureStatus.NONE
    assert outcome.pages_fetched == 2
    assert len(outcome.normalized_rows) == 4
    assert dict(transport.requests[0].query) == {"limit": "3", "offset": "0"}
    assert dict(transport.requests[1].query) == {"limit": "3", "offset": "3"}


def test_acquire_paginated_reports_budget_exhaustion_without_row_pollution() -> None:
    pages = 5
    transport = ScriptedTransport([_ok_response(_market_page(2)) for _ in range(pages)])
    store = RecordingStore()
    outcome = acquire_paginated(
        GAMMA,
        transport=transport,
        store=store,
        items_per_page=2,
        policy=PaginationPolicy(max_pages=5, min_items_per_page=1, max_items_per_page=100),
        parser=parse_gamma_markets,
    )
    assert outcome.failure_status is FailureStatus.PAGINATION_BUDGET_EXHAUSTED
    assert outcome.pages_fetched == 5
    assert len(outcome.normalized_rows) == 10
    for row in outcome.normalized_rows:
        assert row.failure_status == FailureStatus.NONE.value


def test_acquire_paginated_requires_limit_offset_specs() -> None:
    minimal = SourceDefinition(
        source_id="minimal",
        source_family="minimal_family",
        url_template="https://example.com/feed",
        content_type="application/json",
        freshness_policy_seconds=60,
    )
    with pytest.raises(ValueError, match="limit and offset"):
        acquire_paginated(
            minimal,
            transport=ScriptedTransport([]),
            store=RecordingStore(),
            policy=PaginationPolicy(max_pages=2, min_items_per_page=1, max_items_per_page=10),
        )
