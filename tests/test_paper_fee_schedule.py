import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
SAFE_FLAGS = ("paper_only", "readonly", "report_only")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def fee_module():
    return import_module("polymarket_alpha_lab.paper_fee_schedule")


def fee_row(
    *,
    category: str = "politics",
    taker_fee_rate: Decimal = d("0.020000"),
    maker_fee_rate: Decimal = d("0.010000"),
    maker_rebate_share: Decimal = d("0.250000"),
    reason_codes: tuple[str, ...] = ("caller_supplied_fee_schedule",),
    flags: tuple[str, ...] = SAFE_FLAGS,
):
    module = fee_module()
    return module.PaperFeeScheduleRow(
        category=category,
        taker_fee_rate=taker_fee_rate,
        maker_fee_rate=maker_fee_rate,
        maker_rebate_share=maker_rebate_share,
        reason_codes=reason_codes,
        flags=flags,
    )


def build_report(*rows, required_categories: tuple[str, ...] = ()):
    module = fee_module()
    return module.build_paper_fee_schedule_report(
        generated_at=GENERATED_AT,
        config_version="paper-fee-schedule-v0",
        rows=rows,
        required_categories=required_categories,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_summarizes_taker_fees_and_sorts_rows_by_category():
    report = build_report(
        fee_row(category="sports", taker_fee_rate=d("0.000000")),
        fee_row(category="crypto", taker_fee_rate=d("0.030000")),
        fee_row(category="politics", taker_fee_rate=d("0.015000")),
    )

    assert [row.category for row in report.rows] == ["crypto", "politics", "sports"]
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-fee-schedule-v0"
    assert report.row_count == 3
    assert report.max_taker_fee_rate == d("0.030000")
    assert report.average_taker_fee_rate == d("0.015000")
    assert report.zero_taker_fee_count == 1
    assert report.fee_schedule_status == "pass"
    assert report.reason_codes == ("fee_schedule_complete",)
    assert report.flags == SAFE_FLAGS

    crypto = report.rows[0]
    assert crypto.taker_fee_rate == d("0.030000")
    assert crypto.maker_fee_rate == d("0.010000")
    assert crypto.maker_rebate_share == d("0.250000")
    assert crypto.reason_codes == ("caller_supplied_fee_schedule",)
    assert crypto.flags == SAFE_FLAGS


def test_status_blocks_missing_required_categories_watches_empty_and_passes_complete():
    missing_report = build_report(
        fee_row(category="politics"),
        required_categories=("politics", "sports"),
    )
    assert missing_report.fee_schedule_status == "blocked"
    assert missing_report.reason_codes == (
        "missing_required_category:sports",
        "missing_required_fee_categories",
    )

    empty_report = build_report()
    assert empty_report.row_count == 0
    assert empty_report.max_taker_fee_rate == d("0.000000")
    assert empty_report.average_taker_fee_rate == d("0.000000")
    assert empty_report.zero_taker_fee_count == 0
    assert empty_report.fee_schedule_status == "watch"
    assert empty_report.reason_codes == ("fee_schedule_empty",)

    complete_report = build_report(
        fee_row(category="politics"),
        fee_row(category="sports", taker_fee_rate=d("0.000000")),
        required_categories=("sports", "politics"),
    )
    assert complete_report.fee_schedule_status == "pass"
    assert complete_report.reason_codes == ("fee_schedule_complete",)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("taker_fee_rate", d("-0.000001"), "taker_fee_rate"),
        ("taker_fee_rate", d("1.000001"), "taker_fee_rate"),
        ("maker_fee_rate", d("-0.000001"), "maker_fee_rate"),
        ("maker_fee_rate", d("1.000001"), "maker_fee_rate"),
        ("maker_rebate_share", d("-0.000001"), "maker_rebate_share"),
        ("maker_rebate_share", d("1.000001"), "maker_rebate_share"),
    ),
)
def test_rejects_rates_outside_zero_to_one(field_name, bad_value, match):
    kwargs = {field_name: bad_value}
    with pytest.raises(ValueError, match=match):
        fee_row(**kwargs)


def test_rejects_duplicate_categories_and_unsafe_flags():
    with pytest.raises(ValueError, match="duplicate category"):
        build_report(
            fee_row(category="politics"),
            fee_row(category="politics", taker_fee_rate=d("0.030000")),
        )

    with pytest.raises(ValueError, match="flags"):
        fee_row(flags=("paper_only", "report_only"))
    with pytest.raises(ValueError, match="flags"):
        fee_row(flags=("paper_only", "readonly", "report_only", "live_trading"))

    report = build_report(fee_row())
    with pytest.raises(ValueError, match="flags"):
        replace(report, flags=("paper_only", "readonly", "live_trading"))


def test_constructors_validate_consistency_utc_and_decimal_only_inputs():
    eastern = timezone(timedelta(hours=-4))
    module = fee_module()
    report = module.build_paper_fee_schedule_report(
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
        config_version="paper-fee-schedule-v0",
        rows=[fee_row()],
        required_categories=("politics",),
    )
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC

    rebuilt_row = module.PaperFeeScheduleRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]
    rebuilt_report = module.PaperFeeScheduleReport(**field_values(report))
    assert rebuilt_report == report

    with pytest.raises(ValueError, match="generated_at"):
        replace(report, generated_at=_DatetimeSubclass(2026, 6, 19, tzinfo=UTC))
    assert fee_row(taker_fee_rate=d("0.01")).taker_fee_rate == d("0.010000")
    with pytest.raises(ValueError, match="taker_fee_rate"):
        fee_row(taker_fee_rate=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=2)
    with pytest.raises(ValueError, match="max_taker_fee_rate"):
        replace(report, max_taker_fee_rate=d("0.010000"))


def test_dataclasses_are_frozen():
    row = fee_row()
    report = build_report(row)

    with pytest.raises(FrozenInstanceError):
        row.category = "sports"
    with pytest.raises(FrozenInstanceError):
        report.rows = ()


def test_module_has_no_live_auth_order_or_network_imports():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_fee_schedule.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    allowed_imports = {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
    }
    forbidden_fragments = (
        "api",
        "auth",
        "clob",
        "client",
        "exchange",
        "http",
        "network",
        "order",
        "private",
        "request",
        "sign",
        "urllib",
        "wallet",
    )
    assert set(imported_modules) <= allowed_imports
    for module_name in imported_modules:
        normalized = "".join(character for character in module_name.lower() if character.isalnum())
        for fragment in forbidden_fragments:
            assert fragment not in normalized
