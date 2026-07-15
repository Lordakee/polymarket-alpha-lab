from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
import hashlib
import inspect
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_strategy_event_cluster_signal_memory_score_report as api
from polymarket_alpha_lab.research_strategy_event_cluster_signal_memory_score_report import (
    ResearchStrategyEventClusterSignalMemoryObservation,
    ResearchStrategyEventClusterSignalMemoryPublicPayloadItem,
    ResearchStrategyEventClusterSignalMemoryReasonCodeCount,
    ResearchStrategyEventClusterSignalMemoryScoreConfig,
    ResearchStrategyEventClusterSignalMemoryScoreReport,
    ResearchStrategyEventClusterSignalMemoryScoreRow,
    build_research_strategy_event_cluster_signal_memory_score_report,
    research_strategy_event_cluster_signal_memory_score_report_payload,
)


NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
CLUSTER_A = "a" * 64
CLUSTER_B = "b" * 64
SIGNAL_A = "c" * 64
SIGNAL_B = "d" * 64
SIGNAL_C = "e" * 64


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    cluster_fingerprint: str = CLUSTER_A,
    signal_fingerprint: str = SIGNAL_A,
    signal_strength: Decimal = d("0.800000"),
    observed_at: datetime | None = None,
    supports_memory: bool = True,
) -> ResearchStrategyEventClusterSignalMemoryObservation:
    return ResearchStrategyEventClusterSignalMemoryObservation(
        cluster_fingerprint=cluster_fingerprint,
        signal_fingerprint=signal_fingerprint,
        observed_at=observed_at or NOW - timedelta(minutes=30),
        signal_strength=signal_strength,
        supports_memory=supports_memory,
    )


