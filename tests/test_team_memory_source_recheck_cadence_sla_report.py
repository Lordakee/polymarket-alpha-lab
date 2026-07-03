from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 18, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_sla_report",
    )


def _d(value: str) -> Decimal:
    return Decimal(value)


def _config(api: Any, **overrides: object) -> Any:
    values = {
        "source_family_concentration_threshold_ratio": _d("0.666667"),
    }
    values.update(overrides)
    return api.TeamMemorySourceRecheckCadenceSlaConfig(**values)


def _source(
    api: Any,
    source_id: str,
    source_family: str,
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    owner_id: str | None = "analyst-alpha",
    last_rechecked_at: datetime | None = None,
    next_recheck_due_at: datetime | None = None,
    reviewer_acknowledged_at: datetime | None = None,
) -> Any:
    last_rechecked = (
        GENERATED_AT - timedelta(hours=2)
        if last_rechecked_at is None
        else last_rechecked_at
    )
    next_due = (
        GENERATED_AT + timedelta(hours=2)
        if next_recheck_due_at is None
        else next_recheck_due_at
    )
    return api.TeamMemorySourceRecheckCadenceSlaInputRow(
        team_id=team_id,
        category_id=category_id,
        source_id=source_id,
        source_family=source_family,
        owner_id=owner_id,
        last_rechecked_at=last_rechecked,
        next_recheck_due_at=next_due,
        reviewer_acknowledged_at=reviewer_acknowledged_at,
    )


def _build_report(api: Any, *sources: Any) -> Any:
    return api.build_team_memory_source_recheck_cadence_sla_report(
        sources,
        config=_config(api),
        generated_at=GENERATED_AT,
    )


