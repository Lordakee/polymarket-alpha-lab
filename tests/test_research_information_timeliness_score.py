import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_information_timeliness_score"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def source(observed_at: datetime, **overrides: object) -> Any:
    module = api()
    values = {"observed_at": observed_at}
    values.update(overrides)
    return module.ResearchInformationTimelinessSourceObservation(**values)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_INFORMATION_TIMELINESS_SCORE_CONFIG_VERSION,
        "pass_timeliness_score": d("0.800000"),
        "watch_timeliness_score": d("0.500000"),
        "deadline_watch_window_hours": d("24.000000"),
        "finalization_watch_window_hours": d("6.000000"),
        "source_recency_weight": d("0.650000"),
        "source_quorum_weight": d("0.250000"),
        "event_window_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchInformationTimelinessScoreConfig(**values)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "source_observations": (
            source(datetime(2026, 7, 6, 11, 30, tzinfo=UTC)),
            source(datetime(2026, 7, 6, 10, 0, tzinfo=UTC)),
        ),
        "event_deadline_at": datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
        "event_finalization_at": datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        "source_stale_after_hours": d("4.000000"),
        "source_block_after_hours": d("12.000000"),
    }
    values.update(overrides)
    return module.ResearchInformationTimelinessScoreInput(**values)


