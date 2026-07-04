from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 13, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_policy_pollster_methodology_shift_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "us-senate-alpha-dem-wins",
    pollster_id: str = "pollster-alpha",
    contest_key: str = "us-senate-alpha",
    methodology_family: str = "mixed-mode",
    sample_mode_shift_share: str | Decimal = "0.050000",
    weighting_change_count: str | Decimal = "0.000000",
    likely_voter_screen_change: bool = False,
    days_until_event: str | Decimal = "60.000000",
    evidence_confidence: str | Decimal = "0.800000",
    observed_at: datetime = datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = (),
):
    module = digest()
    return module.PolicyPollsterMethodologyShiftObservation(
        source_id=source_id,
        market_slug=market_slug,
        pollster_id=pollster_id,
        contest_key=contest_key,
        methodology_family=methodology_family,
        sample_mode_shift_share=(
            sample_mode_shift_share
            if isinstance(sample_mode_shift_share, Decimal)
            else d(sample_mode_shift_share)
        ),
        weighting_change_count=(
            weighting_change_count
            if isinstance(weighting_change_count, Decimal)
            else d(weighting_change_count)
        ),
        likely_voter_screen_change=likely_voter_screen_change,
        days_until_event=(
            days_until_event
            if isinstance(days_until_event, Decimal)
            else d(days_until_event)
        ),
        evidence_confidence=(
            evidence_confidence
            if isinstance(evidence_confidence, Decimal)
            else d(evidence_confidence)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_policy_pollster_methodology_shift_digest(
        rows,
        config=cfg or module.PolicyPollsterMethodologyShiftDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.PolicyPollsterMethodologyShiftDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-policy-pollster-methodology-shift-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_pollster_methodology_shift_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.sample_mode_shift_row_count == d("0.000000")
    assert digest_report.weighting_change_row_count == d("0.000000")
    assert digest_report.likely_voter_screen_change_count == d("0.000000")
    assert digest_report.near_event_count == d("0.000000")
    assert digest_report.max_methodology_shift_risk_score == d("0.000000")
    assert digest_report.average_methodology_shift_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "pollster_methodology_shift_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.PolicyPollsterMethodologyShiftReasonCodeCount(
            reason_code="pollster_methodology_shift_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_methodology_shift_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "source-high",
            market_slug="us-senate-alpha-dem-wins",
            pollster_id="pollster-alpha",
            sample_mode_shift_share="0.600000",
            weighting_change_count="2.000000",
            likely_voter_screen_change=True,
            days_until_event="7.000000",
            evidence_confidence="0.920000",
        ),
        observation(
            "source-watch",
            market_slug="us-president-beta-dem-wins",
            pollster_id="pollster-beta",
            contest_key="us-president-beta",
            sample_mode_shift_share="0.300000",
            weighting_change_count="1.000000",
            days_until_event="30.000000",
            observed_at=datetime(
                2026,
                7,
                3,
                8,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-pass",
            market_slug="us-house-gamma-dem-wins",
            pollster_id="pollster-gamma",
            contest_key="us-house-gamma",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_pollster_methodology_shift_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.sample_mode_shift_row_count == d("2.000000")
    assert digest_report.weighting_change_row_count == d("2.000000")
    assert digest_report.likely_voter_screen_change_count == d("1.000000")
    assert digest_report.near_event_count == d("1.000000")
    assert digest_report.max_methodology_shift_risk_score == d("1.000000")
    assert digest_report.average_methodology_shift_risk_score == d("0.471667")
    assert digest_report.reason_codes == (
        "pollster_methodology_shift_below_threshold",
        "pollster_methodology_shift_blocked",
        "pollster_methodology_shift_likely_voter_screen_changed",
        "pollster_methodology_shift_many_weighting_changes",
        "pollster_methodology_shift_near_event",
        "pollster_methodology_shift_sample_mode_high",
        "pollster_methodology_shift_sample_mode_material",
        "pollster_methodology_shift_source_fresh",
        "pollster_methodology_shift_watch",
        "pollster_methodology_shift_weighting_changed",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "us-senate-alpha-dem-wins",
        "us-president-beta-dem-wins",
        "us-house-gamma-dem-wins",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.shift_status == "blocked"
    assert blocked.methodology_shift_risk_score == d("1.000000")
    assert blocked.source_age_seconds == d("5400.000000")
    assert blocked.observed_at == datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "pollster_methodology_shift_blocked",
        "pollster_methodology_shift_likely_voter_screen_changed",
        "pollster_methodology_shift_many_weighting_changes",
        "pollster_methodology_shift_near_event",
        "pollster_methodology_shift_sample_mode_high",
        "pollster_methodology_shift_sample_mode_material",
        "pollster_methodology_shift_source_fresh",
        "pollster_methodology_shift_weighting_changed",
    )
    assert blocked.capped_confidence == d("0.920000")
    assert watch.shift_status == "watch"
    assert watch.methodology_shift_risk_score == d("0.370000")
    assert watch.source_age_seconds == d("2700.000000")
    assert watch.reason_codes == (
        "pollster_methodology_shift_sample_mode_material",
        "pollster_methodology_shift_source_fresh",
        "pollster_methodology_shift_watch",
        "pollster_methodology_shift_weighting_changed",
    )
    assert passed.shift_status == "pass"
    assert passed.methodology_shift_risk_score == d("0.045000")
    assert passed.confidence_cap == d("0.650000")
    assert passed.capped_confidence == d("0.650000")
    assert passed.reason_codes == (
        "pollster_methodology_shift_below_threshold",
        "pollster_methodology_shift_source_fresh",
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="beta-watch",
        sample_mode_shift_share="0.300000",
        weighting_change_count="1.000000",
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        sample_mode_shift_share="0.600000",
        weighting_change_count="2.000000",
        likely_voter_screen_change=True,
        days_until_event="7.000000",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        sample_mode_shift_share="0.300000",
        weighting_change_count="1.000000",
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
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        forward.reason_codes
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="sample_mode_shift_share must be a Decimal"):
        observation(sample_mode_shift_share=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="sample_mode_shift_share must be between 0 and 1"):
        observation(sample_mode_shift_share="1.100000")
    with pytest.raises(ValueError, match="likely_voter_screen_change must be a bool"):
        observation(likely_voter_screen_change=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_policy_pollster_methodology_shift_digest(
            (),
            config=module.PolicyPollsterMethodologyShiftDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.build_market_research_policy_pollster_methodology_shift_digest(
            (observation("source-future"),),
            config=module.PolicyPollsterMethodologyShiftDigestConfig(),
            generated_at=datetime(2026, 7, 3, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="material_sample_mode_shift_share must not exceed high_sample_mode_shift_share",
    ):
        module.PolicyPollsterMethodologyShiftDigestConfig(
            material_sample_mode_shift_share=d("0.700000"),
            high_sample_mode_shift_share=d("0.500000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(
        ValueError,
        match="methodology_shift_risk_score must match row factors",
    ):
        replace(valid_row, methodology_shift_risk_score=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match row factors"):
        replace(
            valid_row,
            reason_codes=(
                "pollster_methodology_shift_below_threshold",
                "pollster_methodology_shift_sample_mode_material",
                "pollster_methodology_shift_source_fresh",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_and_report() -> None:
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
        module.PolicyPollsterMethodologyShiftDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_non_default_thresholds_can_downgrade_moderate_shift_risk() -> None:
    module = digest()
    cfg = module.PolicyPollsterMethodologyShiftDigestConfig(
        watch_methodology_shift_risk_score=d("0.500000"),
        blocked_methodology_shift_risk_score=d("0.900000"),
        material_sample_mode_shift_share=d("0.400000"),
        high_sample_mode_shift_share=d("0.750000"),
        material_weighting_change_count=d("2.000000"),
        high_weighting_change_count=d("4.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            sample_mode_shift_share="0.300000",
            weighting_change_count="1.000000",
            days_until_event="30.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_pollster_methodology_shift_screening"
    )
    assert digest_report.rows[0].shift_status == "pass"
    assert digest_report.rows[0].methodology_shift_risk_score == d("0.230000")
    assert digest_report.rows[0].reason_codes == (
        "pollster_methodology_shift_below_threshold",
        "pollster_methodology_shift_source_fresh",
    )
    assert digest_report.sample_mode_shift_row_count == d("0.000000")
    assert digest_report.weighting_change_row_count == d("0.000000")


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_policy_pollster_methodology_shift_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["sample_mode_shift_share"] == "0.050000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T12:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, Decimal | datetime | float)

    walk_payload(payload)

    for public_record in (
        module.PolicyPollsterMethodologyShiftDigestConfig(),
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
        "src/polymarket_alpha_lab/"
        "market_research_policy_pollster_methodology_shift_digest.py",
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
        "sqlite",
        "pathlib",
        "os",
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
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
