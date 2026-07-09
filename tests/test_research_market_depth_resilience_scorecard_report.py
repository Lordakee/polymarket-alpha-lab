from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedDepthResilienceShape:
    public_observation_label: str
    observed_at: datetime
    near_band_depth_ratio: Decimal
    mid_band_depth_ratio: Decimal
    far_band_depth_ratio: Decimal
    spread_stability_ratio: Decimal
    book_age_seconds: Decimal
    imbalance_volatility_ratio: Decimal
    fee_drag_ratio: Decimal
    slippage_cushion_ratio: Decimal
    settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_depth_resilience_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_depth_band_score": d("0.700000"),
        "minimum_watch_depth_band_score": d("0.400000"),
        "minimum_pass_spread_stability_ratio": d("0.750000"),
        "minimum_watch_spread_stability_ratio": d("0.450000"),
        "maximum_pass_book_age_seconds": d("120.000000"),
        "maximum_watch_book_age_seconds": d("900.000000"),
        "maximum_pass_imbalance_volatility_ratio": d("0.200000"),
        "maximum_watch_imbalance_volatility_ratio": d("0.600000"),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "minimum_pass_slippage_cushion_ratio": d("0.700000"),
        "minimum_watch_slippage_cushion_ratio": d("0.400000"),
        "maximum_pass_settlement_friction_ratio": d("0.150000"),
        "maximum_watch_settlement_friction_ratio": d("0.500000"),
        "near_depth_band_weight": d("0.500000"),
        "mid_depth_band_weight": d("0.300000"),
        "far_depth_band_weight": d("0.200000"),
        "depth_band_weight": d("0.250000"),
        "spread_stability_weight": d("0.150000"),
        "book_age_weight": d("0.150000"),
        "imbalance_volatility_weight": d("0.150000"),
        "fee_drag_weight": d("0.100000"),
        "slippage_cushion_weight": d("0.100000"),
        "settlement_friction_weight": d("0.100000"),
        "pass_resilience_score": d("0.750000"),
        "watch_resilience_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthResilienceScorecardConfig(**values)


