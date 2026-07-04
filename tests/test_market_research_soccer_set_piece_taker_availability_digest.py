from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
BASE_MATCH_START_AT = datetime(2026, 7, 5, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-soccer-set-piece-taker-availability-digest-test-v0"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_soccer_set_piece_taker_availability_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_soccer_set_piece_taker_availability_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "blocked_edge_score_threshold": d("0.700000"),
        "watch_edge_score_threshold": d("0.400000"),
        "primary_taker_unavailable_threshold": d("0.250000"),
        "primary_taker_watch_threshold": d("0.550000"),
        "secondary_taker_readiness_threshold": d("0.500000"),
        "injury_suspension_blocked_count": d("2"),
        "max_lineup_leak_age_minutes": d("90.000000"),
        "high_set_piece_xg_dependency_threshold": d("0.500000"),
        "max_source_disagreement_count": d("0"),
        "max_input_age_hours": d("24.000000"),
    }
    values.update(overrides)
    return module.MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig(**values)


def signal(
    condition_id: str = "condition_alpha",
    market_slug: str = "arsenal-chelsea-set-piece-edge",
    club: str = "arsenal",
    opponent: str = "chelsea",
    match_ref: str = "arsenal_chelsea",
    *,
    match_start_at: datetime = BASE_MATCH_START_AT,
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    primary_taker_availability_score: Decimal = d("0.900000"),
    secondary_taker_readiness_score: Decimal = d("0.900000"),
    injury_suspension_count: Decimal = d("0"),
    lineup_leak_age_minutes: Decimal = d("30.000000"),
    set_piece_xg_dependency: Decimal = d("0.100000"),
    source_disagreement_count: Decimal = d("0"),
    upstream_reason_codes: tuple[str, ...] = (),
    signal_ref: str = "local_set_piece_taker_feed_v0",
    signal_config_version: str = "soccer-set-piece-taker-availability-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal(
        condition_id=condition_id,
        market_slug=market_slug,
        club=club,
        opponent=opponent,
        match_ref=match_ref,
        match_start_at=match_start_at,
        observed_at=observed_at,
        primary_taker_availability_score=primary_taker_availability_score,
        secondary_taker_readiness_score=secondary_taker_readiness_score,
        injury_suspension_count=injury_suspension_count,
        lineup_leak_age_minutes=lineup_leak_age_minutes,
        set_piece_xg_dependency=set_piece_xg_dependency,
        source_disagreement_count=source_disagreement_count,
        upstream_reason_codes=upstream_reason_codes,
        signal_ref=signal_ref,
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
    return module.build_market_research_soccer_set_piece_taker_availability_digest(
        **values,
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in {float, int}:
        pytest.fail(f"found public number in JSON payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_number_payload(child)
    if isinstance(value, list):
        for child in value:
            assert_no_public_number_payload(child)


def test_digest_flags_blocked_watch_and_pass_set_piece_taker_availability_edge() -> None:
    module = api()

    report = build_report(
        signal(
            "condition_watch",
            "psg-bayern-free-kick-edge",
            "psg",
            "bayern",
            "psg_bayern",
            match_start_at=BASE_MATCH_START_AT + timedelta(hours=2),
            observed_at=GENERATED_AT - timedelta(hours=1),
            primary_taker_availability_score=d("0.500000"),
            secondary_taker_readiness_score=d("0.450000"),
            lineup_leak_age_minutes=d("120.000000"),
            set_piece_xg_dependency=d("0.600000"),
            upstream_reason_codes=("lineup_rotation_hint",),
            signal_config_version="soccer-set-piece-taker-availability-feed-v1",
        ),
        signal(
            "condition_pass",
            "milan-inter-corner-edge",
            "milan",
            "inter",
            "milan_inter",
            match_start_at=BASE_MATCH_START_AT + timedelta(hours=3),
            observed_at=GENERATED_AT - timedelta(minutes=30),
            primary_taker_availability_score=d("0.900000"),
            secondary_taker_readiness_score=d("0.900000"),
            set_piece_xg_dependency=d("0.100000"),
        ),
        signal(
            "condition_blocked",
            "liverpool-chelsea-set-piece-edge",
            "liverpool",
            "chelsea",
            "liverpool_chelsea",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=3),
            primary_taker_availability_score=d("0.200000"),
            secondary_taker_readiness_score=d("0.300000"),
            injury_suspension_count=d("2"),
            lineup_leak_age_minutes=d("40.000000"),
            set_piece_xg_dependency=d("0.700000"),
            source_disagreement_count=d("1"),
            upstream_reason_codes=("confirmed_specialist_absent",),
            signal_config_version="soccer-set-piece-taker-availability-feed-v2",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_set_piece_taker_availability_review"
    )
    assert report.signal_count == d("3.000000")
    assert report.pass_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.source_disagreement_signal_count == d("1.000000")
    assert report.blocked_edge_score_signal_count == d("1.000000")
    assert report.watch_edge_score_signal_count == d("1.000000")
    assert report.primary_taker_unavailable_signal_count == d("1.000000")
    assert report.primary_taker_watch_signal_count == d("1.000000")
    assert report.secondary_taker_readiness_gap_signal_count == d("2.000000")
    assert report.injury_suspension_signal_count == d("1.000000")
    assert report.stale_lineup_leak_signal_count == d("1.000000")
    assert report.high_set_piece_xg_dependency_signal_count == d("2.000000")
    assert report.upstream_reason_signal_count == d("2.000000")
    assert report.max_availability_edge_score == d("0.795000")
    assert report.average_availability_edge_score == d("0.436667")
    assert report.reason_codes == (
        "soccer_set_piece_taker_availability_source_disagreement",
        "soccer_set_piece_taker_availability_edge_score_blocked",
        "soccer_set_piece_taker_availability_primary_taker_unavailable",
        "soccer_set_piece_taker_availability_injury_suspension_pressure",
        "soccer_set_piece_taker_availability_edge_score_watch",
        "soccer_set_piece_taker_availability_primary_taker_watch",
        "soccer_set_piece_taker_availability_secondary_taker_readiness_gap",
        "soccer_set_piece_taker_availability_lineup_leak_stale",
        "soccer_set_piece_taker_availability_xg_dependency_high",
        "soccer_set_piece_taker_availability_upstream_reason_present",
    )
    assert report.reason_code_counts == (
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_source_disagreement",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_edge_score_blocked",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_primary_taker_unavailable",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_injury_suspension_pressure",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_edge_score_watch",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_primary_taker_watch",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code=(
                "soccer_set_piece_taker_availability_secondary_taker_readiness_gap"
            ),
            signal_count=d("2.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_lineup_leak_stale",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_xg_dependency_high",
            signal_count=d("2.000000"),
        ),
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code="soccer_set_piece_taker_availability_upstream_reason_present",
            signal_count=d("2.000000"),
        ),
    )
    assert report.signal_config_versions == (
        (
            "liverpool_chelsea",
            "liverpool",
            "soccer-set-piece-taker-availability-feed-v2",
        ),
        ("milan_inter", "milan", "soccer-set-piece-taker-availability-feed-v0"),
        ("psg_bayern", "psg", "soccer-set-piece-taker-availability-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.condition_id for row in report.rows) == (
        "condition_blocked",
        "condition_watch",
        "condition_pass",
    )
    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.availability_edge_score == d("0.795000")
    assert blocked.upstream_reason_codes == ("confirmed_specialist_absent",)
    assert blocked.reason_codes == (
        "soccer_set_piece_taker_availability_source_disagreement",
        "soccer_set_piece_taker_availability_edge_score_blocked",
        "soccer_set_piece_taker_availability_primary_taker_unavailable",
        "soccer_set_piece_taker_availability_injury_suspension_pressure",
        "soccer_set_piece_taker_availability_secondary_taker_readiness_gap",
        "soccer_set_piece_taker_availability_xg_dependency_high",
        "soccer_set_piece_taker_availability_upstream_reason_present",
    )
    watch = report.rows[1]
    assert watch.digest_status == "watch"
    assert watch.availability_edge_score == d("0.435000")
    assert watch.reason_codes == (
        "soccer_set_piece_taker_availability_edge_score_watch",
        "soccer_set_piece_taker_availability_primary_taker_watch",
        "soccer_set_piece_taker_availability_secondary_taker_readiness_gap",
        "soccer_set_piece_taker_availability_lineup_leak_stale",
        "soccer_set_piece_taker_availability_xg_dependency_high",
        "soccer_set_piece_taker_availability_upstream_reason_present",
    )
    passed = report.rows[2]
    assert passed.digest_status == "pass"
    assert passed.availability_edge_score == d("0.080000")
    assert passed.reason_codes == (
        "soccer_set_piece_taker_availability_clear",
    )


def test_empty_and_clear_inputs_pass_with_decimal_zeroes() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_codes == (
        "soccer_set_piece_taker_availability_empty",
    )
    assert empty_report.reason_code_counts == ()
    assert empty_report.max_availability_edge_score == d("0.000000")
    assert empty_report.average_availability_edge_score == d("0.000000")

    clear_report = build_report(
        signal(
            "condition_clear",
            "real-betis-corner-edge",
            "real",
            "betis",
            "real_betis",
            primary_taker_availability_score=d("0.850000"),
            secondary_taker_readiness_score=d("0.800000"),
            set_piece_xg_dependency=d("0.150000"),
        ),
    )

    assert clear_report.digest_status == "pass"
    assert clear_report.reason_codes == (
        "soccer_set_piece_taker_availability_passed",
    )
    assert clear_report.rows[0].digest_status == "pass"
    assert clear_report.rows[0].reason_codes == (
        "soccer_set_piece_taker_availability_clear",
    )


def test_payload_helper_uses_six_decimal_strings_utc_datetimes_and_safe_text() -> None:
    module = api()
    report = build_report(
        signal(
            "condition_payload",
            "dortmund-leipzig-free-kick-edge",
            "dortmund",
            "leipzig",
            "dortmund_leipzig",
            match_start_at=datetime(2026, 7, 5, 21, 0, tzinfo=timezone(timedelta(hours=2))),
            observed_at=datetime(2026, 7, 4, 13, 30, tzinfo=timezone(timedelta(hours=2))),
            primary_taker_availability_score=d("0.600000"),
            secondary_taker_readiness_score=d("0.800000"),
            lineup_leak_age_minutes=d("30.000000"),
            set_piece_xg_dependency=d("0.300000"),
            source_disagreement_count=d("0"),
        ),
    )

    payload = module.market_research_soccer_set_piece_taker_availability_digest_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["match_start_at"] == "2026-07-05T19:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T11:30:00+00:00"
    assert payload["rows"][0]["primary_taker_availability_score"] == "0.600000"
    assert payload["rows"][0]["availability_edge_score"] == "0.255000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_number_payload(payload)
    for token in (
        "wallet",
        "broker",
        "order",
        "account",
        "auth",
        "signing",
        "submit",
        "cancel",
        "advice",
        "database",
        "persist",
        "private_key",
        "exchange",
    ):
        assert token not in encoded.lower()


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimal_only() -> None:
    cfg = config()
    item = signal()
    report = build_report(signal(primary_taker_availability_score=d("0.200000")))

    assert is_dataclass(cfg)
    assert is_dataclass(item)
    assert is_dataclass(report.rows[0])
    assert is_dataclass(report.reason_code_counts[0])
    with pytest.raises(FrozenInstanceError):
        cfg.blocked_edge_score_threshold = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.source_disagreement_count = d("1")  # type: ignore[misc]

    with pytest.raises(ValueError, match="blocked_edge_score_threshold must be a Decimal"):
        config(blocked_edge_score_threshold=1)
    with pytest.raises(ValueError, match="source_disagreement_count must be a Decimal"):
        signal(source_disagreement_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="availability_edge_score must be a Decimal"):
        module = api()
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestRow(
            condition_id="condition_manual",
            market_slug="manual-set-piece-edge",
            club="manual",
            opponent="opponent",
            match_ref="manual_match",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=1),
            primary_taker_availability_score=d("0.900000"),
            secondary_taker_readiness_score=d("0.900000"),
            injury_suspension_count=d("0"),
            lineup_leak_age_minutes=d("30.000000"),
            set_piece_xg_dependency=d("0.100000"),
            source_disagreement_count=d("0"),
            availability_edge_score=_DecimalSubclass("0.080000"),
            upstream_reason_codes=(),
            signal_ref="manual_signal",
            digest_status="pass",
            reason_codes=("soccer_set_piece_taker_availability_clear",),
        )

    numeric_field_names = {
        "blocked_edge_score_threshold",
        "watch_edge_score_threshold",
        "primary_taker_unavailable_threshold",
        "primary_taker_watch_threshold",
        "secondary_taker_readiness_threshold",
        "injury_suspension_blocked_count",
        "max_lineup_leak_age_minutes",
        "high_set_piece_xg_dependency_threshold",
        "max_source_disagreement_count",
        "max_input_age_hours",
        "primary_taker_availability_score",
        "secondary_taker_readiness_score",
        "injury_suspension_count",
        "lineup_leak_age_minutes",
        "set_piece_xg_dependency",
        "source_disagreement_count",
        "availability_edge_score",
        "signal_count",
        "pass_signal_count",
        "watch_signal_count",
        "blocked_signal_count",
        "source_disagreement_signal_count",
        "blocked_edge_score_signal_count",
        "watch_edge_score_signal_count",
        "primary_taker_unavailable_signal_count",
        "primary_taker_watch_signal_count",
        "secondary_taker_readiness_gap_signal_count",
        "injury_suspension_signal_count",
        "stale_lineup_leak_signal_count",
        "high_set_piece_xg_dependency_signal_count",
        "upstream_reason_signal_count",
        "max_availability_edge_score",
        "average_availability_edge_score",
        "signal_count",
    }
    for obj in (cfg, item, report, report.rows[0], report.reason_code_counts[0]):
        assert is_dataclass(obj)
        assert obj.__dataclass_params__.frozen
        for field_name, value in asdict(obj).items():
            if field_name in numeric_field_names:
                assert type(value) is Decimal
    for obj in (cfg, item, report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(obj):
            if field.name in numeric_field_names:
                assert type(getattr(obj, field.name)) is Decimal


def test_validation_rejects_unsafe_inputs_subclasses_duplicates_and_stale_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version must be a string"):
        config(config_version=_StringSubclass("test"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observed_at exceeds max_input_age_hours"):
        build_report(signal(observed_at=GENERATED_AT - timedelta(hours=25)))
    with pytest.raises(ValueError, match="match_start_at must not be in the past"):
        build_report(signal(match_start_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="signal_ref contains unsafe source detail"):
        signal(signal_ref="wallet_private_feed")
    with pytest.raises(ValueError, match="upstream_reason_codes must be sorted"):
        signal(upstream_reason_codes=("zeta_reason", "alpha_reason"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(signal(signal_ref="dup_a"), signal(signal_ref="dup_b"))

    report = build_report(
        signal(
            "condition_blocked",
            "liverpool-chelsea-set-piece-edge",
            "liverpool",
            "chelsea",
            "liverpool_chelsea",
            primary_taker_availability_score=d("0.200000"),
            secondary_taker_readiness_score=d("0.300000"),
            injury_suspension_count=d("2"),
            set_piece_xg_dependency=d("0.700000"),
            source_disagreement_count=d("1"),
        ),
        signal(
            "condition_pass",
            "milan-inter-corner-edge",
            "milan",
            "inter",
            "milan_inter",
            match_start_at=BASE_MATCH_START_AT + timedelta(hours=2),
        ),
    )
    with pytest.raises(ValueError, match="recommended_next_step must match digest_status"):
        replace(report, recommended_next_step="continue_report_only_set_piece_review")
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        module.MarketResearchSoccerSetPieceTakerAvailabilityDigestRow(
            condition_id="condition_manual",
            market_slug="manual-set-piece-edge",
            club="manual",
            opponent="opponent",
            match_ref="manual_match",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=1),
            primary_taker_availability_score=d("0.200000"),
            secondary_taker_readiness_score=d("0.900000"),
            injury_suspension_count=d("0"),
            lineup_leak_age_minutes=d("30.000000"),
            set_piece_xg_dependency=d("0.100000"),
            source_disagreement_count=d("0"),
            availability_edge_score=d("0.305000"),
            upstream_reason_codes=(),
            signal_ref="manual_signal",
            digest_status="blocked",
            reason_codes=(
                "soccer_set_piece_taker_availability_primary_taker_unavailable",
                "soccer_set_piece_taker_availability_edge_score_blocked",
            ),
        )


def test_module_exports_are_explicit_and_do_not_expose_live_or_external_io_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text())

    exported = set(module.__all__)
    assert {
        "DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_TAKER_AVAILABILITY_DIGEST_CONFIG_VERSION",
        "MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig",
        "MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal",
        "MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount",
        "MarketResearchSoccerSetPieceTakerAvailabilityDigestRow",
        "MarketResearchSoccerSetPieceTakerAvailabilityDigestReport",
        "build_market_research_soccer_set_piece_taker_availability_digest",
        "market_research_soccer_set_piece_taker_availability_digest_payload",
    } <= exported

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "patch",
        "commit",
        "execute",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "web3",
        "http",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    source = MODULE_PATH.read_text().lower()
    public_text = "\n".join(
        name
        for name in exported
        if not name.startswith("_")
    ).lower()
    for token in (
        "wallet",
        "broker",
        "order",
        "account",
        "auth",
        "signing",
        "live_trading",
        "exchange",
        "network",
        "secret",
        "database",
        "subprocess",
        "socket",
        "psycopg",
        "supabase",
        "private_key",
    ):
        assert token not in public_text
        assert token not in source
