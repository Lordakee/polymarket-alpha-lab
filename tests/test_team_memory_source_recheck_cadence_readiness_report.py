from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 18, 0, tzinfo=UTC)
MODULE_PATH = "src/polymarket_alpha_lab/team_memory_source_recheck_cadence_readiness_report.py"


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _FloatSubclass(float):
    pass


_DEFAULT_EVIDENCE_AT = object()
_DEFAULT_DUE_AT = object()


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_readiness_report",
    )


def _config(api: Any, **overrides: object) -> Any:
    values = {
        "fresh_age_threshold_seconds": Decimal("7200"),
        "stale_age_threshold_seconds": Decimal("14400"),
        "due_soon_window_seconds": Decimal("1800"),
    }
    values.update(overrides)
    return api.TeamMemorySourceRecheckCadenceReadinessConfig(**values)


def _row(
    api: Any,
    source_key: str,
    source_family: str,
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    last_evidence_at: datetime | None | object = _DEFAULT_EVIDENCE_AT,
    next_recheck_due_at: datetime | object = _DEFAULT_DUE_AT,
    evidence_count: Decimal = Decimal("1"),
) -> Any:
    evidence_at = (
        GENERATED_AT - timedelta(hours=1)
        if last_evidence_at is _DEFAULT_EVIDENCE_AT
        else last_evidence_at
    )
    due_at = (
        GENERATED_AT + timedelta(hours=1)
        if next_recheck_due_at is _DEFAULT_DUE_AT
        else next_recheck_due_at
    )
    return api.TeamMemorySourceRecheckCadenceReadinessInputRow(
        team_id=team_id,
        category_id=category_id,
        source_key=source_key,
        source_family=source_family,
        last_evidence_at=evidence_at,
        next_recheck_due_at=due_at,
        evidence_count=evidence_count,
    )


