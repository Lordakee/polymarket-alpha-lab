from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-minutes-restriction-digest-test-v0"


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


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_minutes_restriction_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "minutes_cap_threshold": d("24.000000"),
        "minutes_gap_threshold": d("6.000000"),
        "confidence_threshold": d("0.700000"),
        "restriction_age_seconds_threshold": d("7200.000000"),
    }
    values.update(overrides)
    return module.MarketResearchBasketballMinutesRestrictionDigestConfig(**values)


def signal(
    condition_id: str = "condition_alpha",
    player_key: str = "player_embiid",
    *,
    league_key: str = "nba",
    team_key: str = "phi",
    source_ref: str = "official_injury_report",
    observed_at: datetime = BASE_OBSERVED_AT,
    projected_minutes: Decimal = d("34.000000"),
    restricted_minutes_cap: Decimal | None = d("24.000000"),
    restriction_confidence: Decimal = d("0.900000"),
    restriction_active: bool = True,
    signal_config_version: str = "basketball-minutes-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchBasketballMinutesRestrictionDigestSignal(
        condition_id=condition_id,
        league_key=league_key,
        team_key=team_key,
        player_key=player_key,
        source_ref=source_ref,
        observed_at=observed_at,
        projected_minutes=projected_minutes,
        restricted_minutes_cap=restricted_minutes_cap,
        restriction_confidence=restriction_confidence,
        restriction_active=restriction_active,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object):
    module = api()
    values: dict[str, object] = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_market_research_basketball_minutes_restriction_digest(**values)


def walk(value: object) -> tuple[object, ...]:
    children = (value,)
    if isinstance(value, dict):
        for item in value.values():
            children += walk(item)
    if isinstance(value, list):
        for item in value:
            children += walk(item)
    return children


