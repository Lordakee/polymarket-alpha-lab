from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_domain_team_memory_alpha_decay_report import (
    DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_STATUSES,
    ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
    ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount,
    ResearchStrategyDomainTeamMemoryAlphaDecayReport,
    ResearchStrategyDomainTeamMemoryAlphaDecayRow,
    ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot,
    build_research_strategy_domain_team_memory_alpha_decay_report,
    research_strategy_domain_team_memory_alpha_decay_report_digest,
    research_strategy_domain_team_memory_alpha_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_domain_team_memory_alpha_decay_report.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot(
    domain_ref: str = "domain-ref:finance.crypto?token=hidden",
    team_ref: str = "team-ref:alpha-team-wallet-private",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    last_alpha_signal_at: datetime = GENERATED_AT - timedelta(days=1),
    baseline_alpha_score: Decimal = d("0.100000"),
    current_alpha_score: Decimal = d("0.090000"),
    memory_reuse_score: Decimal = d("0.900000"),
    calibration_memory_score: Decimal = d("0.850000"),
    evidence_memory_score: Decimal = d("0.800000"),
    stale_memory_pressure_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = ("memory_snapshot_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot:
    return ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot(
        domain_ref=domain_ref,
        team_ref=team_ref,
        observed_at=observed_at,
        last_alpha_signal_at=last_alpha_signal_at,
        baseline_alpha_score=baseline_alpha_score,
        current_alpha_score=current_alpha_score,
        memory_reuse_score=memory_reuse_score,
        calibration_memory_score=calibration_memory_score,
        evidence_memory_score=evidence_memory_score,
        stale_memory_pressure_score=stale_memory_pressure_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object) -> ResearchStrategyDomainTeamMemoryAlphaDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_REPORT_CONFIG_VERSION
        ),
        "max_pass_alpha_signal_age_seconds": d("604800.000000"),
        "max_watch_alpha_signal_age_seconds": d("2592000.000000"),
        "max_pass_alpha_decay_ratio": d("0.200000"),
        "max_watch_alpha_decay_ratio": d("0.450000"),
        "min_pass_memory_reuse_score": d("0.750000"),
        "min_watch_memory_reuse_score": d("0.500000"),
        "min_pass_calibration_memory_score": d("0.750000"),
        "min_watch_calibration_memory_score": d("0.500000"),
        "min_pass_evidence_memory_score": d("0.700000"),
        "min_watch_evidence_memory_score": d("0.450000"),
        "max_pass_stale_memory_pressure_score": d("0.200000"),
        "max_watch_stale_memory_pressure_score": d("0.450000"),
        "alpha_retention_weight": d("0.300000"),
        "memory_reuse_weight": d("0.200000"),
        "calibration_memory_weight": d("0.200000"),
        "evidence_memory_weight": d("0.150000"),
        "signal_freshness_weight": d("0.100000"),
        "stale_memory_relief_weight": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategyDomainTeamMemoryAlphaDecayConfig(**values)


def report(
    *items: ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot,
    cfg: ResearchStrategyDomainTeamMemoryAlphaDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyDomainTeamMemoryAlphaDecayReport:
    return build_research_strategy_domain_team_memory_alpha_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def clone_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload))


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for key, item in value.items():
            values.append(key)
            values.extend(walk_payload(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload(item))
        return tuple(values)
    return (value,)


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"raw numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def assert_no_forbidden_public_payload_surface(payload: dict[str, Any]) -> None:
    encoded_values = " ".join(str(value).lower() for value in walk_payload(payload))
    forbidden_fragments = (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "live",
        "trading",
        "database",
        "network",
        "sizing",
        "recommend",
        "secret",
        "credential",
        "private",
    )
    assert not any(fragment in encoded_values for fragment in forbidden_fragments)


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"} or item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_score",
                "_seconds",
                "_weight",
                "_pressure",
            ),
        ):
            assert type(item) is Decimal


