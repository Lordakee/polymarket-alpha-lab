from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_strategy_cycle_report_db_row import (
    PaperStrategyCycleReportDbRow,
    paper_strategy_cycle_report_from_db_row,
    paper_strategy_cycle_report_to_db_row,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningConfig,
    build_paper_project_screening_report,
)
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


GENERATED_AT = datetime(2026, 6, 14, 9, 0, tzinfo=UTC)
COST_REPORT_AT = datetime(2026, 6, 14, 9, 1, tzinfo=UTC)


class PaperStrategyCycleReportSubclass(PaperStrategyCycleReport):
    pass


class PaperStrategyCycleReportDbRowSubclass(PaperStrategyCycleReportDbRow):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _side_result(
    *,
    side: str,
    fair_probability: str,
    executable_price: str,
    ask_size: str,
    net_edge_per_share: str,
) -> PaperCostAwareEventSideResult:
    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=d(fair_probability),
        executable_price=d(executable_price),
        ask_size=d(ask_size),
        gross_edge_per_share=d("0.180000" if side == "yes" else "0.020000"),
        fee_cost_per_share=d("0.004968" if side == "yes" else "0.004968"),
        non_fee_cost_per_share=d("0.001000"),
        total_cost_per_share=d("0.005968"),
        net_edge_per_share=d(net_edge_per_share),
        reason_codes=(f"{side}_paper_edge_complete",),
    )


def _gate(
    gate_name: str,
    observed_value: object,
    threshold: object,
) -> PaperCostAwareEventStrategyGateResult:
    return PaperCostAwareEventStrategyGateResult(
        gate_name=gate_name,
        status="pass",
        reason_code=f"{gate_name}_ready",
        message=f"{gate_name} gate is ready.",
        observed_value=observed_value,
        threshold=threshold,
    )


def _cost_aware_report(
    *,
    generated_at: datetime = COST_REPORT_AT,
    decimal_variant: bool = False,
) -> PaperCostAwareEventStrategyReport:
    if decimal_variant:
        fair_probability_yes = "0.7200"
        confidence = "0.8500"
        yes_bid = "0.5200"
        no_bid = "0.4400"
        spread = "0.0200"
        resolution_risk = "0.0500"
        yes_executable = "0.5400"
        yes_size = "250.0"
        yes_edge = "0.174032"
        no_executable = "0.4600"
        no_size = "180.0"
        no_edge = "0.014032"
    else:
        fair_probability_yes = "0.720000"
        confidence = "0.850000"
        yes_bid = "0.520000"
        no_bid = "0.440000"
        spread = "0.020000"
        resolution_risk = "0.050000"
        yes_executable = "0.540000"
        yes_size = "250.000000"
        yes_edge = "0.174032"
        no_executable = "0.460000"
        no_size = "180.000000"
        no_edge = "0.014032"
    return PaperCostAwareEventStrategyReport(
        generated_at=generated_at,
        config_version="cost-aware-v1",
        market_slug="example-market",
        question="Will the example market resolve yes?",
        fair_probability_yes=d(fair_probability_yes),
        confidence=d(confidence),
        yes_bid=d(yes_bid),
        no_bid=d(no_bid),
        spread=d(spread),
        resolution_risk=d(resolution_risk),
        selected_side="yes",
        status="paper_review_ready",
        yes_result=_side_result(
            side="yes",
            fair_probability=fair_probability_yes,
            executable_price=yes_executable,
            ask_size=yes_size,
            net_edge_per_share=yes_edge,
        ),
        no_result=_side_result(
            side="no",
            fair_probability="0.280000",
            executable_price=no_executable,
            ask_size=no_size,
            net_edge_per_share=no_edge,
        ),
        gate_results=(
            _gate("data_integrity", "yes_or_no_ask", "one_executable_ask"),
            _gate("confidence", "0.850000", "0.700000"),
            _gate("spread", "0.020000", "0.050000"),
            _gate("resolution_risk", "0.050000", "0.200000"),
            _gate("yes_depth", "250.000000", "1.000000"),
            _gate("no_depth", "180.000000", "1.000000"),
            _gate("edge_threshold", "0.174032", "0.010000"),
        ),
    )


def _screening_report(*, decimal_variant: bool = False):
    return build_paper_project_screening_report(
        reports=(_cost_aware_report(decimal_variant=decimal_variant),),
        config=PaperProjectScreeningConfig(
            config_version="screening-v1",
            min_screening_score=d("0.0100"),
            reference_ask_size=d("100.0000"),
        ),
        generated_at=GENERATED_AT,
    )