def report(
    observations: tuple[ResearchStrategyEventClusterSignalMemoryObservation, ...],
    *,
    config: ResearchStrategyEventClusterSignalMemoryScoreConfig | None = None,
    public_payload: tuple[ResearchStrategyEventClusterSignalMemoryPublicPayloadItem, ...] = (),
) -> ResearchStrategyEventClusterSignalMemoryScoreReport:
    return build_research_strategy_event_cluster_signal_memory_score_report(
        observations,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_empty_input_returns_block_report_only_snapshot() -> None:
    memory_report = report(())

    assert type(memory_report) is ResearchStrategyEventClusterSignalMemoryScoreReport
    assert memory_report.generated_at == NOW
    assert memory_report.status == "block"
    assert memory_report.cluster_count == d("0.000000")
    assert memory_report.signal_count == d("0.000000")
    assert memory_report.pass_count == d("0.000000")
    assert memory_report.watch_count == d("0.000000")
    assert memory_report.block_count == d("0.000000")
    assert memory_report.average_memory_score == d("0.000000")
    assert memory_report.rows == ()
    assert memory_report.reason_codes == ("empty_signal_memory",)
    assert memory_report.reason_code_counts == (
        ResearchStrategyEventClusterSignalMemoryReasonCodeCount(
            reason_code="empty_signal_memory",
            count=d("1.000000"),
        ),
    )
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True


def test_distinct_fresh_supportive_signals_pass_with_deterministic_score() -> None:
    memory_report = report(
        (
            observation(signal_fingerprint=SIGNAL_B, signal_strength=d("0.700000")),
            observation(signal_fingerprint=SIGNAL_A, signal_strength=d("0.800000")),
        ),
    )

    row = memory_report.rows[0]
    assert memory_report.status == "pass"
    assert memory_report.cluster_count == d("1.000000")
    assert memory_report.signal_count == d("2.000000")
    assert memory_report.pass_count == d("1.000000")
    assert memory_report.average_memory_score == d("0.891667")
    assert row.cluster_fingerprint == CLUSTER_A
    assert row.signal_count == d("2.000000")
    assert row.unique_signal_count == d("2.000000")
    assert row.duplicate_signal_count == d("0.000000")
    assert row.latest_signal_age_seconds == d("1800.000000")
    assert row.recency_memory_score == d("0.979167")
    assert row.average_signal_strength == d("0.750000")
    assert row.unique_signal_ratio == d("1.000000")
    assert row.duplicate_signal_penalty == d("0.000000")
    assert row.memory_score == d("0.891667")
    assert row.status == "pass"
    assert row.reason_codes == (
        "fresh_signal_memory",
        "unique_signal_memory",
        "signal_memory_pass",
    )


def test_duplicate_signals_are_penalized_and_watch() -> None:
    memory_report = report(
        (
            observation(signal_fingerprint=SIGNAL_A, signal_strength=d("0.700000")),
            observation(signal_fingerprint=SIGNAL_A, signal_strength=d("0.700000")),
        ),
    )

    row = memory_report.rows[0]
    assert memory_report.status == "watch"
    assert row.unique_signal_count == d("1.000000")
    assert row.duplicate_signal_count == d("1.000000")
    assert row.unique_signal_ratio == d("0.500000")
    assert row.duplicate_signal_penalty == d("0.150000")
    assert row.memory_score == d("0.621667")
    assert row.status == "watch"
    assert row.reason_codes == (
        "fresh_signal_memory",
        "insufficient_unique_signals",
        "duplicate_signal_memory",
        "signal_memory_watch",
    )


def test_stale_weak_signal_blocks_cluster_memory_with_block_status() -> None:
    memory_report = report(
        (
            observation(
                cluster_fingerprint=CLUSTER_B,
                signal_fingerprint=SIGNAL_C,
                signal_strength=d("0.100000"),
                observed_at=NOW - timedelta(days=2),
            ),
        ),
    )

    row = memory_report.rows[0]
    assert memory_report.status == "block"
    assert row.latest_signal_age_seconds == d("172800.000000")
    assert row.recency_memory_score == d("0.000000")
    assert row.memory_score == d("0.240000")
    assert row.status == "block"
    assert row.reason_codes == (
        "stale_signal_memory",
        "insufficient_signal_count",
        "insufficient_unique_signals",
        "low_signal_memory_score",
        "signal_memory_block",
    )


def test_payload_is_deterministic_decimal_string_json_with_digest_validation() -> None:
    memory_report = report(
        (
            observation(signal_fingerprint=SIGNAL_B, signal_strength=d("0.700000")),
            observation(signal_fingerprint=SIGNAL_A, signal_strength=d("0.800000")),
        ),
        public_payload=(
            ResearchStrategyEventClusterSignalMemoryPublicPayloadItem(
                "safe_context",
                "research memo",
            ),
        ),
    )

    payload = research_strategy_event_cluster_signal_memory_score_report_payload(memory_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == memory_report.payload
    assert payload["cluster_count"] == "1.000000"
    assert payload["rows"][0]["memory_score"] == "0.891667"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["derived_validation_digest"] == memory_report.derived_validation_digest
    assert len(memory_report.derived_validation_digest) == 64
    assert encoded == json.dumps(memory_report.payload, sort_keys=True)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(payload))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(memory_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            memory_report,
            public_payload=(
                ResearchStrategyEventClusterSignalMemoryPublicPayloadItem(
                    "safe_context",
                    "changed memo",
                ),
            ),
        )


def test_validation_rejects_bad_types_flags_times_statuses_and_subclasses() -> None:
    with pytest.raises(ValueError, match="pass_memory_score"):
        ResearchStrategyEventClusterSignalMemoryScoreConfig(
            pass_memory_score=0.7,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyEventClusterSignalMemoryScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="cluster_fingerprint"):
        observation(cluster_fingerprint="raw-cluster")
    with pytest.raises(ValueError, match="signal_strength"):
        observation(signal_strength=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(observed_at=NOW + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="supports_memory"):
        replace(observation(), supports_memory=1)  # type: ignore[arg-type]

    memory_report = report((observation(signal_fingerprint=SIGNAL_A),))
    with pytest.raises(FrozenInstanceError):
        memory_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(memory_report.rows[0], status="review")
    with pytest.raises(ValueError, match="status"):
        replace(memory_report, status="review")
    with pytest.raises(TypeError):

        class BadReport(ResearchStrategyEventClusterSignalMemoryScoreReport):
            pass


def test_public_dataclasses_are_frozen_slotted_and_exact() -> None:
    memory_report = report((observation(signal_fingerprint=SIGNAL_A),))
    instances = (
        ResearchStrategyEventClusterSignalMemoryScoreConfig(),
        observation(),
        ResearchStrategyEventClusterSignalMemoryPublicPayloadItem(
            "safe_context",
            "research memo",
        ),
        memory_report.rows[0],
        memory_report.reason_code_counts[0],
        memory_report,
    )

    for item in instances:
        assert type(item).__module__ == api.__name__
        assert not hasattr(item, "__dict__")
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert inspect.isclass(type(item))


def test_decimal_arithmetic_uses_fixed_context_and_canonicalizes_signed_zero() -> None:
    inputs = (
        observation(
            signal_fingerprint=SIGNAL_A,
            signal_strength=Decimal("-0.000000"),
            observed_at=NOW,
        ),
        observation(
            signal_fingerprint=SIGNAL_B,
            signal_strength=Decimal("0.700000"),
            observed_at=NOW - timedelta(seconds=1),
        ),
    )

    with localcontext(Context(prec=6, rounding=ROUND_DOWN)):
        constrained = report(inputs)
    unconstrained = report(inputs)

    assert constrained == unconstrained
    assert str(inputs[0].signal_strength) == "0.000000"
    assert str(constrained.rows[0].average_signal_strength) == "0.350000"
    assert str(constrained.rows[0].latest_signal_age_seconds) == "0.000000"


def test_payload_revalidates_low_level_report_tampering() -> None:
    memory_report = report(
        (
            observation(signal_fingerprint=SIGNAL_A, signal_strength=d("0.700000")),
            observation(signal_fingerprint=SIGNAL_B, signal_strength=d("0.800000")),
        ),
    )

    object.__setattr__(memory_report.rows[0], "memory_score", d("0.100000"))

    with pytest.raises(ValueError, match="memory_score|derived_validation_digest"):
        research_strategy_event_cluster_signal_memory_score_report_payload(
            memory_report,
        )


def test_payload_revalidates_canonical_and_resigned_mapping_schemas() -> None:
    memory_report = report(
        (
            observation(signal_fingerprint=SIGNAL_A, signal_strength=d("0.700000")),
            observation(signal_fingerprint=SIGNAL_B, signal_strength=d("0.800000")),
        ),
    )
    payload = research_strategy_event_cluster_signal_memory_score_report_payload(
        memory_report,
    )

    assert research_strategy_event_cluster_signal_memory_score_report_payload(payload) == payload

    extended = dict(payload)
    extended["extra_safe_field"] = "research memo"
    extended["derived_validation_digest"] = _resign_payload(extended)
    with pytest.raises(ValueError, match="schema"):
        research_strategy_event_cluster_signal_memory_score_report_payload(extended)

    drifted = json.loads(json.dumps(payload))
    drifted["pass_count"] = "0.000000"
    drifted["derived_validation_digest"] = _resign_payload(drifted)
    with pytest.raises(ValueError, match="pass_count|derived_validation_digest"):
        research_strategy_event_cluster_signal_memory_score_report_payload(drifted)


def test_public_payload_and_public_surfaces_do_not_expose_unsafe_identifiers() -> None:
    unsafe_terms = (
        "candidate",
        "market",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "network",
        "database",
        "live",
    )
    for key in ("candidate_id", "market_id", "market_slug", "source_url", "dsn", "token"):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyEventClusterSignalMemoryPublicPayloadItem(key, "safe memo")
    for value in (
        "candidate-123",
        "market_slug_alpha",
        "Will this question resolve?",
        "https://example.invalid/source",
        "wallet detail",
        "order detail",
        "trade detail",
        "position sizing",
        "recommendation detail",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyEventClusterSignalMemoryPublicPayloadItem("safe_context", value)

    memory_report = report(
        (
            observation(signal_fingerprint=SIGNAL_B, signal_strength=d("0.700000")),
            observation(signal_fingerprint=SIGNAL_A, signal_strength=d("0.800000")),
        ),
    )
    payload_text = json.dumps(memory_report.payload, sort_keys=True).lower()
    for forbidden_fragment in (
        "candidate-123",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "wallet",
        "order",
        "trade",
        "recommendation",
    ):
        assert forbidden_fragment not in payload_text

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchStrategyEventClusterSignalMemoryScoreConfig,
        ResearchStrategyEventClusterSignalMemoryObservation,
        ResearchStrategyEventClusterSignalMemoryPublicPayloadItem,
        ResearchStrategyEventClusterSignalMemoryScoreRow,
        ResearchStrategyEventClusterSignalMemoryReasonCodeCount,
        ResearchStrategyEventClusterSignalMemoryScoreReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_event_cluster_signal_memory_score_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    for forbidden_term in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
    ):
        assert forbidden_term not in source


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _resign_payload(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
