from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 3, 10, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-lineup-volatility-digest-test-v0"


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_lineup_volatility_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "volatility_score_threshold": d("0.250000"),
        "minutes_delta_threshold": d("6.000000"),
        "starter_flip_threshold": d("1"),
        "source_disagreement_threshold": d("1"),
        "stale_update_seconds_threshold": d("3600.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBasketballLineupVolatilityDigestConfig(**values)


def signal(
    condition_id: str = "condition_alpha",
    lineup_key: str = "nba_bos_nyk_tatum",
    *,
    league_key: str = "nba",
    team_key: str = "bos",
    player_key: str = "player_tatum",
    source_ref: str = "official_lineup",
    observed_at: datetime = BASE_OBSERVED_AT,
    projected_minutes: Decimal = d("34.000000"),
    starter_probability: Decimal = d("1.000000"),
    status_rank: Decimal = d("1"),
    source_disagreement_count: Decimal = d("0"),
    signal_config_version: str = "basketball-lineup-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBasketballLineupVolatilityDigestSignal(
        condition_id=condition_id,
        lineup_key=lineup_key,
        league_key=league_key,
        team_key=team_key,
        player_key=player_key,
        source_ref=source_ref,
        observed_at=observed_at,
        projected_minutes=projected_minutes,
        starter_probability=starter_probability,
        status_rank=status_rank,
        source_disagreement_count=source_disagreement_count,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals, **overrides):
    digest = module()
    values = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_basketball_lineup_volatility_digest(**values)


def test_lineup_volatility_digest_flags_minutes_starter_disagreement_and_stale_updates() -> None:
    report = build_report(
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_old",
            observed_at=BASE_OBSERVED_AT,
            projected_minutes=d("36.000000"),
            starter_probability=d("1.000000"),
            status_rank=d("1"),
            signal_config_version="basketball-lineup-feed-v0",
        ),
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_new",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_minutes=d("24.000000"),
            starter_probability=d("0.200000"),
            status_rank=d("3"),
            source_disagreement_count=d("2"),
            signal_config_version="basketball-lineup-feed-v1",
        ),
        signal(
            "condition_alpha",
            "nba_bos_nyk_tatum",
            source_ref="celtics_official",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            projected_minutes=d("34.000000"),
            starter_probability=d("1.000000"),
            status_rank=d("1"),
        ),
        signal(
            "condition_alpha",
            "nba_bos_nyk_tatum",
            source_ref="celtics_beat",
            observed_at=GENERATED_AT - timedelta(minutes=5),
            projected_minutes=d("35.000000"),
            starter_probability=d("0.950000"),
            status_rank=d("1"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_basketball_lineup_volatility"
    )
    assert report.lineup_count == d("2")
    assert report.signal_count == d("4")
    assert report.clear_lineup_count == d("1")
    assert report.watch_lineup_count == d("1")
    assert report.high_minutes_delta_lineup_count == d("1")
    assert report.starter_flip_lineup_count == d("1")
    assert report.source_disagreement_lineup_count == d("1")
    assert report.stale_update_lineup_count == d("1")
    assert report.max_minutes_delta == d("12.000000")
    assert report.max_starter_probability_delta == d("0.800000")
    assert report.max_status_rank_delta == d("2")
    assert report.max_update_age_seconds == d("5400.000000")
    assert report.reason_codes == (
        "basketball_lineup_volatility_minutes_delta_high",
        "basketball_lineup_volatility_source_disagreement_high",
        "basketball_lineup_volatility_stale_update_cadence",
        "basketball_lineup_volatility_starter_flip_high",
    )
    assert report.reason_code_counts == (
        module().MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
            reason_code="basketball_lineup_volatility_minutes_delta_high",
            lineup_count=d("1"),
        ),
        module().MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
            reason_code="basketball_lineup_volatility_source_disagreement_high",
            lineup_count=d("1"),
        ),
        module().MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
            reason_code="basketball_lineup_volatility_stale_update_cadence",
            lineup_count=d("1"),
        ),
        module().MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
            reason_code="basketball_lineup_volatility_starter_flip_high",
            lineup_count=d("1"),
        ),
    )
    assert report.signal_config_versions == (
        ("celtics_beat", "basketball-lineup-feed-v0"),
        ("celtics_official", "basketball-lineup-feed-v0"),
        ("lakers_new", "basketball-lineup-feed-v1"),
        ("lakers_old", "basketball-lineup-feed-v0"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.lineup_key, row.team_key, row.player_key) for row in report.rows) == (
        ("nba_lal_den_davis", "lal", "player_davis"),
        ("nba_bos_nyk_tatum", "bos", "player_tatum"),
    )
    volatile = report.rows[0]
    assert volatile.digest_status == "watch"
    assert volatile.signal_count == d("2")
    assert volatile.minutes_min == d("24.000000")
    assert volatile.minutes_max == d("36.000000")
    assert volatile.minutes_delta == d("12.000000")
    assert volatile.starter_probability_delta == d("0.800000")
    assert volatile.status_rank_delta == d("2")
    assert volatile.source_disagreement_count == d("2")
    assert volatile.update_age_seconds == d("5400.000000")
    assert volatile.volatility_score == d("1.000000")
    assert volatile.reason_codes == (
        "basketball_lineup_volatility_minutes_delta_high",
        "basketball_lineup_volatility_source_disagreement_high",
        "basketball_lineup_volatility_stale_update_cadence",
        "basketball_lineup_volatility_starter_flip_high",
    )

    clear = report.rows[1]
    assert clear.digest_status == "clear"
    assert clear.minutes_delta == d("1.000000")
    assert clear.starter_probability_delta == d("0.050000")
    assert clear.volatility_score == d("0.060000")
    assert clear.reason_codes == ("basketball_lineup_volatility_clear",)