def test_builds_readiness_report_with_due_overdue_fresh_stale_rollups() -> None:
    api = _api()

    report = api.build_team_memory_source_recheck_cadence_readiness_report(
        (
            _row(
                api,
                "politics-official",
                "official-results",
                last_evidence_at=GENERATED_AT - timedelta(hours=1),
                next_recheck_due_at=GENERATED_AT + timedelta(hours=2),
            ),
            _row(
                api,
                "politics-polling",
                "polling",
                last_evidence_at=GENERATED_AT - timedelta(hours=3),
                next_recheck_due_at=GENERATED_AT + timedelta(minutes=20),
            ),
            _row(
                api,
                "politics-court",
                "official-results",
                last_evidence_at=GENERATED_AT - timedelta(hours=5),
                next_recheck_due_at=GENERATED_AT - timedelta(minutes=15),
            ),
            _row(
                api,
                "btc-exchange",
                "exchange-filings",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                last_evidence_at=GENERATED_AT - timedelta(minutes=30),
                next_recheck_due_at=GENERATED_AT + timedelta(hours=3),
            ),
            _row(
                api,
                "btc-flow",
                "etf-flow",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                last_evidence_at=None,
                next_recheck_due_at=GENERATED_AT - timedelta(minutes=5),
                evidence_count=Decimal("0"),
            ),
        ),
        config=_config(api),
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.TeamMemorySourceRecheckCadenceReadinessReport
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == api.DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_READINESS_CONFIG_VERSION
    )
    assert report.readiness_status == "blocked"
    assert report.team_count == Decimal("2.000000")
    assert report.team_category_count == Decimal("2.000000")
    assert report.source_family_count == Decimal("4.000000")
    assert report.source_count == Decimal("5.000000")
    assert report.fresh_source_count == Decimal("2.000000")
    assert report.due_source_count == Decimal("1.000000")
    assert report.overdue_source_count == Decimal("2.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.missing_evidence_source_count == Decimal("1.000000")
    assert report.ready_team_count == Decimal("0.000000")
    assert report.watch_team_count == Decimal("0.000000")
    assert report.blocked_team_count == Decimal("2.000000")
    assert report.fresh_source_ratio == Decimal("0.400000")
    assert report.overdue_source_ratio == Decimal("0.400000")
    assert report.max_evidence_age_seconds == Decimal("18000.000000")
    assert report.max_recheck_overdue_age_seconds == Decimal("900.000000")
    assert report.reason_codes == (
        "team_memory_source_recheck_cadence_readiness_missing_evidence",
        "team_memory_source_recheck_cadence_readiness_overdue_recheck",
        "team_memory_source_recheck_cadence_readiness_stale_evidence",
        "team_memory_source_recheck_cadence_readiness_due_recheck",
        "team_memory_source_recheck_cadence_readiness_fresh_evidence",
    )
    assert report.reason_code_counts == (
        api.TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
            reason_code=(
                "team_memory_source_recheck_cadence_readiness_missing_evidence"
            ),
            count=Decimal("1.000000"),
        ),
        api.TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
            reason_code=(
                "team_memory_source_recheck_cadence_readiness_overdue_recheck"
            ),
            count=Decimal("2.000000"),
        ),
        api.TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_readiness_stale_evidence",
            count=Decimal("1.000000"),
        ),
        api.TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_readiness_due_recheck",
            count=Decimal("1.000000"),
        ),
        api.TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_readiness_fresh_evidence",
            count=Decimal("2.000000"),
        ),
    )

    assert tuple(
        (row.readiness_status, row.category_id, row.team_id)
        for row in report.team_rows
    ) == (
        ("blocked", "finance.crypto.btc", "crypto_btc"),
        ("blocked", "politics", "politics"),
    )
    crypto = report.team_rows[0]
    assert crypto.source_count == Decimal("2.000000")
    assert crypto.fresh_source_count == Decimal("1.000000")
    assert crypto.missing_evidence_source_count == Decimal("1.000000")
    assert crypto.overdue_source_count == Decimal("1.000000")
    assert crypto.reason_codes == (
        "team_memory_source_recheck_cadence_readiness_missing_evidence",
        "team_memory_source_recheck_cadence_readiness_overdue_recheck",
        "team_memory_source_recheck_cadence_readiness_fresh_evidence",
    )
    assert tuple(row.source_family for row in crypto.source_family_rows) == (
        "etf-flow",
        "exchange-filings",
    )
    assert crypto.source_family_rows[0].readiness_status == "blocked"
    assert crypto.source_family_rows[0].reason_codes == (
        "team_memory_source_recheck_cadence_readiness_missing_evidence",
        "team_memory_source_recheck_cadence_readiness_overdue_recheck",
    )

    politics = report.team_rows[1]
    assert politics.source_count == Decimal("3.000000")
    assert politics.fresh_source_count == Decimal("1.000000")
    assert politics.due_source_count == Decimal("1.000000")
    assert politics.overdue_source_count == Decimal("1.000000")
    assert politics.stale_source_count == Decimal("1.000000")
    assert politics.max_evidence_age_seconds == Decimal("18000.000000")
    assert tuple(row.source_family for row in politics.source_family_rows) == (
        "official-results",
        "polling",
    )
    official = politics.source_family_rows[0]
    assert official.readiness_status == "blocked"
    assert official.source_count == Decimal("2.000000")
    assert official.fresh_source_count == Decimal("1.000000")
    assert official.overdue_source_count == Decimal("1.000000")
    assert official.stale_source_count == Decimal("1.000000")
    assert official.max_evidence_age_seconds == Decimal("18000.000000")
    assert official.max_recheck_overdue_age_seconds == Decimal("900.000000")
    polling = politics.source_family_rows[1]
    assert polling.readiness_status == "watch"
    assert polling.due_source_count == Decimal("1.000000")
    assert polling.reason_codes == (
        "team_memory_source_recheck_cadence_readiness_due_recheck",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_input_returns_blocked_decimal_zero_report() -> None:
    api = _api()

    report = api.build_team_memory_source_recheck_cadence_readiness_report(
        (),
        config=api.TeamMemorySourceRecheckCadenceReadinessConfig(),
        generated_at=GENERATED_AT,
    )

    assert report == api.TeamMemorySourceRecheckCadenceReadinessReport(
        generated_at=GENERATED_AT,
        config_version=(
            api.DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_READINESS_CONFIG_VERSION
        ),
        readiness_status="blocked",
        team_count=Decimal("0.000000"),
        team_category_count=Decimal("0.000000"),
        source_family_count=Decimal("0.000000"),
        source_count=Decimal("0.000000"),
        fresh_source_count=Decimal("0.000000"),
        due_source_count=Decimal("0.000000"),
        overdue_source_count=Decimal("0.000000"),
        stale_source_count=Decimal("0.000000"),
        missing_evidence_source_count=Decimal("0.000000"),
        ready_team_count=Decimal("0.000000"),
        watch_team_count=Decimal("0.000000"),
        blocked_team_count=Decimal("0.000000"),
        fresh_source_ratio=Decimal("0.000000"),
        overdue_source_ratio=Decimal("0.000000"),
        max_evidence_age_seconds=Decimal("0.000000"),
        max_recheck_overdue_age_seconds=Decimal("0.000000"),
        team_rows=(),
        reason_code_counts=(
            api.TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
                reason_code=(
                    "team_memory_source_recheck_cadence_readiness_empty_observations"
                ),
                count=Decimal("1.000000"),
            ),
        ),
        reason_codes=(
            "team_memory_source_recheck_cadence_readiness_empty_observations",
        ),
    )


