from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_policy_primary_ballot_access_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "presidential-primary-ballot-access-colorado",
    jurisdiction: str = "colorado",
    candidate_name: str = "candidate-alpha",
    office_key: str = "president-primary",
    party_key: str = "democratic",
    filing_status: str = "qualified",
    challenge_count: str | Decimal = "0.000000",
    adverse_ruling_count: str | Decimal = "0.000000",
    appeal_pending_count: str | Decimal = "0.000000",
    days_until_ballot_deadline: str | Decimal = "40.000000",
    evidence_confidence: str | Decimal = "0.840000",
    observed_at: datetime = datetime(2026, 7, 4, 11, 50, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_ballot_notice",),
):
    module = digest()
    return module.PolicyPrimaryBallotAccessObservation(
        source_id=source_id,
        market_slug=market_slug,
        jurisdiction=jurisdiction,
        candidate_name=candidate_name,
        office_key=office_key,
        party_key=party_key,
        filing_status=filing_status,
        challenge_count=(
            challenge_count if isinstance(challenge_count, Decimal) else d(challenge_count)
        ),
        adverse_ruling_count=(
            adverse_ruling_count
            if isinstance(adverse_ruling_count, Decimal)
            else d(adverse_ruling_count)
        ),
        appeal_pending_count=(
            appeal_pending_count
            if isinstance(appeal_pending_count, Decimal)
            else d(appeal_pending_count)
        ),
        days_until_ballot_deadline=(
            days_until_ballot_deadline
            if isinstance(days_until_ballot_deadline, Decimal)
            else d(days_until_ballot_deadline)
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
    return module.build_market_research_policy_primary_ballot_access_digest(
        rows,
        config=cfg or module.PolicyPrimaryBallotAccessDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.PolicyPrimaryBallotAccessDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-policy-primary-ballot-access-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_primary_ballot_access_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.active_challenge_count == d("0.000000")
    assert digest_report.adverse_ruling_row_count == d("0.000000")
    assert digest_report.max_disqualification_risk_score == d("0.000000")
    assert digest_report.average_disqualification_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("primary_ballot_access_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.PolicyPrimaryBallotAccessReasonCodeCount(
            reason_code="primary_ballot_access_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_disqualification_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            market_slug="presidential-primary-ballot-access-colorado",
            filing_status="challenged",
            challenge_count="3.000000",
            adverse_ruling_count="1.000000",
            appeal_pending_count="1.000000",
            days_until_ballot_deadline="2.000000",
            evidence_confidence="0.930000",
            observed_at=datetime(
                2026,
                7,
                4,
                7,
                50,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-watch",
            market_slug="presidential-primary-ballot-access-maine",
            jurisdiction="maine",
            candidate_name="candidate-beta",
            filing_status="pending",
            challenge_count="1.000000",
            appeal_pending_count="1.000000",
            days_until_ballot_deadline="4.000000",
        ),
        observation(
            "source-pass",
            market_slug="presidential-primary-ballot-access-new-hampshire",
            jurisdiction="new-hampshire",
            candidate_name="candidate-gamma",
            filing_status="qualified",
            challenge_count="0.000000",
            adverse_ruling_count="0.000000",
            appeal_pending_count="0.000000",
            days_until_ballot_deadline="40.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_primary_ballot_access_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.active_challenge_count == d("2.000000")
    assert digest_report.adverse_ruling_row_count == d("1.000000")
    assert digest_report.max_disqualification_risk_score == d("1.000000")
    assert digest_report.average_disqualification_risk_score == d("0.508333")
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "presidential-primary-ballot-access-colorado",
        "presidential-primary-ballot-access-maine",
        "presidential-primary-ballot-access-new-hampshire",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.access_status == "blocked"
    assert blocked.disqualification_risk_score == d("1.000000")
    assert blocked.observed_at == datetime(2026, 7, 4, 11, 50, tzinfo=UTC)
    assert blocked.source_age_seconds == d("600.000000")
    assert blocked.reason_codes == (
        "official_ballot_notice",
        "primary_ballot_access_active_challenge",
        "primary_ballot_access_adverse_ruling",
        "primary_ballot_access_appeal_pending",
        "primary_ballot_access_blocked",
        "primary_ballot_access_challenged_status",
        "primary_ballot_access_deadline_imminent",
        "primary_ballot_access_many_challenges",
        "primary_ballot_access_source_fresh",
    )
    assert watched.access_status == "watch"
    assert watched.disqualification_risk_score == d("0.525000")
    assert "primary_ballot_access_watch" in watched.reason_codes
    assert passed.access_status == "pass"
    assert passed.reason_codes == (
        "official_ballot_notice",
        "primary_ballot_access_below_threshold",
        "primary_ballot_access_source_fresh",
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="beta-watch",
        filing_status="pending",
        challenge_count="2.000000",
        days_until_ballot_deadline="4.000000",
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        filing_status="removed",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        filing_status="pending",
        challenge_count="2.000000",
        days_until_ballot_deadline="4.000000",
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
        "official_ballot_notice",
        "primary_ballot_access_active_challenge",
        "primary_ballot_access_blocked",
        "primary_ballot_access_deadline_imminent",
        "primary_ballot_access_many_challenges",
        "primary_ballot_access_pending_status",
        "primary_ballot_access_removed_status",
        "primary_ballot_access_source_fresh",
        "primary_ballot_access_watch",
    )


def test_non_default_thresholds_can_downgrade_moderate_ballot_access_risk() -> None:
    module = digest()
    cfg = module.PolicyPrimaryBallotAccessDigestConfig(
        watch_disqualification_risk_score=d("0.600000"),
        blocked_disqualification_risk_score=d("0.900000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            filing_status="pending",
            challenge_count="1.000000",
            appeal_pending_count="1.000000",
            days_until_ballot_deadline="4.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_primary_ballot_access_screening"
    )
    assert digest_report.rows[0].access_status == "pass"
    assert digest_report.rows[0].disqualification_risk_score == d("0.525000")
    assert "primary_ballot_access_below_threshold" in digest_report.rows[0].reason_codes


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="challenge_count must be a Decimal"):
        observation(challenge_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="days_until_ballot_deadline must be nonnegative"):
        observation(days_until_ballot_deadline="-1.000000")
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 11, 50))
    with pytest.raises(ValueError, match="filing_status must be one of"):
        observation(filing_status="rumored")
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_policy_primary_ballot_access_digest(
            (),
            config=module.PolicyPrimaryBallotAccessDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_disqualification_risk_score"):
        module.PolicyPrimaryBallotAccessDigestConfig(
            watch_disqualification_risk_score=d("0.900000"),
            blocked_disqualification_risk_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            observation(
                "source-future",
                observed_at=datetime(2026, 7, 4, 12, 1, tzinfo=UTC),
            ),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="disqualification_risk_score must match"):
        replace(valid_row, disqualification_risk_score=d("0.999000"))
    with pytest.raises(ValueError, match="access_status must match reason_codes"):
        replace(valid_row, reason_codes=("primary_ballot_access_watch",))

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_reason_counts_and_report() -> None:
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
        module.PolicyPrimaryBallotAccessDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason_code_count paper_only must be True"):
        replace(digest_report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_policy_primary_ballot_access_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["challenge_count"] == "0.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T11:50:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "secret" not in lowered
                assert "token" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.PolicyPrimaryBallotAccessDigestConfig(),
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
        "market_research_policy_primary_ballot_access_digest.py",
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
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
        "auth_token",
        "secret_key",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
