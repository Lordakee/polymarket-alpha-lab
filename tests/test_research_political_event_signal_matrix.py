from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_political_event_signal_matrix import (
    DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
    PoliticalEventSignalMatrixConfig,
    PoliticalEventSignalMatrixObservation,
    PoliticalEventSignalMatrixReasonCodeCount,
    PoliticalEventSignalMatrixReport,
    PoliticalEventSignalMatrixRow,
    build_research_political_event_signal_matrix,
    research_political_event_signal_matrix_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> PoliticalEventSignalMatrixConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
        "fresh_signal_age_seconds": d("86400.000000"),
        "stale_signal_age_seconds": d("604800.000000"),
        "min_independent_family_count": d("2.000000"),
        "watch_priority_score": d("0.450000"),
        "pass_priority_score": d("0.750000"),
        "block_counter_signal_count": d("2.000000"),
        "confidence_weight": d("0.400000"),
        "coverage_weight": d("0.350000"),
        "independence_weight": d("0.250000"),
        "counter_signal_penalty": d("0.350000"),
        "stale_signal_penalty": d("0.250000"),
    }
    values.update(overrides)
    return PoliticalEventSignalMatrixConfig(**values)


def observation(
    index: int,
    *,
    event_key: str = "event-alpha",
    signal_key: str | None = None,
    family_key: str = "polling-family",
    signal_type: str = "polling",
    signal_stance: str = "supporting",
    confidence_score: Decimal = d("0.900000"),
    observed_at: datetime | None = None,
) -> PoliticalEventSignalMatrixObservation:
    return PoliticalEventSignalMatrixObservation(
        event_key=event_key,
        signal_key=signal_key if signal_key is not None else f"signal-{index:03d}",
        family_key=family_key,
        signal_type=signal_type,
        signal_stance=signal_stance,
        confidence_score=confidence_score,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=2)
        ),
    )


