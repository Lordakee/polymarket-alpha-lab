from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 2, 18, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_close_acknowledgement_recheck_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _config(**overrides: object):
    module = api()
    values = {
        "max_recheck_age_seconds": d("3600.000000"),
        "max_close_evidence_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.MarketCloseAcknowledgementRecheckExceptionConfig(**values)


def _input_row(
    market_id: str,
    *,
    team_id: str = "team-alpha",
    category_id: str = "politics",
    market_closed_at: datetime | None = None,
    close_evidence_observed_at: datetime | None = None,
    acknowledgement_observed_at: datetime | None = None,
    rechecked_at: datetime | None = None,
    outcome_source: str = "acknowledgement",
):
    module = api()
    return module.MarketCloseAcknowledgementRecheckExceptionInputRow(
        market_id=market_id,
        team_id=team_id,
        category_id=category_id,
        market_closed_at=market_closed_at or _at(hours=4),
        close_evidence_observed_at=close_evidence_observed_at,
        acknowledgement_observed_at=acknowledgement_observed_at,
        rechecked_at=rechecked_at,
        outcome_source=outcome_source,
    )


def _build_report(*rows, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_close_acknowledgement_recheck_exception_report(
        rows,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_exception_report_flags_market_close_acknowledgement_recheck_exceptions() -> None:
    report = _build_report(
        _input_row(
            "market-clear",
            team_id="team-beta",
            category_id="economics",
            market_closed_at=_at(hours=2),
            close_evidence_observed_at=_at(minutes=20),
            acknowledgement_observed_at=_at(minutes=15),
            rechecked_at=_at(minutes=5),
        ),
        _input_row(
            "market-missing-evidence",
            market_closed_at=_at(hours=6),
            close_evidence_observed_at=None,
            acknowledgement_observed_at=_at(minutes=25),
            rechecked_at=_at(minutes=10),
        ),
        _input_row(
            "market-missing-ack",
            team_id="team-gamma",
            category_id="sports",
            market_closed_at=_at(hours=5),
            close_evidence_observed_at=_at(minutes=30),
            acknowledgement_observed_at=None,
            rechecked_at=_at(minutes=20),
        ),
        _input_row(
            "market-stale-recheck",
            team_id="team-gamma",
            category_id="sports",
            market_closed_at=_at(hours=4),
            close_evidence_observed_at=_at(minutes=40),
            acknowledgement_observed_at=_at(minutes=35),
            rechecked_at=_at(hours=2),
        ),
        _input_row(
            "market-stale-evidence",
            team_id="team-beta",
            category_id="economics",
            market_closed_at=_at(hours=8),
            close_evidence_observed_at=_at(hours=3),
            acknowledgement_observed_at=_at(minutes=45),
            rechecked_at=_at(minutes=30),
        ),
        _input_row(
            "market-non-ack-source",
            team_id="team-alpha",
            category_id="politics",
            market_closed_at=_at(hours=7),
            close_evidence_observed_at=_at(minutes=35),
            acknowledgement_observed_at=_at(minutes=30),
            rechecked_at=_at(minutes=25),
            outcome_source="resolver",
        ),
        _input_row(
            "market-critical-combo",
            team_id="team-alpha",
            category_id="politics",
            market_closed_at=_at(hours=9),
            close_evidence_observed_at=None,
            acknowledgement_observed_at=None,
            rechecked_at=_at(hours=3),
            outcome_source="manual",
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.report_status == "critical"
    assert report.reason_codes == (
        "market_close_ack_recheck_missing_close_evidence",
        "market_close_ack_recheck_missing_acknowledgement",
        "market_close_ack_recheck_stale_recheck",
        "market_close_ack_recheck_stale_close_evidence",
        "market_close_ack_recheck_outcome_source_not_acknowledgement",
    )
    assert report.market_count == d("7.000000")
    assert report.clear_count == d("1.000000")
    assert report.watch_count == d("3.000000")
    assert report.critical_count == d("3.000000")
    assert report.exception_count == d("6.000000")
    assert report.exception_ratio == d("0.857143")
    assert report.missing_close_evidence_count == d("2.000000")
    assert report.missing_acknowledgement_count == d("2.000000")
    assert report.stale_recheck_count == d("2.000000")
    assert report.stale_close_evidence_count == d("1.000000")
    assert report.non_acknowledged_outcome_source_count == d("2.000000")
    assert report.max_recheck_age_seconds_observed == d("10800.000000")
    assert report.max_close_evidence_age_seconds_observed == d("10800.000000")

    assert tuple(row.market_id for row in report.rows) == (
        "market-critical-combo",
        "market-missing-ack",
        "market-missing-evidence",
        "market-non-ack-source",
        "market-stale-evidence",
        "market-stale-recheck",
        "market-clear",
    )

    combo = report.rows[0]
    assert combo.severity == "critical"
    assert combo.reason_codes == (
        "market_close_ack_recheck_missing_close_evidence",
        "market_close_ack_recheck_missing_acknowledgement",
        "market_close_ack_recheck_stale_recheck",
        "market_close_ack_recheck_outcome_source_not_acknowledgement",
    )
    assert combo.close_evidence_age_seconds is None
    assert combo.recheck_age_seconds == d("10800.000000")

    missing_ack = report.rows[1]
    assert missing_ack.severity == "critical"
    assert missing_ack.reason_codes == (
        "market_close_ack_recheck_missing_acknowledgement",
    )

    missing_evidence = report.rows[2]
    assert missing_evidence.severity == "critical"
    assert missing_evidence.reason_codes == (
        "market_close_ack_recheck_missing_close_evidence",
    )

    non_ack_source = report.rows[3]
    assert non_ack_source.severity == "watch"
    assert non_ack_source.outcome_source_acknowledged is False
    assert non_ack_source.reason_codes == (
        "market_close_ack_recheck_outcome_source_not_acknowledgement",
    )

    stale_evidence = report.rows[4]
    assert stale_evidence.reason_codes == (
        "market_close_ack_recheck_stale_close_evidence",
    )
    assert stale_evidence.close_evidence_age_seconds == d("10800.000000")

    stale_recheck = report.rows[5]
    assert stale_recheck.reason_codes == (
        "market_close_ack_recheck_stale_recheck",
    )

    clear = report.rows[6]
    assert clear.severity == "clear"
    assert clear.reason_codes == (
        "market_close_ack_recheck_clear",
    )

    assert tuple(
        (
            row.team_id,
            row.category_id,
            row.severity,
            row.market_count,
            row.exception_ratio,
        )
        for row in report.team_category_rollups
    ) == (
        ("team-alpha", "politics", "critical", d("3.000000"), d("1.000000")),
        ("team-gamma", "sports", "critical", d("2.000000"), d("1.000000")),
        ("team-beta", "economics", "watch", d("2.000000"), d("0.500000")),
    )
    alpha = report.team_category_rollups[0]
    assert alpha.critical_count == d("2.000000")
    assert alpha.watch_count == d("1.000000")
    assert alpha.clear_count == d("0.000000")
    assert alpha.reason_codes == (
        "market_close_ack_recheck_missing_close_evidence",
        "market_close_ack_recheck_missing_acknowledgement",
        "market_close_ack_recheck_stale_recheck",
        "market_close_ack_recheck_outcome_source_not_acknowledgement",
    )

    for value in _decimal_public_values(report):
        assert value is None or type(value) is Decimal
    for row in report.rows:
        for value in _decimal_public_values(row):
            assert value is None or type(value) is Decimal
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True


def test_empty_and_clear_exception_reports_are_deterministic_report_only() -> None:
    empty = _build_report()

    assert empty.report_status == "empty"
    assert empty.reason_codes == (
        "market_close_ack_recheck_exception_report_empty",
    )
    assert empty.market_count == d("0.000000")
    assert empty.exception_count == d("0.000000")
    assert empty.exception_ratio == d("0.000000")
    assert empty.max_recheck_age_seconds_observed == d("0.000000")
    assert empty.max_close_evidence_age_seconds_observed == d("0.000000")
    assert empty.rows == ()
    assert empty.team_category_rollups == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    clear = _build_report(
        _input_row(
            "market-clear",
            close_evidence_observed_at=_at(minutes=20),
            acknowledgement_observed_at=_at(minutes=15),
            rechecked_at=_at(minutes=5),
        ),
    )

    assert clear.report_status == "clear"
    assert clear.reason_codes == (
        "market_close_ack_recheck_clear",
    )
    assert clear.clear_count == d("1.000000")
    assert clear.exception_count == d("0.000000")
    assert clear.exception_ratio == d("0.000000")
    assert clear.rows[0].severity == "clear"


def test_max_decimal_helper_quantizes_observed_seconds() -> None:
    module = api()

    assert module._max_decimal(  # noqa: SLF001
        (
            d("1.0000004"),
            d("2.1234564"),
            None,
        ),
    ) == d("2.123456")


def test_json_ready_payload_has_no_floats_and_uses_utc_datetime_strings() -> None:
    module = api()
    generated_at = datetime(2026, 7, 2, 10, 0, tzinfo=timezone(timedelta(hours=-8)))
    local_closed_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-8)))
    local_evidence_at = datetime(2026, 7, 2, 9, 0, tzinfo=timezone(timedelta(hours=-8)))
    local_ack_at = datetime(2026, 7, 2, 9, 30, tzinfo=timezone(timedelta(hours=-8)))
    local_recheck_at = datetime(2026, 7, 2, 9, 45, tzinfo=timezone(timedelta(hours=-8)))

    report = module.build_market_close_acknowledgement_recheck_exception_report(
        (
            _input_row(
                "market-offset",
                market_closed_at=local_closed_at,
                close_evidence_observed_at=local_evidence_at,
                acknowledgement_observed_at=local_ack_at,
                rechecked_at=local_recheck_at,
            ),
        ),
        config=module.MarketCloseAcknowledgementRecheckExceptionConfig(),
        generated_at=generated_at,
    )

    payload = module.market_close_acknowledgement_recheck_exception_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T18:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["exception_ratio"] == "0.000000"
    assert payload["rows"][0]["market_closed_at"] == "2026-07-02T16:00:00+00:00"
    assert (
        payload["rows"][0]["close_evidence_observed_at"]
        == "2026-07-02T17:00:00+00:00"
    )
    assert payload["rows"][0]["acknowledgement_age_seconds"] == "1800.000000"
    assert payload["rows"][0]["recheck_age_seconds"] == "900.000000"


def test_public_contracts_are_frozen_decimal_only_and_reject_unsafe_inputs() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_EXCEPTION_CONFIG_VERSION",
        "MarketCloseAcknowledgementRecheckExceptionConfig",
        "MarketCloseAcknowledgementRecheckExceptionInputRow",
        "MarketCloseAcknowledgementRecheckExceptionReport",
        "MarketCloseAcknowledgementRecheckExceptionRollupRow",
        "MarketCloseAcknowledgementRecheckExceptionRow",
        "build_market_close_acknowledgement_recheck_exception_report",
        "market_close_acknowledgement_recheck_exception_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
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

    report = _build_report(
        _input_row(
            "market-frozen",
            close_evidence_observed_at=_at(minutes=20),
            acknowledgement_observed_at=_at(minutes=15),
            rechecked_at=_at(minutes=5),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].severity = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_close_acknowledgement_recheck_exception_report(
            (),
            config=module.MarketCloseAcknowledgementRecheckExceptionConfig(),
            generated_at=datetime(2026, 7, 2, 18, 0),
        )
    with pytest.raises(ValueError, match="max_recheck_age_seconds must be Decimal"):
        module.MarketCloseAcknowledgementRecheckExceptionConfig(
            max_recheck_age_seconds=3600,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="max_recheck_age_seconds must be Decimal"):
        module.MarketCloseAcknowledgementRecheckExceptionConfig(
            max_recheck_age_seconds=_DecimalSubclass("3600.000000"),
        )
    with pytest.raises(
        ValueError,
        match="max_recheck_age_seconds must be positive at 0.000001 precision",
    ):
        module.MarketCloseAcknowledgementRecheckExceptionConfig(
            max_recheck_age_seconds=d("0.0000004"),
        )
    with pytest.raises(ValueError, match="config_version contains unsafe public text"):
        module.MarketCloseAcknowledgementRecheckExceptionConfig(
            config_version="market-close-secret",
        )
    with pytest.raises(ValueError, match="market_id contains unsafe public text"):
        _input_row("market-private_key")
    with pytest.raises(ValueError, match="outcome_source"):
        _input_row(
            "market-bad-source",
            outcome_source="wallet",
        )
    with pytest.raises(ValueError, match="paper_only/report_only/readonly"):
        module.MarketCloseAcknowledgementRecheckExceptionConfig(paper_only=False)
    with pytest.raises(ValueError, match="market_closed_at cannot be after generated_at"):
        _build_report(
            _input_row(
                "market-future",
                market_closed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="generated_at cannot be before"):
        _build_report(
            _input_row(
                "market-before-close",
                market_closed_at=_at(hours=1),
                close_evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    with pytest.raises(ValueError, match="market_count must equal rows length"):
        replace(report, market_count=d("2.000000"))
    with pytest.raises(ValueError, match="market_count must be an integral Decimal count"):
        replace(report, market_count=d("1.0000004"))
    with pytest.raises(ValueError, match="exception_ratio must be <= 1.000000"):
        replace(report, exception_ratio=d("1.0000004"))


def test_module_has_no_io_trading_auth_or_float_surface() -> None:
    module = api()
    path = Path(module.__file__)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".", maxsplit=1)[0] for alias in node.names}
            assert not imported & forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".", maxsplit=1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            assert call_name not in {"open", "print", "exec", "eval", "compile"}

    forbidden_fragments = (
        "db",
        "database",
        "network",
        "trade",
        "trading",
        "wallet",
        "broker",
        "order",
        "sign",
        "auth",
        "advice",
    )
    public_names = [
        name
        for name in dir(module)
        if not name.startswith("_") and name not in {"Any", "UTC", "Decimal"}
    ]
    assert not any(
        fragment in name.lower()
        for name in public_names
        for fragment in forbidden_fragments
    )


def _decimal_public_values(value: object) -> tuple[Decimal | None, ...]:
    values: list[Decimal | None] = []
    if is_dataclass(value):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            field_value = getattr(value, field.name)
            if isinstance(field_value, Decimal) or field_value is None:
                values.append(field_value)
    return tuple(values)


def _float_paths(value: Any, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
