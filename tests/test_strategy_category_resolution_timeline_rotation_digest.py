from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.strategy_category_resolution_timeline_rotation_digest"
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 11, 50, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CATEGORY_RESOLUTION_TIMELINE_ROTATION_DIGEST_CONFIG_VERSION
        ),
        "maximum_stale_close_age_seconds": d("3600.000000"),
        "watch_stale_close_age_seconds": d("7200.000000"),
        "maximum_unresolved_closed_ratio": d("0.250000"),
        "watch_unresolved_closed_ratio": d("0.400000"),
        "maximum_settlement_pressure_ratio": d("0.300000"),
        "watch_settlement_pressure_ratio": d("0.500000"),
        "minimum_readiness_ratio": d("0.600000"),
        "watch_readiness_ratio": d("0.300000"),
        "maximum_evidence_age_seconds": d("1800.000000"),
        "watch_evidence_age_seconds": d("5400.000000"),
        "minimum_recommended_categories": d("1.000000"),
    }
    values.update(overrides)
    return module.StrategyCategoryResolutionTimelineRotationDigestConfig(**values)


def category(
    category_id: str = "macro",
    *,
    team_id: str = "alpha_team",
    observed_at: datetime = OBSERVED_AT,
    market_count: Decimal = d("10.000000"),
    closed_market_count: Decimal = d("4.000000"),
    unresolved_closed_market_count: Decimal = d("1.000000"),
    stale_closed_market_count: Decimal = d("1.000000"),
    pending_settlement_market_count: Decimal = d("2.000000"),
    ready_to_settle_market_count: Decimal = d("7.000000"),
    oldest_unresolved_close_at: datetime | None = GENERATED_AT - timedelta(minutes=45),
    latest_evidence_at: datetime = GENERATED_AT - timedelta(minutes=10),
    timeline_reference: str = "plain-paper-case",
    reason_codes: tuple[str, ...] = ("category_resolution_timeline_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.StrategyCategoryResolutionTimelineRotationInput(
        category_id=category_id,
        team_id=team_id,
        observed_at=observed_at,
        market_count=market_count,
        closed_market_count=closed_market_count,
        unresolved_closed_market_count=unresolved_closed_market_count,
        stale_closed_market_count=stale_closed_market_count,
        pending_settlement_market_count=pending_settlement_market_count,
        ready_to_settle_market_count=ready_to_settle_market_count,
        oldest_unresolved_close_at=oldest_unresolved_close_at,
        latest_evidence_at=latest_evidence_at,
        timeline_reference=timeline_reference,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_category_resolution_timeline_rotation_digest_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_digest_recommends_categories_with_low_resolution_timeline_pressure() -> None:
    digest = report(
        category(
            "crypto",
            team_id="crypto_team",
            market_count=d("12.000000"),
            closed_market_count=d("4.000000"),
            unresolved_closed_market_count=d("1.000000"),
            stale_closed_market_count=d("1.000000"),
            pending_settlement_market_count=d("2.000000"),
            ready_to_settle_market_count=d("9.000000"),
            oldest_unresolved_close_at=GENERATED_AT - timedelta(minutes=30),
            latest_evidence_at=GENERATED_AT - timedelta(minutes=5),
            timeline_reference="https://example.test/path?token=secret",
        ),
        category(
            "sports",
            team_id="sports_team",
            market_count=d("10.000000"),
            closed_market_count=d("6.000000"),
            unresolved_closed_market_count=d("6.000000"),
            stale_closed_market_count=d("6.000000"),
            pending_settlement_market_count=d("7.000000"),
            ready_to_settle_market_count=d("1.000000"),
            oldest_unresolved_close_at=GENERATED_AT - timedelta(hours=3),
            latest_evidence_at=GENERATED_AT - timedelta(hours=2),
            reason_codes=("category_resolution_timeline_input_available", "wallet_0xabc_secret"),
        ),
        category(
            "macro",
            team_id="macro_team",
            closed_market_count=d("5.000000"),
            unresolved_closed_market_count=d("2.000000"),
            stale_closed_market_count=d("2.000000"),
            pending_settlement_market_count=d("4.000000"),
            ready_to_settle_market_count=d("4.000000"),
            oldest_unresolved_close_at=GENERATED_AT - timedelta(minutes=90),
            latest_evidence_at=GENERATED_AT - timedelta(minutes=45),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == "strategy-category-resolution-timeline-rotation-digest-v0"
    assert digest.category_count == d("3.000000")
    assert digest.recommend_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.status == "paper_rotation_ready"
    assert digest.recommended_next_step == (
        "review_paper_resolution_timeline_rotation_candidates"
    )
    assert digest.recommended_category_ids == ("crypto",)
    assert digest.reason_codes == (
        "category_readiness_blocked",
        "category_resolution_evidence_stale_blocked",
        "category_resolution_timeline_ready",
        "category_settlement_pressure_blocked",
        "category_stale_close_window_blocked",
        "category_unresolved_closed_ratio_blocked",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert_public_numeric_fields_are_decimal(digest)

    assert tuple(row.category_id for row in digest.category_rows) == (
        "crypto",
        "macro",
        "sports",
    )
    top = digest.category_rows[0]
    assert top.rank == d("1.000000")
    assert top.rotation_status == "recommend"
    assert top.rotation_score == d("0.796296")
    assert top.unresolved_closed_ratio == d("0.250000")
    assert top.stale_close_ratio == d("0.250000")
    assert top.settlement_pressure_ratio == d("0.166667")
    assert top.readiness_ratio == d("0.750000")
    assert top.stale_close_age_seconds == d("1800.000000")
    assert top.evidence_age_seconds == d("300.000000")
    assert top.redacted_timeline_reference == "<redacted>"
    assert top.reason_codes == (
        "category_evidence_fresh",
        "category_readiness_sufficient",
        "category_resolution_timeline_input_available",
        "category_settlement_pressure_clear",
        "category_stale_close_window_clear",
        "category_unresolved_closed_ratio_clear",
    )

    watch = digest.category_rows[1]
    assert watch.rotation_status == "watch"
    assert watch.reason_codes == (
        "category_readiness_watch",
        "category_resolution_evidence_stale_watch",
        "category_resolution_timeline_input_available",
        "category_settlement_pressure_watch",
        "category_stale_close_window_watch",
        "category_unresolved_closed_ratio_watch",
    )

    blocked = digest.category_rows[2]
    assert blocked.rotation_status == "blocked"
    assert blocked.reason_codes == (
        "category_readiness_blocked",
        "category_resolution_evidence_stale_blocked",
        "category_resolution_timeline_input_available",
        "category_settlement_pressure_blocked",
        "category_stale_close_window_blocked",
        "category_unresolved_closed_ratio_blocked",
        "reference_redacted",
    )


def test_empty_digest_is_report_only_readonly_and_decimal_zeroed() -> None:
    digest = report()

    assert digest.category_count == ZERO
    assert digest.recommend_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.recommended_category_ids == ()
    assert digest.status == "blocked"
    assert digest.recommended_next_step == "review_resolution_timeline_blockers"
    assert digest.reason_codes == (
        "strategy_category_resolution_timeline_rotation_digest_empty",
    )
    assert digest.reason_code_counts == ()
    assert digest.category_rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert_public_numeric_fields_are_decimal(digest)


def test_payload_serializes_decimal_strings_and_redacts_sensitive_references() -> None:
    module = api()
    digest = report(
        category(
            timeline_reference="https://example.test/feed?api_key=secret",
            latest_evidence_at=datetime(
                2026,
                7,
                4,
                7,
                50,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            4,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    payload = module.strategy_category_resolution_timeline_rotation_digest_payload(digest)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["category_count"] == "1.000000"
    assert payload["category_rows"][0]["rank"] == "1.000000"
    assert payload["category_rows"][0]["rotation_score"] == "0.752315"
    assert payload["category_rows"][0]["redacted_timeline_reference"] == "<redacted>"
    assert "timeline_reference" not in payload["category_rows"][0]
    assert "api_key=secret" not in encoded
    assert not re.search(r":\s*-?\d+\.\d+", encoded)
    assert_no_float_or_int_values(payload)

    assert module.strategy_category_resolution_timeline_rotation_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly.*True"):
        module.strategy_category_resolution_timeline_rotation_digest_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="category_count.*Decimal"):
        module.strategy_category_resolution_timeline_rotation_digest_payload(
            {**payload, "category_count": 1},
        )
    with pytest.raises(ValueError, match="rotation_score.*float"):
        bad_payload = dict(payload)
        bad_payload["category_rows"] = [
            {**payload["category_rows"][0], "rotation_score": 0.5},
        ]
        module.strategy_category_resolution_timeline_rotation_digest_payload(bad_payload)
    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        module.strategy_category_resolution_timeline_rotation_digest_payload(
            {**payload, "generated_at": datetime(2026, 7, 4, 12, 0)},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_category_resolution_timeline_rotation_digest_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )


def test_input_validation_frozen_datetimes_flags_and_no_secret_repr() -> None:
    safe = category(
        timeline_reference="https://example.test/private?token=secret",
        observed_at=datetime(2026, 7, 4, 7, 50, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert safe.observed_at == OBSERVED_AT
    assert "token=secret" not in repr(safe)
    assert "private" not in repr(safe).lower()

    digest = report(safe)
    row = digest.category_rows[0]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    with pytest.raises(FrozenInstanceError):
        row.rotation_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="category_id must be a nonblank trimmed string"):
        category(category_id=_StringSubclass("macro"))
    with pytest.raises(ValueError, match="market_count must be a Decimal"):
        category(market_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_count must be exactly Decimal"):
        category(market_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="closed_market_count must not exceed market_count"):
        category(closed_market_count=d("11.000000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        category(observed_at=datetime(2026, 7, 4, 11, 50))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        category(
            observed_at=datetime(2026, 7, 4, 11, 50, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(category(), generated_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        category(paper_only=False)
    with pytest.raises(ValueError, match="duplicate category_id"):
        report(category("crypto"), category("crypto"))
    with pytest.raises(ValueError, match="config must be"):
        api().build_strategy_category_resolution_timeline_rotation_digest_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_dataclass_rejects_inconsistent_rows_and_counts() -> None:
    digest = report(
        category("crypto"),
        category(
            "macro",
            closed_market_count=d("5.000000"),
            unresolved_closed_market_count=d("2.000000"),
            stale_closed_market_count=d("2.000000"),
            pending_settlement_market_count=d("4.000000"),
            ready_to_settle_market_count=d("4.000000"),
            oldest_unresolved_close_at=GENERATED_AT - timedelta(minutes=90),
            latest_evidence_at=GENERATED_AT - timedelta(minutes=45),
        ),
    )
    module = api()

    with pytest.raises(ValueError, match="category_rows must contain exact row values"):
        replace(digest, category_rows=(object(),))
    with pytest.raises(ValueError, match="recommend_count must match category_rows"):
        replace(digest, recommend_count=ZERO)
    with pytest.raises(ValueError, match="category_rows must use deterministic sort"):
        replace(digest, category_rows=tuple(reversed(digest.category_rows)))

    assert digest.reason_code_counts == tuple(
        sorted(
            digest.reason_code_counts,
            key=lambda row: (-row.count, row.reason_code),
        ),
    )
    assert all(
        field.type == "Decimal"
        for field in fields(module.StrategyCategoryResolutionTimelineRotationDigestReport)
        if field.name.endswith("_count") or field.name.endswith("_ratio")
    )


def test_module_is_pure_report_only_and_contains_no_runtime_io_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_category_resolution_timeline_rotation_digest.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    forbidden_calls = {"open", "print", "float"}
    forbidden_import_roots = {
        "http",
        "json",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
