from __future__ import annotations

import ast
import importlib
import importlib.util
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_tennis_altitude_ball_speed_shift_digest"
)
SOURCE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_tennis_altitude_ball_speed_shift_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "tennis altitude ball-speed shift digest module must exist"
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(mod: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            mod.DEFAULT_MARKET_RESEARCH_TENNIS_ALTITUDE_BALL_SPEED_SHIFT_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("86400.000000"),
        "high_altitude_meters_threshold": d("1000.000000"),
        "ball_speed_shift_ratio_watch_threshold": d("0.060000"),
        "altitude_ball_speed_pressure_watch_threshold": d("0.650000"),
        "altitude_ball_speed_pressure_blocked_threshold": d("0.850000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_confidence_score": d("0.600000"),
    }
    values.update(overrides)
    return mod.MarketResearchTennisAltitudeBallSpeedShiftDigestConfig(**values)


def observation(
    mod: Any,
    market_id: str = "tennis.altitude.default",
    *,
    tournament_key: str = "wimbledon",
    match_key: str = "alcaraz.sinner.default",
    venue_key: str = "centre-court",
    public_evidence_reference: str = "official-ball-speed-note",
    observed_at: datetime | None = None,
    match_start_at: datetime | None = None,
    venue_altitude_meters: Decimal = d("1609.000000"),
    baseline_ball_speed_kph: Decimal = d("120.000000"),
    current_ball_speed_kph: Decimal = d("132.000000"),
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("3.000000"),
    conflicting_source_count: Decimal = d("0.000000"),
    confidence_score: Decimal = d("0.920000"),
    observation_config_version: str = "tennis-altitude-ball-speed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return mod.MarketResearchTennisAltitudeBallSpeedShiftObservation(
        market_id=market_id,
        tournament_key=tournament_key,
        match_key=match_key,
        venue_key=venue_key,
        public_evidence_reference=public_evidence_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        match_start_at=match_start_at or datetime(2026, 7, 6, 14, 0, tzinfo=UTC),
        venue_altitude_meters=venue_altitude_meters,
        baseline_ball_speed_kph=baseline_ball_speed_kph,
        current_ball_speed_kph=current_ball_speed_kph,
        source_count=source_count,
        independent_source_count=independent_source_count,
        conflicting_source_count=conflicting_source_count,
        confidence_score=confidence_score,
        observation_config_version=observation_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    mod: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return mod.build_market_research_tennis_altitude_ball_speed_shift_digest(
        rows,
        config=cfg or config(mod),
        generated_at=generated_at,
    )


def test_empty_tennis_altitude_ball_speed_shift_digest_is_blocked_and_zeroed() -> None:
    mod = module()

    summary = report(mod, ())

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_tennis_altitude_ball_speed_shift_digest"
    )
    assert summary.observation_count == d("0.000000")
    assert summary.ready_observation_count == d("0.000000")
    assert summary.watch_observation_count == d("0.000000")
    assert summary.blocked_observation_count == d("0.000000")
    assert summary.average_ball_speed_shift_ratio == d("0.000000")
    assert summary.max_absolute_ball_speed_shift_ratio == d("0.000000")
    assert summary.max_altitude_ball_speed_pressure_index == d("0.000000")
    assert summary.rows == ()
    assert summary.observation_config_versions == ()
    assert summary.reason_codes == (
        "market_research_tennis_altitude_ball_speed_shift_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        mod.MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount(
            reason_code=(
                "market_research_tennis_altitude_ball_speed_shift_digest_no_inputs"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_high_risk_altitude_ball_speed_shift_blocks_probability_screening() -> None:
    mod = module()

    summary = report(
        mod,
        (
            observation(
                mod,
                "tennis.denver.final.market",
                tournament_key="denver-open",
                match_key="rune.fritz.final",
                venue_key="mile-high-tennis-center",
                public_evidence_reference="https://tennis.example/speed?api_key=abc123",
                venue_altitude_meters=d("1609.000000"),
                baseline_ball_speed_kph=d("120.000000"),
                current_ball_speed_kph=d("132.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_tennis_altitude_ball_speed_shift_digest"
    )
    assert summary.observation_count == d("1.000000")
    assert summary.blocked_observation_count == d("1.000000")
    assert summary.high_altitude_observation_count == d("1.000000")
    assert summary.ball_speed_shift_observation_count == d("1.000000")
    assert summary.pressure_blocked_observation_count == d("1.000000")
    assert summary.average_ball_speed_shift_ratio == d("0.100000")
    assert summary.max_absolute_ball_speed_shift_ratio == d("0.100000")
    assert summary.average_confidence_score == d("0.920000")
    assert summary.max_altitude_ball_speed_pressure_index == d("1.000000")

    row = summary.rows[0]
    assert row.market_id == "tennis.denver.final.market"
    assert row.digest_status == "blocked"
    assert row.observation_age_seconds == d("3600.000000")
    assert row.ball_speed_shift_kph == d("12.000000")
    assert row.ball_speed_shift_ratio == d("0.100000")
    assert row.altitude_pressure_ratio == d("1.000000")
    assert row.ball_speed_pressure_ratio == d("1.000000")
    assert row.altitude_ball_speed_pressure_index == d("1.000000")
    assert row.redacted_public_evidence_reference.startswith("sha256:")
    assert row.reason_codes == (
        "market_research_tennis_altitude_ball_speed_shift_digest_ball_speed_acceleration",
        "market_research_tennis_altitude_ball_speed_shift_digest_high_altitude",
        "market_research_tennis_altitude_ball_speed_shift_digest_pressure_blocked",
    )
    assert summary.reason_code_counts == (
        mod.MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount(
            reason_code=(
                "market_research_tennis_altitude_ball_speed_shift_digest_"
                "ball_speed_acceleration"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        mod.MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount(
            reason_code=(
                "market_research_tennis_altitude_ball_speed_shift_digest_high_altitude"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        mod.MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount(
            reason_code=(
                "market_research_tennis_altitude_ball_speed_shift_digest_pressure_blocked"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == tuple(item.reason_code for item in summary.reason_code_counts)
    assert summary.observation_config_versions == (
        ("tennis.denver.final.market", "tennis-altitude-ball-speed-v0"),
    )


def test_tennis_altitude_ball_speed_shift_digest_is_deterministic() -> None:
    mod = module()
    high_risk = observation(
        mod,
        "tennis.altitude.blocked",
        match_start_at=datetime(2026, 7, 7, 16, 0, tzinfo=UTC),
    )
    ready = observation(
        mod,
        "tennis.altitude.ready",
        venue_altitude_meters=d("250.000000"),
        baseline_ball_speed_kph=d("120.000000"),
        current_ball_speed_kph=d("121.000000"),
        match_start_at=datetime(2026, 7, 5, 11, 0, tzinfo=UTC),
    )

    left = report(mod, (ready, high_risk))
    right = report(mod, (high_risk, ready))

    assert mod.market_research_tennis_altitude_ball_speed_shift_digest_payload(left) == (
        mod.market_research_tennis_altitude_ball_speed_shift_digest_payload(right)
    )
    assert tuple(row.market_id for row in left.rows) == (
        "tennis.altitude.blocked",
        "tennis.altitude.ready",
    )
    for row in left.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert left.reason_codes == tuple(sorted(left.reason_codes))


def test_tennis_altitude_ball_speed_shift_digest_validates_inputs() -> None:
    mod = module()

    assert mod.MarketResearchTennisAltitudeBallSpeedShiftDigestConfig.__dataclass_params__.frozen
    assert mod.MarketResearchTennisAltitudeBallSpeedShiftObservation.__dataclass_params__.frozen
    assert mod.MarketResearchTennisAltitudeBallSpeedShiftRow.__dataclass_params__.frozen
    assert mod.MarketResearchTennisAltitudeBallSpeedShiftReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(mod, config_version=_StringSubclass("tennis-altitude-v0"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(mod, min_source_count=2)
    with pytest.raises(ValueError, match="blocked"):
        config(
            mod,
            altitude_ball_speed_pressure_watch_threshold=d("0.700000"),
            altitude_ball_speed_pressure_blocked_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="current_ball_speed_kph"):
        observation(mod, current_ball_speed_kph=_DecimalSubclass("132.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(mod, observed_at=_DatetimeSubclass(2026, 7, 4, 17, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(mod, observed_at=datetime(2026, 7, 4, 17, 0))
    with pytest.raises(ValueError, match="baseline_ball_speed_kph"):
        observation(mod, baseline_ball_speed_kph=d("0.000000"))
    with pytest.raises(ValueError, match="independent_source_count"):
        observation(
            mod,
            independent_source_count=d("3.000000"),
            source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="MarketResearchTennisAltitudeBallSpeedShift"):
        mod.build_market_research_tennis_altitude_ball_speed_shift_digest(
            [object()],
            config=config(mod),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        report(
            mod,
            (observation(mod, observed_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="unique"):
        report(
            mod,
            (
                observation(mod, "tennis.duplicate"),
                observation(mod, "tennis.duplicate"),
            ),
        )
    with pytest.raises(TypeError):
        type(
            "ConfigSubclass",
            (mod.MarketResearchTennisAltitudeBallSpeedShiftDigestConfig,),
            {},
        )


def test_tennis_altitude_ball_speed_shift_digest_enforces_hard_flags() -> None:
    mod = module()

    with pytest.raises(ValueError, match="paper_only"):
        config(mod, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(mod, report_only=False)
    with pytest.raises(FrozenInstanceError):
        observation(mod).paper_only = False  # type: ignore[misc]

    summary = report(mod, (observation(mod),))
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert summary.rows[0].paper_only is True
    assert summary.rows[0].report_only is True
    assert summary.rows[0].readonly is True
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


def test_non_default_thresholds_can_clear_altitude_ball_speed_shift() -> None:
    mod = module()
    strict_config = config(
        mod,
        high_altitude_meters_threshold=d("3000.000000"),
        ball_speed_shift_ratio_watch_threshold=d("0.250000"),
        altitude_ball_speed_pressure_watch_threshold=d("0.900000"),
        altitude_ball_speed_pressure_blocked_threshold=d("0.990000"),
    )

    summary = report(
        mod,
        (
            observation(
                mod,
                "tennis.altitude.nondefault",
                venue_altitude_meters=d("1200.000000"),
                baseline_ball_speed_kph=d("100.000000"),
                current_ball_speed_kph=d("110.000000"),
            ),
        ),
        cfg=strict_config,
    )

    assert summary.digest_status == "ready"
    assert summary.ready_observation_count == d("1.000000")
    assert summary.blocked_observation_count == d("0.000000")
    assert summary.high_altitude_meters_threshold == d("3000.000000")
    assert summary.ball_speed_shift_ratio_watch_threshold == d("0.250000")
    row = summary.rows[0]
    assert row.digest_status == "ready"
    assert row.altitude_pressure_ratio == d("0.400000")
    assert row.ball_speed_pressure_ratio == d("0.400000")
    assert row.altitude_ball_speed_pressure_index == d("0.400000")
    assert row.reason_codes == (
        "market_research_tennis_altitude_ball_speed_shift_digest_ready",
    )


def test_tennis_altitude_ball_speed_shift_payload_redacts_and_stringifies() -> None:
    mod = module()
    summary = report(
        mod,
        (
            observation(
                mod,
                "tennis.payload.altitude",
                public_evidence_reference="https://tennis.example/speed?api_key=abc123",
            ),
        ),
    )

    payload = mod.market_research_tennis_altitude_ball_speed_shift_digest_payload(summary)
    encoded = repr(payload)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["venue_altitude_meters"] == "1609.000000"
    assert payload["rows"][0]["ball_speed_shift_ratio"] == "0.100000"
    assert payload["rows"][0]["redacted_public_evidence_reference"].startswith("sha256:")
    assert "abc123" not in encoded
    assert not any(type(value) in (Decimal, int, float) for value in walk_values(payload))


def test_tennis_altitude_ball_speed_shift_module_scope_is_pure_report_only() -> None:
    assert SOURCE_PATH.exists(), "digest source file must exist"
    source = SOURCE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "exchange",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "open(",
        "read_text",
        "write_text",
    ):
        assert forbidden not in source.lower()


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)