def test_lineup_volatility_digest_blocks_empty_and_passes_stable_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "blocked"
    assert (
        empty_report.recommended_next_step
        == "block_report_only_basketball_lineup_volatility"
    )
    assert empty_report.lineup_count == d("0")
    assert empty_report.signal_count == d("0")
    assert empty_report.reason_codes == ("basketball_lineup_volatility_empty",)
    assert empty_report.reason_code_counts == (
        module().MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
            reason_code="basketball_lineup_volatility_empty",
            lineup_count=d("1.000000"),
        ),
    )
    assert empty_report.rows == ()
    assert empty_report.max_minutes_delta is None
    assert empty_report.max_update_age_seconds is None

    stable_report = build_report(
        signal(
            "condition_alpha",
            "nba_bos_nyk_tatum",
            source_ref="alpha_old",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            projected_minutes=d("33.000000"),
            starter_probability=d("0.900000"),
        ),
        signal(
            "condition_alpha",
            "nba_bos_nyk_tatum",
            source_ref="alpha_new",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            projected_minutes=d("35.000000"),
            starter_probability=d("1.000000"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == ("basketball_lineup_volatility_passed",)
    assert stable_report.rows[0].digest_status == "clear"
    assert stable_report.rows[0].reason_codes == ("basketball_lineup_volatility_clear",)


def test_payload_helper_uses_json_ready_decimal_strings_and_no_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        signal(
            "condition_payload",
            "nba_mia_bos_butler",
            team_key="mia",
            player_key="player_butler",
            source_ref="payload_safe_ref",
            observed_at=datetime(2026, 7, 3, 7, 0, tzinfo=timezone(timedelta(hours=-3))),
            projected_minutes=d("30.000000"),
            starter_probability=d("0.700000"),
        ),
        signal(
            "condition_payload",
            "nba_mia_bos_butler",
            team_key="mia",
            player_key="player_butler",
            source_ref="payload_safe_ref_new",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            projected_minutes=d("39.000000"),
            starter_probability=d("1.000000"),
        ),
    )

    payload = digest.market_research_basketball_lineup_volatility_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["lineup_count"] == "1.000000"
    assert payload["rows"][0]["observed_at_latest"] == "2026-07-03T11:40:00+00:00"
    assert payload["rows"][0]["minutes_delta"] == "9.000000"
    assert payload["rows"][0]["signal_count"] == "2.000000"
    assert payload["rows"][0]["status_rank_min"] == "1.000000"
    assert payload["max_minutes_delta"] == "9.000000"
    assert payload["max_status_rank_delta"] == "0.000000"
    assert payload["volatility_score_threshold"] == "0.250000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    payload_text = repr(payload).lower()
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
        "api_key",
        "private_key",
        "secret",
        "token",
        "exchange",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in payload_text


def test_dataclasses_are_frozen_validate_decimal_datetime_and_flags() -> None:
    digest = module()

    row = signal()
    with pytest.raises(FrozenInstanceError):
        row.projected_minutes = d("35.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="projected_minutes must be a Decimal"):
        signal(projected_minutes=30.5)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="starter_probability"):
        signal(starter_probability=d("1.100000"))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 10, 0))

    with pytest.raises(ValueError, match="condition_id must be a string"):
        signal(condition_id=_StringSubclass("condition_alpha"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(signal(), generated_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        digest.MarketResearchBasketballLineupVolatilityDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="contains unsafe source detail"):
        signal(condition_id="market_slug_alpha")

    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(
            signal("condition_alpha", "nba_bos_nyk_tatum", source_ref="same_ref"),
            signal("condition_alpha", "nba_bos_nyk_tatum", source_ref="same_ref"),
        )

    with pytest.raises(ValueError, match="volatility_score_threshold"):
        config(volatility_score_threshold=_DecimalSubclass("0.250000"))


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    (
        ("condition_id", "exchange_lineup_alpha"),
        ("lineup_key", "cancel_lineup_alpha"),
        ("source_ref", "official_secret_token"),
        ("signal_config_version", "provider_api_key_feed"),
    ),
)
def test_public_signal_text_rejects_secret_and_mutation_surfaces(
    field_name: str,
    unsafe_value: str,
) -> None:
    with pytest.raises(ValueError, match="contains unsafe source detail"):
        signal(**{field_name: unsafe_value})


def test_reason_code_counts_reject_zero_and_must_match_report_rows() -> None:
    digest = module()

    with pytest.raises(ValueError, match="lineup_count must be positive"):
        digest.MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
            reason_code="basketball_lineup_volatility_minutes_delta_high",
            lineup_count=d("0.000000"),
        )

    watched = build_report(
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_old",
            observed_at=BASE_OBSERVED_AT,
            projected_minutes=d("36.000000"),
        ),
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_new",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_minutes=d("24.000000"),
            starter_probability=d("0.200000"),
            status_rank=d("3"),
            source_disagreement_count=d("2"),
        ),
    )
    wrong_count = digest.MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
        reason_code="basketball_lineup_volatility_minutes_delta_high",
        lineup_count=d("2.000000"),
    )
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(watched, reason_code_counts=(wrong_count,))

    empty_report = build_report()
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(empty_report, reason_code_counts=())
    with pytest.raises(ValueError, match="digest_status must match rows"):
        replace(
            empty_report,
            digest_status="pass",
            recommended_next_step=(
                "continue_report_only_basketball_lineup_volatility_monitoring"
            ),
        )