def test_zero_evidence_count_is_missing_not_fresh_or_stale() -> None:
    api = _api()

    report = api.build_team_memory_source_recheck_cadence_readiness_report(
        (
            _row(
                api,
                "zero-evidence-with-timestamp",
                "calendar",
                last_evidence_at=GENERATED_AT - timedelta(minutes=30),
                next_recheck_due_at=GENERATED_AT + timedelta(hours=3),
                evidence_count=Decimal("0"),
            ),
        ),
        config=_config(api),
        generated_at=GENERATED_AT,
    )

    family = report.team_rows[0].source_family_rows[0]
    assert family.readiness_status == "blocked"
    assert family.missing_evidence_source_count == Decimal("1.000000")
    assert family.fresh_source_count == Decimal("0.000000")
    assert family.stale_source_count == Decimal("0.000000")
    assert family.reason_codes == (
        "team_memory_source_recheck_cadence_readiness_missing_evidence",
    )
    assert report.fresh_source_count == Decimal("0.000000")
    assert report.fresh_source_ratio == Decimal("0.000000")
    assert report.reason_code_counts == (
        api.TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
            reason_code=(
                "team_memory_source_recheck_cadence_readiness_missing_evidence"
            ),
            count=Decimal("1.000000"),
        ),
    )


def test_payload_is_json_ready_without_floats_or_unsafe_surfaces() -> None:
    api = _api()

    report = api.build_team_memory_source_recheck_cadence_readiness_report(
        (
            _row(
                api,
                "private-row-key",
                "official-results",
                last_evidence_at=GENERATED_AT - timedelta(hours=2),
                next_recheck_due_at=GENERATED_AT - timedelta(seconds=60),
            ),
        ),
        config=_config(api),
        generated_at=GENERATED_AT,
    )

    payload = api.team_memory_source_recheck_cadence_readiness_report_payload(report)

    assert payload["source_count"] == "1.000000"
    assert payload["team_rows"][0]["source_family_rows"][0]["source_family"] == (
        "official-results"
    )
    assert "source_key" not in json.dumps(payload, sort_keys=True)
    assert "private-row-key" not in json.dumps(payload, sort_keys=True)
    assert "action" not in json.dumps(payload, sort_keys=True).lower()
    assert "advice" not in json.dumps(payload, sort_keys=True).lower()

    def walk(value: object) -> None:
        if isinstance(value, float):
            raise AssertionError(f"float leaked into payload: {value!r}")
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    encoded = json.dumps(payload, sort_keys=True)
    assert json.loads(encoded) == payload


def test_rejects_non_public_source_family_values_that_would_reach_payload() -> None:
    api = _api()

    unsafe_values = (
        "li" "ve-feed",
        "au" "th-feed",
        "wal" "let-feed",
        "ord" "er-feed",
        "can" "cel-feed",
        "rep" "lace-feed",
        "tr" "ade-feed",
        "bro" "ker-feed",
        "cred" "ential-feed",
        "sec" "ret-feed",
        "private" "_" "key-feed",
        "bal" "ance-feed",
        "acc" "ount-feed",
    )

    for index, unsafe_value in enumerate(unsafe_values):
        with pytest.raises(ValueError, match="source_family must be public"):
            _row(api, f"row-{index}", unsafe_value)


