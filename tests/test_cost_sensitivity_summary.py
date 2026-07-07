from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_sensitivity import (
    PaperCostSensitivityConfig,
    PaperCostSensitivityReport,
    PaperCostSensitivityRow,
    build_paper_cost_sensitivity_report,
)
from polymarket_alpha_lab.cost_sensitivity_summary import (
    PaperCostSensitivitySummaryConfig,
    PaperCostSensitivitySummaryReport,
    build_paper_cost_sensitivity_summary_report,
    paper_cost_sensitivity_summary_payload,
)


GENERATED_AT = datetime(2026, 6, 18, 20, 0, tzinfo=UTC)


def _summary_config(**overrides):
    values = {
        "config_version": "cost-sensitivity-summary-v0",
        "taker_fee_rate": Decimal("0.02"),
    }
    values.update(overrides)
    return PaperCostSensitivitySummaryConfig(**values)


def _source_report(**overrides):
    rows = overrides.pop(
        "rows",
        (
            PaperCostSensitivityRow(
                market_slug="market-alpha",
                selected_side="yes",
                base_net_edge_per_share=Decimal("0.030000"),
                cost_shock_per_share=Decimal("0.000000"),
                stressed_net_edge_per_share=Decimal("0.030000"),
                status="pass",
                reason_codes=("stressed_net_edge_ready",),
            ),
            PaperCostSensitivityRow(
                market_slug="market-alpha",
                selected_side="yes",
                base_net_edge_per_share=Decimal("0.030000"),
                cost_shock_per_share=Decimal("0.025000"),
                stressed_net_edge_per_share=Decimal("0.005000"),
                status="watch",
                reason_codes=("stressed_net_edge_below_minimum",),
            ),
        ),
    )
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "cost-sensitivity-v0",
        "source_report_count": 1,
        "row_count": len(rows),
        "pass_count": sum(1 for row in rows if row.status == "pass"),
        "watch_count": sum(1 for row in rows if row.status == "watch"),
        "blocked_count": sum(1 for row in rows if row.status == "blocked"),
        "status": "blocked"
        if any(row.status == "blocked" for row in rows)
        else "watch"
        if any(row.status == "watch" for row in rows)
        else "pass",
        "rows": rows,
    }
    values.update(overrides)
    return PaperCostSensitivityReport(**values)


def test_summary_reduces_cost_sensitivity_reports_without_market_identifiers():
    report = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=_summary_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperCostSensitivitySummaryReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "cost-sensitivity-summary-v0"
    assert type(report.source_report_count) is Decimal
    assert type(report.source_row_count) is Decimal
    assert type(report.pass_count) is Decimal
    assert type(report.watch_count) is Decimal
    assert type(report.blocked_count) is Decimal
    assert report.source_report_count == 1
    assert report.source_row_count == 2
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert report.pass_ratio == Decimal("0.500000")
    assert report.watch_ratio == Decimal("0.500000")
    assert report.blocked_ratio == Decimal("0.000000")
    assert report.mean_base_net_edge_per_share == Decimal("0.030000")
    assert report.mean_cost_shock_per_share == Decimal("0.012500")
    assert report.mean_stressed_net_edge_per_share == Decimal("0.017500")
    assert report.worst_stressed_net_edge_per_share == Decimal("0.005000")
    assert report.taker_fee_rate == Decimal("0.020000")
    assert report.status == "watch"
    assert report.reason_codes == ("cost_sensitivity_watch_rows",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert not hasattr(report, "market_slug")
    assert not hasattr(report, "question")
    assert report.validation_digest.startswith("pcs-summary-v1:")


def test_summary_uses_default_two_percent_taker_fee_and_allows_decimal_override():
    default_report = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=PaperCostSensitivitySummaryConfig(
            config_version="cost-sensitivity-summary-v0",
        ),
        generated_at=GENERATED_AT,
    )
    override_report = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=_summary_config(taker_fee_rate=Decimal("0.015")),
        generated_at=GENERATED_AT,
    )

    assert default_report.taker_fee_rate == Decimal("0.020000")
    assert override_report.taker_fee_rate == Decimal("0.015000")