def test_digest_flags_active_cap_gap_confidence_and_stale_restrictions() -> None:
    report = build_report(
        signal(
            "condition_beta",
            "player_davis",
            team_key="lal",
            source_ref="team_report_old",
            observed_at=GENERATED_AT - timedelta(hours=3),
            projected_minutes=d("36.000000"),
            restricted_minutes_cap=d("22.000000"),
            restriction_confidence=d("0.850000"),
            signal_config_version="basketball-minutes-feed-v1",
        ),
        signal(
            "condition_alpha",
            "player_tatum",
            team_key="bos",
            source_ref="rotation_note",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            projected_minutes=d("35.000000"),
            restricted_minutes_cap=None,
            restriction_confidence=d("0.000000"),
            restriction_active=False,
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.research_scope == (
        "basketball minutes restriction research digest only"
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_basketball_minutes_restrictions"
    )
    assert report.player_count == d("2")
    assert report.signal_count == d("2")
    assert report.clear_player_count == d("1")
    assert report.watch_player_count == d("1")
    assert report.active_restriction_player_count == d("1")
    assert report.low_cap_player_count == d("1")
    assert report.high_minutes_gap_player_count == d("1")
    assert report.high_confidence_player_count == d("1")
    assert report.stale_restriction_player_count == d("1")
    assert report.max_minutes_gap == d("14.000000")
    assert report.max_restriction_age_seconds == d("10800.000000")
    assert report.average_restriction_confidence == d("0.425000")
    assert report.reason_codes == (
        "basketball_minutes_restriction_active",
        "basketball_minutes_restriction_low_cap",
        "basketball_minutes_restriction_gap_high",
        "basketball_minutes_restriction_confidence_high",
        "basketball_minutes_restriction_stale",
    )
    assert report.signal_config_versions == (
        ("rotation_note", "basketball-minutes-feed-v0"),
        ("team_report_old", "basketball-minutes-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.player_key, row.team_key) for row in report.rows) == (
        ("player_davis", "lal"),
        ("player_tatum", "bos"),
    )
    restricted = report.rows[0]
    assert restricted.digest_status == "watch"
    assert restricted.signal_count == d("1")
    assert restricted.projected_minutes_max == d("36.000000")
    assert restricted.restricted_minutes_cap_min == d("22.000000")
    assert restricted.minutes_gap == d("14.000000")
    assert restricted.restriction_age_seconds == d("10800.000000")
    assert restricted.restriction_confidence_max == d("0.850000")
    assert restricted.reason_codes == (
        "basketball_minutes_restriction_active",
        "basketball_minutes_restriction_low_cap",
        "basketball_minutes_restriction_gap_high",
        "basketball_minutes_restriction_confidence_high",
        "basketball_minutes_restriction_stale",
    )

    clear = report.rows[1]
    assert clear.digest_status == "clear"
    assert clear.restricted_minutes_cap_min is None
    assert clear.minutes_gap == d("0.000000")
    assert clear.reason_codes == ("basketball_minutes_restriction_clear",)


def test_digest_passes_for_empty_and_unrestricted_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "blocked"
    assert empty_report.recommended_next_step == (
        "block_report_only_basketball_minutes_restrictions"
    )
    assert empty_report.player_count == d("0")
    assert empty_report.signal_count == d("0")
    assert empty_report.reason_codes == ("basketball_minutes_restriction_empty",)
    assert tuple(
        (item.reason_code, item.player_count)
        for item in empty_report.reason_code_counts
    ) == (("basketball_minutes_restriction_empty", d("1.000000")),)
    assert empty_report.rows == ()
    assert empty_report.max_minutes_gap is None
    assert empty_report.max_restriction_age_seconds is None
    assert empty_report.average_restriction_confidence == d("0.000000")

    stable_report = build_report(
        signal(
            "condition_alpha",
            "player_tatum",
            source_ref="rotation_note",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            projected_minutes=d("32.000000"),
            restricted_minutes_cap=d("30.000000"),
            restriction_confidence=d("0.300000"),
            restriction_active=False,
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == ("basketball_minutes_restriction_passed",)
    assert stable_report.reason_code_counts == ()
    assert stable_report.rows[0].digest_status == "clear"


def test_rows_and_reason_counts_sort_deterministically() -> None:
    report = build_report(
        signal(
            "condition_zeta",
            "player_zeta",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            projected_minutes=d("35.000000"),
            restricted_minutes_cap=d("20.000000"),
            source_ref="zeta",
        ),
        signal(
            "condition_alpha",
            "player_alpha",
            observed_at=GENERATED_AT - timedelta(hours=4),
            projected_minutes=d("32.000000"),
            restricted_minutes_cap=d("25.000000"),
            source_ref="alpha",
        ),
        signal(
            "condition_beta",
            "player_beta",
            observed_at=GENERATED_AT - timedelta(minutes=5),
            projected_minutes=d("30.000000"),
            restricted_minutes_cap=None,
            restriction_active=False,
            restriction_confidence=d("0.000000"),
            source_ref="beta",
        ),
    )

    assert tuple(row.player_key for row in report.rows) == (
        "player_zeta",
        "player_alpha",
        "player_beta",
    )
    assert tuple((item.reason_code, item.player_count) for item in report.reason_code_counts) == (
        ("basketball_minutes_restriction_active", d("2")),
        ("basketball_minutes_restriction_low_cap", d("1")),
        ("basketball_minutes_restriction_gap_high", d("2")),
        ("basketball_minutes_restriction_confidence_high", d("2")),
        ("basketball_minutes_restriction_stale", d("1")),
    )


def test_payload_uses_decimal_strings_iso_datetimes_and_no_public_numeric_ints() -> None:
    payload = api().market_research_basketball_minutes_restriction_digest_payload(
        build_report(
            signal(
                "condition_payload",
                "player_payload",
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    8,
                    0,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                projected_minutes=d("31.000000"),
                restricted_minutes_cap=d("23.000000"),
            ),
        ),
    )

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T18:00:00Z"
    assert payload["player_count"] == "1.000000"
    assert payload["max_minutes_gap"] == "8.000000"
    assert payload["rows"][0]["observed_at_latest"] == "2026-07-04T12:00:00Z"
    assert payload["rows"][0]["minutes_gap"] == "8.000000"
    assert payload["reason_code_counts"][0]["player_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(item, float) for item in walk(payload))

    for item in walk(payload):
        if isinstance(item, bool):
            continue
        assert not isinstance(item, int)
        if isinstance(item, str):
            try:
                Decimal(item)
            except Exception:
                continue
            assert item == Decimal(item).quantize(Decimal("0.000001")).to_eng_string()


def test_builder_rejects_tampered_config_flags() -> None:
    cfg = config()
    object.__setattr__(cfg, "readonly", False)

    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(signal(), config=cfg)


def test_payload_revalidates_nested_public_dataclasses_before_serializing() -> None:
    module = api()

    def reject_after_tamper(mutator: Any, match: str) -> None:
        report = build_report(signal())
        mutator(report)
        with pytest.raises(ValueError, match=match):
            module.market_research_basketball_minutes_restriction_digest_payload(report)

    reject_after_tamper(
        lambda report: object.__setattr__(report, "report_only", False),
        "report_only",
    )
    reject_after_tamper(
        lambda report: object.__setattr__(report.rows[0], "readonly", False),
        "readonly",
    )
    reject_after_tamper(
        lambda report: object.__setattr__(
            report.reason_code_counts[0],
            "paper_only",
            False,
        ),
        "paper_only",
    )
    reject_after_tamper(
        lambda report: object.__setattr__(
            report.rows[0],
            "minutes_gap",
            d("0.0000001"),
        ),
        "six decimals",
    )
    reject_after_tamper(
        lambda report: object.__setattr__(
            report.rows[0],
            "minutes_gap",
            _DecimalSubclass("10.000000"),
        ),
        "must be a Decimal",
    )
    reject_after_tamper(
        lambda report: object.__setattr__(
            report.rows[0],
            "minutes_gap",
            d("1.000000"),
        ),
        "constructor-valid",
    )
    reject_after_tamper(
        lambda report: object.__setattr__(
            report.rows[0],
            "observed_at_latest",
            datetime(
                2026,
                7,
                4,
                11,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        "normalized to UTC",
    )
    reject_after_tamper(
        lambda report: object.__setattr__(report, "rows", list(report.rows)),
        "constructor-normalized",
    )


def test_validation_rejects_bad_values_flags_duplicates_and_manual_drift() -> None:
    module = api()

    with pytest.raises(ValueError, match="projected_minutes must be a Decimal"):
        signal(projected_minutes=30)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="restriction_confidence must be a Decimal"):
        signal(restriction_confidence=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="restricted_minutes_cap must be nonnegative"):
        signal(restricted_minutes_cap=d("-1.000000"))
    with pytest.raises(ValueError, match="restriction_confidence must be at most 1"):
        signal(restriction_confidence=d("1.000001"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(signal(), generated_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))
    with pytest.raises(ValueError, match="condition_id must be a string"):
        signal(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(
            signal("condition_alpha", "player_alpha", source_ref="same_ref"),
            signal("condition_alpha", "player_alpha", source_ref="same_ref"),
        )
    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="contains unsafe source detail"):
        signal(condition_id="market_slug_alpha")
    with pytest.raises(ValueError, match="minutes_cap_threshold must be a Decimal"):
        config(minutes_cap_threshold=_DecimalSubclass("24.000000"))

    report = build_report(signal())
    with pytest.raises(ValueError, match="player_count must be a Decimal"):
        replace(report, player_count=1)
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="digest_status must match rows"):
        replace(
            build_report(),
            digest_status="pass",
            recommended_next_step=(
                "continue_report_only_basketball_minutes_restriction_monitoring"
            ),
        )
    with pytest.raises(ValueError, match="reason_code_counts reason_code values must be unique"):
        replace(
            report,
            reason_code_counts=(report.reason_code_counts[0], *report.reason_code_counts),
        )
    with pytest.raises(ValueError, match="reason_code_counts must be sorted by reason code rank"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    ordered_report = build_report(
        signal(
            "condition_beta",
            "player_beta",
            source_ref="beta",
            projected_minutes=d("36.000000"),
            restricted_minutes_cap=d("20.000000"),
        ),
        signal(
            "condition_alpha",
            "player_alpha",
            source_ref="alpha",
            projected_minutes=d("30.000000"),
            restricted_minutes_cap=d("28.000000"),
            restriction_active=False,
            restriction_confidence=d("0.000000"),
        ),
    )
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(ordered_report, rows=tuple(reversed(ordered_report.rows)))
    with pytest.raises(ValueError, match="signal_config_versions must be sorted"):
        replace(
            ordered_report,
            signal_config_versions=tuple(reversed(ordered_report.signal_config_versions)),
        )
    with pytest.raises(ValueError, match="player_count must be positive"):
        module.MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount(
            reason_code="basketball_minutes_restriction_empty",
            player_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="minutes_gap must match calculated value"):
        replace(report.rows[0], minutes_gap=d("1.000000"))
    with pytest.raises(ValueError, match="report must be exactly"):
        module.market_research_basketball_minutes_restriction_digest_payload("bad")


def test_report_constructor_canonicalizes_signal_config_version_pairs() -> None:
    report = build_report(signal())

    rebuilt = replace(
        report,
        signal_config_versions=[
            [
                "official_injury_report",
                "basketball-minutes-feed-v0",
            ],
        ],
    )

    assert rebuilt.signal_config_versions == (
        ("official_injury_report", "basketball-minutes-feed-v0"),
    )
    assert type(rebuilt.signal_config_versions) is tuple
    assert type(rebuilt.signal_config_versions[0]) is tuple


def test_payload_helpers_reject_unknown_objects_and_non_canonical_values() -> None:
    module = api()

    @dataclass(frozen=True)
    class UnknownPublicObject:
        value: Decimal

    with pytest.raises(ValueError, match="known public dataclass"):
        module._require_payload_safe_value(
            "payload",
            UnknownPublicObject(d("1.000000")),
        )
    with pytest.raises(ValueError, match="known public dataclass"):
        module._to_plain(UnknownPublicObject(d("1.000000")))
    with pytest.raises(ValueError, match="six decimals"):
        module._to_plain(d("1.0000001"))

    for raw_value in (
        [d("1.000000")],
        {"value": d("1.000000")},
        {d("1.000000")},
    ):
        with pytest.raises(ValueError, match="constructor-normalized"):
            module._require_payload_safe_value("payload", raw_value)
        with pytest.raises(ValueError, match="safe"):
            module._to_plain(raw_value)


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_BASKETBALL_MINUTES_RESTRICTION_DIGEST_CONFIG_VERSION",
        "BASKETBALL_MINUTES_RESTRICTION_RESEARCH_SCOPE",
        "MarketResearchBasketballMinutesRestrictionDigestConfig",
        "MarketResearchBasketballMinutesRestrictionDigestSignal",
        "MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount",
        "MarketResearchBasketballMinutesRestrictionDigestRow",
        "MarketResearchBasketballMinutesRestrictionDigestReport",
        "build_market_research_basketball_minutes_restriction_digest",
        "market_research_basketball_minutes_restriction_digest_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(signal())
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "watch"

    for item in (report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(item):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_threshold")
                or field.name.endswith("_minutes")
                or field.name.endswith("_gap")
                or field.name.endswith("_seconds")
                or field.name.endswith("_confidence")
            ):
                value = getattr(item, field.name)
                if value is not None:
                    assert type(value) is Decimal


def test_public_dataclasses_reject_subclassing() -> None:
    module = api()

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            with pytest.raises(TypeError, match="does not support subclassing"):
                type(f"Bad{exported_name}", (value,), {})


def test_module_scope_has_no_io_live_trading_float_or_sensitive_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_research_basketball_minutes_restriction_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    forbidden_imports = {
        "pathlib",
        "os",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    assert imported_modules.isdisjoint(forbidden_imports)
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "wallet",
        "broker",
        "order",
        "account",
        "advice",
        "auth",
        "signing",
        "cancel",
        "replace",
        "exchange mutation",
    ):
        assert forbidden not in lowered
