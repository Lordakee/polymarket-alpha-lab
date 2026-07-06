from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_basketball_rotation_usage_spike_digest import (
    DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION,
    MarketResearchBasketballRotationUsageSpikeDigestConfig,
    MarketResearchBasketballRotationUsageSpikeDigestObservation,
    MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount,
    MarketResearchBasketballRotationUsageSpikeDigestReport,
    MarketResearchBasketballRotationUsageSpikeDigestRow,
    build_market_research_basketball_rotation_usage_spike_digest,
    market_research_basketball_rotation_usage_spike_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 5, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchBasketballRotationUsageSpikeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "min_source_count": d("2.000000"),
        "watch_minutes_delta": d("6.000000"),
        "blocked_minutes_delta": d("10.000000"),
        "watch_usage_rate_delta": d("0.040000"),
        "blocked_usage_rate_delta": d("0.080000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchBasketballRotationUsageSpikeDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    signal_id: str = "signal_alpha",
    *,
    event_id: str = "nba_event_alpha",
    team_id: str = "team_alpha",
    player_id: str = "player_alpha",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    baseline_minutes: Decimal = d("24.000000"),
    projected_minutes: Decimal = d("26.000000"),
    baseline_usage_rate: Decimal = d("0.210000"),
    projected_usage_rate: Decimal = d("0.230000"),
    source_count: Decimal = d("2.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "basketball-rotation-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchBasketballRotationUsageSpikeDigestObservation:
    return MarketResearchBasketballRotationUsageSpikeDigestObservation(
        condition_id=condition_id,
        signal_id=signal_id,
        event_id=event_id,
        team_id=team_id,
        player_id=player_id,
        observed_at=observed_at,
        baseline_minutes=baseline_minutes,
        projected_minutes=projected_minutes,
        baseline_usage_rate=baseline_usage_rate,
        projected_usage_rate=projected_usage_rate,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *observations: MarketResearchBasketballRotationUsageSpikeDigestObservation,
    config: MarketResearchBasketballRotationUsageSpikeDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchBasketballRotationUsageSpikeDigestReport:
    return build_market_research_basketball_rotation_usage_spike_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_rotation_usage_spike_digest_flags_pressure_and_sorts() -> None:
    summary = _report(
        _observation(
            "condition_ready",
            "signal_ready",
            player_id="player_ready",
        ),
        _observation(
            "condition_blocked",
            "signal_blocked",
            event_id="nba_event_beta",
            team_id="team_beta",
            player_id="player_blocked",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            baseline_minutes=d("18.000000"),
            projected_minutes=d("30.000000"),
            baseline_usage_rate=d("0.180000"),
            projected_usage_rate=d("0.270000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(
            "condition_watch",
            "signal_watch",
            event_id="nba_event_gamma",
            team_id="team_gamma",
            player_id="player_watch",
            baseline_minutes=d("20.000000"),
            projected_minutes=d("27.000000"),
            baseline_usage_rate=d("0.240000"),
            projected_usage_rate=d("0.260000"),
            source_count=d("1.000000"),
        ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_basketball_rotation_usage_spike_digest"
    )
    assert summary.observation_count == d("3.000000")
    assert summary.ready_observation_count == d("1.000000")
    assert summary.watch_observation_count == d("1.000000")
    assert summary.blocked_observation_count == d("1.000000")
    assert summary.minutes_spike_count == d("2.000000")
    assert summary.usage_rate_spike_count == d("1.000000")
    assert summary.combined_spike_count == d("1.000000")
    assert summary.source_gap_count == d("2.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.confidence_gap_count == d("1.000000")
    assert summary.average_minutes_spike_delta == d("7.000000")
    assert summary.average_usage_rate_spike_delta == d("0.043333")
    assert summary.max_minutes_spike_delta == d("12.000000")
    assert summary.max_usage_rate_spike_delta == d("0.090000")

    assert tuple((row.condition_id, row.signal_id) for row in summary.rows) == (
        ("condition_blocked", "signal_blocked"),
        ("condition_watch", "signal_watch"),
        ("condition_ready", "signal_ready"),
    )

    blocked = summary.rows[0]
    assert blocked.spike_status == "blocked"
    assert blocked.observation_age_seconds == d("2400.000000")
    assert blocked.minutes_delta == d("12.000000")
    assert blocked.minutes_spike_delta == d("12.000000")
    assert blocked.usage_rate_delta == d("0.090000")
    assert blocked.usage_rate_spike_delta == d("0.090000")
    assert blocked.reason_codes == (
        "market_research_basketball_rotation_usage_spike_digest_minutes_spike",
        "market_research_basketball_rotation_usage_spike_digest_usage_rate_spike",
        "market_research_basketball_rotation_usage_spike_digest_combined_spike",
        "market_research_basketball_rotation_usage_spike_digest_source_gap",
        "market_research_basketball_rotation_usage_spike_digest_stale_observation",
        "market_research_basketball_rotation_usage_spike_digest_confidence_gap",
    )
    assert summary.reason_codes == (
        "market_research_basketball_rotation_usage_spike_digest_minutes_spike",
        "market_research_basketball_rotation_usage_spike_digest_usage_rate_spike",
        "market_research_basketball_rotation_usage_spike_digest_combined_spike",
        "market_research_basketball_rotation_usage_spike_digest_source_gap",
        "market_research_basketball_rotation_usage_spike_digest_stale_observation",
        "market_research_basketball_rotation_usage_spike_digest_confidence_gap",
    )
    assert summary.reason_code_counts == (
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code="market_research_basketball_rotation_usage_spike_digest_minutes_spike",
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_rotation_usage_spike_digest_usage_rate_spike"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code="market_research_basketball_rotation_usage_spike_digest_combined_spike",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code="market_research_basketball_rotation_usage_spike_digest_source_gap",
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_rotation_usage_spike_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code="market_research_basketball_rotation_usage_spike_digest_confidence_gap",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code="market_research_basketball_rotation_usage_spike_digest_ready",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )


def test_empty_input_is_blocked_report_only_digest_with_positive_reason_count() -> None:
    summary = _report(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))

    assert summary.generated_at == GENERATED_AT
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "hold_report_only_market_research_basketball_rotation_usage_spike_digest"
    )
    assert summary.observation_count == ZERO
    assert summary.ready_observation_count == ZERO
    assert summary.watch_observation_count == ZERO
    assert summary.blocked_observation_count == ZERO
    assert summary.reason_codes == (
        "market_research_basketball_rotation_usage_spike_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code="market_research_basketball_rotation_usage_spike_digest_no_inputs",
            count=d("1.000000"),
            observation_ratio=ZERO,
        ),
    )
    assert summary.rows == ()
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_serializes_public_values_and_enforces_utc_payload_time() -> None:
    summary = _report(
        _observation(
            observed_at=datetime(2026, 7, 5, 19, 58, tzinfo=timezone(timedelta(hours=4))),
            baseline_minutes=d("20.000000"),
            projected_minutes=d("27.000000"),
            baseline_usage_rate=d("0.240000"),
            projected_usage_rate=d("0.280000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    payload = market_research_basketball_rotation_usage_spike_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-05T16:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_minutes_spike_delta"] == "7.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T15:58:00+00:00"
    assert payload["rows"][0]["projected_usage_rate"] == "0.280000"
    assert payload["rows"][0]["usage_rate_spike_delta"] == "0.040000"
    assert payload["reason_code_counts"][0]["observation_ratio"] == "1.000000"
    _assert_no_float_decimal_or_datetime_payload(payload)

    object.__setattr__(
        summary,
        "generated_at",
        datetime(2026, 7, 5, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="normalized to UTC"):
        market_research_basketball_rotation_usage_spike_digest_payload(summary)

    summary = _report(_observation())
    object.__setattr__(
        summary.rows[0],
        "observed_at",
        datetime(2026, 7, 5, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="normalized to UTC"):
        market_research_basketball_rotation_usage_spike_digest_payload(summary)


def test_payload_recursively_revalidates_nested_public_dataclasses() -> None:
    summary = _report(
        _observation(
            baseline_minutes=d("20.000000"),
            projected_minutes=d("27.000000"),
        ),
    )

    object.__setattr__(summary.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_basketball_rotation_usage_spike_digest_payload(summary)
    object.__setattr__(summary.rows[0], "readonly", True)

    object.__setattr__(summary.reason_code_counts[0], "count", ZERO)
    with pytest.raises(ValueError, match="constructor-valid"):
        market_research_basketball_rotation_usage_spike_digest_payload(summary)
    object.__setattr__(summary.reason_code_counts[0], "count", d("1.000000"))

    object.__setattr__(summary.rows[0], "minutes_spike_delta", d("0.000001"))
    with pytest.raises(ValueError, match="constructor-valid"):
        market_research_basketball_rotation_usage_spike_digest_payload(summary)


def test_builder_recursively_revalidates_tampered_observations() -> None:
    tampered = _observation()
    object.__setattr__(tampered, "observed_at", datetime(2026, 7, 5, 12, 0, tzinfo=timezone(timedelta(hours=-4))))
    with pytest.raises(ValueError, match="observed_at must be normalized to UTC"):
        _report(tampered)

    tampered = _observation(signal_id="signal_tampered_delta")
    object.__setattr__(tampered, "projected_minutes", d("26.0"))
    with pytest.raises(ValueError, match="projected_minutes must be an exact six-place Decimal"):
        _report(tampered)


def test_public_constructors_reject_lists_and_nondeterministic_sequences() -> None:
    summary = _report(
        _observation(
            "condition_b",
            "signal_b",
            player_id="player_b",
            baseline_minutes=d("20.000000"),
            projected_minutes=d("27.000000"),
        ),
        _observation(
            "condition_a",
            "signal_a",
            player_id="player_a",
            baseline_minutes=d("20.000000"),
            projected_minutes=d("31.000000"),
            baseline_usage_rate=d("0.180000"),
            projected_usage_rate=d("0.270000"),
            source_count=d("1.000000"),
        ),
    )

    with pytest.raises(ValueError, match="observations must be a tuple"):
        build_market_research_basketball_rotation_usage_spike_digest(
            [_observation()],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(summary.rows[0], reason_codes=list(summary.rows[0].reason_codes))
    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(summary, rows=list(summary.rows))
    with pytest.raises(ValueError, match="deterministic sequence"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(summary, source_config_versions=tuple(reversed(summary.source_config_versions)))


def test_public_values_are_frozen_exact_decimal_and_type_safe() -> None:
    public_values = (
        _config(),
        _observation(),
        *_report(_observation()).rows,
        *_report(_observation(projected_minutes=d("31.000000"))).reason_code_counts,
        _report(_observation()),
    )
    for value in public_values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False

    with pytest.raises(ValueError, match="config_version"):
        _config(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="watch_minutes_delta"):
        _config(watch_minutes_delta=_DecimalSubclass("6.000000"))
    with pytest.raises(ValueError, match="watch_minutes_delta"):
        _config(watch_minutes_delta=d("6.0"))
    with pytest.raises(ValueError, match="watch_usage_rate_delta"):
        _config(watch_usage_rate_delta=d("0.0400000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=2)
    with pytest.raises(ValueError, match="projected_minutes"):
        _observation(projected_minutes=26.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_id"):
        _observation(event_id=_StringSubclass("nba_event_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-" + "api" + "_" + "key" + "-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 5, 16, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        _observation(observed_at=datetime(2026, 7, 5, 16, 0, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        _observation(paper_only=False)

    public_type_kwargs = (
        (MarketResearchBasketballRotationUsageSpikeDigestConfig, {}),
        (
            MarketResearchBasketballRotationUsageSpikeDigestObservation,
            _observation_kwargs(),
        ),
    )
    for public_type, kwargs in public_type_kwargs:
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})
        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)

    numeric_names = {
        field.name
        for value in public_values
        for field in fields(value)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_delta")
            or field.name.endswith("_seconds")
            or field.name.endswith("_minutes")
            or field.name.startswith("max_")
            or field.name.startswith("average_")
            or field.name == "confidence"
            or field.name == "min_confidence"
        )
    }
    assert numeric_names
    for value in public_values:
        for field in fields(value):
            if field.name in numeric_names:
                public_value = getattr(value, field.name)
                assert type(public_value) is Decimal, field.name
                assert public_value.as_tuple().exponent == -6, field.name


def test_module_excludes_io_asdict_and_live_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_rotation_usage_spike_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered_source = source.lower()
    tree = ast.parse(source)

    assert "asdict" not in lowered_source
    forbidden_literals = (
        "market_" + "slug",
        "ques" + "tion",
        "payload_" + "json",
        "buy",
        "sell",
        "tr" + "ade",
        "wallet",
        "ord" + "er",
        "position",
        "au" + "th",
        "cancel",
        "exchange",
        "mutation",
        "replace",
        "secret",
        "private" + "_" + "key",
        "api" + "_" + "key",
        "token",
    )
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "sqlite",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _observation_kwargs(**overrides: object) -> dict[str, object]:
    values = {
        "condition_id": "condition_alpha",
        "signal_id": "signal_alpha",
        "event_id": "nba_event_alpha",
        "team_id": "team_alpha",
        "player_id": "player_alpha",
        "observed_at": GENERATED_AT - timedelta(seconds=120),
        "baseline_minutes": d("24.000000"),
        "projected_minutes": d("26.000000"),
        "baseline_usage_rate": d("0.210000"),
        "projected_usage_rate": d("0.230000"),
        "source_count": d("2.000000"),
        "confidence": d("0.820000"),
        "source_config_version": "basketball-rotation-source-v0",
    }
    values.update(overrides)
    return values


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]


def _assert_no_float_decimal_or_datetime_payload(value: object) -> None:
    if isinstance(value, (float, Decimal, datetime)):
        pytest.fail("public payload must not contain float, Decimal, or datetime values")
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float_decimal_or_datetime_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_float_decimal_or_datetime_payload(child)
