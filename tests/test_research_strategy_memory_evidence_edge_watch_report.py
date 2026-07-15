from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_memory_evidence_edge_watch_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_memory_evidence_edge_watch_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def load_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_MEMORY_EVIDENCE_EDGE_WATCH_REPORT_CONFIG_VERSION
        ),
        "memory_pass_floor": d("0.750000"),
        "memory_watch_floor": d("0.550000"),
        "evidence_pass_floor": d("0.800000"),
        "evidence_watch_floor": d("0.600000"),
        "edge_pass_floor": d("0.700000"),
        "edge_watch_floor": d("0.500000"),
        "stale_memory_pressure_watch": d("0.400000"),
        "stale_memory_pressure_block": d("0.750000"),
        "contradictory_evidence_pressure_watch": d("0.350000"),
        "contradictory_evidence_pressure_block": d("0.700000"),
        "unresolved_edge_pressure_watch": d("0.400000"),
        "unresolved_edge_pressure_block": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMemoryEvidenceEdgeWatchConfig(**values)


def watch_input(
    module: Any,
    memory_key: str = "memory-alpha",
    *,
    memory_reuse_score: Decimal = d("0.820000"),
    evidence_alignment_score: Decimal = d("0.860000"),
    edge_confidence_score: Decimal = d("0.780000"),
    stale_memory_pressure: Decimal = d("0.100000"),
    contradictory_evidence_pressure: Decimal = d("0.100000"),
    unresolved_edge_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyMemoryEvidenceEdgeWatchInput(
        memory_key=memory_key,
        memory_reuse_score=memory_reuse_score,
        evidence_alignment_score=evidence_alignment_score,
        edge_confidence_score=edge_confidence_score,
        stale_memory_pressure=stale_memory_pressure,
        contradictory_evidence_pressure=contradictory_evidence_pressure,
        unresolved_edge_pressure=unresolved_edge_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    module: Any,
    *rows: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_memory_evidence_edge_watch_report(
        rows,
        config=cfg(module) if config is None else config,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_public_dataclasses_decimal_bounds_signed_zero_and_context_are_strict() -> None:
    module = load_module()
    public_types = (
        module.ResearchStrategyMemoryEvidenceEdgeWatchConfig,
        module.ResearchStrategyMemoryEvidenceEdgeWatchInput,
        module.ResearchStrategyMemoryEvidenceEdgeWatchRow,
        module.ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount,
        module.ResearchStrategyMemoryEvidenceEdgeWatchReport,
    )

    for public_type in public_types:
        with pytest.raises(TypeError):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

    with pytest.raises(ValueError, match="signed zero"):
        watch_input(module, stale_memory_pressure=Decimal("-0.000000"))
    with pytest.raises(ValueError, match="memory_reuse_score"):
        watch_input(module, memory_reuse_score=d("1.0000004"))
    with pytest.raises(ValueError, match="stale_memory_pressure"):
        watch_input(module, stale_memory_pressure=d("-0.0000004"))
    with pytest.raises(ValueError, match="memory_watch_floor"):
        cfg(module, memory_watch_floor=d("-0.0000004"))

    edge = watch_input(
        module,
        "memory-context",
        memory_reuse_score=d("0.777777"),
        evidence_alignment_score=d("0.777777"),
        edge_confidence_score=d("0.777777"),
        stale_memory_pressure=d("0.777777"),
    )
    expected = report(module, edge).rows[0].edge_watch_readiness_score

    assert expected == d("0.622222")
    with localcontext(Context(prec=3)):
        constrained = report(module, edge).rows[0].edge_watch_readiness_score
    assert constrained == expected


def test_public_boundaries_revalidate_object_setattr_tampering() -> None:
    module = load_module()
    config = cfg(module)
    object.__setattr__(config, "memory_watch_floor", d("0.900000"))
    with pytest.raises(ValueError, match="memory_pass_floor"):
        report(module, watch_input(module), config=config)

    mutated_reason_input = watch_input(module)
    object.__setattr__(mutated_reason_input, "reason_codes", ["manual_review_needed"])
    with pytest.raises(ValueError, match="reason_codes"):
        report(module, mutated_reason_input)

    rounded_into_bounds_input = watch_input(module)
    object.__setattr__(
        rounded_into_bounds_input,
        "memory_reuse_score",
        d("1.0000004"),
    )
    with pytest.raises(ValueError, match="memory_reuse_score"):
        report(module, rounded_into_bounds_input)

    forged = report(
        module,
        watch_input(module, memory_reuse_score=d("0.700000")),
    )
    row = forged.rows[0]
    object.__setattr__(row, "status", "pass")
    object.__setattr__(forged, "pass_count", ONE)
    object.__setattr__(forged, "watch_count", ZERO)
    object.__setattr__(forged, "attention_count", ZERO)
    object.__setattr__(forged, "status", "pass")
    object.__setattr__(
        forged,
        "reason_codes",
        ("memory_evidence_edge_watch_pass", "memory_reuse_watch"),
    )
    object.__setattr__(
        forged,
        "reason_code_counts",
        (
            module.ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount(
                reason_code="memory_evidence_edge_watch_pass",
                count=ONE,
            ),
            module.ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount(
                reason_code="memory_reuse_watch",
                count=ONE,
            ),
        ),
    )
    object.__setattr__(forged, "public_digest", module._computed_report_digest(forged))

    with pytest.raises(ValueError, match="status"):
        module.research_strategy_memory_evidence_edge_watch_report_digest(forged)
    with pytest.raises(ValueError, match="status"):
        module.research_strategy_memory_evidence_edge_watch_report_payload(forged)

    mutated_count = report(module, watch_input(module))
    object.__setattr__(mutated_count.reason_code_counts[0], "count", Decimal("1"))
    object.__setattr__(
        mutated_count,
        "public_digest",
        module._computed_report_digest(mutated_count),
    )
    with pytest.raises(ValueError, match="count"):
        module.research_strategy_memory_evidence_edge_watch_report_payload(mutated_count)


def test_payload_schema_order_and_digest_are_canonical_sha256() -> None:
    module = load_module()
    edge_watch = report(module, watch_input(module))
    payload = module.research_strategy_memory_evidence_edge_watch_report_payload(edge_watch)
    payload_keys = (
        "generated_at",
        "config_version",
        "memory_edge_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "mean_memory_reuse_score",
        "mean_evidence_alignment_score",
        "mean_edge_confidence_score",
        "mean_edge_watch_readiness_score",
        "max_stale_memory_pressure",
        "max_contradictory_evidence_pressure",
        "max_unresolved_edge_pressure",
        "status",
        "public_digest",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
    )
    signed_payload_keys = tuple(key for key in payload_keys if key != "public_digest")

    assert tuple(payload) == payload_keys
    assert tuple(payload["rows"][0]) == (
        "aggregate_row_number",
        "aggregate_row_hash",
        "status",
        "memory_reuse_score",
        "evidence_alignment_score",
        "edge_confidence_score",
        "stale_memory_pressure",
        "contradictory_evidence_pressure",
        "unresolved_edge_pressure",
        "edge_watch_readiness_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["reason_code_counts"][0]) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["memory_edge_count"] == "1.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"

    signed_payload = {key: payload[key] for key in signed_payload_keys}
    encoded = json.dumps(
        signed_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    assert sha256(encoded.encode("utf-8")).hexdigest() == payload["public_digest"]


def test_complete_deterministic_tie_breaks_precede_public_hash() -> None:
    module = load_module()
    stale_pressure = watch_input(
        module,
        "memory-stale",
        memory_reuse_score=d("0.800000"),
        evidence_alignment_score=d("0.800000"),
        edge_confidence_score=d("0.800000"),
        stale_memory_pressure=d("0.400000"),
        contradictory_evidence_pressure=d("0.100000"),
        unresolved_edge_pressure=d("0.100000"),
    )
    contradictory_pressure = watch_input(
        module,
        "memory-contradictory",
        memory_reuse_score=d("0.800000"),
        evidence_alignment_score=d("0.800000"),
        edge_confidence_score=d("0.800000"),
        stale_memory_pressure=d("0.100000"),
        contradictory_evidence_pressure=d("0.400000"),
        unresolved_edge_pressure=d("0.100000"),
    )

    edge_watch = report(module, contradictory_pressure, stale_pressure)

    assert tuple(row.reason_codes for row in edge_watch.rows) == (
        ("stale_memory_pressure_watch",),
        ("contradictory_evidence_pressure_watch",),
    )


def test_report_aggregates_rows_redacts_keys_payload_and_digest() -> None:
    module = load_module()
    pass_item = watch_input(module, "private-memory-pass")
    watch_item = watch_input(
        module,
        "private-memory-watch",
        memory_reuse_score=d("0.700000"),
        evidence_alignment_score=d("0.650000"),
        edge_confidence_score=d("0.620000"),
        stale_memory_pressure=d("0.450000"),
        contradictory_evidence_pressure=d("0.360000"),
        unresolved_edge_pressure=d("0.500000"),
        reason_codes=("manual_review_needed",),
    )
    block_item = watch_input(
        module,
        "private-memory-block",
        memory_reuse_score=d("0.500000"),
        evidence_alignment_score=d("0.550000"),
        edge_confidence_score=d("0.450000"),
        stale_memory_pressure=d("0.800000"),
        contradictory_evidence_pressure=d("0.720000"),
        unresolved_edge_pressure=d("0.770000"),
    )

    first = report(module, watch_item, pass_item, block_item)
    second = report(module, block_item, watch_item, pass_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_MEMORY_EVIDENCE_EDGE_WATCH_REPORT_CONFIG_VERSION
    )
    assert first.memory_edge_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.attention_count == d("2.000000")
    assert first.status == "block"
    assert first.mean_memory_reuse_score == d("0.673333")
    assert first.mean_evidence_alignment_score == d("0.686667")
    assert first.mean_edge_confidence_score == d("0.616667")
    assert first.mean_edge_watch_readiness_score == d("0.565556")
    assert first.max_stale_memory_pressure == d("0.800000")
    assert first.max_contradictory_evidence_pressure == d("0.720000")
    assert first.max_unresolved_edge_pressure == d("0.770000")
    assert first.reason_codes == (
        "memory_evidence_edge_watch_block",
        "memory_reuse_block",
        "evidence_alignment_block",
        "edge_confidence_block",
        "stale_memory_pressure_block",
        "contradictory_evidence_pressure_block",
        "unresolved_edge_pressure_block",
        "memory_reuse_watch",
        "evidence_alignment_watch",
        "edge_confidence_watch",
        "stale_memory_pressure_watch",
        "contradictory_evidence_pressure_watch",
        "unresolved_edge_pressure_watch",
        "input_manual_review_needed",
    )
    assert first.reason_code_counts[0].reason_code == "memory_evidence_edge_watch_block"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.aggregate_row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.rows[0].edge_watch_readiness_score == d("0.340000")
    assert first.rows[1].edge_watch_readiness_score == d("0.556667")
    assert first.rows[2].edge_watch_readiness_score == d("0.800000")
    assert first.rows[0].reason_codes == (
        "memory_reuse_block",
        "evidence_alignment_block",
        "edge_confidence_block",
        "stale_memory_pressure_block",
        "contradictory_evidence_pressure_block",
        "unresolved_edge_pressure_block",
    )
    assert first.rows[2].reason_codes == ("memory_evidence_edge_watch_clear",)
    assert not hasattr(first.rows[0], "memory_key")

    payload = module.research_strategy_memory_evidence_edge_watch_report_payload(first)
    assert payload == module.research_strategy_memory_evidence_edge_watch_report_payload(
        second,
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["memory_edge_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["edge_watch_readiness_score"] == "0.340000"
    assert payload["public_digest"] == first.public_digest
    assert "memory_key" not in encoded
    assert "private-memory-block" not in encoded
    assert "private-memory-watch" not in encoded
    assert "private-memory-pass" not in encoded
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = module.research_strategy_memory_evidence_edge_watch_report_digest(first)
    assert digest == first.public_digest
    assert_digest(digest)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    module = load_module()

    edge_watch = report(module)

    assert edge_watch.status == "block"
    assert edge_watch.memory_edge_count == ZERO
    assert edge_watch.pass_count == ZERO
    assert edge_watch.watch_count == ZERO
    assert edge_watch.block_count == ZERO
    assert edge_watch.attention_count == ZERO
    assert edge_watch.mean_edge_watch_readiness_score == ZERO
    assert edge_watch.max_unresolved_edge_pressure == ZERO
    assert edge_watch.reason_codes == ("memory_evidence_edge_watch_no_inputs",)
    assert edge_watch.reason_code_counts == (
        module.ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount(
            reason_code="memory_evidence_edge_watch_no_inputs",
            count=ONE,
        ),
    )
    assert edge_watch.rows == ()


def test_decimal_datetime_digest_status_and_public_boundary_validation() -> None:
    module = load_module()

    edge_watch = report(module, watch_input(module))

    with pytest.raises(FrozenInstanceError):
        edge_watch.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        edge_watch.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="memory_reuse_score"):
        watch_input(module, memory_reuse_score=d("1.000001"))
    with pytest.raises(ValueError, match="memory_reuse_score"):
        watch_input(module, memory_reuse_score=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="memory_reuse_score"):
        watch_input(module, memory_reuse_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(module, watch_input(module), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            module,
            watch_input(module),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        watch_input(module, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(edge_watch.rows[0], status="blocked")
    with pytest.raises(ValueError, match="public_digest"):
        replace(edge_watch, public_digest="0" * 64)
    with pytest.raises(ValueError, match="unsafe"):
        watch_input(module, reason_codes=("source_url_seen",))


def test_public_payload_rejects_prohibited_surface_terms() -> None:
    module = load_module()
    unsafe_values = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
    )

    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe"):
            watch_input(module, reason_codes=(unsafe_value,))


def test_owned_module_has_no_runtime_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
    )

    assert all(term not in source for term in forbidden_terms)
