from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_tennis_warmup_withdrawal_risk_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    player: str = "carlos-alcaraz",
    opponent: str = "jannik-sinner",
    tournament: str = "wimbledon",
    market_slug: str = "alcaraz-vs-sinner-match-winner",
    warmup_participation_score: str | Decimal = "0.920000",
    medical_timeout_history_count: str | Decimal = "0.000000",
    travel_fatigue_score: str | Decimal = "0.100000",
    surface_transition_score: str | Decimal = "0.100000",
    source_disagreement_score: str | Decimal = "0.100000",
    match_start_at: datetime = datetime(2026, 7, 4, 18, 0, tzinfo=UTC),
    source_reported_at: datetime = datetime(2026, 7, 4, 14, 45, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = (),
):
    module = digest()
    return module.TennisWarmupWithdrawalRiskObservation(
        source_id=source_id,
        player=player,
        opponent=opponent,
        tournament=tournament,
        market_slug=market_slug,
        warmup_participation_score=(
            warmup_participation_score
            if isinstance(warmup_participation_score, Decimal)
            else d(warmup_participation_score)
        ),
        medical_timeout_history_count=(
            medical_timeout_history_count
            if isinstance(medical_timeout_history_count, Decimal)
            else d(medical_timeout_history_count)
        ),
        travel_fatigue_score=(
            travel_fatigue_score
            if isinstance(travel_fatigue_score, Decimal)
            else d(travel_fatigue_score)
        ),
        surface_transition_score=(
            surface_transition_score
            if isinstance(surface_transition_score, Decimal)
            else d(surface_transition_score)
        ),
        source_disagreement_score=(
            source_disagreement_score
            if isinstance(source_disagreement_score, Decimal)
            else d(source_disagreement_score)
        ),
        match_start_at=match_start_at,
        source_reported_at=source_reported_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_tennis_warmup_withdrawal_risk_digest(
        rows,
        config=cfg or module.TennisWarmupWithdrawalRiskDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.TennisWarmupWithdrawalRiskDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-tennis-warmup-withdrawal-risk-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_tennis_warmup_withdrawal_risk_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.low_warmup_participation_count == d("0.000000")
    assert digest_report.medical_timeout_history_count == d("0.000000")
    assert digest_report.source_quality_gap_count == d("0.000000")
    assert digest_report.max_risk_score == d("0.000000")
    assert digest_report.average_risk_score == d("0.000000")
    assert digest_report.risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("tennis_warmup_withdrawal_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.TennisWarmupWithdrawalRiskReasonCodeCount(
            reason_code="tennis_warmup_withdrawal_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_warmup_withdrawal_risk_blocks_match_event_market() -> None:
    module = digest()

    digest_report = report(
        observation(
            "source-physio",
            market_slug="alcaraz-vs-sinner-match-winner",
            warmup_participation_score="0.100000",
            medical_timeout_history_count="2.000000",
            travel_fatigue_score="0.800000",
            surface_transition_score="0.750000",
            source_disagreement_score="0.800000",
            match_start_at=datetime(2026, 7, 4, 15, 20, tzinfo=UTC),
            source_reported_at=datetime(2026, 7, 4, 13, 30, tzinfo=UTC),
            upstream_reason_codes=("visible-treatment",),
        ),
        observation(
            "source-court",
            player="iga-swiatek",
            opponent="aryna-sabalenka",
            tournament="us-open",
            market_slug="swiatek-vs-sabalenka-match-winner",
            warmup_participation_score="0.400000",
            medical_timeout_history_count="1.000000",
            travel_fatigue_score="0.600000",
            surface_transition_score="0.300000",
            source_disagreement_score="0.200000",
            match_start_at=datetime(2026, 7, 4, 15, 25, tzinfo=UTC),
            source_reported_at=datetime(
                2026,
                7,
                4,
                10,
                50,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation("source-inline"),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_tennis_warmup_withdrawal_risk_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.low_warmup_participation_count == d("2.000000")
    assert digest_report.medical_timeout_history_count == d("2.000000")
    assert digest_report.source_quality_gap_count == d("1.000000")
    assert digest_report.max_risk_score == d("0.800000")
    assert digest_report.average_risk_score == d("0.466000")
    assert digest_report.risk_score == d("0.800000")
    assert digest_report.reason_codes == (
        "tennis_warmup_withdrawal_blocked_risk_present",
        "tennis_warmup_withdrawal_watch_risk_present",
        "tennis_warmup_withdrawal_low_warmup_participation_present",
        "tennis_warmup_withdrawal_medical_timeout_history_present",
        "tennis_warmup_withdrawal_travel_surface_overlap",
        "tennis_warmup_withdrawal_match_start_imminent_present",
        "tennis_warmup_withdrawal_source_quality_gap_present",
        "tennis_warmup_withdrawal_upstream_signal_present",
    )
    assert tuple(item.count for item in digest_report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert tuple(item.row_ratio for item in digest_report.reason_code_counts) == (
        d("0.333333"),
        d("0.333333"),
        d("0.666667"),
        d("0.666667"),
        d("0.333333"),
        d("0.333333"),
        d("0.333333"),
        d("0.333333"),
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "alcaraz-vs-sinner-match-winner",
        "swiatek-vs-sabalenka-match-winner",
        "alcaraz-vs-sinner-match-winner",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.risk_status == "blocked"
    assert blocked.risk_score == d("0.800000")
    assert blocked.source_age_minutes == d("90.000000")
    assert blocked.match_start_proximity_minutes == d("110.000000")
    assert blocked.source_reported_at == datetime(2026, 7, 4, 13, 30, tzinfo=UTC)
    assert blocked.match_start_at == datetime(2026, 7, 4, 15, 20, tzinfo=UTC)
    assert blocked.reason_codes == (
        "tennis_warmup_withdrawal_low_warmup_participation",
        "tennis_warmup_withdrawal_medical_timeout_history",
        "tennis_warmup_withdrawal_travel_fatigue",
        "tennis_warmup_withdrawal_surface_transition",
        "tennis_warmup_withdrawal_stale_source",
        "tennis_warmup_withdrawal_source_disagreement",
        "tennis_warmup_withdrawal_upstream_signal",
        "tennis_warmup_withdrawal_risk_score_blocked",
    )
    assert watched.risk_status == "watch"
    assert watched.source_reported_at == datetime(2026, 7, 4, 14, 50, tzinfo=UTC)
    assert watched.match_start_proximity_minutes == d("35.000000")
    assert watched.reason_codes == (
        "tennis_warmup_withdrawal_low_warmup_participation",
        "tennis_warmup_withdrawal_medical_timeout_history",
        "tennis_warmup_withdrawal_travel_fatigue",
        "tennis_warmup_withdrawal_match_start_imminent",
        "tennis_warmup_withdrawal_risk_score_watch",
    )
    assert passed.risk_status == "pass"
    assert passed.reason_codes == ("tennis_warmup_withdrawal_inline",)

    assert isinstance(blocked.upstream_reason_codes, tuple)
    assert blocked.upstream_reason_codes == ("visible-treatment",)


def test_rows_reasons_and_counts_are_sorted_deterministically() -> None:
    module = digest()
    first = observation(
        "source-watch-b",
        player="beta-player",
        opponent="beta-opponent",
        market_slug="beta-watch",
        warmup_participation_score="0.420000",
        medical_timeout_history_count="1.000000",
        match_start_at=datetime(2026, 7, 4, 15, 50, tzinfo=UTC),
        source_reported_at=datetime(2026, 7, 4, 14, 30, tzinfo=UTC),
    )
    second = observation(
        "source-blocked",
        player="alpha-player",
        opponent="alpha-opponent",
        market_slug="alpha-blocked",
        warmup_participation_score="0.120000",
        medical_timeout_history_count="2.000000",
        source_disagreement_score="0.900000",
        match_start_at=datetime(2026, 7, 4, 15, 15, tzinfo=UTC),
        source_reported_at=datetime(2026, 7, 4, 14, 45, tzinfo=UTC),
    )
    third = observation(
        "source-watch-a",
        player="alpha-watch",
        opponent="alpha-opponent",
        market_slug="alpha-watch",
        warmup_participation_score="0.410000",
        medical_timeout_history_count="1.000000",
        match_start_at=datetime(2026, 7, 4, 15, 45, tzinfo=UTC),
        source_reported_at=datetime(2026, 7, 4, 14, 30, tzinfo=UTC),
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(
            reason_code
            for reason_code in module.ROW_REASON_CODES
            if reason_code in row.reason_codes
        )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "tennis_warmup_withdrawal_blocked_risk_present",
        "tennis_warmup_withdrawal_watch_risk_present",
        "tennis_warmup_withdrawal_low_warmup_participation_present",
        "tennis_warmup_withdrawal_medical_timeout_history_present",
        "tennis_warmup_withdrawal_match_start_imminent_present",
        "tennis_warmup_withdrawal_source_quality_gap_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_warmup_risk() -> None:
    module = digest()
    cfg = module.TennisWarmupWithdrawalRiskDigestConfig(
        watch_risk_score_threshold=d("0.950000"),
        blocked_risk_score_threshold=d("0.990000"),
        watch_warmup_participation_score=d("0.200000"),
        blocked_warmup_participation_score=d("0.050000"),
        watch_medical_timeout_history_count=d("3.000000"),
        blocked_medical_timeout_history_count=d("5.000000"),
        travel_fatigue_watch_score=d("0.950000"),
        surface_transition_watch_score=d("0.950000"),
        source_disagreement_watch_score=d("0.950000"),
        source_disagreement_blocked_score=d("0.990000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            warmup_participation_score="0.600000",
            medical_timeout_history_count="1.000000",
            travel_fatigue_score="0.900000",
            surface_transition_score="0.900000",
            source_disagreement_score="0.900000",
            match_start_at=datetime(2026, 7, 4, 18, 0, tzinfo=UTC),
            source_reported_at=datetime(2026, 7, 4, 14, 55, tzinfo=UTC),
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_tennis_warmup_withdrawal_risk_screening"
    )
    assert digest_report.rows[0].risk_status == "pass"
    assert digest_report.rows[0].reason_codes == ("tennis_warmup_withdrawal_inline",)
    assert digest_report.risk_score == d("0.510000")
    assert digest_report.reason_codes == ("tennis_warmup_withdrawal_digest_clear",)


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="warmup_participation_score must be a Decimal"):
        observation(warmup_participation_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="warmup_participation_score must be between zero and one"):
        observation(warmup_participation_score="1.100000")
    with pytest.raises(ValueError, match="source_reported_at must be timezone-aware"):
        observation(source_reported_at=datetime(2026, 7, 4, 14, 45))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_tennis_warmup_withdrawal_risk_digest(
            (),
            config=module.TennisWarmupWithdrawalRiskDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_risk_score_threshold"):
        module.TennisWarmupWithdrawalRiskDigestConfig(
            watch_risk_score_threshold=d("0.900000"),
            blocked_risk_score_threshold=d("0.800000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="risk_score must match risk inputs"):
        replace(valid_row, risk_score=d("0.999999"))
    with pytest.raises(ValueError, match="reason_codes must match risk_status"):
        replace(
            valid_row,
            reason_codes=(
                "tennis_warmup_withdrawal_inline",
                "tennis_warmup_withdrawal_low_warmup_participation",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_counts_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in digest_report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.TennisWarmupWithdrawalRiskDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count report_only must be True"):
        replace(digest_report.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_six_decimal_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_tennis_warmup_withdrawal_risk_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["risk_score"] == "0.058000"
    assert payload["rows"][0]["warmup_participation_score"] == "0.920000"
    assert payload["rows"][0]["risk_score"] == "0.058000"
    assert payload["rows"][0]["source_reported_at"] == "2026-07-04T14:45:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "order" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.TennisWarmupWithdrawalRiskDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/market_research_tennis_warmup_withdrawal_risk_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