def test_summary_reports_empty_history_without_metric_values():
    report = build_paper_cost_sensitivity_summary_report(
        [],
        config=_summary_config(),
        generated_at=GENERATED_AT,
    )

    assert report.source_report_count == 0
    assert report.source_row_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.pass_ratio is None
    assert report.watch_ratio is None
    assert report.blocked_ratio is None
    assert report.mean_base_net_edge_per_share is None
    assert report.mean_cost_shock_per_share is None
    assert report.mean_stressed_net_edge_per_share is None
    assert report.worst_stressed_net_edge_per_share is None
    assert report.status == "empty_cost_sensitivity_summary"
    assert report.reason_codes == ("cost_sensitivity_summary_empty",)


def test_summary_counts_blocked_rows_and_ignores_missing_edge_metrics():
    blocked_report = _source_report(
        rows=(
            PaperCostSensitivityRow(
                market_slug="market-beta",
                selected_side="none",
                base_net_edge_per_share=None,
                cost_shock_per_share=Decimal("0.010000"),
                stressed_net_edge_per_share=None,
                status="blocked",
                reason_codes=("missing_selected_side",),
            ),
            PaperCostSensitivityRow(
                market_slug="market-gamma",
                selected_side="yes",
                base_net_edge_per_share=Decimal("0.040000"),
                cost_shock_per_share=Decimal("0.020000"),
                stressed_net_edge_per_share=Decimal("0.020000"),
                status="pass",
                reason_codes=("stressed_net_edge_ready",),
            ),
        ),
    )

    report = build_paper_cost_sensitivity_summary_report(
        [blocked_report],
        config=_summary_config(),
        generated_at=GENERATED_AT,
    )

    assert report.source_row_count == 2
    assert report.pass_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 1
    assert report.pass_ratio == Decimal("0.500000")
    assert report.blocked_ratio == Decimal("0.500000")
    assert report.mean_base_net_edge_per_share == Decimal("0.040000")
    assert report.mean_cost_shock_per_share == Decimal("0.015000")
    assert report.mean_stressed_net_edge_per_share == Decimal("0.020000")
    assert report.worst_stressed_net_edge_per_share == Decimal("0.020000")
    assert report.status == "blocked"
    assert report.reason_codes == ("cost_sensitivity_blocked_rows",)


def test_summary_normalizes_generated_at_to_utc():
    generated_at = datetime(
        2026,
        6,
        18,
        16,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=_summary_config(),
        generated_at=generated_at,
    )

    assert report.generated_at == datetime(2026, 6, 18, 20, 30, tzinfo=UTC)


def test_summary_rejects_invalid_inputs_flags_and_exact_types():
    class ConfigSubclass(PaperCostSensitivitySummaryConfig):
        pass

    class ReportSubclass(PaperCostSensitivityReport):
        pass

    class DateTimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="config"):
        build_paper_cost_sensitivity_summary_report(
            [_source_report()],
            config=ConfigSubclass(config_version="cost-sensitivity-summary-v0"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_cost_sensitivity_summary_report(
            [_source_report()],
            config=_summary_config(),
            generated_at=DateTimeSubclass(2026, 6, 18, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reports"):
        build_paper_cost_sensitivity_summary_report(
            object(),
            config=_summary_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="reports"):
        build_paper_cost_sensitivity_summary_report(
            [ReportSubclass(**_source_report().__dict__)],
            config=_summary_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="taker_fee_rate"):
        PaperCostSensitivitySummaryConfig(
            config_version="cost-sensitivity-summary-v0",
            taker_fee_rate=0.02,
        )
    unsafe_report = _source_report()
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        build_paper_cost_sensitivity_summary_report(
            [unsafe_report],
            config=_summary_config(),
            generated_at=GENERATED_AT,
        )


def test_summary_dataclasses_are_frozen_and_revalidate_consistency():
    config = _summary_config()
    report = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.taker_fee_rate = Decimal("0")
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="source_row_count"):
        replace(report, source_row_count=3)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="pass")


def test_summary_validation_digest_is_deterministic_and_tamper_evident():
    first = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=_summary_config(),
        generated_at=GENERATED_AT,
    )
    second = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=_summary_config(),
        generated_at=GENERATED_AT,
    )

    assert first.validation_digest == second.validation_digest
    assert first.validation_digest.startswith("pcs-summary-v1:")

    object.__setattr__(first, "watch_count", 0)
    with pytest.raises(ValueError, match="validation_digest|tamper"):
        paper_cost_sensitivity_summary_payload(first)


