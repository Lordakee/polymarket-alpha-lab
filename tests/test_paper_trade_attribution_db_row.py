from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json

import pytest

from polymarket_alpha_lab.paper_trade_attribution import (
    PaperTradeAttributionReport,
    PaperTradeAttributionRow,
)
from polymarket_alpha_lab.paper_trade_attribution_db_row import (
    PaperTradeAttributionReportDbRow,
    paper_trade_attribution_report_from_db_row,
    paper_trade_attribution_report_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
FIRST_DECISION_AT = datetime(2026, 6, 18, 9, 1, 30, tzinfo=UTC)
LATEST_DECISION_AT = datetime(2026, 6, 18, 9, 4, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-trade-attribution-db-v0"


class PaperTradeAttributionReportSubclass(PaperTradeAttributionReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _row(
    *,
    market_slug: str = "market-a",
    side: str = "yes",
    status: str = "complete",
    trade_count: int = 2,
    filled_count: int = 2,
    complete_fill_count: int = 2,
    partial_fill_count: int = 0,
    resolved_count: int | None = 1,
    pending_count: int | None = 1,
    realized_win_count: int | None = 1,
    realized_loss_count: int | None = 0,
    total_requested_size: Decimal = d("150"),
    total_filled_size: Decimal = d("150"),
    total_unfilled_size: Decimal = d("0"),
    total_notional: Decimal = d("79.0000"),
    reason_codes: tuple[str, ...] = (
        "fill_complete",
        "sizing_limiter:max_executable_size",
    ),
) -> PaperTradeAttributionRow:
    return PaperTradeAttributionRow(
        market_slug=market_slug,
        side=side,
        status=status,
        trade_count=trade_count,
        filled_count=filled_count,
        complete_fill_count=complete_fill_count,
        partial_fill_count=partial_fill_count,
        resolved_count=resolved_count,
        pending_count=pending_count,
        realized_win_count=realized_win_count,
        realized_loss_count=realized_loss_count,
        total_requested_size=total_requested_size,
        total_filled_size=total_filled_size,
        total_unfilled_size=total_unfilled_size,
        total_notional=total_notional,
        reason_codes=reason_codes,
    )


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
) -> PaperTradeAttributionReport:
    rows = (
        _row(),
        _row(
            market_slug="market-b",
            side="no",
            status="partial",
            complete_fill_count=0,
            partial_fill_count=2,
            resolved_count=1,
            pending_count=1,
            realized_win_count=0,
            realized_loss_count=1,
            total_requested_size=d("200"),
            total_filled_size=d("70"),
            total_unfilled_size=d("130"),
            total_notional=d("19.0000"),
            reason_codes=("fill_partial", "sizing_limiter:book_depth"),
        ),
    )
    return PaperTradeAttributionReport(
        generated_at=generated_at,
        config_version=CONFIG_VERSION,
        trade_count=4,
        row_count=2,
        market_count=2,
        filled_count=4,
        complete_fill_count=2,
        partial_fill_count=2,
        resolved_count=2,
        pending_count=2,
        realized_win_count=1,
        realized_loss_count=1,
        total_requested_size=d("350"),
        total_filled_size=d("220"),
        total_unfilled_size=d("130"),
        total_notional=d("98.0000"),
        first_trade_decision_at=FIRST_DECISION_AT,
        latest_trade_decision_at=LATEST_DECISION_AT,
        rows=rows,
    )


def _empty_report() -> PaperTradeAttributionReport:
    return PaperTradeAttributionReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        trade_count=0,
        row_count=0,
        market_count=0,
        filled_count=0,
        complete_fill_count=0,
        partial_fill_count=0,
        resolved_count=None,
        pending_count=None,
        realized_win_count=None,
        realized_loss_count=None,
        total_requested_size=d("0"),
        total_filled_size=d("0"),
        total_unfilled_size=d("0"),
        total_notional=d("0"),
        first_trade_decision_at=None,
        latest_trade_decision_at=None,
        rows=(),
    )


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _unchecked_row(row: object, **overrides: object) -> object:
    values = dict(row.__dict__)
    values.update(overrides)
    unchecked = object.__new__(type(row))
    for field_name, value in values.items():
        object.__setattr__(unchecked, field_name, value)
    return unchecked


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_db_row_serializes_core_attribution_payload_and_round_trips() -> None:
    report = _report(
        generated_at=datetime(2026, 6, 18, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    row = paper_trade_attribution_report_to_db_row(report)

    assert type(row) is PaperTradeAttributionReportDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.trade_count == 4
    assert row.row_count == 2
    assert row.market_count == 2
    assert row.filled_count == 4
    assert row.complete_fill_count == 2
    assert row.partial_fill_count == 2
    assert row.resolved_count == 2
    assert row.pending_count == 2
    assert row.realized_win_count == 1
    assert row.realized_loss_count == 1
    assert row.total_requested_size == d("350")
    assert row.total_filled_size == d("220")
    assert row.total_unfilled_size == d("130")
    assert row.total_notional == d("98.0000")
    assert row.first_trade_decision_at == FIRST_DECISION_AT
    assert row.latest_trade_decision_at == LATEST_DECISION_AT
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json == {
        "generated_at": "2026-06-18T12:00:00+00:00",
        "config_version": CONFIG_VERSION,
        "trade_count": 4,
        "row_count": 2,
        "market_count": 2,
        "filled_count": 4,
        "complete_fill_count": 2,
        "partial_fill_count": 2,
        "resolved_count": 2,
        "pending_count": 2,
        "realized_win_count": 1,
        "realized_loss_count": 1,
        "total_requested_size": "350",
        "total_filled_size": "220",
        "total_unfilled_size": "130",
        "total_notional": "98.0000",
        "first_trade_decision_at": "2026-06-18T09:01:30+00:00",
        "latest_trade_decision_at": "2026-06-18T09:04:30+00:00",
        "rows": [
            {
                "market_slug": "market-a",
                "side": "yes",
                "status": "complete",
                "trade_count": 2,
                "filled_count": 2,
                "complete_fill_count": 2,
                "partial_fill_count": 0,
                "resolved_count": 1,
                "pending_count": 1,
                "realized_win_count": 1,
                "realized_loss_count": 0,
                "total_requested_size": "150",
                "total_filled_size": "150",
                "total_unfilled_size": "0",
                "total_notional": "79.0000",
                "reason_codes": [
                    "fill_complete",
                    "sizing_limiter:max_executable_size",
                ],
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            {
                "market_slug": "market-b",
                "side": "no",
                "status": "partial",
                "trade_count": 2,
                "filled_count": 2,
                "complete_fill_count": 0,
                "partial_fill_count": 2,
                "resolved_count": 1,
                "pending_count": 1,
                "realized_win_count": 0,
                "realized_loss_count": 1,
                "total_requested_size": "200",
                "total_filled_size": "70",
                "total_unfilled_size": "130",
                "total_notional": "19.0000",
                "reason_codes": ["fill_partial", "sizing_limiter:book_depth"],
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _assert_no_floats(row.payload_json)

    assert paper_trade_attribution_report_from_db_row(row) == report


def test_db_row_preserves_empty_report_null_metrics_and_round_trips() -> None:
    row = paper_trade_attribution_report_to_db_row(_empty_report())

    assert row.trade_count == 0
    assert row.row_count == 0
    assert row.market_count == 0
    assert row.resolved_count is None
    assert row.first_trade_decision_at is None
    assert row.latest_trade_decision_at is None
    assert row.total_notional == d("0")
    assert row.payload_json["rows"] == []
    assert row.payload_json["resolved_count"] is None

    assert paper_trade_attribution_report_from_db_row(row) == _empty_report()


def test_db_row_hash_uses_full_canonical_payload_and_is_deterministic() -> None:
    report = _report()
    same_report = PaperTradeAttributionReport(**report.__dict__)
    different_payload_same_summary = replace(
        report,
        config_version="paper-trade-attribution-db-v1",
    )

    first = paper_trade_attribution_report_to_db_row(report)
    second = paper_trade_attribution_report_to_db_row(same_report)
    different = paper_trade_attribution_report_to_db_row(different_payload_same_summary)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != different.report_sha256
    assert first.trade_count == different.trade_count
    assert first.total_notional == different.total_notional


def test_db_row_is_frozen() -> None:
    row = paper_trade_attribution_report_to_db_row(_empty_report())

    with pytest.raises(FrozenInstanceError):
        row.trade_count = 1  # type: ignore[misc]


def test_db_row_rejects_wrong_report_type_and_subclasses() -> None:
    with pytest.raises(ValueError, match="PaperTradeAttributionReport"):
        paper_trade_attribution_report_to_db_row(object())

    report = _empty_report()
    subclass = PaperTradeAttributionReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperTradeAttributionReport"):
        paper_trade_attribution_report_to_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_db_row_rejects_false_report_flags(flag_name: str) -> None:
    report = _empty_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_trade_attribution_report_to_db_row(report)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_db_row_rejects_false_stored_payload_flags(flag_name: str) -> None:
    row = paper_trade_attribution_report_to_db_row(_empty_report())

    with pytest.raises(ValueError, match=flag_name):
        PaperTradeAttributionReportDbRow(
            **{
                **row.__dict__,
                "report_sha256": "a" * 64,
                "payload_json": {**row.payload_json, flag_name: False},
            },
        )


def test_db_row_validates_shape_floats_and_summary_matches_payload() -> None:
    row = paper_trade_attribution_report_to_db_row(_report())

    with pytest.raises(ValueError, match="report_sha256"):
        replace(row, report_sha256="bad")

    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})

    with pytest.raises(ValueError, match="filled_count must match payload_json"):
        replace(row, filled_count=3)

    with pytest.raises(ValueError, match="report_sha256 must match payload_json"):
        replace(row, report_sha256="b" * 64)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("total_requested_size", d("350.0000")),
        ("total_filled_size", d("220.0")),
        ("total_unfilled_size", d("130.000000")),
        ("total_notional", d("98")),
    ),
)
def test_db_row_from_db_row_accepts_equivalent_materialized_decimal_exponents(
    field_name: str,
    value: Decimal,
) -> None:
    row = paper_trade_attribution_report_to_db_row(_report())
    equivalent = _unchecked_row(row, **{field_name: value})

    assert paper_trade_attribution_report_from_db_row(equivalent) == _report()


def test_db_row_from_db_row_accepts_self_hashed_legacy_decimal_payload_strings() -> None:
    row = paper_trade_attribution_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload.update(
        {
            "total_requested_size": "350.0000",
            "total_filled_size": "220.0",
            "total_unfilled_size": "130.000000",
            "total_notional": "98",
        },
    )
    payload["rows"][0]["total_notional"] = "79"

    legacy_row = PaperTradeAttributionReportDbRow(
        **{
            **row.__dict__,
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
        },
    )

    assert paper_trade_attribution_report_from_db_row(legacy_row) == _report()


def test_db_row_rejects_raw_decimal_payload_before_normalization() -> None:
    row = paper_trade_attribution_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["total_notional"] = Decimal("98")

    with pytest.raises(ValueError, match="Decimal|JSON"):
        PaperTradeAttributionReportDbRow(**{**row.__dict__, "payload_json": payload})

    with pytest.raises(ValueError, match="Decimal|JSON"):
        paper_trade_attribution_report_from_db_row(
            _unchecked_row(row, payload_json=payload),
        )


def test_db_row_rejects_raw_datetime_payload_before_normalization() -> None:
    row = paper_trade_attribution_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["generated_at"] = GENERATED_AT

    with pytest.raises(ValueError, match="datetime|JSON"):
        PaperTradeAttributionReportDbRow(**{**row.__dict__, "payload_json": payload})

    with pytest.raises(ValueError, match="datetime|JSON"):
        paper_trade_attribution_report_from_db_row(
            _unchecked_row(row, payload_json=payload),
        )


def test_db_row_from_db_row_rejects_bool_int_confusion_in_bypassed_row() -> None:
    row = paper_trade_attribution_report_to_db_row(_report())

    with pytest.raises(ValueError, match="paper_only"):
        paper_trade_attribution_report_from_db_row(_unchecked_row(row, paper_only=1))

    payload = deepcopy(row.payload_json)
    payload["trade_count"] = True
    with pytest.raises(ValueError, match="trade_count"):
        paper_trade_attribution_report_from_db_row(
            _unchecked_row(
                row,
                report_sha256=_canonical_payload_sha256(payload),
                payload_json=payload,
            ),
        )


def test_db_row_from_db_row_rejects_unchecked_payload_row_total_mismatch() -> None:
    row = paper_trade_attribution_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["rows"][0]["total_notional"] = "80"
    malformed = _unchecked_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="total_notional|payload_json"):
        paper_trade_attribution_report_from_db_row(malformed)
