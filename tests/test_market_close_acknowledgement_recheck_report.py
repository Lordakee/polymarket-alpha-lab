from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_close_acknowledgement_recheck_report",
    )


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _d(value: str) -> Decimal:
    return Decimal(value)


def _input_row(
    market_id: str,
    *,
    team_owner_id: str | None = "resolution-team",
    source_id: str = "official-source",
    latest_update_id: str = "update-current",
    acknowledged_update_id: str | None = "update-current",
    market_closed_at: datetime | None = None,
    latest_update_at: datetime | None = None,
    acknowledgement_at: datetime | None = None,
    source_contradicts_outcome: bool = False,
):
    recheck_module = module()
    return recheck_module.MarketCloseAcknowledgementRecheckInputRow(
        market_id=market_id,
        team_owner_id=team_owner_id,
        source_id=source_id,
        latest_update_id=latest_update_id,
        acknowledged_update_id=acknowledged_update_id,
        market_closed_at=market_closed_at or _at(hours=2),
        latest_update_at=latest_update_at or _at(minutes=45),
        acknowledgement_at=acknowledgement_at,
        source_contradicts_outcome=source_contradicts_outcome,
    )


def _build_report(*rows):
    recheck_module = module()
    return recheck_module.build_market_close_acknowledgement_recheck_report(
        rows,
        config=recheck_module.MarketCloseAcknowledgementRecheckConfig(
            config_version="market-close-acknowledgement-recheck-test-v0",
            stale_acknowledgement_seconds=_d("3600.000000"),
            close_age_pressure_seconds=_d("7200.000000"),
        ),
        generated_at=GENERATED_AT,
    )


