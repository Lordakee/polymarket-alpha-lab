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


GENERATED_AT = datetime(2026, 7, 2, 16, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_close_acknowledgement_recheck_status_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _config(**overrides: object):
    module = api()
    values = {
        "overdue_recheck_seconds": d("3600.000000"),
        "source_stale_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.MarketCloseAcknowledgementRecheckStatusConfig(**values)


def _input_row(
    market_id: str,
    *,
    team_id: str = "team-alpha",
    category_id: str = "politics",
    market_closed_at: datetime | None = None,
    recheck_requested_at: datetime | None = None,
    source_observed_at: datetime | None = None,
    acknowledgement_at: datetime | None = None,
    rechecked_at: datetime | None = None,
    recheck_blocked: bool = False,
    source_contradicts_acknowledgement: bool = False,
):
    module = api()
    return module.MarketCloseAcknowledgementRecheckStatusInputRow(
        market_id=market_id,
        team_id=team_id,
        category_id=category_id,
        market_closed_at=market_closed_at or _at(hours=4),
        recheck_requested_at=recheck_requested_at or _at(minutes=30),
        source_observed_at=source_observed_at or _at(minutes=15),
        acknowledgement_at=acknowledgement_at,
        rechecked_at=rechecked_at,
        recheck_blocked=recheck_blocked,
        source_contradicts_acknowledgement=source_contradicts_acknowledgement,
    )


def _build_report(*rows, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_close_acknowledgement_recheck_status_report(
        rows,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_status_report_summarizes_states_by_team_category_with_stable_sorting() -> None:
    report = _build_report(
        _input_row(
            "market-cleared",
            team_id="team-beta",
            category_id="economics",
            market_closed_at=_at(hours=2),
            recheck_requested_at=_at(minutes=30),
            source_observed_at=_at(minutes=10),
            acknowledgement_at=_at(minutes=20),
            rechecked_at=_at(minutes=5),
        ),
        _input_row(
            "market-overdue",
            team_id="team-alpha",
            category_id="politics",
            market_closed_at=_at(hours=3),
            recheck_requested_at=_at(hours=2),
            source_observed_at=_at(minutes=20),
        ),
        _input_row(
            "market-blocked",
            team_id="team-alpha",
            category_id="politics",
            market_closed_at=_at(hours=5),
            recheck_requested_at=_at(minutes=45),
            source_observed_at=_at(minutes=20),
            recheck_blocked=True,
        ),
        _input_row(
            "market-watch",
            team_id="team-gamma",
            category_id="sports",
            market_closed_at=_at(hours=2),
            recheck_requested_at=_at(minutes=20),
            source_observed_at=_at(minutes=10),
        ),
        _input_row(
            "market-stale",
            team_id="team-gamma",
            category_id="sports",
            market_closed_at=_at(hours=2),
            recheck_requested_at=_at(minutes=15),
            source_observed_at=_at(hours=1),
            acknowledgement_at=_at(minutes=12),
            rechecked_at=_at(minutes=10),
        ),
        _input_row(
            "market-contradiction",
            team_id="team-alpha",
            category_id="politics",
            market_closed_at=_at(hours=4),
            recheck_requested_at=_at(minutes=40),
            source_observed_at=_at(minutes=12),
            acknowledgement_at=_at(minutes=30),
            rechecked_at=_at(minutes=5),
            source_contradicts_acknowledgement=True,
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_close_acknowledgement_recheck_status_blocked",
        "market_close_acknowledgement_recheck_status_overdue",
        "market_close_acknowledgement_recheck_status_watch",
        "market_close_acknowledgement_recheck_status_stale_source",
        "market_close_acknowledgement_recheck_status_contradiction",
    )
    assert report.market_count == d("6.000000")
    assert report.blocked_count == d("2.000000")
    assert report.overdue_count == d("1.000000")
    assert report.watch_count == d("2.000000")
    assert report.cleared_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.contradiction_count == d("1.000000")
    assert report.issue_count == d("5.000000")
    assert report.issue_ratio == d("0.833333")
    assert report.max_recheck_age_seconds == d("7200.000000")
    assert report.max_source_age_seconds == d("3600.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_id for row in report.rows) == (
        "market-blocked",
        "market-contradiction",
        "market-overdue",
        "market-stale",
        "market-watch",
        "market-cleared",
    )
    assert report.rows[0].status == "blocked"
    assert report.rows[0].reason_codes == (
        "market_close_acknowledgement_recheck_status_blocked",
    )
    assert report.rows[1].reason_codes == (
        "market_close_acknowledgement_recheck_status_contradiction",
    )
    assert report.rows[2].status == "overdue"
    assert report.rows[2].recheck_age_seconds == d("7200.000000")
    assert report.rows[3].status == "watch"
    assert report.rows[3].reason_codes == (
        "market_close_acknowledgement_recheck_status_stale_source",
    )
    assert report.rows[4].reason_codes == (
        "market_close_acknowledgement_recheck_status_watch",
    )
    assert report.rows[5].status == "cleared"
    assert report.rows[5].reason_codes == (
        "market_close_acknowledgement_recheck_status_cleared",
    )
    assert report.rows[5].acknowledgement_age_seconds == d("1200.000000")

    assert tuple(
        (row.team_id, row.category_id, row.status, row.market_count, row.issue_ratio)
        for row in report.team_category_rows
    ) == (
        ("team-alpha", "politics", "blocked", d("3.000000"), d("1.000000")),
        ("team-gamma", "sports", "watch", d("2.000000"), d("1.000000")),
        ("team-beta", "economics", "cleared", d("1.000000"), d("0.000000")),
    )
    alpha = report.team_category_rows[0]
    assert alpha.blocked_count == d("2.000000")
    assert alpha.overdue_count == d("1.000000")
    assert alpha.watch_count == d("0.000000")
    assert alpha.cleared_count == d("0.000000")
    assert alpha.contradiction_count == d("1.000000")
    assert alpha.reason_codes == (
        "market_close_acknowledgement_recheck_status_blocked",
        "market_close_acknowledgement_recheck_status_overdue",
        "market_close_acknowledgement_recheck_status_contradiction",
    )


def test_empty_and_clear_reports_use_decimal_zeroes_and_report_only_flags() -> None:
    empty = _build_report()

    assert empty.report_status == "empty"
    assert empty.reason_codes == (
        "market_close_acknowledgement_recheck_status_empty",
    )
    assert empty.market_count == d("0.000000")
    assert empty.issue_count == d("0.000000")
    assert empty.issue_ratio == d("0.000000")
    assert empty.max_recheck_age_seconds == d("0.000000")
    assert empty.max_source_age_seconds == d("0.000000")
    assert empty.rows == ()
    assert empty.team_category_rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    clear = _build_report(
        _input_row(
            "market-clear",
            team_id="team-beta",
            category_id="economics",
            acknowledgement_at=_at(minutes=20),
            rechecked_at=_at(minutes=5),
        ),
    )

    assert clear.report_status == "cleared"
    assert clear.reason_codes == (
        "market_close_acknowledgement_recheck_status_cleared",
    )
    assert clear.cleared_count == d("1.000000")
    assert clear.issue_ratio == d("0.000000")
    assert clear.team_category_rows[0].status == "cleared"


def test_json_ready_payload_has_no_floats_and_uses_utc_datetime_strings() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-8)))
    local_requested_at = datetime(2026, 7, 2, 7, 0, tzinfo=timezone(timedelta(hours=-8)))
    local_source_at = datetime(2026, 7, 2, 7, 45, tzinfo=timezone(timedelta(hours=-8)))
    local_ack_at = datetime(2026, 7, 2, 7, 50, tzinfo=timezone(timedelta(hours=-8)))
    local_rechecked_at = datetime(2026, 7, 2, 7, 55, tzinfo=timezone(timedelta(hours=-8)))

    report = _build_report(
        _input_row(
            "market-json",
            market_closed_at=datetime(2026, 7, 2, 6, 0, tzinfo=timezone(timedelta(hours=-8))),
            recheck_requested_at=local_requested_at,
            source_observed_at=local_source_at,
            acknowledgement_at=local_ack_at,
            rechecked_at=local_rechecked_at,
        ),
        config=_config(
            overdue_recheck_seconds=d("99999.000000"),
            source_stale_seconds=d("99999.000000"),
        ),
        generated_at=generated_at,
    )

    payload = api().market_close_acknowledgement_recheck_status_report_to_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["issue_ratio"] == "0.000000"
    assert payload["rows"][0]["recheck_requested_at"] == "2026-07-02T15:00:00+00:00"
    assert payload["rows"][0]["source_observed_at"] == "2026-07-02T15:45:00+00:00"
    assert payload["rows"][0]["recheck_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["acknowledgement_age_seconds"] == "600.000000"
    assert payload["team_category_rows"][0]["issue_ratio"] == "0.000000"


def test_contracts_are_frozen_decimal_only_and_reject_bad_inputs() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_STATUS_CONFIG_VERSION",
        "MarketCloseAcknowledgementRecheckStatusConfig",
        "MarketCloseAcknowledgementRecheckStatusInputRow",
        "MarketCloseAcknowledgementRecheckStatusReport",
        "MarketCloseAcknowledgementRecheckStatusRow",
        "MarketCloseAcknowledgementRecheckStatusTeamCategoryRow",
        "build_market_close_acknowledgement_recheck_status_report",
        "market_close_acknowledgement_recheck_status_report_to_payload",
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

    row = _input_row("market-frozen")
    with pytest.raises(FrozenInstanceError):
        row.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="overdue_recheck_seconds must be a Decimal"):
        module.MarketCloseAcknowledgementRecheckStatusConfig(
            overdue_recheck_seconds=3600,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="source_stale_seconds must be a Decimal"):
        module.MarketCloseAcknowledgementRecheckStatusConfig(
            source_stale_seconds=_DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.MarketCloseAcknowledgementRecheckStatusConfig(), paper_only=False)
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row("market-naive", recheck_requested_at=datetime(2026, 7, 2, 15, 0))
    with pytest.raises(ValueError, match="recheck_blocked must be a bool"):
        _input_row("market-bool", recheck_blocked=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_contradicts_acknowledgement must be a bool"):
        _input_row("market-contradict-bool", source_contradicts_acknowledgement=1)  # type: ignore[arg-type]


def test_duplicates_future_times_and_manual_inconsistency_are_rejected() -> None:
    module = api()

    duplicate = _input_row("market-duplicate")
    with pytest.raises(ValueError, match="market_id values must be unique"):
        _build_report(duplicate, duplicate)

    with pytest.raises(ValueError, match="recheck_requested_at must not be after generated_at"):
        _build_report(
            _input_row(
                "market-future",
                recheck_requested_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    report = _build_report(
        _input_row(
            "market-manual",
            acknowledgement_at=_at(minutes=20),
            rechecked_at=_at(minutes=5),
        ),
    )
    with pytest.raises(ValueError, match="market_count must match rows"):
        module.MarketCloseAcknowledgementRecheckStatusReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            report_status=report.report_status,
            reason_codes=report.reason_codes,
            market_count=d("2.000000"),
            blocked_count=report.blocked_count,
            overdue_count=report.overdue_count,
            watch_count=report.watch_count,
            cleared_count=report.cleared_count,
            stale_source_count=report.stale_source_count,
            contradiction_count=report.contradiction_count,
            issue_count=report.issue_count,
            issue_ratio=report.issue_ratio,
            max_recheck_age_seconds=report.max_recheck_age_seconds,
            max_source_age_seconds=report.max_source_age_seconds,
            rows=report.rows,
            team_category_rows=report.team_category_rows,
        )


def test_module_surface_stays_pure_in_memory_report_only() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered = source.lower()

    assert _forbidden_text_fragments().isdisjoint(lowered)

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _float_paths(value: Any, prefix: str = "$") -> tuple[str, ...]:
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


def _forbidden_text_fragments() -> set[str]:
    return {
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
    }


def _join(*parts: str) -> str:
    return "".join(parts)