def test_summary_payload_is_safe_public_json_with_decimal_strings():
    report = build_paper_cost_sensitivity_summary_report(
        [_source_report()],
        config=_summary_config(),
        generated_at=GENERATED_AT,
    )

    payload = paper_cost_sensitivity_summary_payload(report)
    payload_text = repr(payload).lower()

    assert payload["generated_at"] == "2026-06-18T20:00:00+00:00"
    assert payload["source_report_count"] == "1"
    assert payload["source_row_count"] == "2"
    assert payload["pass_count"] == "1"
    assert payload["watch_count"] == "1"
    assert payload["blocked_count"] == "0"
    assert payload["pass_ratio"] == "0.500000"
    assert payload["mean_cost_shock_per_share"] == "0.012500"
    assert payload["taker_fee_rate"] == "0.020000"
    assert payload["validation_digest"] == report.validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "market-alpha" not in payload_text
    assert "market_slug" not in payload_text
    assert "question" not in payload_text


def test_summary_payload_accepts_safe_dicts_and_rejects_numeric_or_flag_drift():
    class PayloadDict(dict):
        pass

    payload = paper_cost_sensitivity_summary_payload(
        {
            "generated_at": GENERATED_AT,
            "source_report_count": Decimal("1"),
            "source_row_count": Decimal("0"),
            "pass_count": Decimal("0"),
            "watch_count": Decimal("0"),
            "blocked_count": Decimal("0"),
            "pass_ratio": None,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert payload["generated_at"] == "2026-06-18T20:00:00+00:00"
    assert payload["source_report_count"] == "1"

    with pytest.raises(ValueError, match="paper_only"):
        paper_cost_sensitivity_summary_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="Decimal"):
        paper_cost_sensitivity_summary_payload(
            {"source_report_count": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe|sensitive|field"):
        paper_cost_sensitivity_summary_payload(
            {"market_slug": "market-alpha", "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe|sensitive"):
        paper_cost_sensitivity_summary_payload(
            {"note": "wallet order", "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="plain"):
        paper_cost_sensitivity_summary_payload(
            {"nested": PayloadDict({"note": "safe"}), "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        paper_cost_sensitivity_summary_payload(
            {
                "generated_at": datetime(2026, 6, 18, 20, 0),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_summary_can_reduce_existing_cost_sensitivity_report_output():
    config = PaperCostSensitivityConfig(
        config_version="cost-sensitivity-v0",
        min_stressed_net_edge=Decimal("0.010000"),
        cost_shock_per_share_values=(
            Decimal("0.000000"),
            Decimal("0.025000"),
        ),
    )
    source = _source_report()
    sensitivity_report = build_paper_cost_sensitivity_report(
        [],
        config=config,
        generated_at=source.generated_at,
    )

    report = build_paper_cost_sensitivity_summary_report(
        [sensitivity_report],
        config=_summary_config(),
        generated_at=GENERATED_AT,
    )

    assert report.source_report_count == 1
    assert report.source_row_count == 0
    assert report.status == "empty_cost_sensitivity_summary"


def test_cost_sensitivity_summary_public_names_and_source_stay_report_only():
    import inspect
    import polymarket_alpha_lab.cost_sensitivity_summary as module

    forbidden_public_terms = ("rank", "recommend", "advice", "slug", "question")
    forbidden_source_fragments = (
        "auth",
        "wallet",
        "account",
        "order",
        "live",
        "fast",
        "market_slug",
        "question",
    )

    assert module.__all__ == (
        "PaperCostSensitivitySummaryConfig",
        "PaperCostSensitivitySummaryReport",
        "build_paper_cost_sensitivity_summary_report",
        "paper_cost_sensitivity_summary_payload",
    )
    assert all(
        term not in public_name.lower()
        for public_name in module.__all__
        for term in forbidden_public_terms
    )
    source = inspect.getsource(module).lower()
    assert all(fragment not in source for fragment in forbidden_source_fragments)