def resilience_input(
    public_observation_label: str = "alpha-pass",
    *,
    observed_at: datetime = GENERATED_AT,
    near_band_depth_ratio: Decimal = d("0.900000"),
    mid_band_depth_ratio: Decimal = d("0.850000"),
    far_band_depth_ratio: Decimal = d("0.800000"),
    spread_stability_ratio: Decimal = d("0.900000"),
    book_age_seconds: Decimal = d("60.000000"),
    imbalance_volatility_ratio: Decimal = d("0.100000"),
    fee_drag_ratio: Decimal = d("0.005000"),
    slippage_cushion_ratio: Decimal = d("0.850000"),
    settlement_friction_ratio: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketDepthResilienceScorecardInput(
        public_observation_label=public_observation_label,
        observed_at=observed_at,
        near_band_depth_ratio=near_band_depth_ratio,
        mid_band_depth_ratio=mid_band_depth_ratio,
        far_band_depth_ratio=far_band_depth_ratio,
        spread_stability_ratio=spread_stability_ratio,
        book_age_seconds=book_age_seconds,
        imbalance_volatility_ratio=imbalance_volatility_ratio,
        fee_drag_ratio=fee_drag_ratio,
        slippage_cushion_ratio=slippage_cushion_ratio,
        settlement_friction_ratio=settlement_friction_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_depth_resilience_scorecard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_depth_resilience_review_with_digest() -> None:
    module = api()
    empty = report()

    assert module.MARKET_DEPTH_RESILIENCE_SCORECARD_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "MARKET_DEPTH_RESILIENCE_SCORECARD_STATUSES",
        "DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION",
        "ResearchMarketDepthResilienceScorecardConfig",
        "ResearchMarketDepthResilienceScorecardInput",
        "ResearchMarketDepthResilienceScorecardReasonCodeCount",
        "ResearchMarketDepthResilienceScorecardReport",
        "ResearchMarketDepthResilienceScorecardRow",
        "build_research_market_depth_resilience_scorecard_report",
        "research_market_depth_resilience_scorecard_report_digest",
        "research_market_depth_resilience_scorecard_report_payload",
    )
    assert type(empty) is module.ResearchMarketDepthResilienceScorecardReport
    assert is_dataclass(empty)
    assert empty.generated_at == GENERATED_AT
    assert empty.config_version == "research-market-depth-resilience-scorecard-report-v0"
    assert empty.observation_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.depth_band_pressure_count == ZERO
    assert empty.spread_instability_count == ZERO
    assert empty.stale_book_count == ZERO
    assert empty.imbalance_volatility_count == ZERO
    assert empty.fee_drag_count == ZERO
    assert empty.slippage_cushion_count == ZERO
    assert empty.settlement_friction_count == ZERO
    assert empty.average_resilience_score is None
    assert empty.min_depth_band_score == ZERO
    assert empty.min_spread_stability_ratio == ZERO
    assert empty.max_book_age_seconds == ZERO
    assert empty.max_imbalance_volatility_ratio == ZERO
    assert empty.max_fee_drag_ratio == ZERO
    assert empty.min_slippage_cushion_ratio == ZERO
    assert empty.max_settlement_friction_ratio == ZERO
    assert empty.status == "block"
    assert empty.rows == ()
    assert empty.reason_codes == ("no_depth_resilience_observations",)
    assert empty.reason_code_counts == (
        module.ResearchMarketDepthResilienceScorecardReasonCodeCount(
            reason_code="no_depth_resilience_observations",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_depth_spread_age_imbalance_fees_slippage_and_settlement() -> None:
    combined = report(
        resilience_input(
            "alpha-block",
            near_band_depth_ratio=d("0.200000"),
            mid_band_depth_ratio=d("0.200000"),
            far_band_depth_ratio=d("0.100000"),
            spread_stability_ratio=d("0.300000"),
            book_age_seconds=d("1200.000000"),
            imbalance_volatility_ratio=d("0.800000"),
            fee_drag_ratio=d("0.040000"),
            slippage_cushion_ratio=d("0.200000"),
            settlement_friction_ratio=d("0.700000"),
            reason_codes=("manual_depth_check",),
        ),
        resilience_input("beta-pass"),
        resilience_input(
            "gamma-watch",
            near_band_depth_ratio=d("0.600000"),
            mid_band_depth_ratio=d("0.500000"),
            far_band_depth_ratio=d("0.400000"),
            spread_stability_ratio=d("0.600000"),
            book_age_seconds=d("300.000000"),
            imbalance_volatility_ratio=d("0.400000"),
            fee_drag_ratio=d("0.020000"),
            slippage_cushion_ratio=d("0.550000"),
            settlement_friction_ratio=d("0.300000"),
        ),
    )

    assert combined.observation_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.depth_band_pressure_count == d("2.000000")
    assert combined.spread_instability_count == d("2.000000")
    assert combined.stale_book_count == d("2.000000")
    assert combined.imbalance_volatility_count == d("2.000000")
    assert combined.fee_drag_count == d("2.000000")
    assert combined.slippage_cushion_count == d("2.000000")
    assert combined.settlement_friction_count == d("2.000000")
    assert combined.average_resilience_score == d("0.500267")
    assert combined.min_depth_band_score == d("0.180000")
    assert combined.min_spread_stability_ratio == d("0.300000")
    assert combined.max_book_age_seconds == d("1200.000000")
    assert combined.max_imbalance_volatility_ratio == d("0.800000")
    assert combined.max_fee_drag_ratio == d("0.040000")
    assert combined.min_slippage_cushion_ratio == d("0.200000")
    assert combined.max_settlement_friction_ratio == d("0.700000")
    assert combined.status == "block"
    assert combined.reason_codes == (
        "depth_resilience_block",
        "depth_band_block",
        "spread_stability_block",
        "book_age_block",
        "imbalance_volatility_block",
        "fee_drag_block",
        "slippage_cushion_block",
        "settlement_friction_block",
        "depth_band_watch",
        "spread_stability_watch",
        "book_age_watch",
        "imbalance_volatility_watch",
        "fee_drag_watch",
        "slippage_cushion_watch",
        "settlement_friction_watch",
    )

    block_row, pass_row, watch_row = combined.rows
    assert tuple(row.public_row_ref for row in combined.rows) == (
        "depth_resilience_group_001",
        "depth_resilience_group_002",
        "depth_resilience_group_003",
    )
    assert tuple(row.status for row in combined.rows) == ("block", "pass", "watch")
    assert block_row.depth_band_score == d("0.180000")
    assert block_row.book_age_score == d("0.000000")
    assert block_row.resilience_score == d("0.110000")
    assert "input_manual_depth_check" in block_row.reason_codes
    assert pass_row.depth_band_score == d("0.865000")
    assert pass_row.imbalance_stability_score == d("0.833333")
    assert pass_row.fee_drag_score == d("0.833333")
    assert pass_row.resilience_score == d("0.874583")
    assert watch_row.depth_band_score == d("0.530000")
    assert watch_row.book_age_score == d("0.769231")
    assert watch_row.resilience_score == d("0.516218")
    assert "depth_band_watch" in watch_row.reason_codes
    assert "settlement_friction_watch" in watch_row.reason_codes
    assert combined.reason_code_counts == tuple(
        sorted(combined.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        SuppliedDepthResilienceShape(
            public_observation_label="zulu-depth",
            observed_at=GENERATED_AT,
            near_band_depth_ratio=d("0.600000"),
            mid_band_depth_ratio=d("0.500000"),
            far_band_depth_ratio=d("0.400000"),
            spread_stability_ratio=d("0.600000"),
            book_age_seconds=d("300.000000"),
            imbalance_volatility_ratio=d("0.400000"),
            fee_drag_ratio=d("0.020000"),
            slippage_cushion_ratio=d("0.550000"),
            settlement_friction_ratio=d("0.300000"),
            reason_codes=("zeta", "alpha"),
        ),
        resilience_input("alpha-depth"),
    )
    second = report(
        resilience_input("alpha-depth"),
        SuppliedDepthResilienceShape(
            public_observation_label="zulu-depth",
            observed_at=GENERATED_AT,
            near_band_depth_ratio=d("0.600000"),
            mid_band_depth_ratio=d("0.500000"),
            far_band_depth_ratio=d("0.400000"),
            spread_stability_ratio=d("0.600000"),
            book_age_seconds=d("300.000000"),
            imbalance_volatility_ratio=d("0.400000"),
            fee_drag_ratio=d("0.020000"),
            slippage_cushion_ratio=d("0.550000"),
            settlement_friction_ratio=d("0.300000"),
            reason_codes=("alpha", "zeta"),
        ),
    )

    first_payload = module.research_market_depth_resilience_scorecard_report_payload(first)
    second_payload = module.research_market_depth_resilience_scorecard_report_payload(second)
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert (
        module.research_market_depth_resilience_scorecard_report_digest(first)
        == first.derived_validation_digest
    )
    assert hashlib.sha256(encoded.encode("utf-8")).hexdigest() == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["resilience_score"] == "0.874583"
    assert first_payload["rows"][1]["book_age_score"] == "0.769231"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ":0.5" not in json.dumps(first_payload, sort_keys=True)
    encoded_public = json.dumps(first_payload, sort_keys=True).lower()
    assert all(
        fragment not in encoded_public
        for fragment in (
            "candidate_id",
            "market_id",
            "condition_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
            "live",
            "recommend",
            "sizing",
        )
    )


def test_accepts_flagged_public_mapping_inputs_without_identifier_leakage() -> None:
    mapped = report(
        {
            "public_observation_label": "mapped-depth",
            "observed_at": GENERATED_AT,
            "near_band_depth_ratio": d("0.900000"),
            "mid_band_depth_ratio": d("0.850000"),
            "far_band_depth_ratio": d("0.800000"),
            "spread_stability_ratio": d("0.900000"),
            "book_age_seconds": d("60.000000"),
            "imbalance_volatility_ratio": d("0.100000"),
            "fee_drag_ratio": d("0.005000"),
            "slippage_cushion_ratio": d("0.850000"),
            "settlement_friction_ratio": d("0.100000"),
            "reason_codes": ("manual_depth_check",),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert mapped.observation_count == d("1.000000")
    assert mapped.rows[0].public_row_ref == "depth_resilience_group_001"
    assert mapped.rows[0].status == "pass"
    assert "input_manual_depth_check" in mapped.rows[0].reason_codes


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_values() -> None:
    with pytest.raises(ValueError, match="resilience weights"):
        config(depth_band_weight=d("0.100000"))
    with pytest.raises(ValueError, match="depth band weights"):
        config(near_depth_band_weight=d("0.400000"))
    with pytest.raises(ValueError, match="minimum_pass_depth_band_score"):
        config(minimum_pass_depth_band_score=d("0.300000"))
    with pytest.raises(ValueError, match="maximum_pass_book_age_seconds"):
        config(maximum_pass_book_age_seconds=d("901.000000"))
    with pytest.raises(ValueError, match="maximum_pass_fee_drag_ratio"):
        config(maximum_pass_fee_drag_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="maximum_watch_imbalance_volatility_ratio"):
        config(
            maximum_pass_imbalance_volatility_ratio=d("0.000000"),
            maximum_watch_imbalance_volatility_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="maximum_watch_fee_drag_ratio"):
        config(
            maximum_pass_fee_drag_ratio=d("0.000000"),
            maximum_watch_fee_drag_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="maximum_watch_settlement_friction_ratio"):
        config(
            maximum_pass_settlement_friction_ratio=d("0.000000"),
            maximum_watch_settlement_friction_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="near_depth_band_weight"):
        config(near_depth_band_weight=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="book_age_seconds"):
        config(maximum_pass_book_age_seconds=120)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(resilience_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            resilience_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="check url")
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="raw-market-alpha")
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="candidateid-alpha")
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="candidate-alpha")
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="market-id-alpha")
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="source-url-alpha")
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="https-alpha")
    with pytest.raises(ValueError, match="public_observation_label"):
        resilience_input(public_observation_label="table-alpha")
    with pytest.raises(ValueError, match="near_band_depth_ratio"):
        resilience_input(near_band_depth_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        resilience_input(fee_drag_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        resilience_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        resilience_input(reason_codes=("auth_required",))
    with pytest.raises(ValueError, match="reason_codes"):
        resilience_input(reason_codes=("execution_ready",))
    with pytest.raises(ValueError, match="reason_codes"):
        resilience_input(reason_codes=("sourceurl",))
    with pytest.raises(ValueError, match="paper_only"):
        resilience_input(paper_only=False)
    with pytest.raises(ValueError, match="public_observation_label values"):
        report(resilience_input("duplicate"), resilience_input("duplicate"))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    depth_report = report(resilience_input())

    with pytest.raises(FrozenInstanceError):
        depth_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        depth_report.rows[0].resilience_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(depth_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="resilience_score"):
        replace(depth_report.rows[0], resilience_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(depth_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="observation_count"):
        replace(depth_report, observation_count=d("2.000000"))


def test_public_payload_rejects_tampered_noncanonical_schema_before_digest() -> None:
    module = api()
    depth_report = report(resilience_input())

    object.__setattr__(depth_report, "observation_count", True)

    for public_function in (
        module.research_market_depth_resilience_scorecard_report_payload,
        module.research_market_depth_resilience_scorecard_report_digest,
    ):
        with pytest.raises(ValueError) as exc_info:
            public_function(depth_report)
        message = str(exc_info.value)
        assert "derived_validation_digest" not in message
        assert "canonical report payload schema" in message or "Decimal" in message


def test_owned_module_has_no_filesystem_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_resilience_scorecard_report.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
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
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )

    assert all(term not in module_text for term in forbidden_terms)


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
