from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re

import pytest

from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.local_observability_trends_db_row import (
    LocalObservabilityTrendsDbRow,
    local_observability_trends_report_from_db_row,
    local_observability_trends_report_to_db_row,
)
from polymarket_alpha_lab.nav_risk_trend import (
    PaperNavRiskTrendConfig,
    build_paper_nav_risk_trend_report,
)
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    build_outcome_freshness_report,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
    build_paper_trade_cost_trend_report,
)
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendConfig,
    build_paper_strategy_evidence_trend_report,
)


GENERATED_AT = datetime(2026, 6, 20, 18, 30, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


MATERIALIZED_MISMATCHES = (
    ("generated_at", datetime(2026, 6, 20, 18, 31, tzinfo=UTC)),
    ("config_version", "local-observability-trends-v1"),
    ("strategy_evidence_snapshot_count", 1),
    ("outcome_freshness_status", "latest_outcomes_fresh"),
    ("outcome_report_count", 1),
    ("nav_risk_status", "latest_nav_risk_observed"),
    ("nav_risk_report_count", 1),
    ("paper_trade_cost_status", "latest_cost_observed"),
    ("paper_trade_cost_report_count", 1),
    ("paper_only", False),
    ("report_only", False),
    ("readonly", False),
)


def _report() -> LocalObservabilityTrendsReport:
    return LocalObservabilityTrendsReport(
        generated_at=GENERATED_AT,
        config_version="local-observability-trends-v0",
        strategy_evidence_trend=build_paper_strategy_evidence_trend_report(
            (),
            config=PaperStrategyEvidenceTrendConfig(
                config_version="strategy-evidence-trend-v0",
            ),
            generated_at=GENERATED_AT,
        ),
        outcome_freshness=build_outcome_freshness_report(
            (),
            config=OutcomeFreshnessConfig(
                config_version="outcome-freshness-v0",
                stale_after_seconds=60,
            ),
            generated_at=GENERATED_AT,
        ),
        nav_risk_trend=build_paper_nav_risk_trend_report(
            (),
            config=PaperNavRiskTrendConfig(config_version="nav-risk-trend-v0"),
            generated_at=GENERATED_AT,
        ),
        paper_trade_cost_trend=build_paper_trade_cost_trend_report(
            (),
            config=PaperTradeCostTrendConfig(
                config_version="paper-trade-cost-trend-v0",
            ),
            generated_at=GENERATED_AT,
        ),
    )


def _payload_sha256(payload_json):
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _row_kwargs(row):
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "strategy_evidence_snapshot_count": row.strategy_evidence_snapshot_count,
        "strategy_evidence_latest_status": row.strategy_evidence_latest_status,
        "outcome_freshness_status": row.outcome_freshness_status,
        "outcome_report_count": row.outcome_report_count,
        "nav_risk_status": row.nav_risk_status,
        "nav_risk_report_count": row.nav_risk_report_count,
        "paper_trade_cost_status": row.paper_trade_cost_status,
        "paper_trade_cost_report_count": row.paper_trade_cost_report_count,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _bypassed_row(row, **overrides):
    values = _row_kwargs(row)
    values.update(overrides)
    bypassed = object.__new__(LocalObservabilityTrendsDbRow)
    for field_name, value in values.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def test_local_observability_trends_db_row_serializes_payload_and_round_trips():
    report = _report()

    row = local_observability_trends_report_to_db_row(report)

    assert isinstance(row, LocalObservabilityTrendsDbRow)
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "local-observability-trends-v0"
    assert row.strategy_evidence_snapshot_count == 0
    assert row.strategy_evidence_latest_status is None
    assert row.outcome_freshness_status == "empty_outcome_history"
    assert row.outcome_report_count == 0
    assert row.nav_risk_status == "empty_nav_risk_history"
    assert row.nav_risk_report_count == 0
    assert row.paper_trade_cost_status == "empty_cost_audit_history"
    assert row.paper_trade_cost_report_count == 0
    assert row.payload_json["generated_at"] == "2026-06-20T18:30:00+00:00"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    recovered = local_observability_trends_report_from_db_row(row)

    assert recovered == report


def test_local_observability_trends_db_row_hash_uses_canonical_full_payload():
    report = _report()
    row = local_observability_trends_report_to_db_row(report)
    mutated_payload = {
        **row.payload_json,
        "config_version": "local-observability-trends-v1",
    }

    with pytest.raises(ValueError, match="report_sha256 must match payload_json"):
        LocalObservabilityTrendsDbRow(
            report_sha256=row.report_sha256,
            generated_at=row.generated_at,
            config_version="local-observability-trends-v1",
            strategy_evidence_snapshot_count=row.strategy_evidence_snapshot_count,
            strategy_evidence_latest_status=row.strategy_evidence_latest_status,
            outcome_freshness_status=row.outcome_freshness_status,
            outcome_report_count=row.outcome_report_count,
            nav_risk_status=row.nav_risk_status,
            nav_risk_report_count=row.nav_risk_report_count,
            paper_trade_cost_status=row.paper_trade_cost_status,
            paper_trade_cost_report_count=row.paper_trade_cost_report_count,
            payload_json=mutated_payload,
        )


def test_local_observability_trends_db_row_rejects_wrong_report_type_and_subclasses():
    report = _report()

    class ReportSubclass(LocalObservabilityTrendsReport):
        pass

    subclass = ReportSubclass(**report.__dict__)

    with pytest.raises(ValueError, match="report must be a LocalObservabilityTrendsReport"):
        local_observability_trends_report_to_db_row(subclass)
    with pytest.raises(ValueError, match="report must be a LocalObservabilityTrendsReport"):
        local_observability_trends_report_to_db_row(object())


def test_local_observability_trends_db_row_rejects_false_report_flags():
    report = _report()
    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "paper_only", False)

    with pytest.raises(ValueError, match="report paper_only must be True"):
        local_observability_trends_report_to_db_row(unsafe_report)


