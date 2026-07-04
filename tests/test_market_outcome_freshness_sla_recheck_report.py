from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_outcome_freshness_sla_recheck_report import (
    MarketOutcomeFreshnessSlaRecheckConfig,
    MarketOutcomeFreshnessSlaRecheckObservation,
    MarketOutcomeFreshnessSlaRecheckReport,
    MarketOutcomeFreshnessSlaRecheckRow,
    MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow,
    build_market_outcome_freshness_sla_recheck_report,
    market_outcome_freshness_sla_recheck_report_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
BREACHED_AT = datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
CONFIG_VERSION = "market-outcome-freshness-sla-recheck-v0"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_freshness_sla_recheck_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    market_id: str = "market-a",
    outcome_id: str = "yes",
    team_id: str = "team-alpha",
    category_id: str = "finance.crypto",
    prior_breach_detected_at: datetime = BREACHED_AT,
    rechecked_at: datetime = GENERATED_AT,
    source_updated_at: datetime | None = GENERATED_AT - timedelta(minutes=2),
    acknowledged_at: datetime | None = BREACHED_AT + timedelta(minutes=4),
    contradiction_state: str = "none",
    prior_team_category_miss_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketOutcomeFreshnessSlaRecheckObservation:
    return MarketOutcomeFreshnessSlaRecheckObservation(
        market_id=market_id,
        outcome_id=outcome_id,
        team_id=team_id,
        category_id=category_id,
        prior_breach_detected_at=prior_breach_detected_at,
        rechecked_at=rechecked_at,
        source_updated_at=source_updated_at,
        acknowledged_at=acknowledged_at,
        contradiction_state=contradiction_state,
        prior_team_category_miss_count=prior_team_category_miss_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(
    *,
    max_source_age_seconds: Decimal = d("300"),
    max_acknowledgement_lag_seconds: Decimal = d("600"),
    repeated_team_category_miss_threshold: Decimal = d("2"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketOutcomeFreshnessSlaRecheckConfig:
    return MarketOutcomeFreshnessSlaRecheckConfig(
        config_version=CONFIG_VERSION,
        max_source_age_seconds=max_source_age_seconds,
        max_acknowledgement_lag_seconds=max_acknowledgement_lag_seconds,
        repeated_team_category_miss_threshold=repeated_team_category_miss_threshold,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *observations: MarketOutcomeFreshnessSlaRecheckObservation,
    cfg: MarketOutcomeFreshnessSlaRecheckConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketOutcomeFreshnessSlaRecheckReport:
    return build_market_outcome_freshness_sla_recheck_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("freshness SLA recheck report must not expose float values")
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field in fields(value):
            assert_no_float_values(getattr(value, field.name))
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_no_float_values(key)
            assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_sla_recheck_report_measures_recovery_lag_contradictions_and_repeats() -> None:
    report = build_report(
        observation(
            market_id="market-recovered",
            outcome_id="yes",
            team_id="team-alpha",
            category_id="finance.crypto",
        ),
        observation(
            market_id="market-open-contradiction",
            outcome_id="no",
            team_id="team-alpha",
            category_id="finance.crypto",
            source_updated_at=BREACHED_AT - timedelta(minutes=5),
            acknowledged_at=None,
            contradiction_state="open",
            prior_team_category_miss_count=d("1"),
        ),
        observation(
            market_id="market-resolved-contradiction",
            outcome_id="yes",
            team_id="team-beta",
            category_id="politics.us",
            source_updated_at=GENERATED_AT - timedelta(minutes=1),
            acknowledged_at=BREACHED_AT + timedelta(minutes=15),
            contradiction_state="resolved",
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is MarketOutcomeFreshnessSlaRecheckReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.input_count == d("3")
    assert report.row_count == d("3")
    assert report.recovered_count == d("1")
    assert report.watch_count == d("1")
    assert report.breached_count == d("1")
    assert report.source_recovered_count == d("2")
    assert report.source_stale_count == d("1")
    assert report.source_missing_count == d("0")
    assert report.acknowledged_count == d("1")
    assert report.acknowledgement_late_count == d("1")
    assert report.acknowledgement_missing_count == d("1")
    assert report.contradiction_open_count == d("1")
    assert report.repeated_team_category_miss_count == d("1")
    assert report.recovery_ratio == d("0.333333")
    assert report.oldest_breach_age_seconds == d("1800.000000")
    assert report.status == "breached"
    assert report.reason_codes == (
        "source_not_recovered",
        "acknowledgement_missing",
        "acknowledgement_late",
        "contradiction_open",
        "contradiction_resolved",
        "repeated_team_category_miss",
    )

    assert [
        (
            row.market_id,
            row.outcome_id,
            row.breach_age_seconds,
            row.source_age_seconds,
            row.acknowledgement_lag_seconds,
            row.source_freshness_status,
            row.acknowledgement_status,
            row.contradiction_state,
            row.recheck_status,
            row.reason_codes,
        )
        for row in report.rows
    ] == [
        (
            "market-open-contradiction",
            "no",
            d("1800.000000"),
            d("2100.000000"),
            None,
            "stale",
            "missing",
            "open",
            "breached",
            (
                "source_not_recovered",
                "acknowledgement_missing",
                "contradiction_open",
                "repeated_team_category_miss",
            ),
        ),
        (
            "market-resolved-contradiction",
            "yes",
            d("1800.000000"),
            d("60.000000"),
            d("900.000000"),
            "recovered",
            "late",
            "resolved",
            "watch",
            ("acknowledgement_late", "contradiction_resolved"),
        ),
        (
            "market-recovered",
            "yes",
            d("1800.000000"),
            d("120.000000"),
            d("240.000000"),
            "recovered",
            "acknowledged",
            "none",
            "recovered",
            ("sla_recovered",),
        ),
    ]
    assert [
        (
            row.team_id,
            row.category_id,
            row.miss_count,
            row.repeated_miss,
            row.reason_codes,
        )
        for row in report.team_category_miss_rows
    ] == [
        (
            "team-alpha",
            "finance.crypto",
            d("2"),
            True,
            ("repeated_team_category_miss",),
        ),
        ("team-beta", "politics.us", d("0"), False, ("no_repeated_miss",)),
    ]
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_no_float_values(report)


def test_sla_recheck_payload_is_json_ready_and_contains_no_float_values() -> None:
    report = build_report(
        observation(
            prior_breach_detected_at=GENERATED_AT - timedelta(seconds=1, microseconds=250000),
            source_updated_at=GENERATED_AT - timedelta(microseconds=500000),
            acknowledged_at=GENERATED_AT - timedelta(microseconds=250000),
        ),
    )

    payload = market_outcome_freshness_sla_recheck_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["recovery_ratio"] == "1.000000"
    assert payload["rows"][0]["breach_age_seconds"] == "1.250000"
    assert payload["rows"][0]["source_age_seconds"] == "0.500000"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "1.000000"
    assert_no_float_values(payload)


def test_sla_recheck_public_reports_do_not_allow_unsafe_surface_injection() -> None:
    report = build_report(observation())

    assert not hasattr(report, "__dict__")
    with pytest.raises((AttributeError, TypeError)):
        object.__setattr__(report, "wallet_order_cancel_replace_auth", "redacted")


def test_sla_recheck_constructors_validate_consistency_and_hard_flags() -> None:
    report = build_report(observation())
    rebuilt_row = MarketOutcomeFreshnessSlaRecheckRow(**field_values(report.rows[0]))
    rebuilt_group = MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow(
        **field_values(report.team_category_miss_rows[0]),
    )

    assert rebuilt_row == report.rows[0]
    assert rebuilt_group == report.team_category_miss_rows[0]
    with pytest.raises(ValueError, match="input_count"):
        replace(report, input_count=d("2"))
    with pytest.raises(ValueError, match="recovery_ratio"):
        replace(report, recovery_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="source_freshness_status"):
        replace(report.rows[0], source_freshness_status="stale")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=("acknowledgement_missing",))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.team_category_miss_rows[0], reason_codes=("repeated_team_category_miss",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)


def test_sla_recheck_rejects_bad_public_types_and_is_frozen() -> None:
    class ConfigSubclass(MarketOutcomeFreshnessSlaRecheckConfig):
        pass

    class ObservationSubclass(MarketOutcomeFreshnessSlaRecheckObservation):
        pass

    class DateTimeSubclass(datetime):
        pass

    item = observation()
    cfg = config()

    with pytest.raises(FrozenInstanceError):
        item.market_id = "changed"
    with pytest.raises(FrozenInstanceError):
        cfg.max_source_age_seconds = d("120")
    with pytest.raises(FrozenInstanceError):
        build_report(item).rows = ()
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        replace(cfg, max_source_age_seconds=300)
    with pytest.raises(ValueError, match="prior_team_category_miss_count"):
        replace(item, prior_team_category_miss_count=d("1.5"))
    with pytest.raises(ValueError, match="contradiction_state"):
        replace(item, contradiction_state="unknown")
    with pytest.raises(ValueError, match="source_updated_at"):
        replace(item, source_updated_at=DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="prior_breach_detected_at"):
        replace(item, prior_breach_detected_at=datetime(2026, 7, 2, 11, 30))
    with pytest.raises(ValueError, match="config"):
        build_market_outcome_freshness_sla_recheck_report(
            [item],
            config=ConfigSubclass(**field_values(cfg)),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations"):
        build_market_outcome_freshness_sla_recheck_report(
            [ObservationSubclass(**field_values(item))],
            config=cfg,
            generated_at=GENERATED_AT,
        )


def test_sla_recheck_returns_empty_report_for_empty_safe_input() -> None:
    report = build_report()

    assert report.input_count == d("0")
    assert report.row_count == d("0")
    assert report.recovered_count == d("0")
    assert report.watch_count == d("0")
    assert report.breached_count == d("0")
    assert report.recovery_ratio is None
    assert report.oldest_breach_age_seconds is None
    assert report.status == "empty"
    assert report.reason_codes == ("no_rechecks",)
    assert report.rows == ()
    assert report.team_category_miss_rows == ()


EXPECTED_EXPORTS = (
    "MarketOutcomeFreshnessSlaRecheckConfig",
    "MarketOutcomeFreshnessSlaRecheckObservation",
    "MarketOutcomeFreshnessSlaRecheckRow",
    "MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow",
    "MarketOutcomeFreshnessSlaRecheckReport",
    "build_market_outcome_freshness_sla_recheck_report",
    "market_outcome_freshness_sla_recheck_report_payload",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
    "polymarket_alpha_lab.team_paper_guard",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "clob_client",
    "duckdb",
    "eth_account",
    "http",
    "httpx",
    "json",
    "os",
    "pathlib",
    "polymarket",
    "py_clob_client",
    "requests",
    "socket",
    "sqlite3",
    "subprocess",
    "urllib",
    "web3",
    "websocket",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "account",
    "advice",
    "apikey",
    "apitoken",
    "auth",
    "broker",
    "cancel",
    "client",
    "credential",
    "fast",
    "fetch",
    "live",
    "network",
    "order",
    "private",
    "secret",
    "sign",
    "submit",
    "token",
    "trade",
    "wallet",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
    "read",
    "write",
}

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "readonly",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> list[str]:
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def module_exports(tree: ast.Module) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def collected_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def public_field_names(tree: ast.Module) -> set[str]:
    field_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    field_names.add(statement.target.id)
    return field_names


def test_sla_recheck_imports_only_allowed_dependencies() -> None:
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_sla_recheck_does_not_import_forbidden_surfaces() -> None:
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_sla_recheck_exports_only_report_api() -> None:
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS


def test_sla_recheck_defines_no_forbidden_live_or_sensitive_names() -> None:
    tree = parse_module()
    normalized_names = {
        normalize_identifier(name)
        for name in collected_names(tree)
        if normalize_identifier(name) not in ALLOWED_FORBIDDEN_NAME_MATCHES
    }

    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in name for name in normalized_names
        ), (
            fragment,
            normalized_names,
        )


def test_sla_recheck_public_counts_ratios_and_age_seconds_are_decimal() -> None:
    report = build_report(observation())

    for instance in (
        config(),
        observation(),
        report,
        report.rows[0],
        report.team_category_miss_rows[0],
    ):
        for field in fields(instance):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                value = getattr(instance, field.name)
                assert value is None or type(value) is Decimal, (field.name, value)


def test_sla_recheck_does_not_perform_io_dynamic_execution_or_advice() -> None:
    tree = parse_module()
    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    assert "buy" not in source
    assert "sell" not in source
    assert "investment advice" not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALL_NAMES, node.func.attr