def test_payload_revalidates_nested_dataclasses_flags_and_decimal_scale() -> None:
    digest = module()

    def watched_report():
        return build_report(
            signal(
                "condition_beta",
                "nba_lal_den_davis",
                team_key="lal",
                player_key="player_davis",
                source_ref="lakers_old",
                observed_at=BASE_OBSERVED_AT,
                projected_minutes=d("36.000000"),
            ),
            signal(
                "condition_beta",
                "nba_lal_den_davis",
                team_key="lal",
                player_key="player_davis",
                source_ref="lakers_new",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
                projected_minutes=d("24.000000"),
                starter_probability=d("0.200000"),
                status_rank=d("3"),
                source_disagreement_count=d("2"),
            ),
        )

    nested_flag_report = watched_report()
    object.__setattr__(nested_flag_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="row paper_only must be True"):
        digest.market_research_basketball_lineup_volatility_digest_payload(
            nested_flag_report,
        )

    nested_count_flag_report = watched_report()
    object.__setattr__(nested_count_flag_report.reason_code_counts[0], "readonly", False)
    with pytest.raises(ValueError, match="reason_code_count readonly must be True"):
        digest.market_research_basketball_lineup_volatility_digest_payload(
            nested_count_flag_report,
        )

    decimal_scale_report = watched_report()
    object.__setattr__(decimal_scale_report.rows[0], "minutes_delta", d("12.0000001"))
    with pytest.raises(ValueError, match="minutes_delta must be six-decimal"):
        digest.market_research_basketball_lineup_volatility_digest_payload(
            decimal_scale_report,
        )

    nested_type_report = watched_report()
    object.__setattr__(nested_type_report, "rows", ({"lineup_key": "not_a_row"},))
    with pytest.raises(ValueError, match="rows"):
        digest.market_research_basketball_lineup_volatility_digest_payload(
            nested_type_report,
        )