def test_local_observability_trends_db_row_rejects_unsafe_stored_payload_flags():
    row = local_observability_trends_report_to_db_row(_report())
    payload = {**row.payload_json, "readonly": False}

    with pytest.raises(ValueError, match="payload_json readonly"):
        replace(row, payload_json=payload)


def test_local_observability_trends_db_row_rejects_float_payload_values():
    row = local_observability_trends_report_to_db_row(_report())
    payload = {**row.payload_json, "bad_float": 1.25}

    with pytest.raises(ValueError, match="payload_json must not contain floats"):
        replace(row, payload_json=payload)


def test_local_observability_trends_db_row_rejects_materialized_payload_mismatches():
    row = local_observability_trends_report_to_db_row(_report())

    with pytest.raises(ValueError, match="outcome_report_count must match payload_json"):
        replace(row, outcome_report_count=1)


@pytest.mark.parametrize(("field_name", "mismatched_value"), MATERIALIZED_MISMATCHES)
def test_local_observability_trends_db_row_constructor_rejects_materialized_payload_mismatches(
    field_name,
    mismatched_value,
):
    row = local_observability_trends_report_to_db_row(_report())
    kwargs = _row_kwargs(row)
    kwargs[field_name] = mismatched_value
    if field_name == "strategy_evidence_snapshot_count":
        kwargs["strategy_evidence_latest_status"] = "no_local_evidence"

    with pytest.raises(ValueError, match=f"{field_name} must match payload_json"):
        LocalObservabilityTrendsDbRow(**kwargs)


def test_local_observability_trends_db_row_constructor_rejects_nested_latest_status_mismatch():
    row = local_observability_trends_report_to_db_row(_report())
    payload = {
        **row.payload_json,
        "strategy_evidence_trend": {
            **row.payload_json["strategy_evidence_trend"],
            "latest_status": "no_local_evidence",
        },
    }
    kwargs = _row_kwargs(row)
    kwargs["payload_json"] = payload
    kwargs["report_sha256"] = _payload_sha256(payload)

    with pytest.raises(
        ValueError,
        match="strategy_evidence_latest_status must match payload_json",
    ):
        LocalObservabilityTrendsDbRow(**kwargs)


def test_local_observability_trends_db_row_constructor_rejects_unrecoverable_payload_with_matching_hash():
    row = local_observability_trends_report_to_db_row(_report())
    outcome_freshness = row.payload_json["outcome_freshness"]
    assert isinstance(outcome_freshness, dict)
    payload = {
        **row.payload_json,
        "outcome_freshness": {
            **outcome_freshness,
            "status_rows": [],
        },
    }
    kwargs = _row_kwargs(row)
    kwargs["payload_json"] = payload
    kwargs["report_sha256"] = _payload_sha256(payload)

    with pytest.raises(ValueError, match="payload_json|status_rows"):
        LocalObservabilityTrendsDbRow(**kwargs)


def test_local_observability_trends_from_db_row_rejects_bypassed_missing_payload_hard_flags():
    row = local_observability_trends_report_to_db_row(_report())
    payload = {
        key: value
        for key, value in row.payload_json.items()
        if key not in {"paper_only", "report_only", "readonly"}
    }
    bypassed_row = _bypassed_row(
        row,
        report_sha256=_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="hard flags|paper_only"):
        local_observability_trends_report_from_db_row(bypassed_row)


def test_local_observability_trends_report_from_db_row_still_rejects_bypassed_mismatch():
    row = local_observability_trends_report_to_db_row(_report())
    bypassed_row = _bypassed_row(row, outcome_report_count=1)

    with pytest.raises(ValueError, match="outcome_report_count must match payload_json"):
        local_observability_trends_report_from_db_row(
            bypassed_row,
        )


def test_local_observability_trends_db_row_validates_shape_and_scalars():
    row = local_observability_trends_report_to_db_row(_report())

    with pytest.raises(ValueError, match="report_sha256 must be a lowercase sha256"):
        replace(row, report_sha256="not-a-sha")
    with pytest.raises(ValueError, match="outcome_report_count must be nonnegative"):
        replace(row, outcome_report_count=-1)
    with pytest.raises(ValueError, match="nav_risk_status must be a known status"):
        replace(row, nav_risk_status="unknown")
    with pytest.raises(ValueError, match="payload_json must be a JSON object"):
        replace(row, payload_json=[])


def test_local_observability_trends_db_row_validates_strategy_status_count_pair():
    row = local_observability_trends_report_to_db_row(_report())

    with pytest.raises(
        ValueError,
        match="strategy_evidence_latest_status must be null when",
    ):
        replace(row, strategy_evidence_latest_status="no_local_evidence")
    with pytest.raises(
        ValueError,
        match="strategy_evidence_latest_status must be present when",
    ):
        replace(
            row,
            strategy_evidence_snapshot_count=1,
            strategy_evidence_latest_status=None,
        )