def test_validates_utc_datetimes_decimal_inputs_and_hard_flags() -> None:
    api = _api()

    generated_at = datetime(2026, 7, 2, 14, 0, tzinfo=timezone(timedelta(hours=-4)))
    evidence_at = datetime(2026, 7, 2, 12, 30, tzinfo=timezone(timedelta(hours=-4)))
    due_at = datetime(2026, 7, 2, 20, 20, tzinfo=timezone(timedelta(hours=2)))

    report = api.build_team_memory_source_recheck_cadence_readiness_report(
        (
            _row(
                api,
                "offset-row",
                "calendar",
                last_evidence_at=evidence_at,
                next_recheck_due_at=due_at,
            ),
        ),
        config=_config(api),
        generated_at=generated_at,
    )

    family = report.team_rows[0].source_family_rows[0]
    assert report.generated_at == GENERATED_AT
    assert family.max_evidence_age_seconds == Decimal("5400.000000")
    assert family.max_recheck_overdue_age_seconds == Decimal("0.000000")

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_team_memory_source_recheck_cadence_readiness_report(
            (_row(api, "row", "calendar"),),
            config=_config(api),
            generated_at=_DateTimeSubclass(2026, 7, 2, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_evidence_at must be timezone-aware"):
        _row(
            api,
            "row",
            "calendar",
            last_evidence_at=datetime(2026, 7, 2, 17, 0),
        )
    with pytest.raises(ValueError, match="evidence_count must be a Decimal"):
        _row(api, "row", "calendar", evidence_count=_FloatSubclass(1.0))
    with pytest.raises(ValueError, match="fresh_age_threshold_seconds must be a Decimal"):
        api.TeamMemorySourceRecheckCadenceReadinessConfig(
            fresh_age_threshold_seconds=_DecimalSubclass("1"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(_config(api), paper_only=False)


def test_public_contract_is_frozen_decimal_only_and_in_memory() -> None:
    api = _api()
    report = api.build_team_memory_source_recheck_cadence_readiness_report(
        (_row(api, "row", "calendar"),),
        config=_config(api),
        generated_at=GENERATED_AT,
    )

    public_types = {
        "TeamMemorySourceRecheckCadenceReadinessConfig",
        "TeamMemorySourceRecheckCadenceReadinessInputRow",
        "TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow",
        "TeamMemorySourceRecheckCadenceReadinessTeamRow",
        "TeamMemorySourceRecheckCadenceReadinessReasonCodeCount",
        "TeamMemorySourceRecheckCadenceReadinessReport",
    }
    for name in public_types:
        cls = getattr(api, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.readiness_status = "ready"  # type: ignore[misc]

    decimal_fields = {
        "team_count",
        "team_category_count",
        "source_family_count",
        "source_count",
        "fresh_source_count",
        "due_source_count",
        "overdue_source_count",
        "stale_source_count",
        "missing_evidence_source_count",
        "ready_team_count",
        "watch_team_count",
        "blocked_team_count",
        "fresh_source_ratio",
        "overdue_source_ratio",
        "max_evidence_age_seconds",
        "max_recheck_overdue_age_seconds",
    }
    for field_name in decimal_fields:
        assert type(getattr(report, field_name)) is Decimal

    tree = ast.parse(open(MODULE_PATH, encoding="utf-8").read())
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not (imports & forbidden_import_roots)

    text = open(MODULE_PATH, encoding="utf-8").read().lower()
    for forbidden in (
        "live",
        "auth",
        "order",
        "cancel",
        "replace",
        "trade",
        "broker",
        "wallet",
        "credential",
        "secret",
        "supabase",
        "sqlite",
        "postgres",
        "insert",
        "update",
        "delete",
        "upsert",
        "execute",
        "commit",
        "cursor",
    ):
        assert forbidden not in text