def score(
    item: Any | None = None,
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.score_research_information_timeliness(
        item or signal(),
        config=cfg or config(),
        generated_at=generated_at,
    )


def payload_with_matching_digest(
    payload: dict[str, Any],
    **overrides: object,
) -> dict[str, Any]:
    tampered = {**payload, **overrides}
    digest_values = {
        key: value
        for key, value in tampered.items()
        if key != "derived_validation_digest"
    }
    tampered["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            digest_values,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return tampered


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float, field.name
        assert type(value) is not int, field.name


def assert_no_runtime_numeric_or_datetime(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, (Decimal, datetime))
    if isinstance(value, dict):
        for child in value.values():
            assert_no_runtime_numeric_or_datetime(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_runtime_numeric_or_datetime(child)


def test_scores_pass_when_source_observations_are_fresh_for_open_windows() -> None:
    module = api()

    result = score(
        signal(
            source_observations=(
                source(
                    datetime(
                        2026,
                        7,
                        6,
                        7,
                        30,
                        tzinfo=timezone(timedelta(hours=-4)),
                    ),
                ),
                source(datetime(2026, 7, 6, 10, 0, tzinfo=UTC)),
            ),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(result, module.ResearchInformationTimelinessScoreReport)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.config_version == "research-information-timeliness-score-v1"
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.source_count == d("2")
    assert result.source_observed_at_values == (
        datetime(2026, 7, 6, 10, 0, tzinfo=UTC),
        datetime(2026, 7, 6, 11, 30, tzinfo=UTC),
    )
    assert result.newest_source_observed_at == datetime(2026, 7, 6, 11, 30, tzinfo=UTC)
    assert result.oldest_source_observed_at == datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    assert result.newest_source_age_hours == d("0.500000")
    assert result.oldest_source_age_hours == d("2.000000")
    assert result.stale_source_count == d("0")
    assert result.stale_source_ratio == d("0.000000")
    assert result.deadline_window_hours == d("24.000000")
    assert result.finalization_window_hours == d("48.000000")
    assert result.source_recency_score == d("0.958333")
    assert result.source_quorum_score == d("1.000000")
    assert result.event_window_score == d("1.000000")
    assert result.timeliness_score == d("0.972916")
    assert result.timeliness_status == "pass"
    assert result.reason_codes == (
        "deadline_open",
        "finalization_open",
        "source_newest_fresh",
        "source_quorum_clean",
        "timeliness_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_scores_watch_when_some_evidence_is_stale_near_deadline() -> None:
    result = score(
        signal(
            source_observations=(
                source(datetime(2026, 7, 6, 10, 0, tzinfo=UTC)),
                source(datetime(2026, 7, 6, 9, 0, tzinfo=UTC)),
                source(datetime(2026, 7, 6, 7, 0, tzinfo=UTC)),
            ),
            event_deadline_at=datetime(2026, 7, 7, 0, 0, tzinfo=UTC),
            event_finalization_at=datetime(2026, 7, 8, 0, 0, tzinfo=UTC),
        ),
    )

    assert result.source_count == d("3")
    assert result.newest_source_age_hours == d("2.000000")
    assert result.oldest_source_age_hours == d("5.000000")
    assert result.stale_source_count == d("1")
    assert result.stale_source_ratio == d("0.333333")
    assert result.deadline_window_hours == d("12.000000")
    assert result.finalization_window_hours == d("36.000000")
    assert result.source_recency_score == d("0.833333")
    assert result.source_quorum_score == d("0.666667")
    assert result.event_window_score == d("0.500000")
    assert result.timeliness_score == d("0.758333")
    assert result.timeliness_status == "watch"
    assert result.reason_codes == (
        "deadline_compressed",
        "finalization_open",
        "source_newest_fresh",
        "source_quorum_stale",
        "timeliness_watch",
    )


def test_scores_block_when_newest_source_exceeds_block_threshold() -> None:
    result = score(
        signal(
            source_observations=(
                source(datetime(2026, 7, 5, 23, 0, tzinfo=UTC)),
                source(datetime(2026, 7, 5, 21, 0, tzinfo=UTC)),
            ),
            event_deadline_at=datetime(2026, 7, 6, 13, 0, tzinfo=UTC),
            event_finalization_at=datetime(2026, 7, 6, 16, 0, tzinfo=UTC),
        ),
    )

    assert result.newest_source_age_hours == d("13.000000")
    assert result.oldest_source_age_hours == d("15.000000")
    assert result.stale_source_count == d("2")
    assert result.stale_source_ratio == d("1.000000")
    assert result.source_recency_score == d("0.000000")
    assert result.source_quorum_score == d("0.000000")
    assert result.event_window_score == d("0.041667")
    assert result.timeliness_score == d("0.004167")
    assert result.timeliness_status == "block"
    assert result.reason_codes == (
        "deadline_compressed",
        "finalization_compressed",
        "source_newest_blocked",
        "source_quorum_stale",
        "timeliness_block",
    )


def test_scores_block_when_finalization_window_has_elapsed() -> None:
    result = score(
        signal(
            event_deadline_at=datetime(2026, 7, 6, 10, 0, tzinfo=UTC),
            event_finalization_at=datetime(2026, 7, 6, 11, 0, tzinfo=UTC),
        ),
    )

    assert result.deadline_window_hours == d("0.000000")
    assert result.finalization_window_hours == d("0.000000")
    assert result.event_window_score == d("0.000000")
    assert result.timeliness_status == "block"
    assert result.reason_codes == (
        "deadline_elapsed",
        "finalization_elapsed",
        "source_newest_fresh",
        "source_quorum_clean",
        "timeliness_block",
    )


def test_custom_config_values_drive_report_validation_and_payload_digest() -> None:
    module = api()
    custom_config = config(
        pass_timeliness_score=d("0.900000"),
        watch_timeliness_score=d("0.600000"),
        deadline_watch_window_hours=d("48.000000"),
        finalization_watch_window_hours=d("24.000000"),
        source_recency_weight=d("0.500000"),
        source_quorum_weight=d("0.300000"),
        event_window_weight=d("0.200000"),
    )

    result = score(cfg=custom_config)

    assert result.pass_timeliness_score == d("0.900000")
    assert result.watch_timeliness_score == d("0.600000")
    assert result.deadline_watch_window_hours == d("48.000000")
    assert result.finalization_watch_window_hours == d("24.000000")
    assert result.source_recency_weight == d("0.500000")
    assert result.source_quorum_weight == d("0.300000")
    assert result.event_window_weight == d("0.200000")
    assert result.event_window_score == d("0.500000")
    assert result.timeliness_score == d("0.879166")
    assert result.timeliness_status == "watch"
    assert result.reason_codes == (
        "deadline_compressed",
        "finalization_open",
        "source_newest_fresh",
        "source_quorum_clean",
        "timeliness_watch",
    )

    payload = module.research_information_timeliness_score_payload(result)
    assert payload["pass_timeliness_score"] == "0.900000"
    assert payload["deadline_watch_window_hours"] == "48.000000"

    tampered = payload_with_matching_digest(
        payload,
        deadline_watch_window_hours="24.000000",
    )
    with pytest.raises(
        ValueError,
        match="report reason_codes must match|payload derived|report derived validation",
    ):
        module.research_information_timeliness_score_payload(tampered)


def test_payload_is_json_ready_guarded_and_digest_checked() -> None:
    module = api()
    result = score()

    payload = module.research_information_timeliness_score_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["source_observed_at_values"] == [
        "2026-07-06T10:00:00+00:00",
        "2026-07-06T11:30:00+00:00",
    ]
    assert payload["timeliness_score"] == "0.972916"
    assert payload["source_count"] == "2"
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert not any(fragment in encoded.lower() for fragment in ("api_key=secret", "token=secret"))
    assert not any(
        field in payload
        for field in (
            "candidate_id",
            "market_id",
            "market_slug",
            "question",
            "source_ref",
            "source_url",
            "dsn",
            "table_name",
        )
    )
    assert_no_runtime_numeric_or_datetime(payload)
    assert module.research_information_timeliness_score_payload(payload) == payload

    with pytest.raises(ValueError, match="payload fields must match"):
        module.research_information_timeliness_score_payload(
            {key: value for key, value in payload.items() if key != "timeliness_score"},
        )
    with pytest.raises(ValueError, match="unsafe|payload fields"):
        module.research_information_timeliness_score_payload(
            {**payload, "market_slug": "example-market"},
        )
    with pytest.raises(ValueError, match="payload derived validation failed"):
        module.research_information_timeliness_score_payload(
            {**payload, "timeliness_score": "0.900000"},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.research_information_timeliness_score_payload({**payload, "readonly": False})
    with pytest.raises(ValueError, match="Decimal-string"):
        module.research_information_timeliness_score_payload(
            {**payload, "timeliness_score": d("0.972916")},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_information_timeliness_score_payload(
            {**payload, "timeliness_score": 0.5},
        )
    with pytest.raises(ValueError, match="sensitive|unsafe"):
        module.research_information_timeliness_score_payload(
            {**payload, "timeliness_status": "buy now"},
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.research_information_timeliness_score_payload(
            {**payload, "generated_at": datetime(2026, 7, 6, 12, 0)},
        )
    with pytest.raises(ValueError, match="Decimal-string|precision"):
        module.research_information_timeliness_score_payload(
            payload_with_matching_digest(payload, timeliness_score="0.9729160"),
        )


def test_inputs_config_and_report_validate_decimal_time_consistency_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        source(datetime(2026, 7, 6, 11, 30))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        source(datetime(2026, 7, 6, 11, 30, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="source_stale_after_hours must be a Decimal"):
        signal(source_stale_after_hours=1)
    with pytest.raises(ValueError, match="source_stale_after_hours must be exactly Decimal"):
        signal(source_stale_after_hours=_DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="source_block_after_hours must exceed"):
        signal(source_block_after_hours=d("4.000000"))
    with pytest.raises(ValueError, match="source_observations must not be empty"):
        signal(source_observations=())
    with pytest.raises(ValueError, match="event_finalization_at must not be before"):
        signal(
            event_deadline_at=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
            event_finalization_at=datetime(2026, 7, 7, 11, 59, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config weights must sum to 1.000000"):
        config(source_recency_weight=d("0.700000"))
    with pytest.raises(ValueError, match="pass_timeliness_score must be at least"):
        config(pass_timeliness_score=d("0.400000"))
    with pytest.raises(ValueError, match="source observation paper_only must be True"):
        source(datetime(2026, 7, 6, 11, 30, tzinfo=UTC), paper_only=False)
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        score(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source observed_at must not be after generated_at"):
        score(
            signal(
                source_observations=(
                    source(datetime(2026, 7, 6, 12, 1, tzinfo=UTC)),
                ),
            ),
        )

    result = score()
    with pytest.raises(FrozenInstanceError):
        result.timeliness_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="report reason_codes must match"):
        module.ResearchInformationTimelinessScoreReport(
            **{**result.__dict__, "reason_codes": ("timeliness_pass",)},
        )
    with pytest.raises(ValueError, match="report derived validation failed"):
        module.ResearchInformationTimelinessScoreReport(
            **{**result.__dict__, "source_quorum_score": d("0.900000")},
        )
    with pytest.raises(
        ValueError,
        match="derived_validation_digest|report derived validation failed",
    ):
        module.ResearchInformationTimelinessScoreReport(
            **{**result.__dict__, "timeliness_score": d("0.900000")},
        )
    with pytest.raises(ValueError, match="report readonly must be True"):
        module.ResearchInformationTimelinessScoreReport(
            **{**result.__dict__, "readonly": False},
        )


def test_module_is_phase_one_readonly_paper_report_only_with_no_io_or_action_surface() -> None:
    path = Path("src/polymarket_alpha_lab/research_information_timeliness_score.py")
    source_text = path.read_text(encoding="utf-8")
    tree = ast.parse(source_text)

    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "open",
        "connect",
        "cancel",
        "replace",
        "create_order",
        "place_order",
        "submit_order",
        "trade",
        "auth",
        "login",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_call_names

    forbidden_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_ref",
        "private key",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position sizing",
        "database",
        "dsn",
        "table_name",
        "live trading",
        "network",
        "persist",
        "requests",
        "httpx",
        "socket",
        "subprocess",
    )
    lowered = source_text.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