def _full_report(
    *,
    generated_at: datetime = GENERATED_AT,
    decimal_variant: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
) -> PaperStrategyCycleReport:
    cost_report = _cost_aware_report(
        generated_at=COST_REPORT_AT,
        decimal_variant=decimal_variant,
    )
    return PaperStrategyCycleReport(
        generated_at=generated_at,
        config_version="strategy-cycle-v1",
        scan_market_count=4,
        considered_count=3,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts=(
            ("blocked_fetch_error", 1),
            ("blocked_non_binary_market", 1),
        ),
        screening_report=_screening_report(decimal_variant=decimal_variant),
        cost_aware_reports=(cost_report,),
        paper_only=paper_only,
        report_only=report_only,
    )


def _empty_report() -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=GENERATED_AT,
        config_version="strategy-cycle-v1",
        scan_market_count=0,
        considered_count=0,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(),
        screening_report=None,
        cost_aware_reports=(),
    )


def _payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bypassed_row(
    row: PaperStrategyCycleReportDbRow,
    **overrides: object,
) -> PaperStrategyCycleReportDbRow:
    malformed = object.__new__(PaperStrategyCycleReportDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    for field_name, value in overrides.items():
        object.__setattr__(malformed, field_name, value)
    return malformed


def _row_copy(
    row: PaperStrategyCycleReportDbRow,
    **changes: object,
) -> PaperStrategyCycleReportDbRow:
    return replace(row, **changes)


def _assert_json_clean(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, Decimal):
        pytest.fail("DB payload must not contain raw Decimal values")
    if isinstance(value, datetime):
        pytest.fail("DB payload must not contain raw datetime values")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _assert_json_clean(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_json_clean(item)


def test_strategy_cycle_report_db_row_module_is_pure_paper_only_codec() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_strategy_cycle_report_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "private_key",
        "wallet",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "exchange",
    ):
        assert banned not in source.lower()


def test_strategy_cycle_report_db_row_serializes_full_payload_and_round_trips() -> None:
    report = _full_report(
        generated_at=datetime(2026, 6, 14, 5, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    row = paper_strategy_cycle_report_to_db_row(report)

    assert type(row) is PaperStrategyCycleReportDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "strategy-cycle-v1"
    assert row.scan_market_count == 4
    assert row.considered_count == 3
    assert row.snapshot_ready_count == 1
    assert row.cost_aware_report_count == 1
    assert row.blocked_counts_json == [
        ["blocked_fetch_error", 1],
        ["blocked_non_binary_market", 1],
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.payload_json["generated_at"] == "2026-06-14T09:00:00+00:00"
    assert row.payload_json["blocked_counts"] == row.blocked_counts_json
    assert row.payload_json["screening_report"]["generated_at"] == (
        "2026-06-14T09:00:00+00:00"
    )
    assert row.payload_json["screening_report"]["candidates"][0][
        "screening_score"
    ] == "0.492242"
    assert row.payload_json["cost_aware_reports"][0]["generated_at"] == (
        "2026-06-14T09:01:00+00:00"
    )
    assert row.payload_json["cost_aware_reports"][0]["yes_result"][
        "net_edge_per_share"
    ] == "0.174032"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.report_sha256 == _payload_sha256(row.payload_json)
    _assert_json_clean(row.payload_json)

    recovered = paper_strategy_cycle_report_from_db_row(row)
    assert recovered == report
    assert recovered.cost_aware_reports == report.cost_aware_reports
    assert recovered.screening_report == report.screening_report


def test_strategy_cycle_report_db_row_round_trips_without_screening_report() -> None:
    report = _empty_report()

    row = paper_strategy_cycle_report_to_db_row(report)

    assert row.screening_report is None if hasattr(row, "screening_report") else True
    assert row.blocked_counts_json == []
    assert row.cost_aware_report_count == 0
    assert row.payload_json["screening_report"] is None
    assert row.payload_json["cost_aware_reports"] == []
    assert paper_strategy_cycle_report_from_db_row(row) == report


def test_strategy_cycle_report_db_row_hash_is_deterministic_for_equivalent_payloads() -> None:
    first = paper_strategy_cycle_report_to_db_row(_full_report())
    second = paper_strategy_cycle_report_to_db_row(
        _full_report(
            generated_at=datetime(
                2026,
                6,
                14,
                5,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            decimal_variant=True,
        ),
    )

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json


def test_strategy_cycle_report_db_row_rejects_wrong_report_type_and_subclasses() -> None:
    with pytest.raises(ValueError, match="PaperStrategyCycleReport"):
        paper_strategy_cycle_report_to_db_row(object())

    report = _full_report()
    subclass = PaperStrategyCycleReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperStrategyCycleReport"):
        paper_strategy_cycle_report_to_db_row(subclass)


def test_strategy_cycle_report_from_db_row_rejects_wrong_row_type_and_subclasses() -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())

    with pytest.raises(ValueError, match="PaperStrategyCycleReportDbRow"):
        paper_strategy_cycle_report_from_db_row(object())

    subclass = PaperStrategyCycleReportDbRowSubclass(**row.__dict__)
    with pytest.raises(ValueError, match="PaperStrategyCycleReportDbRow"):
        paper_strategy_cycle_report_from_db_row(subclass)


def test_strategy_cycle_report_db_row_hard_enforces_paper_and_report_only() -> None:
    report = _full_report()
    object.__setattr__(report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        paper_strategy_cycle_report_to_db_row(report)

    report = _full_report()
    object.__setattr__(report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        paper_strategy_cycle_report_to_db_row(report)

    row = paper_strategy_cycle_report_to_db_row(_full_report())
    with pytest.raises(ValueError, match="paper_only"):
        _row_copy(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _row_copy(row, report_only=False)

    payload_json = deepcopy(row.payload_json)
    payload_json["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        PaperStrategyCycleReportDbRow(
            **{
                **row.__dict__,
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_strategy_cycle_report_db_row_rejects_payload_that_is_not_json_object() -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())

    with pytest.raises(ValueError, match="payload_json"):
        _row_copy(row, payload_json=[])


@pytest.mark.parametrize(
    ("bad_value", "match"),
    (
        (0.1, "float|payload_json"),
        (Decimal("0.100000"), "Decimal|payload_json"),
        (datetime(2026, 6, 14, 9, 0, tzinfo=UTC), "datetime|payload_json"),
    ),
)
def test_strategy_cycle_report_db_row_rejects_raw_non_json_payload_values(
    bad_value: object,
    match: str,
) -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())
    payload_json = deepcopy(row.payload_json)
    payload_json["cost_aware_reports"][0]["yes_result"]["net_edge_per_share"] = bad_value

    with pytest.raises(ValueError, match=match):
        _row_copy(row, payload_json=payload_json)

    with pytest.raises(ValueError, match=match):
        paper_strategy_cycle_report_from_db_row(
            _bypassed_row(row, payload_json=payload_json),
        )


def test_strategy_cycle_report_db_row_rejects_payload_that_cannot_recover_report() -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())
    payload_json = deepcopy(row.payload_json)
    del payload_json["config_version"]

    with pytest.raises(ValueError, match="payload_json|config_version"):
        PaperStrategyCycleReportDbRow(
            **{
                **row.__dict__,
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )

    with pytest.raises(ValueError, match="payload_json|config_version"):
        paper_strategy_cycle_report_from_db_row(
            _bypassed_row(
                row,
                report_sha256=_payload_sha256(payload_json),
                payload_json=payload_json,
            ),
        )


def test_strategy_cycle_report_db_row_payload_recovers_compatible_report() -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())

    recovered = from_jsonable(PaperStrategyCycleReport, row.payload_json)

    assert type(recovered) is PaperStrategyCycleReport
    assert recovered == _full_report()


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("report_sha256", "a" * 64),
        ("generated_at", datetime(2026, 6, 14, 9, 1, tzinfo=UTC)),
        ("config_version", "strategy-cycle-v2"),
        ("scan_market_count", 5),
        ("considered_count", 4),
        ("snapshot_ready_count", 2),
        ("cost_aware_report_count", 2),
        ("blocked_counts_json", [["blocked_fetch_error", 2]]),
        ("paper_only", False),
        ("report_only", False),
    ),
)
def test_strategy_cycle_report_db_row_validates_materialized_columns_match_payload(
    field_name: str,
    bad_value: object,
) -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())

    with pytest.raises(ValueError, match=field_name):
        _row_copy(row, **{field_name: bad_value})


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("report_sha256", "a" * 64),
        ("generated_at", datetime(2026, 6, 14, 9, 1, tzinfo=UTC)),
        ("config_version", "strategy-cycle-v2"),
        ("scan_market_count", 5),
        ("considered_count", 4),
        ("snapshot_ready_count", 2),
        ("cost_aware_report_count", 2),
        ("blocked_counts_json", [["blocked_fetch_error", 2]]),
        ("paper_only", 1),
        ("report_only", 1),
    ),
)
def test_strategy_cycle_report_from_db_row_defends_against_bypassed_materialized_mismatch(
    field_name: str,
    bad_value: object,
) -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())

    with pytest.raises(ValueError, match=field_name):
        paper_strategy_cycle_report_from_db_row(
            _bypassed_row(row, **{field_name: bad_value}),
        )


def test_strategy_cycle_report_db_row_rejects_unstable_blocked_counts_json_shape() -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())

    with pytest.raises(ValueError, match="blocked_counts_json"):
        _row_copy(row, blocked_counts_json=[("blocked_fetch_error", 1)])

    with pytest.raises(ValueError, match="blocked_counts_json"):
        _row_copy(row, blocked_counts_json=[["blocked_fetch_error", True]])


def test_strategy_cycle_report_db_row_is_frozen() -> None:
    row = paper_strategy_cycle_report_to_db_row(_full_report())

    with pytest.raises(FrozenInstanceError):
        row.config_version = "changed"  # type: ignore[misc]
