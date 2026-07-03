from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_source_family_divergence_recheck_report"
GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _input_row(
    market_id: str,
    source_family: str,
    observed_value: str,
    *,
    source_updated_at: datetime,
) -> object:
    return _api().MarketSourceFamilyDivergenceRecheckInputRow(
        market_id=market_id,
        source_family=source_family,
        observed_value=observed_value,
        source_updated_at=source_updated_at,
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_RECHECK_REPORT_CONFIG_VERSION
        ),
        "official_stale_after_seconds": d("3600.000000"),
        "acknowledgement_required_after_seconds": d("600.000000"),
    }
    values.update(overrides)
    return api.MarketSourceFamilyDivergenceRecheckConfig(**values)


def _report(*rows: object, **config_overrides: object) -> object:
    return _api().build_market_source_family_divergence_recheck_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_module_import_surface_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_build_report_rechecks_source_family_divergence_after_new_updates() -> None:
    api = _api()

    report = _report(
        _input_row(
            "market-divergent",
            "official",
            "resolved_yes",
            source_updated_at=_at(hours=2),
        ),
        _input_row(
            "market-divergent",
            "primary",
            "resolved_no",
            source_updated_at=_at(minutes=30),
        ),
        _input_row(
            "market-divergent",
            "proxy",
            "resolved_yes",
            source_updated_at=_at(minutes=20),
        ),
        _input_row(
            "market-proxy-only",
            "proxy",
            "resolved_yes",
            source_updated_at=_at(minutes=20),
        ),
        _input_row(
            "market-stale-acknowledged",
            "official",
            "open",
            source_updated_at=_at(hours=2),
        ),
        _input_row(
            "market-stale-acknowledged",
            "primary",
            "open",
            source_updated_at=_at(minutes=15),
        ),
        _input_row(
            "market-stale-acknowledged",
            "team_acknowledged",
            "open",
            source_updated_at=_at(minutes=10),
        ),
        _input_row(
            "market-clear",
            "official",
            "open",
            source_updated_at=_at(minutes=30),
        ),
        _input_row(
            "market-clear",
            "primary",
            "open",
            source_updated_at=_at(minutes=25),
        ),
        _input_row(
            "market-clear",
            "proxy",
            "open",
            source_updated_at=_at(minutes=20),
        ),
        _input_row(
            "market-clear",
            "team_acknowledged",
            "open",
            source_updated_at=_at(minutes=15),
        ),
    )

    assert type(report) is api.MarketSourceFamilyDivergenceRecheckReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_RECHECK_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_source_family_divergence_recheck_unresolved_divergence",
        "market_source_family_divergence_recheck_stale_official_source",
        "market_source_family_divergence_recheck_proxy_only_confirmation",
        "market_source_family_divergence_recheck_missing_team_acknowledgement",
    )
    assert report.market_count == d("4.000000")
    assert report.source_update_count == d("11.000000")
    assert report.clear_market_count == d("1.000000")
    assert report.watch_market_count == d("1.000000")
    assert report.blocked_market_count == d("2.000000")
    assert report.recheck_required_market_count == d("3.000000")
    assert report.unresolved_divergence_market_count == d("1.000000")
    assert report.stale_official_market_count == d("2.000000")
    assert report.proxy_only_confirmation_market_count == d("1.000000")
    assert report.missing_team_acknowledgement_market_count == d("2.000000")
    assert report.recheck_required_ratio == d("0.750000")
    assert report.unresolved_divergence_ratio == d("0.250000")
    assert report.stale_official_ratio == d("0.500000")
    assert report.proxy_only_confirmation_ratio == d("0.250000")
    assert report.missing_team_acknowledgement_ratio == d("0.500000")
    assert report.max_official_age_seconds == d("7200.000000")
    assert report.max_source_age_seconds == d("7200.000000")
    assert tuple(row.market_id for row in report.rows) == (
        "market-divergent",
        "market-proxy-only",
        "market-stale-acknowledged",
        "market-clear",
    )

    divergent = report.rows[0]
    assert divergent.recheck_status == "blocked"
    assert divergent.recheck_required is True
    assert divergent.official_value == "resolved_yes"
    assert divergent.primary_value == "resolved_no"
    assert divergent.proxy_value == "resolved_yes"
    assert divergent.team_acknowledged_value is None
    assert divergent.source_update_count == d("3.000000")
    assert divergent.divergent_source_family_count == d("1.000000")
    assert divergent.official_age_seconds == d("7200.000000")
    assert divergent.max_source_age_seconds == d("7200.000000")
    assert divergent.divergence_ratio == d("0.333333")
    assert divergent.unresolved_divergence_count == d("1.000000")
    assert divergent.stale_official_source_count == d("1.000000")
    assert divergent.proxy_only_confirmation_count == d("0.000000")
    assert divergent.missing_team_acknowledgement_count == d("1.000000")
    assert divergent.reason_codes == (
        "market_source_family_divergence_recheck_unresolved_divergence",
        "market_source_family_divergence_recheck_stale_official_source",
        "market_source_family_divergence_recheck_missing_team_acknowledgement",
    )

    proxy_only = report.rows[1]
    assert proxy_only.recheck_status == "blocked"
    assert proxy_only.official_value is None
    assert proxy_only.primary_value is None
    assert proxy_only.proxy_value == "resolved_yes"
    assert proxy_only.source_update_count == d("1.000000")
    assert proxy_only.official_age_seconds == d("0.000000")
    assert proxy_only.max_source_age_seconds == d("1200.000000")
    assert proxy_only.proxy_only_confirmation_count == d("1.000000")
    assert proxy_only.missing_team_acknowledgement_count == d("1.000000")
    assert proxy_only.reason_codes == (
        "market_source_family_divergence_recheck_proxy_only_confirmation",
        "market_source_family_divergence_recheck_missing_team_acknowledgement",
    )

    stale_acknowledged = report.rows[2]
    assert stale_acknowledged.recheck_status == "watch"
    assert stale_acknowledged.recheck_required is True
    assert stale_acknowledged.reason_codes == (
        "market_source_family_divergence_recheck_stale_official_source",
    )

    clear = report.rows[3]
    assert clear.recheck_status == "clear"
    assert clear.recheck_required is False
    assert clear.reason_codes == (
        "market_source_family_divergence_recheck_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_clear_decimal_only_and_deterministic() -> None:
    report = _report()

    assert report.report_status == "clear"
    assert report.reason_codes == ("market_source_family_divergence_recheck_clear",)
    assert report.market_count == d("0.000000")
    assert report.source_update_count == d("0.000000")
    assert report.recheck_required_market_count == d("0.000000")
    assert report.recheck_required_ratio == d("0.000000")
    assert report.unresolved_divergence_ratio == d("0.000000")
    assert report.max_official_age_seconds == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_helper_is_json_ready_without_float_values_and_uses_utc_strings() -> None:
    offset = timezone(timedelta(hours=-4))
    api = _api()
    report = api.build_market_source_family_divergence_recheck_report(
        (
            api.MarketSourceFamilyDivergenceRecheckInputRow(
                market_id="market-offset",
                source_family="official",
                observed_value="open",
                source_updated_at=datetime(2026, 7, 2, 7, 30, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergenceRecheckInputRow(
                market_id="market-offset",
                source_family="primary",
                observed_value="open",
                source_updated_at=datetime(2026, 7, 2, 7, 40, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergenceRecheckInputRow(
                market_id="market-offset",
                source_family="proxy",
                observed_value="open",
                source_updated_at=datetime(2026, 7, 2, 7, 45, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergenceRecheckInputRow(
                market_id="market-offset",
                source_family="team_acknowledged",
                observed_value="open",
                source_updated_at=datetime(2026, 7, 2, 7, 50, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
    )

    payload = api.market_source_family_divergence_recheck_report_to_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["recheck_required_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["market_id"] == "market-offset"
    assert payload["rows"][0]["max_source_age_seconds"] == "1800.000000"

    with pytest.raises(ValueError, match="report must be"):
        api.market_source_family_divergence_recheck_report_to_payload(object())


def test_public_dataclasses_are_frozen_decimal_only_and_validate_times_and_flags() -> None:
    api = _api()
    contract_classes = (
        api.MarketSourceFamilyDivergenceRecheckConfig,
        api.MarketSourceFamilyDivergenceRecheckInputRow,
        api.MarketSourceFamilyDivergenceRecheckRow,
        api.MarketSourceFamilyDivergenceRecheckReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field_name, hint in get_type_hints(contract_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)

    row = _input_row(
        "market-frozen",
        "official",
        "open",
        source_updated_at=_at(minutes=5),
    )
    with pytest.raises(FrozenInstanceError):
        row.observed_value = "closed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="official_stale_after_seconds"):
        api.MarketSourceFamilyDivergenceRecheckConfig(
            official_stale_after_seconds=3600,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        api.MarketSourceFamilyDivergenceRecheckInputRow(
            market_id="market-naive",
            source_family="official",
            observed_value="open",
            source_updated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_market_source_family_divergence_recheck_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="source_updated_at"):
        _report(
            _input_row(
                "market-future",
                "official",
                "open",
                source_updated_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        api.MarketSourceFamilyDivergenceRecheckRow(
            market_id="market-impossible-age",
            official_value="open",
            primary_value=None,
            proxy_value=None,
            team_acknowledged_value=None,
            source_update_count=d("1.000000"),
            divergent_source_family_count=d("0.000000"),
            unresolved_divergence_count=d("0.000000"),
            stale_official_source_count=d("0.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_team_acknowledgement_count=d("0.000000"),
            official_age_seconds=d("60.000000"),
            max_source_age_seconds=d("30.000000"),
            divergence_ratio=d("0.000000"),
            recheck_status="clear",
            recheck_required=False,
            reason_codes=("market_source_family_divergence_recheck_clear",),
        )
    with pytest.raises(ValueError, match="source_family"):
        _input_row(
            "market-family",
            "community",
            "open",
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="market_id"):
        _input_row(
            _join_parts("wal", "let"),
            "official",
            "open",
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="unique"):
        _report(
            _input_row(
                "market-duplicate",
                "official",
                "open",
                source_updated_at=_at(minutes=5),
            ),
            _input_row(
                "market-duplicate",
                "official",
                "closed",
                source_updated_at=_at(minutes=4),
            ),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)


def test_recheck_row_rejects_impossible_public_count_states() -> None:
    api = _api()

    with pytest.raises(ValueError, match="divergent_source_family_count"):
        api.MarketSourceFamilyDivergenceRecheckRow(
            market_id="market-fractional-count",
            official_value="yes",
            primary_value="no",
            proxy_value=None,
            team_acknowledged_value=None,
            source_update_count=d("2.000000"),
            divergent_source_family_count=d("0.500000"),
            unresolved_divergence_count=d("1.000000"),
            stale_official_source_count=d("0.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_team_acknowledgement_count=d("0.000000"),
            official_age_seconds=d("60.000000"),
            max_source_age_seconds=d("60.000000"),
            divergence_ratio=d("0.250000"),
            recheck_status="blocked",
            recheck_required=True,
            reason_codes=(
                "market_source_family_divergence_recheck_unresolved_divergence",
            ),
        )

    with pytest.raises(ValueError, match="stale_official_source_count"):
        api.MarketSourceFamilyDivergenceRecheckRow(
            market_id="market-stale-without-official",
            official_value=None,
            primary_value="open",
            proxy_value=None,
            team_acknowledged_value=None,
            source_update_count=d("1.000000"),
            divergent_source_family_count=d("0.000000"),
            unresolved_divergence_count=d("0.000000"),
            stale_official_source_count=d("1.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_team_acknowledgement_count=d("0.000000"),
            official_age_seconds=d("0.000000"),
            max_source_age_seconds=d("7200.000000"),
            divergence_ratio=d("0.000000"),
            recheck_status="watch",
            recheck_required=True,
            reason_codes=(
                "market_source_family_divergence_recheck_stale_official_source",
            ),
        )

    with pytest.raises(ValueError, match="stale_official_source_count"):
        api.MarketSourceFamilyDivergenceRecheckRow(
            market_id="market-stale-with-fresh-official",
            official_value="open",
            primary_value=None,
            proxy_value=None,
            team_acknowledged_value=None,
            source_update_count=d("1.000000"),
            divergent_source_family_count=d("0.000000"),
            unresolved_divergence_count=d("0.000000"),
            stale_official_source_count=d("1.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_team_acknowledgement_count=d("0.000000"),
            official_age_seconds=d("0.000000"),
            max_source_age_seconds=d("0.000000"),
            divergence_ratio=d("0.000000"),
            recheck_status="watch",
            recheck_required=True,
            reason_codes=(
                "market_source_family_divergence_recheck_stale_official_source",
            ),
        )

    with pytest.raises(ValueError, match="divergent_source_family_count"):
        api.MarketSourceFamilyDivergenceRecheckRow(
            market_id="market-divergent-mismatch",
            official_value="yes",
            primary_value="no",
            proxy_value=None,
            team_acknowledged_value=None,
            source_update_count=d("2.000000"),
            divergent_source_family_count=d("2.000000"),
            unresolved_divergence_count=d("1.000000"),
            stale_official_source_count=d("0.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_team_acknowledgement_count=d("0.000000"),
            official_age_seconds=d("60.000000"),
            max_source_age_seconds=d("60.000000"),
            divergence_ratio=d("1.000000"),
            recheck_status="blocked",
            recheck_required=True,
            reason_codes=(
                "market_source_family_divergence_recheck_unresolved_divergence",
            ),
        )

    with pytest.raises(ValueError, match="missing_team_acknowledgement_count"):
        api.MarketSourceFamilyDivergenceRecheckRow(
            market_id="market-missing-with-team-acknowledgement",
            official_value="open",
            primary_value=None,
            proxy_value=None,
            team_acknowledged_value="open",
            source_update_count=d("2.000000"),
            divergent_source_family_count=d("0.000000"),
            unresolved_divergence_count=d("0.000000"),
            stale_official_source_count=d("1.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_team_acknowledgement_count=d("1.000000"),
            official_age_seconds=d("7200.000000"),
            max_source_age_seconds=d("7200.000000"),
            divergence_ratio=d("0.000000"),
            recheck_status="blocked",
            recheck_required=True,
            reason_codes=(
                "market_source_family_divergence_recheck_stale_official_source",
                "market_source_family_divergence_recheck_missing_team_acknowledgement",
            ),
        )

    with pytest.raises(ValueError, match="missing_team_acknowledgement_count"):
        api.MarketSourceFamilyDivergenceRecheckRow(
            market_id="market-missing-without-trigger",
            official_value="open",
            primary_value=None,
            proxy_value=None,
            team_acknowledged_value=None,
            source_update_count=d("1.000000"),
            divergent_source_family_count=d("0.000000"),
            unresolved_divergence_count=d("0.000000"),
            stale_official_source_count=d("0.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_team_acknowledgement_count=d("1.000000"),
            official_age_seconds=d("60.000000"),
            max_source_age_seconds=d("60.000000"),
            divergence_ratio=d("0.000000"),
            recheck_status="blocked",
            recheck_required=True,
            reason_codes=(
                "market_source_family_divergence_recheck_missing_team_acknowledgement",
            ),
        )


def test_module_is_pure_in_memory_report_only_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert api.__all__ == (
        "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_RECHECK_REPORT_CONFIG_VERSION",
        "MarketSourceFamilyDivergenceRecheckConfig",
        "MarketSourceFamilyDivergenceRecheckInputRow",
        "MarketSourceFamilyDivergenceRecheckReport",
        "MarketSourceFamilyDivergenceRecheckRow",
        "build_market_source_family_divergence_recheck_report",
        "market_source_family_divergence_recheck_report_to_payload",
    )
    assert ".total_seconds(" not in source
    assert "float(" not in source
    for banned in (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "buy",
                "connect",
                "execute",
                "executemany",
                "open",
                "patch",
                "place",
                "post",
                "put",
                "request",
                "sell",
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


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
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


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))
