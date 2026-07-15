from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_outcome_freshness_recheck_readiness_report import (
    MarketOutcomeFreshnessRecheckReadinessConfig,
    MarketOutcomeFreshnessRecheckReadinessReport,
    MarketOutcomeFreshnessRecheckReadinessRow,
    MarketOutcomeFreshnessRecheckReadinessSource,
    build_market_outcome_freshness_recheck_readiness_report,
    market_outcome_freshness_recheck_readiness_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 18, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_freshness_recheck_readiness_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketOutcomeFreshnessRecheckReadinessConfig:
    values = {
        "outcome_fresh_after_seconds": d("900.000000"),
        "recheck_fresh_after_seconds": d("1800.000000"),
        "config_version": "market-outcome-freshness-recheck-readiness-test-v0",
    }
    values.update(overrides)
    return MarketOutcomeFreshnessRecheckReadinessConfig(**values)


def source(
    market_id: str,
    *,
    market_slug: str | None = None,
    category_id: str = "finance.crypto",
    outcome_observed_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    outcome_source_checked_at: datetime | None = GENERATED_AT - timedelta(minutes=4),
    official_source_url: str | None = "https://example.test/resolution",
    queued_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketOutcomeFreshnessRecheckReadinessSource:
    return MarketOutcomeFreshnessRecheckReadinessSource(
        market_id=market_id,
        market_slug=market_slug or f"{market_id}-slug",
        category_id=category_id,
        outcome_observed_at=outcome_observed_at,
        outcome_source_checked_at=outcome_source_checked_at,
        official_source_url=official_source_url,
        queued_at=queued_at,
        acknowledged_at=acknowledged_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *sources: MarketOutcomeFreshnessRecheckReadinessSource,
    cfg: MarketOutcomeFreshnessRecheckReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketOutcomeFreshnessRecheckReadinessReport:
    return build_market_outcome_freshness_recheck_readiness_report(
        sources,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(value.values()) + tuple(item for v in value.values() for item in walk(v))
    if isinstance(value, list):
        return tuple(value) + tuple(item for v in value for item in walk(v))
    return (value,)


def float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_delta")
        ):
            assert type(value) is Decimal, field.name


def test_builds_deterministic_phase_1_outcome_freshness_recheck_readiness() -> None:
    readiness = report(
        source(
            "market-ready",
            market_slug="zeta",
            category_id="finance.crypto",
            outcome_observed_at=GENERATED_AT - timedelta(minutes=4),
            outcome_source_checked_at=GENERATED_AT - timedelta(minutes=3),
            queued_at=GENERATED_AT - timedelta(minutes=12),
            acknowledged_at=GENERATED_AT - timedelta(minutes=7),
        ),
        source(
            "market-stale-outcome",
            market_slug="alpha",
            category_id="politics.us",
            outcome_observed_at=GENERATED_AT - timedelta(hours=2),
            outcome_source_checked_at=GENERATED_AT - timedelta(minutes=5),
            queued_at=GENERATED_AT - timedelta(minutes=40),
            acknowledged_at=GENERATED_AT - timedelta(minutes=20),
        ),
        source(
            "market-stale-recheck",
            market_slug="beta",
            category_id="politics.us",
            outcome_observed_at=GENERATED_AT - timedelta(minutes=5),
            outcome_source_checked_at=GENERATED_AT - timedelta(hours=2),
            queued_at=GENERATED_AT - timedelta(minutes=50),
            acknowledged_at=GENERATED_AT - timedelta(minutes=35),
        ),
        source(
            "market-missing-source",
            market_slug="gamma",
            category_id="sports.soccer",
            official_source_url=None,
            outcome_observed_at=GENERATED_AT - timedelta(minutes=3),
            outcome_source_checked_at=GENERATED_AT - timedelta(minutes=3),
            queued_at=GENERATED_AT - timedelta(minutes=10),
            acknowledged_at=GENERATED_AT - timedelta(minutes=9),
        ),
        source(
            "market-queue-blocked",
            market_slug="delta",
            category_id="sports.soccer",
            queued_at=None,
            acknowledged_at=None,
            outcome_observed_at=GENERATED_AT - timedelta(minutes=2),
            outcome_source_checked_at=GENERATED_AT - timedelta(minutes=2),
        ),
        source(
            "market-ack-watch",
            market_slug="epsilon",
            category_id="finance.crypto",
            queued_at=GENERATED_AT - timedelta(minutes=10),
            acknowledged_at=None,
            outcome_observed_at=GENERATED_AT - timedelta(minutes=2),
            outcome_source_checked_at=GENERATED_AT - timedelta(minutes=2),
        ),
    )

    assert is_dataclass(readiness)
    assert readiness.status == "blocked"
    assert readiness.reason_codes == (
        "missing_official_source",
        "stale_outcome_timestamp",
        "stale_recheck_age",
        "queue_not_ready",
        "ack_not_ready",
    )
    assert readiness.market_count == d("6")
    assert readiness.ready_count == d("1")
    assert readiness.watch_count == d("4")
    assert readiness.blocked_count == d("1")
    assert readiness.missing_official_source_count == d("1")
    assert readiness.stale_outcome_count == d("1")
    assert readiness.stale_recheck_count == d("1")
    assert readiness.queue_ready_count == d("5")
    assert readiness.ack_ready_count == d("4")
    assert readiness.ready_ratio == d("0.166667")
    assert readiness.queue_ready_ratio == d("0.833333")
    assert readiness.ack_ready_ratio == d("0.666667")
    assert readiness.max_outcome_age_seconds == d("7200.000000")
    assert readiness.max_recheck_age_seconds == d("7200.000000")
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    assert tuple(row.market_id for row in readiness.rows) == (
        "market-queue-blocked",
        "market-missing-source",
        "market-stale-outcome",
        "market-stale-recheck",
        "market-ack-watch",
        "market-ready",
    )
    assert readiness.rows[0].status == "blocked"
    assert readiness.rows[0].queue_bucket == "not_queued"
    assert readiness.rows[0].ack_bucket == "missing_ack"
    assert readiness.rows[0].reason_codes == ("queue_not_ready", "ack_not_ready")
    assert readiness.rows[1].status == "watch"
    assert readiness.rows[1].reason_codes == ("missing_official_source",)
    assert readiness.rows[2].outcome_age_seconds == d("7200.000000")
    assert readiness.rows[2].outcome_age_delta_seconds == d("6300.000000")
    assert readiness.rows[2].reason_codes == ("stale_outcome_timestamp",)
    assert readiness.rows[3].recheck_age_seconds == d("7200.000000")
    assert readiness.rows[3].recheck_age_delta_seconds == d("5400.000000")
    assert readiness.rows[3].reason_codes == ("stale_recheck_age",)
    assert readiness.rows[4].queue_bucket == "queued_waiting_ack"
    assert readiness.rows[4].ack_bucket == "missing_ack"
    assert readiness.rows[4].reason_codes == ("ack_not_ready",)
    assert readiness.rows[5].status == "ready"
    assert readiness.rows[5].queue_bucket == "queued"
    assert readiness.rows[5].ack_bucket == "acknowledged"
    assert readiness.rows[5].reason_codes == ("outcome_freshness_recheck_ready",)

    assert readiness.category_rollups == (
        ("finance.crypto", d("2"), d("1"), d("1"), d("0")),
        ("politics.us", d("2"), d("0"), d("2"), d("0")),
        ("sports.soccer", d("2"), d("0"), d("1"), d("1")),
    )


def test_pending_acknowledgement_metrics_surface_manual_review_readiness() -> None:
    readiness = report(
        source(
            "market-ready",
            queued_at=GENERATED_AT - timedelta(minutes=18),
            acknowledged_at=GENERATED_AT - timedelta(minutes=12),
        ),
        source(
            "market-pending-short",
            queued_at=GENERATED_AT - timedelta(minutes=7),
            acknowledged_at=None,
        ),
        source(
            "market-pending-long",
            queued_at=GENERATED_AT - timedelta(minutes=33),
            acknowledged_at=None,
        ),
        source(
            "market-not-queued",
            queued_at=None,
            acknowledged_at=None,
        ),
    )

    assert readiness.pending_ack_count == d("2")
    assert readiness.pending_ack_ratio == d("0.500000")
    assert readiness.max_pending_ack_age_seconds == d("1980.000000")

    pending_rows = {
        row.market_id: row.pending_ack_age_seconds
        for row in readiness.rows
        if row.queue_bucket == "queued_waiting_ack"
    }
    assert pending_rows == {
        "market-pending-long": d("1980.000000"),
        "market-pending-short": d("420.000000"),
    }
    assert readiness.rows[-1].pending_ack_age_seconds == d("0.000000")

    payload = market_outcome_freshness_recheck_readiness_payload(readiness)
    assert payload["pending_ack_count"] == "2"
    assert payload["pending_ack_ratio"] == "0.500000"
    assert payload["max_pending_ack_age_seconds"] == "1980.000000"
    assert payload["rows"][1]["pending_ack_age_seconds"] == "1980.000000"


def test_empty_report_is_report_only_and_json_ready() -> None:
    readiness = report()

    assert readiness == MarketOutcomeFreshnessRecheckReadinessReport(
        generated_at=GENERATED_AT,
        config_version="market-outcome-freshness-recheck-readiness-test-v0",
        outcome_fresh_after_seconds=d("900.000000"),
        recheck_fresh_after_seconds=d("1800.000000"),
        market_count=d("0"),
        ready_count=d("0"),
        watch_count=d("0"),
        blocked_count=d("0"),
        missing_official_source_count=d("0"),
        stale_outcome_count=d("0"),
        stale_recheck_count=d("0"),
        queue_ready_count=d("0"),
        ack_ready_count=d("0"),
        pending_ack_count=d("0"),
        ready_ratio=d("0.000000"),
        queue_ready_ratio=d("0.000000"),
        ack_ready_ratio=d("0.000000"),
        pending_ack_ratio=d("0.000000"),
        max_outcome_age_seconds=d("0.000000"),
        max_recheck_age_seconds=d("0.000000"),
        max_pending_ack_age_seconds=d("0.000000"),
        status="empty",
        reason_codes=("outcome_freshness_recheck_readiness_empty",),
        category_rollups=(),
        rows=(),
    )
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    payload = market_outcome_freshness_recheck_readiness_payload(readiness)
    assert payload["generated_at"] == "2026-07-02T18:00:00+00:00"
    assert payload["market_count"] == "0"
    assert payload["ready_ratio"] == "0.000000"
    assert payload["category_rollups"] == []
    assert payload["rows"] == []
    assert float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_payload_uses_decimal_strings_iso_datetimes_and_no_action_surface() -> None:
    readiness = report(source("market-ready"))

    payload = market_outcome_freshness_recheck_readiness_payload(readiness)

    assert payload["market_count"] == "1"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["max_outcome_age_seconds"] == "300.000000"
    assert payload["rows"][0]["outcome_observed_at"] == "2026-07-02T17:55:00+00:00"
    assert payload["rows"][0]["outcome_age_seconds"] == "300.000000"
    assert payload["rows"][0]["recheck_age_delta_seconds"] == "0.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert not any(isinstance(value, float) for value in walk(payload))

    lowered = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "sign",
        "trade",
        "live",
        "advice",
        "recommend",
    ):
        assert forbidden not in lowered


def test_public_dataclasses_are_frozen_and_validate_strict_types_flags_and_times() -> None:
    readiness = report(source("market-ready"))

    with pytest.raises(FrozenInstanceError):
        readiness.status = "ready"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="outcome_fresh_after_seconds must be a Decimal"):
        config(outcome_fresh_after_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="recheck_fresh_after_seconds must be positive"):
        config(recheck_fresh_after_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="outcome_observed_at must be timezone-aware"):
        source("market-naive", outcome_observed_at=datetime(2026, 7, 2, 17, 55))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(source("market-ready"), generated_at=datetime(2026, 7, 2, 18, 0))
    with pytest.raises(ValueError, match="outcome_observed_at must be <= generated_at"):
        report(
            source(
                "market-future-outcome",
                outcome_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="acknowledged_at must be >= queued_at"):
        source(
            "market-bad-ack",
            queued_at=GENERATED_AT - timedelta(minutes=5),
            acknowledged_at=GENERATED_AT - timedelta(minutes=6),
        )
    with pytest.raises(ValueError, match="paper_only"):
        source("market-flag", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="market_id values must be unique"):
        report(source("market-dup"), source("market-dup"))
    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)
    with pytest.raises(ValueError, match="rows must contain"):
        replace(readiness, rows=(object(),))  # type: ignore[arg-type]

    row = readiness.rows[0]
    explicit_row = MarketOutcomeFreshnessRecheckReadinessRow(
        market_id=row.market_id,
        market_slug=row.market_slug,
        category_id=row.category_id,
        outcome_observed_at=row.outcome_observed_at,
        outcome_source_checked_at=row.outcome_source_checked_at,
        official_source_url=row.official_source_url,
        queued_at=row.queued_at,
        acknowledged_at=row.acknowledged_at,
        outcome_age_seconds=row.outcome_age_seconds,
        recheck_age_seconds=row.recheck_age_seconds,
        outcome_age_delta_seconds=row.outcome_age_delta_seconds,
        recheck_age_delta_seconds=row.recheck_age_delta_seconds,
        pending_ack_age_seconds=row.pending_ack_age_seconds,
        queue_bucket=row.queue_bucket,
        ack_bucket=row.ack_bucket,
        status=row.status,
        reason_codes=row.reason_codes,
    )
    assert explicit_row == row

    with pytest.raises(ValueError, match="pending_ack_count must match rows"):
        replace(readiness, pending_ack_count=d("2"))
    with pytest.raises(ValueError, match="pending_ack_ratio must match rows"):
        replace(readiness, pending_ack_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="max_pending_ack_age_seconds must match rows"):
        replace(readiness, max_pending_ack_age_seconds=d("1.000000"))

    for instance in (config(), source("market-decimal"), readiness, readiness.rows[0]):
        assert_public_numeric_fields_are_decimal(instance)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_public_dataclasses_reject_truthy_non_true_hard_flags(flag_name: str) -> None:
    readiness = report(source("market-ready"))
    row = readiness.rows[0]

    with pytest.raises(ValueError, match=flag_name):
        config(**{flag_name: 1})
    with pytest.raises(ValueError, match=flag_name):
        source("market-truthy-flag", **{flag_name: 1})
    with pytest.raises(ValueError, match=flag_name):
        replace(row, **{flag_name: 1})
    with pytest.raises(ValueError, match=flag_name):
        replace(readiness, **{flag_name: 1})


def test_timezone_normalization_and_exact_freshness_boundaries() -> None:
    readiness = report(
        source(
            "market-local",
            outcome_observed_at=datetime(2026, 7, 2, 13, 45, tzinfo=timezone(timedelta(hours=-4))),
            outcome_source_checked_at=datetime(
                2026,
                7,
                2,
                13,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            queued_at=datetime(2026, 7, 2, 13, 20, tzinfo=timezone(timedelta(hours=-4))),
            acknowledged_at=datetime(
                2026,
                7,
                2,
                13,
                25,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        cfg=config(
            outcome_fresh_after_seconds=d("900.000000"),
            recheck_fresh_after_seconds=d("1800.000000"),
        ),
        generated_at=datetime(2026, 7, 2, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert readiness.generated_at == GENERATED_AT
    assert readiness.status == "ready"
    assert readiness.rows[0].outcome_observed_at == datetime(2026, 7, 2, 17, 45, tzinfo=UTC)
    assert readiness.rows[0].outcome_source_checked_at == datetime(
        2026,
        7,
        2,
        17,
        30,
        tzinfo=UTC,
    )
    assert readiness.rows[0].outcome_age_seconds == d("900.000000")
    assert readiness.rows[0].recheck_age_seconds == d("1800.000000")
    assert readiness.rows[0].outcome_age_delta_seconds == d("0.000000")
    assert readiness.rows[0].recheck_age_delta_seconds == d("0.000000")
    assert readiness.rows[0].reason_codes == ("outcome_freshness_recheck_ready",)


def test_module_does_not_import_io_network_or_execution_surfaces() -> None:
    tree = compile(
        MODULE_PATH.read_text(encoding="utf-8"),
        str(MODULE_PATH),
        "exec",
        ast.PyCF_ONLY_AST,
    )
    imported_names: set[str] = set()
    call_names: set[str] = set()
    attr_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                attr_names.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attr_names.add(node.attr)

    forbidden_imports = {
        "asyncio",
        "http",
        "jsonlines",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "execute",
        "executemany",
        "submit",
        "cancel",
        "sign",
        "place_order",
        "create_order",
    }
    forbidden_attrs = {
        "connect",
        "request",
        "urlopen",
        "execute",
        "executemany",
        "submit",
        "cancel",
        "sign",
        "place_order",
        "create_order",
    }

    assert imported_names.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert attr_names.isdisjoint(forbidden_attrs)
