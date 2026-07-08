from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_risk_budget_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_risk_budget_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def decimal_arg(value: object) -> object:
    if type(value) is str:
        return d(value)
    return value


def signal(
    domain: str = "btc",
    *,
    allocated_research_units: str | Decimal = "8.000000",
    required_research_units: str | Decimal = "10.000000",
    available_review_units: str | Decimal = "5.000000",
    required_review_units: str | Decimal = "5.000000",
    information_risk_score: str | Decimal = "0.250000",
    upstream_reason_codes: tuple[str, ...] = ("daily_domain_scan",),
):
    module = api()
    return module.ResearchDomainRiskBudgetSignal(
        domain=domain,
        allocated_research_units=decimal_arg(allocated_research_units),
        required_research_units=decimal_arg(required_research_units),
        available_review_units=decimal_arg(available_review_units),
        required_review_units=decimal_arg(required_review_units),
        information_risk_score=decimal_arg(information_risk_score),
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*items: object, cfg: object | None = None):
    module = api()
    return module.build_research_domain_risk_budget_report(
        items,
        config=cfg or module.ResearchDomainRiskBudgetConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def assert_no_public_payload_objects(value: object) -> None:
    if isinstance(value, (Decimal, datetime, float)):
        raise AssertionError(f"payload contains non-json value: {value!r}")
    if is_dataclass(value):
        raise AssertionError(f"payload contains dataclass value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_payload_objects(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_payload_objects(item)


def test_module_file_exists_for_report_only_domain_budget() -> None:
    assert MODULE_PATH.exists()


def test_six_domain_budget_classifies_resource_review_and_information_risk() -> None:
    module = api()

    budget_report = report(
        signal(
            "basketball",
            allocated_research_units="12.000000",
            required_research_units="10.000000",
            available_review_units="2.000000",
            required_review_units="3.000000",
            information_risk_score="0.600000",
        ),
        signal(
            "soccer",
            allocated_research_units="10.000000",
            required_research_units="10.000000",
            available_review_units="1.000000",
            required_review_units="3.000000",
            information_risk_score="0.200000",
        ),
        signal(
            "gold",
            allocated_research_units="10.000000",
            required_research_units="10.000000",
            available_review_units="5.000000",
            required_review_units="5.000000",
            information_risk_score="0.550000",
        ),
        signal(
            "equity_index",
            allocated_research_units="4.000000",
            required_research_units="10.000000",
            available_review_units="5.000000",
            required_review_units="5.000000",
            information_risk_score="0.100000",
        ),
        signal(
            "btc",
            allocated_research_units="6.000000",
            required_research_units="10.000000",
            available_review_units="5.000000",
            required_review_units="5.000000",
            information_risk_score="0.200000",
        ),
        signal(
            "politics",
            allocated_research_units="10.000000",
            required_research_units="10.000000",
            available_review_units="5.000000",
            required_review_units="5.000000",
            information_risk_score="0.200000",
        ),
    )

    assert isinstance(budget_report, module.ResearchDomainRiskBudgetReport)
    assert is_dataclass(budget_report)
    assert budget_report.__dataclass_params__.frozen
    assert budget_report.generated_at == GENERATED_AT
    assert budget_report.config_version == "research-domain-risk-budget-report-v0"
    assert budget_report.report_status == "block"
    assert budget_report.review_step == "hold_report_only_domain_research_budget_review"
    assert budget_report.input_count == d("6.000000")
    assert budget_report.domain_count == d("6.000000")
    assert budget_report.pass_count == d("1.000000")
    assert budget_report.watch_count == d("3.000000")
    assert budget_report.block_count == d("2.000000")
    assert budget_report.average_research_resource_coverage == d("0.833333")
    assert budget_report.average_review_capacity_coverage == d("0.833333")
    assert budget_report.max_information_risk_score == d("0.600000")
    assert budget_report.overall_risk_score == d("0.666667")
    assert budget_report.paper_only is True
    assert budget_report.report_only is True
    assert budget_report.readonly is True

    assert tuple(row.domain for row in budget_report.rows) == (
        "politics",
        "btc",
        "equity_index",
        "gold",
        "soccer",
        "basketball",
    )
    assert tuple(row.domain_status for row in budget_report.rows) == (
        "pass",
        "watch",
        "block",
        "watch",
        "block",
        "watch",
    )
    assert budget_report.rows[0].reason_codes == ("research_domain_budget_clear",)
    assert budget_report.rows[1].reason_codes == (
        "research_domain_resource_watch",
    )
    assert budget_report.rows[2].reason_codes == (
        "research_domain_resource_block",
    )
    assert budget_report.rows[3].reason_codes == (
        "research_domain_information_watch",
    )
    assert budget_report.rows[4].reason_codes == (
        "research_domain_review_block",
    )
    assert budget_report.rows[5].reason_codes == (
        "research_domain_information_watch",
        "research_domain_review_watch",
    )
    assert budget_report.rows[4].review_capacity_coverage == d("0.333333")
    assert budget_report.rows[5].review_capacity_coverage == d("0.666667")
    assert budget_report.reason_codes == (
        "research_domain_budget_block_present",
        "research_domain_information_risk_present",
        "research_domain_resource_gap_present",
        "research_domain_review_capacity_gap_present",
    )


def test_empty_input_blocks_without_resource_or_review_evidence() -> None:
    module = api()

    budget_report = report()

    assert budget_report.report_status == "block"
    assert budget_report.review_step == "hold_report_only_domain_research_budget_review"
    assert budget_report.input_count == d("0.000000")
    assert budget_report.domain_count == d("0.000000")
    assert budget_report.pass_count == d("0.000000")
    assert budget_report.watch_count == d("0.000000")
    assert budget_report.block_count == d("0.000000")
    assert budget_report.average_research_resource_coverage == d("0.000000")
    assert budget_report.average_review_capacity_coverage == d("0.000000")
    assert budget_report.max_information_risk_score == d("0.000000")
    assert budget_report.overall_risk_score == d("0.000000")
    assert budget_report.rows == ()
    assert budget_report.reason_codes == ("research_domain_risk_budget_empty",)
    assert budget_report.reason_code_counts == (
        module.ResearchDomainRiskBudgetReasonCodeCount(
            reason_code="research_domain_risk_budget_empty",
            count=d("1.000000"),
            domain_ratio=d("0.000000"),
        ),
    )


def test_non_default_thresholds_can_allow_a_moderate_resource_gap() -> None:
    module = api()
    cfg = module.ResearchDomainRiskBudgetConfig(
        watch_research_resource_coverage=d("0.500000"),
        block_research_resource_coverage=d("0.250000"),
        watch_review_capacity_coverage=d("0.500000"),
        block_review_capacity_coverage=d("0.250000"),
        watch_information_risk_score=d("0.700000"),
        block_information_risk_score=d("0.900000"),
    )

    budget_report = report(
        signal(
            "btc",
            allocated_research_units="6.000000",
            required_research_units="10.000000",
            information_risk_score="0.600000",
        ),
        cfg=cfg,
    )

    assert budget_report.report_status == "pass"
    assert budget_report.review_step == "allow_report_only_domain_research_budget_review"
    assert budget_report.rows[0].domain_status == "pass"
    assert budget_report.rows[0].reason_codes == ("research_domain_budget_clear",)
    assert budget_report.reason_codes == ("research_domain_budget_clear",)


def test_payload_uses_decimal_strings_lists_and_no_public_objects() -> None:
    module = api()
    budget_report = report(
        signal(
            "politics",
            allocated_research_units="7.1234567",
            required_research_units="10.000000",
            available_review_units="2.000000",
            required_review_units="4.000000",
            information_risk_score="0.500000",
        ),
    )

    payload = module.research_domain_risk_budget_report_payload(budget_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert budget_report.payload == payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-08T12:30:00+00:00"
    assert payload["input_count"] == "1.000000"
    assert payload["average_research_resource_coverage"] == "0.712346"
    assert payload["rows"][0]["allocated_research_units"] == "7.123457"
    assert payload["rows"][0]["upstream_reason_codes"] == ["daily_domain_scan"]
    assert '"0.712346"' in encoded
    assert_no_public_payload_objects(payload)


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    module = api()
    budget_report = report(signal("btc"))
    public_records = (
        module.ResearchDomainRiskBudgetConfig(),
        signal("gold"),
        budget_report.rows[0],
        budget_report.reason_code_counts[0],
        budget_report,
    )

    for public_record in public_records:
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        hints = get_type_hints(type(public_record))
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert hints[field.name] is Decimal
                assert type(field_value) is Decimal


def test_validation_rejects_bad_types_ranges_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="domain must be supported"):
        signal("tennis")
    with pytest.raises(ValueError, match="domain must be supported"):
        signal(_StringSubclass("btc"))
    with pytest.raises(ValueError, match="allocated_research_units must be a Decimal"):
        signal(allocated_research_units=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="required_research_units must be a Decimal"):
        signal(required_research_units=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="required_research_units must be positive"):
        signal(required_research_units="0.000000")
    with pytest.raises(ValueError, match="available_review_units must be nonnegative"):
        signal(available_review_units="-0.000001")
    with pytest.raises(ValueError, match="information_risk_score must be between"):
        signal(information_risk_score="1.000001")
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_domain_risk_budget_report(
            (),
            config=module.ResearchDomainRiskBudgetConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="signals must contain"):
        report("btc")
    with pytest.raises(ValueError, match="duplicate domain"):
        report(signal("btc"), signal("btc"))
    with pytest.raises(ValueError, match="watch_research_resource_coverage"):
        module.ResearchDomainRiskBudgetConfig(
            watch_research_resource_coverage=d("0.200000"),
            block_research_resource_coverage=d("0.300000"),
        )
    with pytest.raises(ValueError, match="signal report_only must be True"):
        replace(signal("btc"), report_only=False)

    budget_report = report(signal("gold"))
    with pytest.raises(ValueError, match="row domain_risk_score must match"):
        replace(budget_report.rows[0], domain_risk_score=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            budget_report.rows[0],
            reason_codes=(
                "research_domain_budget_clear",
                "research_domain_resource_watch",
            ),
        )
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(budget_report, paper_only=False)
    with pytest.raises(FrozenInstanceError):
        budget_report.report_status = "watch"  # type: ignore[misc]


def test_module_has_no_external_write_surface_or_forbidden_language() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "trade",
        "trading",
        "position",
        "buy",
        "sell",
        "recommend",
        "notional",
        "order",
        "wallet",
        "broker",
        "submit",
        "cancel",
        "replace",
        "auth",
        "requests",
        "http",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "connect(",
        "execute(",
        "open(",
        "urlopen",
        "os.environ",
        "getenv",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
