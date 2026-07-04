from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_policy_congress_whip_count_break_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "policy-congress-whip-break-house-budget",
    chamber: str = "house",
    vote_key: str = "fy2027-budget-resolution",
    caucus_key: str = "majority-caucus",
    expected_outcome: str = "passage_expected",
    required_vote_count: str | Decimal = "218.000000",
    committed_support_count: str | Decimal = "225.000000",
    committed_opposition_count: str | Decimal = "210.000000",
    undecided_count: str | Decimal = "0.000000",
    public_break_count: str | Decimal = "0.000000",
    observed_at: datetime = datetime(2026, 7, 4, 15, 50, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_congress_whip_count_feed",),
):
    module = digest()
    return module.PolicyCongressWhipCountBreakObservation(
        source_id=source_id,
        market_slug=market_slug,
        chamber=chamber,
        vote_key=vote_key,
        caucus_key=caucus_key,
        expected_outcome=expected_outcome,
        required_vote_count=(
            required_vote_count
            if isinstance(required_vote_count, Decimal)
            else d(required_vote_count)
        ),
        committed_support_count=(
            committed_support_count
            if isinstance(committed_support_count, Decimal)
            else d(committed_support_count)
        ),
        committed_opposition_count=(
            committed_opposition_count
            if isinstance(committed_opposition_count, Decimal)
            else d(committed_opposition_count)
        ),
        undecided_count=(
            undecided_count if isinstance(undecided_count, Decimal) else d(undecided_count)
        ),
        public_break_count=(
            public_break_count
            if isinstance(public_break_count, Decimal)
            else d(public_break_count)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_policy_congress_whip_count_break_digest(
        rows,
        config=cfg or module.PolicyCongressWhipCountBreakDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.PolicyCongressWhipCountBreakDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-policy-congress-whip-count-break-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_congress_whip_count_break_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.support_gap_row_count == d("0.000000")
    assert digest_report.public_break_row_count == d("0.000000")
    assert digest_report.high_undecided_row_count == d("0.000000")
    assert digest_report.max_support_gap_count == d("0.000000")
    assert digest_report.max_public_break_count == d("0.000000")
    assert digest_report.average_whip_break_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("congress_whip_count_break_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.PolicyCongressWhipCountBreakReasonCodeCount(
            reason_code="congress_whip_count_break_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_support_gap_public_breaks_or_undecideds_block_congress_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            market_slug="policy-congress-whip-break-house-budget",
            chamber="house",
            required_vote_count="218.000000",
            committed_support_count="214.000000",
            committed_opposition_count="219.000000",
            public_break_count="6.000000",
            undecided_count="24.000000",
            observed_at=datetime(
                2026,
                7,
                4,
                11,
                55,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-watch",
            market_slug="policy-congress-whip-break-senate-nomination",
            chamber="senate",
            vote_key="cabinet-confirmation",
            required_vote_count="51.000000",
            committed_support_count="54.000000",
            committed_opposition_count="46.000000",
            public_break_count="2.000000",
            undecided_count="12.000000",
        ),
        observation(
            "source-pass",
            market_slug="policy-congress-whip-break-house-rules",
            chamber="house",
            vote_key="rules-package",
            required_vote_count="218.000000",
            committed_support_count="225.000000",
            committed_opposition_count="205.000000",
            public_break_count="0.000000",
            undecided_count="0.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_congress_whip_count_break_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.support_gap_row_count == d("1.000000")
    assert digest_report.public_break_row_count == d("2.000000")
    assert digest_report.high_undecided_row_count == d("2.000000")
    assert digest_report.max_support_gap_count == d("4.000000")
    assert digest_report.max_public_break_count == d("6.000000")
    assert digest_report.average_whip_break_risk_score == d("0.533333")
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "policy-congress-whip-break-house-budget",
        "policy-congress-whip-break-senate-nomination",
        "policy-congress-whip-break-house-rules",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.whip_break_status == "blocked"
    assert blocked.support_gap_count == d("4.000000")
    assert blocked.support_surplus_count == d("0.000000")
    assert blocked.whip_break_risk_score == d("1.000000")
    assert blocked.observed_at == datetime(2026, 7, 4, 15, 55, tzinfo=UTC)
    assert blocked.source_age_seconds == d("300.000000")
    assert blocked.reason_codes == (
        "congress_whip_count_break_blocked",
        "congress_whip_count_public_break_blocked",
        "congress_whip_count_source_fresh",
        "congress_whip_count_support_gap_blocked",
        "congress_whip_count_undecided_blocked",
        "official_congress_whip_count_feed",
    )
    assert watched.whip_break_status == "watch"
    assert watched.support_gap_count == d("0.000000")
    assert watched.support_surplus_count == d("3.000000")
    assert watched.whip_break_risk_score == d("0.600000")
    assert watched.reason_codes == (
        "congress_whip_count_break_watch",
        "congress_whip_count_margin_watch",
        "congress_whip_count_public_break_watch",
        "congress_whip_count_source_fresh",
        "congress_whip_count_undecided_watch",
        "official_congress_whip_count_feed",
    )
    assert passed.whip_break_status == "pass"
    assert passed.reason_codes == (
        "congress_whip_count_break_below_threshold",
        "congress_whip_count_source_fresh",
        "official_congress_whip_count_feed",
    )


def test_stale_source_blocks_even_when_whip_metrics_are_below_threshold() -> None:
    digest_report = report(
        observation(
            "source-stale",
            observed_at=datetime(2026, 7, 3, 15, 59, 59, tzinfo=UTC),
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.stale_source_count == d("1.000000")
    assert digest_report.rows[0].whip_break_status == "blocked"
    assert digest_report.rows[0].source_age_seconds == d("86401.000000")
    assert "congress_whip_count_source_stale" in digest_report.rows[0].reason_codes


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="beta-watch",
        required_vote_count="218.000000",
        committed_support_count="222.000000",
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        required_vote_count="218.000000",
        committed_support_count="217.000000",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        required_vote_count="218.000000",
        committed_support_count="222.000000",
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
        "congress_whip_count_break_blocked",
        "congress_whip_count_break_watch",
        "congress_whip_count_margin_watch",
        "congress_whip_count_source_fresh",
        "congress_whip_count_support_gap_blocked",
        "official_congress_whip_count_feed",
    )


def test_non_default_thresholds_can_downgrade_moderate_whip_break_risk() -> None:
    module = digest()
    cfg = module.PolicyCongressWhipCountBreakDigestConfig(
        watch_margin_votes=d("2.000000"),
        watch_public_break_count=d("4.000000"),
        blocked_public_break_count=d("10.000000"),
        watch_undecided_count=d("20.000000"),
        blocked_undecided_count=d("50.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            required_vote_count="218.000000",
            committed_support_count="221.000000",
            public_break_count="2.000000",
            undecided_count="12.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_congress_whip_count_break_screening"
    )
    assert digest_report.rows[0].whip_break_status == "pass"
    assert digest_report.rows[0].whip_break_risk_score == d("0.240000")
    assert digest_report.rows[0].reason_codes == (
        "congress_whip_count_break_below_threshold",
        "congress_whip_count_source_fresh",
        "official_congress_whip_count_feed",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="committed_support_count must be a Decimal"):
        observation(committed_support_count=_DecimalSubclass("225.000000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 15, 50))
    with pytest.raises(ValueError, match="chamber must be supported"):
        observation(chamber="committee")
    with pytest.raises(ValueError, match="unsafe public text"):
        observation(market_slug="wallet-risk")
    with pytest.raises(ValueError, match="unsafe public text"):
        observation(upstream_reason_codes=("auth_token_leak",))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_policy_congress_whip_count_break_digest(
            (),
            config=module.PolicyCongressWhipCountBreakDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_public_break_count"):
        module.PolicyCongressWhipCountBreakDigestConfig(
            watch_public_break_count=d("10.000000"),
            blocked_public_break_count=d("5.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            observation(
                "source-future",
                observed_at=datetime(2026, 7, 4, 16, 1, tzinfo=UTC),
            ),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="support_gap_count must match"):
        replace(valid_row, support_gap_count=d("99.000000"))
    with pytest.raises(ValueError, match="whip_break_status must match reason_codes"):
        replace(valid_row, reason_codes=("congress_whip_count_break_watch",))

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
        module.PolicyCongressWhipCountBreakDigestConfig(paper_only=False)
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

    payload = module.market_research_policy_congress_whip_count_break_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["required_vote_count"] == "218.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T15:50:00+00:00"

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
        module.PolicyCongressWhipCountBreakDigestConfig(),
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
        "market_research_policy_congress_whip_count_break_digest.py",
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
        "fast_mode",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