def test_scores_domain_team_memory_alpha_decay_pass_watch_and_block() -> None:
    summary = report(
        snapshot(
            "domain-ref:block?candidate=raw&market=secret",
            "team-ref:block?wallet=hidden",
            last_alpha_signal_at=GENERATED_AT - timedelta(days=45),
            current_alpha_score=d("0.040000"),
            memory_reuse_score=d("0.300000"),
            calibration_memory_score=d("0.400000"),
            evidence_memory_score=d("0.200000"),
            stale_memory_pressure_score=d("0.700000"),
            reason_codes=("memory_snapshot_ready", "calibration_memory_observed"),
        ),
        snapshot(
            "domain-ref:watch?slug=raw-market",
            "team-ref:watch",
            last_alpha_signal_at=GENERATED_AT - timedelta(days=14),
            current_alpha_score=d("0.070000"),
            memory_reuse_score=d("0.650000"),
            calibration_memory_score=d("0.600000"),
            evidence_memory_score=d("0.550000"),
            stale_memory_pressure_score=d("0.300000"),
            reason_codes=("evidence_memory_observed",),
        ),
        snapshot(
            "domain-ref:pass?source_url=https://example.invalid/private",
            "team-ref:pass?token=hidden",
            reason_codes=("memory_snapshot_ready",),
        ),
    )

    assert RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyDomainTeamMemoryAlphaDecayReport
    assert summary.status == "block"
    assert summary.snapshot_count == d("3.000000")
    assert summary.domain_count == d("3.000000")
    assert summary.team_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_memory_alpha_decay_score == d("0.605833")
    assert summary.min_memory_alpha_decay_score == d("0.305000")
    assert summary.max_alpha_decay_ratio == d("0.600000")
    assert summary.max_alpha_signal_age_seconds == d("3888000.000000")
    assert summary.min_memory_reuse_score == d("0.300000")
    assert summary.min_calibration_memory_score == d("0.400000")
    assert summary.min_evidence_memory_score == d("0.200000")
    assert summary.max_stale_memory_pressure_score == d("0.700000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked, watched, passed = summary.rows
    assert type(blocked) is ResearchStrategyDomainTeamMemoryAlphaDecayRow
    assert blocked.alpha_decay_ratio == d("0.600000")
    assert blocked.alpha_retention_score == d("0.400000")
    assert blocked.alpha_signal_age_seconds == d("3888000.000000")
    assert blocked.signal_freshness_score == d("0.000000")
    assert blocked.stale_memory_relief_score == d("0.300000")
    assert blocked.memory_alpha_decay_score == d("0.305000")
    assert blocked.reason_codes == (
        "memory_snapshot_ready",
        "calibration_memory_observed",
        "alpha_decay_block",
        "alpha_signal_age_block",
        "memory_reuse_block",
        "calibration_memory_block",
        "evidence_memory_block",
        "stale_memory_pressure_block",
        "memory_alpha_decay_score_block",
    )

    assert watched.alpha_decay_ratio == d("0.300000")
    assert watched.alpha_retention_score == d("0.700000")
    assert watched.alpha_signal_age_seconds == d("1209600.000000")
    assert watched.signal_freshness_score == d("0.533333")
    assert watched.stale_memory_relief_score == d("0.700000")
    assert watched.memory_alpha_decay_score == d("0.630833")
    assert watched.reason_codes == (
        "evidence_memory_observed",
        "alpha_decay_watch",
        "alpha_signal_age_watch",
        "memory_reuse_watch",
        "calibration_memory_watch",
        "evidence_memory_watch",
        "stale_memory_pressure_watch",
        "memory_alpha_decay_score_watch",
    )

    assert passed.alpha_decay_ratio == d("0.100000")
    assert passed.alpha_retention_score == d("0.900000")
    assert passed.memory_alpha_decay_score == d("0.881667")
    assert passed.reason_codes == (
        "memory_snapshot_ready",
        "memory_alpha_decay_pass",
    )

    counts = {item.reason_code: item for item in summary.reason_counts}
    assert counts["alpha_decay_block"] == ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount(
        reason_code="alpha_decay_block",
        count=d("1.000000"),
        row_ratio=d("0.333333"),
    )


def test_empty_report_is_report_only_block() -> None:
    summary = report()

    assert summary.status == "block"
    assert summary.snapshot_count == ZERO
    assert summary.domain_count == ZERO
    assert summary.team_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_memory_alpha_decay_score == ZERO
    assert summary.min_memory_alpha_decay_score == ZERO
    assert summary.max_alpha_decay_ratio == ZERO
    assert summary.max_alpha_signal_age_seconds == ZERO
    assert summary.min_memory_reuse_score == ZERO
    assert summary.min_calibration_memory_score == ZERO
    assert summary.min_evidence_memory_score == ZERO
    assert summary.max_stale_memory_pressure_score == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == ("memory_alpha_decay_no_snapshots",)
    assert summary.reason_counts == (
        ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount(
            reason_code="memory_alpha_decay_no_snapshots",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_public_payload_is_deterministic_digest_bound_and_leak_free() -> None:
    first = report(
        snapshot("domain-ref:one?candidate=raw", "team-ref:one?wallet=hidden"),
        snapshot("domain-ref:two?market=raw", "team-ref:two?token=hidden"),
    )
    second = report(
        snapshot("domain-ref:two?market=raw", "team-ref:two?token=hidden"),
        snapshot("domain-ref:one?candidate=raw", "team-ref:one?wallet=hidden"),
    )

    first_payload = research_strategy_domain_team_memory_alpha_decay_report_payload(first)
    second_payload = research_strategy_domain_team_memory_alpha_decay_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first.public_payload == first_payload
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_strategy_domain_team_memory_alpha_decay_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["snapshot_count"] == "2.000000"
    assert first_payload["rows"][0]["domain_ref_digest"].startswith("sha256:")
    assert first_payload["rows"][0]["team_ref_digest"].startswith("sha256:")
    assert first_payload["rows"][0]["memory_alpha_decay_score"] == "0.881667"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.881667"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["snapshot_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(tampered)


def test_rejects_signed_zero_and_raw_bounds_before_quantization() -> None:
    with pytest.raises(ValueError, match="current_alpha_score must not be signed zero"):
        snapshot(current_alpha_score=d("-0.000000"))
    with pytest.raises(ValueError, match="memory_reuse_score must be >= 0.000000"):
        snapshot(memory_reuse_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="memory_reuse_score must be <= 1.000000"):
        snapshot(memory_reuse_score=d("1.0000004"))
    with pytest.raises(
        ValueError,
        match="max_pass_alpha_signal_age_seconds must be > 0.000000",
    ):
        config(max_pass_alpha_signal_age_seconds=d("0.0000004"))


def test_public_payload_uses_exact_canonical_schemas_and_ranked_rows() -> None:
    payload = research_strategy_domain_team_memory_alpha_decay_report_payload(
        report(snapshot()),
    )

    assert set(payload) == {
        "generated_at",
        "config_version",
        "max_pass_alpha_signal_age_seconds",
        "max_watch_alpha_signal_age_seconds",
        "max_pass_alpha_decay_ratio",
        "max_watch_alpha_decay_ratio",
        "min_pass_memory_reuse_score",
        "min_watch_memory_reuse_score",
        "min_pass_calibration_memory_score",
        "min_watch_calibration_memory_score",
        "min_pass_evidence_memory_score",
        "min_watch_evidence_memory_score",
        "max_pass_stale_memory_pressure_score",
        "max_watch_stale_memory_pressure_score",
        "min_pass_memory_alpha_decay_score",
        "min_watch_memory_alpha_decay_score",
        "alpha_retention_weight",
        "memory_reuse_weight",
        "calibration_memory_weight",
        "evidence_memory_weight",
        "signal_freshness_weight",
        "stale_memory_relief_weight",
        "status",
        "snapshot_count",
        "domain_count",
        "team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_memory_alpha_decay_score",
        "min_memory_alpha_decay_score",
        "max_alpha_decay_ratio",
        "max_alpha_signal_age_seconds",
        "min_memory_reuse_score",
        "min_calibration_memory_score",
        "min_evidence_memory_score",
        "max_stale_memory_pressure_score",
        "rows",
        "reason_codes",
        "reason_counts",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["rows"][0]) == {
        "rank",
        "domain_ref_digest",
        "team_ref_digest",
        "observed_at",
        "alpha_signal_age_seconds",
        "baseline_alpha_score",
        "current_alpha_score",
        "alpha_decay_ratio",
        "alpha_retention_score",
        "memory_reuse_score",
        "calibration_memory_score",
        "evidence_memory_score",
        "stale_memory_pressure_score",
        "signal_freshness_score",
        "stale_memory_relief_score",
        "memory_alpha_decay_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["reason_counts"][0]) == {
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert payload["rows"][0]["rank"] == "1.000000"


def test_composite_score_thresholds_are_independent_from_memory_reuse_thresholds() -> None:
    composite_block = report(
        snapshot(),
        cfg=config(
            min_pass_memory_reuse_score=d("0.200000"),
            min_watch_memory_reuse_score=d("0.100000"),
            min_pass_memory_alpha_decay_score=d("0.950000"),
            min_watch_memory_alpha_decay_score=d("0.900000"),
        ),
    )
    assert composite_block.rows[0].status == "block"
    assert "memory_reuse_block" not in composite_block.rows[0].reason_codes
    assert "memory_alpha_decay_score_block" in composite_block.rows[0].reason_codes

    reuse_block = report(
        snapshot(memory_reuse_score=d("0.850000")),
        cfg=config(
            min_pass_memory_reuse_score=d("0.950000"),
            min_watch_memory_reuse_score=d("0.900000"),
            min_pass_memory_alpha_decay_score=d("0.200000"),
            min_watch_memory_alpha_decay_score=d("0.100000"),
        ),
    )
    assert reuse_block.rows[0].status == "block"
    assert "memory_reuse_block" in reuse_block.rows[0].reason_codes
    assert "memory_alpha_decay_score_block" not in reuse_block.rows[0].reason_codes


def test_complete_tie_break_and_rank_are_input_order_independent() -> None:
    older = snapshot(
        "domain-ref:same",
        "team-ref:same",
        observed_at=GENERATED_AT - timedelta(hours=2),
    )
    newer = snapshot(
        "domain-ref:same",
        "team-ref:same",
        observed_at=GENERATED_AT - timedelta(hours=1),
    )

    first = report(newer, older)
    second = report(older, newer)

    assert first == second
    assert tuple(row.observed_at for row in first.rows) == (
        older.observed_at,
        newer.observed_at,
    )
    assert tuple(row.rank for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
    )


def test_public_dataclasses_are_slotted_and_reject_subclasses() -> None:
    dataclass_types = (
        ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
        ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot,
        ResearchStrategyDomainTeamMemoryAlphaDecayRow,
        ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount,
        ResearchStrategyDomainTeamMemoryAlphaDecayReport,
    )

    for dataclass_type in dataclass_types:
        assert hasattr(dataclass_type, "__slots__")
        assert "__dict__" not in dataclass_type.__slots__
        with pytest.raises(TypeError, match="rejects subclassing"):
            type(f"{dataclass_type.__name__}Child", (dataclass_type,), {})


def test_builder_revalidates_tampered_snapshot_before_decimal_arithmetic() -> None:
    tampered = snapshot()
    object.__setattr__(tampered, "baseline_alpha_score", 0.1)

    with pytest.raises(ValueError, match="baseline_alpha_score must be exactly Decimal"):
        report(tampered)


def test_builder_revalidates_tampered_config_before_decimal_arithmetic() -> None:
    tampered = config()
    object.__setattr__(tampered, "max_watch_alpha_signal_age_seconds", 2592000.0)

    with pytest.raises(
        ValueError,
        match="max_watch_alpha_signal_age_seconds must be exactly Decimal",
    ):
        report(snapshot(), cfg=tampered)


def test_resigned_payload_rejects_noncanonical_reason_code_arrays() -> None:
    original = research_strategy_domain_team_memory_alpha_decay_report_payload(
        report(snapshot()),
    )
    duplicate = clone_payload(original)
    duplicate["rows"][0]["reason_codes"].append(
        duplicate["rows"][0]["reason_codes"][0],
    )

    with pytest.raises(ValueError, match="canonical report payload schema"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(duplicate),
        )


def test_digest_and_public_payload_revalidate_low_level_report_tampering() -> None:
    tampered = report(snapshot())
    object.__setattr__(tampered, "status", "block")

    with pytest.raises(ValueError, match="status must match rows"):
        research_strategy_domain_team_memory_alpha_decay_report_digest(tampered)
    with pytest.raises(ValueError, match="status must match rows"):
        tampered.public_payload


def test_resigned_payload_requires_exact_json_schema_and_canonical_scalars() -> None:
    original = research_strategy_domain_team_memory_alpha_decay_report_payload(
        report(snapshot()),
    )

    extra_report_field = clone_payload(original)
    extra_report_field["extra_field"] = "pass"
    with pytest.raises(ValueError, match="canonical report payload schema"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(extra_report_field),
        )

    missing_report_field = clone_payload(original)
    missing_report_field.pop("status")
    with pytest.raises(ValueError, match="canonical report payload schema"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(missing_report_field),
        )

    extra_row_field = clone_payload(original)
    extra_row_field["rows"][0]["extra_field"] = "pass"
    with pytest.raises(ValueError, match="canonical row payload schema"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(extra_row_field),
        )

    extra_reason_count_field = clone_payload(original)
    extra_reason_count_field["reason_counts"][0]["extra_field"] = "pass"
    with pytest.raises(ValueError, match="canonical reason_count payload schema"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(extra_reason_count_field),
        )

    noncanonical_decimal = clone_payload(original)
    noncanonical_decimal["snapshot_count"] = "1"
    with pytest.raises(ValueError, match="canonical Decimal string"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(noncanonical_decimal),
        )

    signed_zero = clone_payload(original)
    signed_zero["watch_count"] = "-0.000000"
    with pytest.raises(ValueError, match="canonical Decimal string"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(signed_zero),
        )

    tuple_array = clone_payload(original)
    tuple_array["reason_codes"] = tuple(tuple_array["reason_codes"])
    tuple_array["derived_validation_digest"] = canonical_digest(tuple_array)
    with pytest.raises(ValueError, match="JSON array"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(tuple_array)

    datetime_value = clone_payload(original)
    datetime_value["generated_at"] = GENERATED_AT
    with pytest.raises(ValueError, match="JSON"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(datetime_value)


def test_resigned_payload_rederives_row_status_reasons_and_score() -> None:
    original = research_strategy_domain_team_memory_alpha_decay_report_payload(
        report(snapshot()),
    )

    forged_score = clone_payload(original)
    forged_score["rows"][0]["memory_alpha_decay_score"] = "0.100000"
    forged_score["average_memory_alpha_decay_score"] = "0.100000"
    forged_score["min_memory_alpha_decay_score"] = "0.100000"
    with pytest.raises(ValueError, match="memory_alpha_decay_score must match row metrics"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(forged_score),
        )

    forged_status = clone_payload(original)
    forged_status["rows"][0]["status"] = "block"
    forged_status["status"] = "block"
    forged_status["pass_count"] = "0.000000"
    forged_status["block_count"] = "1.000000"
    with pytest.raises(ValueError, match="status must match row metrics"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(forged_status),
        )

    forged_reasons = clone_payload(original)
    forged_reasons["rows"][0]["reason_codes"] = ["alpha_decay_block"]
    with pytest.raises(ValueError, match="reason_codes must match row metrics"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(forged_reasons),
        )


def test_resigned_payload_rederives_counts_rank_order_and_aggregates() -> None:
    original = research_strategy_domain_team_memory_alpha_decay_report_payload(
        report(
            snapshot(
                "domain-ref:older",
                "team-ref:shared",
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
            snapshot(
                "domain-ref:newer",
                "team-ref:shared",
                observed_at=GENERATED_AT - timedelta(hours=1),
            ),
        ),
    )

    forged_count = clone_payload(original)
    forged_count["snapshot_count"] = "99.000000"
    with pytest.raises(ValueError, match="snapshot_count must match rows"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(forged_count),
        )

    forged_reason_count = clone_payload(original)
    forged_reason_count["reason_counts"][0]["count"] = "99.000000"
    with pytest.raises(ValueError, match="reason_counts must match rows"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(forged_reason_count),
        )

    forged_rank = clone_payload(original)
    forged_rank["rows"][0]["rank"] = "2.000000"
    with pytest.raises(ValueError, match="rank must match row order"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(forged_rank),
        )

    reordered = clone_payload(original)
    reordered["rows"].reverse()
    for index, row_payload in enumerate(reordered["rows"], start=1):
        row_payload["rank"] = f"{index}.000000"
    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        research_strategy_domain_team_memory_alpha_decay_report_payload(
            resign_payload(reordered),
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_snapshot = snapshot()
    sample_report = report(sample_snapshot)
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_counts[0]

    for item in (
        sample_config,
        sample_snapshot,
        sample_row,
        sample_reason_count,
        sample_report,
    ):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_decimal_public_fields(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        snapshot(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(snapshot(readonly=False))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("baseline_alpha_score", 0.1, "baseline_alpha_score must be exactly Decimal"),
        (
            "current_alpha_score",
            _DecimalSubclass("0.100000"),
            "current_alpha_score must be exactly Decimal",
        ),
        ("memory_reuse_score", d("1.000001"), "memory_reuse_score must be <= 1.000000"),
        ("calibration_memory_score", d("-0.000001"), "calibration_memory_score must be >= 0.000000"),
        ("stale_memory_pressure_score", Decimal("NaN"), "stale_memory_pressure_score must be finite"),
    ),
)
def test_snapshot_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        snapshot(**{field_name: bad_value})


def test_validation_rejects_bad_types_ordering_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(snapshot(), generated_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="last_alpha_signal_at must not be after generated_at"):
        report(snapshot(last_alpha_signal_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="max_pass_alpha_decay_ratio must not exceed watch"):
        config(max_pass_alpha_decay_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="min_watch_memory_reuse_score must not exceed pass"):
        config(min_watch_memory_reuse_score=d("0.800000"))
    with pytest.raises(ValueError, match="weights must sum to one"):
        config(stale_memory_relief_weight=d("0.040000"))

    valid_report = report(snapshot())
    values = {field.name: getattr(valid_report, field.name) for field in fields(valid_report)}
    values["derived_validation_digest"] = "f" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        ResearchStrategyDomainTeamMemoryAlphaDecayReport(**values)


def test_module_scope_has_no_db_network_wallet_order_or_live_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "send",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