def test_payload_rejects_tampered_non_utc_datetimes_before_serialization() -> None:
    digest = module()

    report_generated_at = build_report(signal())
    object.__setattr__(
        report_generated_at,
        "generated_at",
        datetime(2026, 7, 3, 7, 0, tzinfo=timezone(timedelta(hours=-5))),
    )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        digest.market_research_basketball_lineup_volatility_digest_payload(
            report_generated_at,
        )

    report_observed_at = build_report(signal())
    object.__setattr__(
        report_observed_at.rows[0],
        "observed_at_latest",
        datetime(2026, 7, 3, 5, 0, tzinfo=timezone(timedelta(hours=-5))),
    )
    with pytest.raises(ValueError, match="observed_at_latest must be UTC"):
        digest.market_research_basketball_lineup_volatility_digest_payload(
            report_observed_at,
        )


def test_payload_rejects_tampered_non_six_decimal_measurements() -> None:
    digest = module()
    report = build_report(
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_old",
            observed_at=BASE_OBSERVED_AT,
            projected_minutes=d("36.000000"),
        ),
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_new",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_minutes=d("24.000000"),
        ),
    )

    object.__setattr__(report.rows[0], "minutes_delta", d("12"))
    with pytest.raises(ValueError, match="minutes_delta must be six-decimal"):
        digest.market_research_basketball_lineup_volatility_digest_payload(report)


def test_payload_plain_helper_rejects_raw_containers_and_unknown_objects() -> None:
    digest = module()

    for raw_value in ([], {}, set(), object()):
        with pytest.raises(ValueError, match="payload values must be JSON-ready"):
            digest._to_plain(raw_value)


def test_public_dataclasses_reject_subclasses_and_keep_decimal_public_numerics() -> None:
    digest = module()
    public_dataclasses = (
        digest.MarketResearchBasketballLineupVolatilityDigestConfig,
        digest.MarketResearchBasketballLineupVolatilityDigestSignal,
        digest.MarketResearchBasketballLineupVolatilityDigestReasonCodeCount,
        digest.MarketResearchBasketballLineupVolatilityDigestRow,
        digest.MarketResearchBasketballLineupVolatilityDigestReport,
    )

    for dataclass_type in public_dataclasses:
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{dataclass_type.__name__}", (dataclass_type,), {})

    public_numeric_markers = (
        "_count",
        "_threshold",
        "_seconds",
        "_minutes",
        "_probability",
        "_rank",
        "_score",
        "_delta",
        "minutes_min",
        "minutes_max",
        "lineup_count",
        "signal_count",
    )
    decimal_annotations = (Decimal, "Decimal", "Decimal | None")
    for dataclass_type in public_dataclasses:
        for field in fields(dataclass_type):
            if field.name.endswith(public_numeric_markers) or field.name in (
                "lineup_count",
                "signal_count",
            ):
                assert field.type in decimal_annotations


def test_report_constructor_rejects_noncanonical_nested_ordering() -> None:
    watched = build_report(
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_old",
            observed_at=BASE_OBSERVED_AT,
            projected_minutes=d("36.000000"),
        ),
        signal(
            "condition_beta",
            "nba_lal_den_davis",
            team_key="lal",
            player_key="player_davis",
            source_ref="lakers_new",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_minutes=d("24.000000"),
            starter_probability=d("0.200000"),
            status_rank=d("3"),
            source_disagreement_count=d("2"),
        ),
        signal(
            "condition_alpha",
            "nba_bos_nyk_tatum",
            source_ref="celtics_official",
            observed_at=GENERATED_AT - timedelta(minutes=15),
        ),
    )

    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(watched, rows=tuple(reversed(watched.rows)))

    with pytest.raises(ValueError, match="signal_config_versions must be sorted"):
        replace(
            watched,
            signal_config_versions=tuple(reversed(watched.signal_config_versions)),
        )

    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(
            watched,
            reason_code_counts=tuple(reversed(watched.reason_code_counts)),
        )


def test_datetimes_reject_timezone_objects_without_offsets() -> None:
    class _NoneOffsetTimezone(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 10, 0, tzinfo=_NoneOffsetTimezone()))


def test_module_scope_has_no_io_live_trading_float_or_sensitive_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_research_basketball_lineup_volatility_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    imported_names: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
            assert node.func.id != "asdict"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr != "asdict"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
            imported_names.update((node.module, alias.name) for alias in node.names)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert ("dataclasses", "asdict") not in imported_names
    for forbidden in (
        "live trading",
        "market_slug",
        "question",
        "payload_json",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "replace_order",
        "account",
        "advice",
        "api_key",
        "private_key",
        "secret",
        "token",
        "exchange",
        "open(",
        "fast",
    ):
        assert forbidden not in lowered


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return tuple(values)
    return (value,)
