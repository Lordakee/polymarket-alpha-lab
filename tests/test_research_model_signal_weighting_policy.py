from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_model_signal_weighting_policy import (
    ResearchModelSignalWeightingConfig,
    ResearchModelSignalWeightingInputRow,
    ResearchModelSignalWeightingReasonCodeCount,
    ResearchModelSignalWeightingReport,
    ResearchModelSignalWeightingRow,
    build_research_model_signal_weighting_policy_report,
    research_model_signal_weighting_policy_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedSignalShape:
    signal_name: str
    raw_signal_id: str | None
    raw_source: str | None
    raw_market_id: str | None
    raw_weight: Decimal
    quality_score: Decimal
    confidence_score: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    enabled: bool = True
    hard_block: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchModelSignalWeightingConfig:
    values = {
        "config_version": "research-model-signal-weighting-policy-v0",
        "pass_min_active_signal_count": d("3"),
        "watch_min_active_signal_count": d("2"),
        "max_single_signal_weight_pass": d("0.600000"),
        "max_single_signal_weight_watch": d("0.800000"),
        "min_human_research_weight_pass": d("0.150000"),
        "min_human_research_weight_watch": d("0.050000"),
        "min_component_watch_score": d("0.250000"),
        "conflict_watch_threshold": d("0.400000"),
        "conflict_block_threshold": d("0.800000"),
    }
    values.update(overrides)
    return ResearchModelSignalWeightingConfig(**values)


def signal(
    signal_name: str,
    *,
    raw_weight: Decimal = d("0.200000"),
    quality_score: Decimal = d("1.000000"),
    confidence_score: Decimal = d("1.000000"),
    freshness_score: Decimal = d("1.000000"),
    conflict_score: Decimal = d("0.000000"),
    enabled: bool = True,
    hard_block: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchModelSignalWeightingInputRow:
    safe_name = signal_name.replace("-", "_")
    return ResearchModelSignalWeightingInputRow(
        signal_name=signal_name,
        raw_signal_id=f"raw-signal-{safe_name}",
        raw_source=f"private-source-{safe_name}",
        raw_market_id=f"market-secret-{safe_name}",
        raw_weight=raw_weight,
        quality_score=quality_score,
        confidence_score=confidence_score,
        freshness_score=freshness_score,
        conflict_score=conflict_score,
        enabled=enabled,
        hard_block=hard_block,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchModelSignalWeightingConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchModelSignalWeightingReport:
    return build_research_model_signal_weighting_policy_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_policy() -> None:
    weighting_report = report(())

    assert type(weighting_report) is ResearchModelSignalWeightingReport
    assert weighting_report.generated_at == GENERATED_AT
    assert weighting_report.config_version == "research-model-signal-weighting-policy-v0"
    assert weighting_report.status == "block"
    assert weighting_report.signal_count == d("0")
    assert weighting_report.active_signal_count == d("0")
    assert weighting_report.watch_signal_count == d("0")
    assert weighting_report.block_signal_count == d("0")
    assert weighting_report.zero_weight_signal_count == d("0")
    assert weighting_report.total_raw_weight == d("0.000000")
    assert weighting_report.total_adjusted_weight == d("0.000000")
    assert weighting_report.max_normalized_weight == d("0.000000")
    assert weighting_report.human_research_normalized_weight == d("0.000000")
    assert weighting_report.rows == ()
    assert weighting_report.reason_codes == (
        "human_research_weight_block",
        "no_signal_weights",
        "signal_weight_policy_block",
        "too_few_active_signals_block",
    )
    assert weighting_report.reason_code_counts == (
        ResearchModelSignalWeightingReasonCodeCount(
            reason_code="human_research_weight_block",
            count=d("1"),
        ),
        ResearchModelSignalWeightingReasonCodeCount(
            reason_code="no_signal_weights",
            count=d("1"),
        ),
        ResearchModelSignalWeightingReasonCodeCount(
            reason_code="signal_weight_policy_block",
            count=d("1"),
        ),
        ResearchModelSignalWeightingReasonCodeCount(
            reason_code="too_few_active_signals_block",
            count=d("1"),
        ),
    )
    assert weighting_report.paper_only is True
    assert weighting_report.report_only is True
    assert weighting_report.readonly is True


def test_balanced_naive_book_llm_manual_and_memory_signals_pass() -> None:
    weighting_report = report(
        (
            signal(
                "team-memory",
                raw_weight=d("0.200000"),
                quality_score=d("0.900000"),
                confidence_score=d("0.850000"),
                freshness_score=d("0.900000"),
                conflict_score=d("0.050000"),
            ),
            signal(
                "naive",
                raw_weight=d("0.100000"),
                quality_score=d("0.900000"),
                confidence_score=d("0.800000"),
                freshness_score=d("0.900000"),
                conflict_score=d("0.050000"),
            ),
            signal(
                "manual-research",
                raw_weight=d("0.250000"),
                quality_score=d("0.950000"),
                confidence_score=d("0.900000"),
                freshness_score=d("0.950000"),
                conflict_score=d("0.050000"),
                reason_codes=("human_reviewed",),
            ),
            signal(
                "llm",
                raw_weight=d("0.250000"),
                quality_score=d("0.850000"),
                confidence_score=d("0.800000"),
                freshness_score=d("0.900000"),
                conflict_score=d("0.100000"),
            ),
            signal(
                "book_imbalance",
                raw_weight=d("0.200000"),
                quality_score=d("0.800000"),
                confidence_score=d("0.700000"),
                freshness_score=d("0.800000"),
                conflict_score=d("0.100000"),
            ),
        ),
    )

    assert weighting_report.status == "pass"
    assert weighting_report.signal_count == d("5")
    assert weighting_report.active_signal_count == d("5")
    assert weighting_report.watch_signal_count == d("0")
    assert weighting_report.block_signal_count == d("0")
    assert weighting_report.zero_weight_signal_count == d("0")
    assert weighting_report.total_raw_weight == d("1.000000")
    assert weighting_report.total_adjusted_weight == d("0.603624")
    assert weighting_report.max_normalized_weight == d("0.319585")
    assert weighting_report.human_research_normalized_weight == d("0.536301")
    assert weighting_report.reason_codes == (
        "balanced_signal_weights",
        "signal_weight_policy_pass",
    )

    rows = weighting_report.rows
    assert tuple(row.signal_name for row in rows) == (
        "naive",
        "book_imbalance",
        "llm",
        "manual-research",
        "team-memory",
    )
    assert rows[0] == ResearchModelSignalWeightingRow(
        signal_name="naive",
        raw_weight=d("0.100000"),
        quality_multiplier=d("0.900000"),
        confidence_multiplier=d("0.800000"),
        freshness_multiplier=d("0.900000"),
        conflict_penalty_multiplier=d("0.950000"),
        adjusted_weight=d("0.061560"),
        normalized_weight=d("0.101984"),
        status="pass",
        reason_codes=("signal_weight_pass",),
    )
    assert rows[3].adjusted_weight == d("0.192909")
    assert rows[3].normalized_weight == d("0.319585")
    assert rows[3].reason_codes == ("input_human_reviewed", "signal_weight_pass")


def test_watch_and_block_thresholds_are_deterministic() -> None:
    watch_report = report(
        (
            signal("naive", raw_weight=d("0.800000")),
            signal("book_imbalance", raw_weight=d("0.150000")),
            signal("manual-research", raw_weight=d("0.050000")),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.max_normalized_weight == d("0.800000")
    assert watch_report.human_research_normalized_weight == d("0.050000")
    assert watch_report.reason_codes == (
        "human_research_weight_watch",
        "signal_weight_policy_watch",
        "single_signal_concentration_watch",
        "watch_signal_present",
    )
    assert watch_report.rows[0].status == "watch"
    assert "single_signal_weight_watch" in watch_report.rows[0].reason_codes

    block_report = report(
        (
            signal("naive", raw_weight=d("0.900000")),
            signal("book_imbalance", raw_weight=d("0.100000")),
            signal("manual-research", raw_weight=d("0.000000")),
        ),
    )

    assert block_report.status == "block"
    assert block_report.max_normalized_weight == d("0.900000")
    assert block_report.human_research_normalized_weight == d("0.000000")
    assert block_report.reason_codes == (
        "block_signal_present",
        "human_research_weight_block",
        "signal_weight_policy_block",
        "single_signal_concentration_block",
        "too_few_active_signals_watch",
    )


def test_payload_is_decimal_only_and_excludes_raw_identifiers() -> None:
    weighting_report = report(
        (
            SuppliedSignalShape(
                signal_name="manual-research",
                raw_signal_id="raw-secret-signal-123",
                raw_source="private-source-secret",
                raw_market_id="market-secret-456",
                raw_weight=d("0.600000"),
                quality_score=d("0.900000"),
                confidence_score=d("0.900000"),
                freshness_score=d("0.900000"),
                conflict_score=d("0.050000"),
            ),
            signal("team-memory", raw_weight=d("0.400000")),
        ),
        cfg=config(pass_min_active_signal_count=d("2")),
    )

    payload = research_model_signal_weighting_policy_payload(weighting_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["input_weight"] == str(weighting_report.rows[0].raw_weight)
    assert payload["rows"][0]["normalized_weight"] == str(
        weighting_report.rows[0].normalized_weight,
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert "raw-secret-signal-123" not in encoded
    assert "private-source-secret" not in encoded
    assert "market-secret-456" not in encoded
    assert "raw_signal_id" not in encoded
    assert "raw_source" not in encoded
    assert "raw_market_id" not in encoded
    assert "total_raw_weight" not in encoded
    assert "raw_weight" not in encoded


def test_validation_rejects_bad_types_enums_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="max_single_signal_weight_watch"):
        config(max_single_signal_weight_pass=d("0.900000"))
    with pytest.raises(ValueError, match="raw_weight"):
        signal("naive", raw_weight=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quality_score"):
        signal("naive", quality_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="signal_name"):
        signal("technical")
    with pytest.raises(ValueError, match="enabled"):
        replace(signal("naive"), enabled=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="hard_block"):
        replace(signal("naive"), hard_block=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report((signal("naive"),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (signal("naive"),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        signal("naive", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        signal("naive", reason_codes=("market_leak",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal("naive"), paper_only=False)
    with pytest.raises(ValueError, match="signal_name values must be unique"):
        report((signal("naive"), signal("naive")))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    weighting_report = report(
        (
            signal("naive", raw_weight=d("0.500000")),
            signal("manual-research", raw_weight=d("0.500000")),
        ),
        cfg=config(pass_min_active_signal_count=d("2")),
    )

    with pytest.raises(FrozenInstanceError):
        weighting_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        weighting_report.rows[0].normalized_weight = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="adjusted_weight"):
        replace(weighting_report.rows[0], adjusted_weight=d("0.900000"))
    with pytest.raises(ValueError, match="status"):
        replace(weighting_report.rows[0], status="block")
    with pytest.raises(ValueError, match="status"):
        replace(weighting_report, status="block")


def test_owned_module_has_no_network_filesystem_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_model_signal_weighting_policy.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
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
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "order",
        "buy",
        "sell",
        "bet",
        "stake",
    )

    assert all(term not in source for term in forbidden_terms)


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