def test_sla_report_flags_overdue_missing_owner_concentration_and_ack() -> None:
    api = _api()

    report = _build_report(
        api,
        _source(
            api,
            "politics-official",
            "official-results",
            last_rechecked_at=datetime(
                2026,
                7,
                1,
                10,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            next_recheck_due_at=GENERATED_AT - timedelta(hours=6),
            reviewer_acknowledged_at=GENERATED_AT - timedelta(minutes=15),
        ),
        _source(
            api,
            "politics-primary",
            "official-results",
            owner_id=None,
            reviewer_acknowledged_at=None,
        ),
        _source(
            api,
            "politics-proxy",
            "official-results",
            reviewer_acknowledged_at=None,
        ),
        _source(
            api,
            "btc-official",
            "exchange-filings",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            reviewer_acknowledged_at=GENERATED_AT - timedelta(minutes=10),
        ),
        _source(
            api,
            "btc-primary",
            "etf-flow",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            reviewer_acknowledged_at=GENERATED_AT - timedelta(minutes=8),
        ),
    )

    assert is_dataclass(report)
    assert type(report) is api.TeamMemorySourceRecheckCadenceSlaReport
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == api.DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_SLA_CONFIG_VERSION
    )
    assert report.sla_status == "blocked"
    assert report.team_category_count == _d("2.000000")
    assert report.source_count == _d("5.000000")
    assert report.overdue_source_count == _d("1.000000")
    assert report.missing_owner_count == _d("1.000000")
    assert report.missing_reviewer_acknowledgement_count == _d("2.000000")
    assert report.source_family_concentration_count == _d("1.000000")
    assert report.max_recheck_overdue_age_seconds == _d("21600.000000")
    assert report.max_last_recheck_age_seconds == _d("100800.000000")
    assert report.max_source_family_concentration_ratio == _d("1.000000")
    assert report.reason_codes == (
        "team_memory_source_recheck_cadence_sla_overdue_cadence",
        "team_memory_source_recheck_cadence_sla_missing_owner",
        "team_memory_source_recheck_cadence_sla_source_family_concentration",
        "team_memory_source_recheck_cadence_sla_missing_reviewer_acknowledgement",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(
        (row.sla_status, row.category_id, row.team_id)
        for row in report.team_category_rows
    ) == (
        ("blocked", "politics", "politics"),
        ("pass", "finance.crypto.btc", "crypto_btc"),
    )

    politics = report.team_category_rows[0]
    assert type(politics) is api.TeamMemorySourceRecheckCadenceSlaTeamCategoryRow
    assert politics.source_count == _d("3.000000")
    assert politics.source_family_count == _d("1.000000")
    assert politics.dominant_source_family == "official-results"
    assert politics.dominant_source_family_count == _d("3.000000")
    assert politics.source_family_concentration_ratio == _d("1.000000")
    assert politics.overdue_source_count == _d("1.000000")
    assert politics.missing_owner_count == _d("1.000000")
    assert politics.missing_reviewer_acknowledgement_count == _d("2.000000")
    assert politics.max_recheck_overdue_age_seconds == _d("21600.000000")
    assert politics.max_last_recheck_age_seconds == _d("100800.000000")
    assert politics.reason_codes == report.reason_codes

    ready = report.team_category_rows[1]
    assert ready.sla_status == "pass"
    assert ready.source_family_concentration_ratio == _d("0.500000")
    assert ready.reason_codes == ("team_memory_source_recheck_cadence_sla_clear",)


def test_empty_input_returns_report_only_decimal_zeroes() -> None:
    api = _api()

    report = api.build_team_memory_source_recheck_cadence_sla_report(
        (),
        config=api.TeamMemorySourceRecheckCadenceSlaConfig(),
        generated_at=GENERATED_AT,
    )

    assert report == api.TeamMemorySourceRecheckCadenceSlaReport(
        generated_at=GENERATED_AT,
        config_version=api.DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_SLA_CONFIG_VERSION,
        sla_status="blocked",
        team_category_count=_d("0.000000"),
        source_count=_d("0.000000"),
        overdue_source_count=_d("0.000000"),
        missing_owner_count=_d("0.000000"),
        source_family_concentration_count=_d("0.000000"),
        missing_reviewer_acknowledgement_count=_d("0.000000"),
        max_recheck_overdue_age_seconds=_d("0.000000"),
        max_last_recheck_age_seconds=_d("0.000000"),
        max_source_family_concentration_ratio=_d("0.000000"),
        team_category_rows=(),
        reason_codes=("team_memory_source_recheck_cadence_sla_empty_sources",),
    )


def test_payload_is_json_ready_without_input_identifiers_or_floats() -> None:
    api = _api()
    source_id = "private-source-row"
    report = _build_report(
        api,
        _source(
            api,
            source_id,
            "official-results",
            reviewer_acknowledged_at=GENERATED_AT - timedelta(minutes=5),
        ),
    )

    payload = api.team_memory_source_recheck_cadence_sla_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T18:30:00+00:00"
    assert payload["source_count"] == "1.000000"
    assert payload["max_last_recheck_age_seconds"] == "7200.000000"
    assert payload["team_category_rows"][0]["source_family_concentration_ratio"] == (
        "1.000000"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert source_id not in repr(payload)
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    _assert_no_floats(payload)


def test_validates_decimals_utc_datetimes_unique_inputs_flags_and_frozen() -> None:
    api = _api()
    source = _source(
        api,
        "politics-official",
        "official-results",
        reviewer_acknowledged_at=GENERATED_AT - timedelta(minutes=5),
    )

    assert is_dataclass(source)
    with pytest.raises(FrozenInstanceError):
        source.source_family = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        api.TeamMemorySourceRecheckCadenceSlaConfig(paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _config(api, source_family_concentration_threshold_ratio=0.7)
    with pytest.raises(ValueError, match="Decimal"):
        _config(
            api,
            source_family_concentration_threshold_ratio=_DecimalSubclass("0.7"),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _source(
            api,
            "naive-last",
            "official-results",
            last_rechecked_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_team_memory_source_recheck_cadence_sla_report(
            (source,),
            config=api.TeamMemorySourceRecheckCadenceSlaConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 18, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        api.build_team_memory_source_recheck_cadence_sla_report(
            (
                _source(
                    api,
                    "future-last",
                    "official-results",
                    last_rechecked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=api.TeamMemorySourceRecheckCadenceSlaConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="category_id"):
        _source(
            api,
            "category-mismatch",
            "official-results",
            team_id="crypto_btc",
            category_id="politics",
        )
    with pytest.raises(ValueError, match="source_family"):
        _source(api, "unsafe-family", "wallet-feed")
    with pytest.raises(ValueError, match="source_id"):
        _source(api, " private-key ", "official-results")
    with pytest.raises(ValueError, match="unique"):
        api.build_team_memory_source_recheck_cadence_sla_report(
            (
                source,
                replace(source, source_family="polling"),
            ),
            config=api.TeamMemorySourceRecheckCadenceSlaConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="input rows"):
        api.build_team_memory_source_recheck_cadence_sla_report(
            (object(),),
            config=api.TeamMemorySourceRecheckCadenceSlaConfig(),
            generated_at=GENERATED_AT,
        )

    report = _build_report(api, source)
    with pytest.raises(FrozenInstanceError):
        report.sla_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="reason_codes"):
        api.TeamMemorySourceRecheckCadenceSlaReport(
            **{
                **report.__dict__,
                "sla_status": "pass",
                "reason_codes": ("team_memory_source_recheck_cadence_sla_clear",),
            },
        )


def test_module_scope_is_pure_in_memory_report_only_without_live_surfaces() -> None:
    module = _api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "trading",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert forbidden not in lowered

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
                "delete",
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


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload contains a float")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, list | tuple):
        for item in value:
            _assert_no_floats(item)