def test_recheck_report_flags_domain_gaps_with_decimal_metrics_and_stable_sorting() -> None:
    report = _build_report(
        _input_row(
            "m-pass",
            market_closed_at=_at(hours=1),
            latest_update_at=_at(minutes=40),
            acknowledgement_at=_at(minutes=30),
        ),
        _input_row(
            "m-stale",
            latest_update_id="update-current",
            acknowledged_update_id="update-previous",
            market_closed_at=_at(hours=2),
            latest_update_at=_at(minutes=50),
            acknowledgement_at=_at(minutes=40),
        ),
        _input_row(
            "m-owner",
            team_owner_id=None,
            market_closed_at=_at(hours=2),
            latest_update_at=_at(minutes=30),
            acknowledgement_at=_at(minutes=20),
        ),
        _input_row(
            "m-contradictory",
            market_closed_at=_at(hours=3),
            latest_update_at=_at(minutes=25),
            acknowledgement_at=_at(minutes=15),
            source_contradicts_outcome=True,
        ),
        _input_row(
            "m-pressure",
            market_closed_at=_at(hours=4),
            latest_update_at=_at(minutes=20),
            acknowledgement_at=_at(minutes=10),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_close_acknowledgement_recheck_stale_acknowledgement",
        "market_close_acknowledgement_recheck_missing_team_owner",
        "market_close_acknowledgement_recheck_contradictory_source",
        "market_close_acknowledgement_recheck_close_age_pressure",
    )
    assert report.market_count == _d("5.000000")
    assert report.pass_market_count == _d("1.000000")
    assert report.watch_market_count == _d("2.000000")
    assert report.blocked_market_count == _d("2.000000")
    assert report.recheck_market_count == _d("4.000000")
    assert report.stale_acknowledgement_count == _d("1.000000")
    assert report.missing_team_owner_count == _d("1.000000")
    assert report.contradictory_source_count == _d("1.000000")
    assert report.close_age_pressure_count == _d("1.000000")
    assert report.recheck_ratio == _d("0.800000")
    assert report.max_market_close_age_seconds == _d("14400.000000")

    assert tuple(row.market_id for row in report.rows) == (
        "m-owner",
        "m-contradictory",
        "m-stale",
        "m-pressure",
        "m-pass",
    )

    owner = report.rows[0]
    contradictory = report.rows[1]
    stale = report.rows[2]
    pressure = report.rows[3]
    passing = report.rows[4]

    assert owner.recheck_status == "blocked"
    assert owner.reason_codes == (
        "market_close_acknowledgement_recheck_missing_team_owner",
    )
    assert contradictory.reason_codes == (
        "market_close_acknowledgement_recheck_contradictory_source",
    )
    assert stale.recheck_status == "watch"
    assert stale.reason_codes == (
        "market_close_acknowledgement_recheck_stale_acknowledgement",
    )
    assert stale.acknowledgement_lag_seconds is None
    assert stale.acknowledgement_age_seconds == _d("2400.000000")
    assert pressure.reason_codes == (
        "market_close_acknowledgement_recheck_close_age_pressure",
    )
    assert pressure.market_close_age_seconds == _d("14400.000000")
    assert passing.recheck_status == "pass"
    assert passing.reason_codes == (
        "market_close_acknowledgement_recheck_clear",
    )
    assert passing.update_age_seconds == _d("2400.000000")
    assert passing.acknowledgement_lag_seconds == _d("600.000000")

    for value in _decimal_public_values(report):
        assert value is None or type(value) is Decimal
    for row in report.rows:
        for value in _decimal_public_values(row):
            assert value is None or type(value) is Decimal
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_recheck_report_is_report_only_and_deterministic() -> None:
    recheck_module = module()

    report = recheck_module.build_market_close_acknowledgement_recheck_report(
        (),
        config=recheck_module.MarketCloseAcknowledgementRecheckConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "empty"
    assert report.reason_codes == (
        "empty_market_close_acknowledgement_recheck_input",
    )
    assert report.market_count == _d("0.000000")
    assert report.recheck_market_count == _d("0.000000")
    assert report.recheck_ratio == _d("0.000000")
    assert report.max_market_close_age_seconds is None
    assert report.max_update_age_seconds is None
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_json_ready_payload_has_no_floats_and_uses_utc_strings() -> None:
    recheck_module = module()
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    market_closed_at = datetime(2026, 7, 2, 7, 0, tzinfo=timezone(timedelta(hours=-4)))
    latest_update_at = datetime(2026, 7, 2, 7, 30, tzinfo=timezone(timedelta(hours=-4)))
    acknowledgement_at = datetime(2026, 7, 2, 7, 45, tzinfo=timezone(timedelta(hours=-4)))

    report = recheck_module.build_market_close_acknowledgement_recheck_report(
        (
            _input_row(
                "m-offset",
                market_closed_at=market_closed_at,
                latest_update_at=latest_update_at,
                acknowledgement_at=acknowledgement_at,
            ),
        ),
        config=recheck_module.MarketCloseAcknowledgementRecheckConfig(),
        generated_at=generated_at,
    )

    payload = recheck_module.market_close_acknowledgement_recheck_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["recheck_ratio"] == "0.000000"
    assert payload["rows"][0]["market_closed_at"] == "2026-07-02T11:00:00+00:00"
    assert payload["rows"][0]["latest_update_at"] == "2026-07-02T11:30:00+00:00"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "900.000000"


def test_public_contracts_are_frozen_and_reject_non_decimal_or_naive_inputs() -> None:
    recheck_module = module()

    assert recheck_module.__all__ == (
        "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_CONFIG_VERSION",
        "MarketCloseAcknowledgementRecheckConfig",
        "MarketCloseAcknowledgementRecheckInputRow",
        "MarketCloseAcknowledgementRecheckReport",
        "MarketCloseAcknowledgementRecheckRow",
        "build_market_close_acknowledgement_recheck_report",
        "market_close_acknowledgement_recheck_report_payload",
    )
    for exported_name in recheck_module.__all__:
        exported = getattr(recheck_module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True
            defaults = {field.name: field.default for field in fields(exported)}
            assert defaults["paper_only"] is True
            assert defaults["report_only"] is True
            assert defaults["readonly"] is True
            for field_name, hint in get_type_hints(exported).items():
                if field_name in {"paper_only", "report_only", "readonly"}:
                    continue
                assert not _type_uses_float(hint)

    row = _input_row("m-frozen", acknowledgement_at=_at(minutes=10))
    with pytest.raises(FrozenInstanceError):
        row.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        recheck_module.MarketCloseAcknowledgementRecheckConfig(
            stale_acknowledgement_seconds=3600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(recheck_module.MarketCloseAcknowledgementRecheckConfig(), paper_only=False)

    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row("m-naive", market_closed_at=datetime(2026, 7, 2, 10, 0))

    with pytest.raises(ValueError, match="source_contradicts_outcome must be a bool"):
        _input_row(
            "m-bool",
            acknowledgement_at=_at(minutes=10),
            source_contradicts_outcome=1,  # type: ignore[arg-type]
        )


def test_future_times_duplicates_and_manual_inconsistency_are_rejected() -> None:
    recheck_module = module()

    with pytest.raises(ValueError, match="market_closed_at"):
        recheck_module.build_market_close_acknowledgement_recheck_report(
            (_input_row("m-future-close", market_closed_at=GENERATED_AT + timedelta(seconds=1)),),
            config=recheck_module.MarketCloseAcknowledgementRecheckConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="latest_update_at"):
        recheck_module.build_market_close_acknowledgement_recheck_report(
            (_input_row("m-future-update", latest_update_at=GENERATED_AT + timedelta(seconds=1)),),
            config=recheck_module.MarketCloseAcknowledgementRecheckConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="acknowledgement_at"):
        recheck_module.build_market_close_acknowledgement_recheck_report(
            (
                _input_row(
                    "m-future-ack",
                    acknowledgement_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=recheck_module.MarketCloseAcknowledgementRecheckConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="acknowledgement_at"):
        _input_row(
            "m-ack-before-close",
            market_closed_at=_at(hours=1),
            latest_update_at=_at(minutes=30),
            acknowledgement_at=_at(hours=2),
        )

    duplicate = _input_row("m-duplicate", acknowledgement_at=_at(minutes=10))
    with pytest.raises(ValueError, match="unique"):
        recheck_module.build_market_close_acknowledgement_recheck_report(
            (duplicate, duplicate),
            config=recheck_module.MarketCloseAcknowledgementRecheckConfig(),
            generated_at=GENERATED_AT,
        )

    report = _build_report(_input_row("m-pass", acknowledgement_at=_at(minutes=10)))
    with pytest.raises(ValueError, match="market_count"):
        recheck_module.MarketCloseAcknowledgementRecheckReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            report_status=report.report_status,
            reason_codes=report.reason_codes,
            market_count=_d("2.000000"),
            pass_market_count=report.pass_market_count,
            watch_market_count=report.watch_market_count,
            blocked_market_count=report.blocked_market_count,
            recheck_market_count=report.recheck_market_count,
            stale_acknowledgement_count=report.stale_acknowledgement_count,
            missing_team_owner_count=report.missing_team_owner_count,
            contradictory_source_count=report.contradictory_source_count,
            close_age_pressure_count=report.close_age_pressure_count,
            recheck_ratio=report.recheck_ratio,
            max_market_close_age_seconds=report.max_market_close_age_seconds,
            max_update_age_seconds=report.max_update_age_seconds,
            max_acknowledgement_age_seconds=report.max_acknowledgement_age_seconds,
            rows=report.rows,
        )


def test_module_surface_stays_pure_in_memory_report_only() -> None:
    source = Path(module().__file__).read_text(encoding="utf-8").lower()

    assert "requests" not in source
    assert "httpx" not in source
    assert "socket" not in source
    assert "web3" not in source
    assert "py_clob_client" not in source
    assert "psycopg" not in source
    for fragment in _unsafe_surface_fragments():
        assert fragment not in source


def _decimal_public_values(value: object) -> tuple[Decimal | None, ...]:
    values: list[Decimal | None] = []
    for field in fields(value):
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
        ):
            item = getattr(value, field.name)
            if item is None:
                values.append(None)
            else:
                assert type(item) is Decimal
                values.append(item)
    return tuple(values)


def _float_paths(value: Any, *, prefix: str = "$") -> tuple[str, ...]:
    if type(value) is float:
        return (prefix,)
    if isinstance(value, dict):
        return tuple(
            path
            for key, item in value.items()
            for path in _float_paths(item, prefix=f"{prefix}.{key}")
        )
    if isinstance(value, list):
        return tuple(
            path
            for index, item in enumerate(value)
            for path in _float_paths(item, prefix=f"{prefix}[{index}]")
        )
    return ()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


def _unsafe_surface_fragments() -> tuple[str, ...]:
    return (
        _join("per", "sistence"),
        _join("net", "work"),
        _join("li", "ve"),
        _join("au", "th"),
        _join("wal", "let"),
        _join("acc", "ount"),
        _join("bro", "ker"),
        _join("or", "der"),
        _join("sub", "mit"),
        _join("can", "cel"),
        _join("sig", "ning"),
        _join("ad", "vice"),
    )


def _join(*parts: str) -> str:
    return "".join(parts)