def report(
    inputs: tuple[PoliticalEventSignalMatrixObservation, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: PoliticalEventSignalMatrixConfig | None = None,
) -> PoliticalEventSignalMatrixReport:
    return build_research_political_event_signal_matrix(
        inputs,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_polling_schedule_and_institution_signals_pass() -> None:
    signal_report = report(
        (
            observation(3, family_key="institution-family", signal_type="institution"),
            observation(1, family_key="polling-family", signal_type="polling"),
            observation(2, family_key="calendar-family", signal_type="schedule"),
        ),
    )

    assert type(signal_report) is PoliticalEventSignalMatrixReport
    assert signal_report.generated_at == GENERATED_AT
    assert signal_report.config_version == DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION
    assert signal_report.status == "pass"
    assert signal_report.event_count == d("1.000000")
    assert signal_report.input_count == d("3.000000")
    assert signal_report.pass_count == d("1.000000")
    assert signal_report.watch_count == d("0.000000")
    assert signal_report.block_count == d("0.000000")
    assert signal_report.average_priority_score == d("1.000000")
    assert signal_report.max_priority_score == d("1.000000")
    assert signal_report.reason_codes == ("political_event_signal_pass",)
    assert signal_report.reason_code_counts == (
        PoliticalEventSignalMatrixReasonCodeCount(
            reason_code="political_event_signal_pass",
            count=d("1.000000"),
        ),
    )
    assert signal_report.paper_only is True
    assert signal_report.report_only is True
    assert signal_report.readonly is True
    assert len(signal_report.derived_validation_digest) == 64

    row = signal_report.rows[0]
    assert type(row) is PoliticalEventSignalMatrixRow
    assert row.event_key == "event-alpha"
    assert row.observation_count == d("3.000000")
    assert row.family_count == d("3.000000")
    assert row.polling_count == d("1.000000")
    assert row.schedule_count == d("1.000000")
    assert row.institution_count == d("1.000000")
    assert row.counter_signal_count == d("0.000000")
    assert row.stale_signal_count == d("0.000000")
    assert row.average_confidence_score == d("0.900000")
    assert row.coverage_score == d("1.000000")
    assert row.independence_score == d("1.000000")
    assert row.counter_penalty_score == d("0.000000")
    assert row.stale_penalty_score == d("0.000000")
    assert row.priority_score == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "polling_signal_present",
        "schedule_signal_present",
        "institution_signal_present",
        "family_independence_met",
        "fresh_signal_context",
        "no_counter_signal",
        "political_event_signal_pass",
    )


def test_single_polling_signal_returns_watch() -> None:
    signal_report = report((observation(1),))
    row = signal_report.rows[0]

    assert signal_report.status == "watch"
    assert signal_report.watch_count == d("1.000000")
    assert signal_report.average_priority_score == d("0.601667")
    assert row.status == "watch"
    assert row.coverage_score == d("0.333333")
    assert row.independence_score == d("0.500000")
    assert row.reason_codes == (
        "polling_signal_present",
        "schedule_signal_missing",
        "institution_signal_missing",
        "family_independence_low",
        "fresh_signal_context",
        "no_counter_signal",
        "political_event_signal_watch",
    )


def test_counter_signals_and_stale_context_block() -> None:
    signal_report = report(
        (
            observation(1, family_key="polling-family", signal_type="polling"),
            observation(2, family_key="calendar-family", signal_type="schedule"),
            observation(3, family_key="institution-family", signal_type="institution"),
            observation(
                4,
                family_key="counter-family-a",
                signal_type="polling",
                signal_stance="counter",
                observed_at=GENERATED_AT - timedelta(days=8),
            ),
            observation(
                5,
                family_key="counter-family-b",
                signal_type="institution",
                signal_stance="counter",
            ),
        ),
    )
    row = signal_report.rows[0]

    assert signal_report.status == "block"
    assert signal_report.block_count == d("1.000000")
    assert row.counter_signal_count == d("2.000000")
    assert row.stale_signal_count == d("1.000000")
    assert row.counter_penalty_score == d("0.700000")
    assert row.stale_penalty_score == d("0.250000")
    assert row.priority_score == d("0.000000")
    assert row.status == "block"
    assert "counter_signal_hard_block" in row.reason_codes
    assert "stale_signal_context" in row.reason_codes
    assert "political_event_signal_block" in row.reason_codes


def test_empty_input_is_report_only_block() -> None:
    signal_report = report(())

    assert signal_report.status == "block"
    assert signal_report.event_count == d("0.000000")
    assert signal_report.input_count == d("0.000000")
    assert signal_report.rows == ()
    assert signal_report.reason_codes == ("empty_input",)
    assert signal_report.reason_code_counts == (
        PoliticalEventSignalMatrixReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
        ),
    )
    assert signal_report.paper_only is True
    assert signal_report.report_only is True
    assert signal_report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    assert is_dataclass(PoliticalEventSignalMatrixConfig)
    assert is_dataclass(PoliticalEventSignalMatrixObservation)
    assert is_dataclass(PoliticalEventSignalMatrixRow)
    assert is_dataclass(PoliticalEventSignalMatrixReport)

    with pytest.raises(ValueError, match="config_version"):
        PoliticalEventSignalMatrixConfig(config_version=_StringSubclass("version-a"))
    with pytest.raises(ValueError, match="watch_priority_score"):
        config(watch_priority_score=0.45)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="counter_signal_penalty"):
        config(counter_signal_penalty=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="confidence_score"):
        observation(1, confidence_score=d("NaN"))
    with pytest.raises(ValueError, match="confidence_score"):
        observation(1, confidence_score=d("0.90"))
    with pytest.raises(ValueError, match="confidence_score"):
        observation(1, confidence_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    signal_report = report((observation(1),))
    with pytest.raises(FrozenInstanceError):
        signal_report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        signal_report.rows[0].status = "block"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("event_key", "candidate-abc"),
        ("event_key", "market-abc"),
        ("event_key", "question-abc"),
        ("signal_key", "source_ref"),
        ("family_key", "source_url"),
        ("family_key", "source text copied from notes"),
        ("family_key", "wallet-auth-token"),
        ("family_key", "order-trade-position"),
        ("family_key", "buy-sell-recommendation"),
    ),
)
def test_public_leak_rejection_for_inputs(field_name: str, field_value: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        observation(1, **{field_name: field_value})


def test_public_payload_serializes_decimals_and_rejects_leaks() -> None:
    signal_report = report(
        (
            observation(2, family_key="calendar-family", signal_type="schedule"),
            observation(1, family_key="polling-family", signal_type="polling"),
        ),
    )

    payload = research_political_event_signal_matrix_payload(signal_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert signal_report.payload == payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "watch"
    assert payload["event_count"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == str(signal_report.rows[0].priority_score)
    assert payload["derived_validation_digest"] == signal_report.derived_validation_digest
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert "source_ref" not in encoded.lower()
    assert "source_url" not in encoded.lower()
    assert "source_text" not in encoded.lower()
    assert "market_slug" not in encoded.lower()
    assert "question" not in encoded.lower()
    assert "dsn" not in encoded.lower()
    assert "table" not in encoded.lower()
    assert "token" not in encoded.lower()
    _assert_public_payload_has_no_blocked_terms(payload)

    tampered = dict(payload)
    tampered["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        research_political_event_signal_matrix_payload(tampered)

    tampered = dict(payload)
    tampered["reason_codes"] = ["buy_signal"]
    with pytest.raises(ValueError, match="unsafe public"):
        research_political_event_signal_matrix_payload(tampered)


def test_report_and_digest_are_deterministic() -> None:
    rows = (
        observation(
            1,
            event_key="event-c",
            family_key="counter-family-a",
            signal_stance="counter",
        ),
        observation(
            2,
            event_key="event-c",
            family_key="counter-family-b",
            signal_stance="counter",
        ),
        observation(3, event_key="event-a", family_key="polling-family", signal_type="polling"),
        observation(4, event_key="event-a", family_key="calendar-family", signal_type="schedule"),
        observation(5, event_key="event-a", family_key="institution-family", signal_type="institution"),
        observation(6, event_key="event-b", family_key="polling-family", signal_type="polling"),
    )

    report_a = report(rows)
    report_b = report(tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_political_event_signal_matrix_payload(
        report_a,
    ) == research_political_event_signal_matrix_payload(report_b)
    assert tuple(row.event_key for row in report_a.rows) == (
        "event-c",
        "event-b",
        "event-a",
    )


def test_report_digest_rejects_tampering_and_payload_mismatch() -> None:
    signal_report = report((observation(1),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(signal_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="event_count"):
        replace(signal_report, event_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(signal_report, rows=())

    payload = research_political_event_signal_matrix_payload(signal_report)
    tampered = dict(payload)
    tampered["event_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_political_event_signal_matrix_payload(tampered)


def test_module_scope_excludes_network_storage_and_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_political_event_signal_matrix",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION",
        "PoliticalEventSignalMatrixConfig",
        "PoliticalEventSignalMatrixObservation",
        "PoliticalEventSignalMatrixReasonCodeCount",
        "PoliticalEventSignalMatrixReport",
        "PoliticalEventSignalMatrixRow",
        "build_research_political_event_signal_matrix",
        "research_political_event_signal_matrix_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
        "sqlite",
        "web3",
        "eth_account",
        "ccxt",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for key, item in value.items():
            values.append(key)
            values.extend(_walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return tuple(values)
    return (value,)


def _assert_public_payload_has_no_blocked_terms(payload: dict[str, object]) -> None:
    rendered = repr(payload).casefold()
    for token in (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "blocked",
    ):
        assert token not in rendered
