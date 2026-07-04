from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_policy_campaign_finance_filing_lag_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "policy-campaign-finance-reporting-california",
    jurisdiction: str = "california",
    committee_id: str = "committee-alpha",
    filing_type: str = "late_contribution",
    expected_filing_count: str | Decimal = "1.000000",
    received_filing_count: str | Decimal = "1.000000",
    filing_lag_days: str | Decimal = "1.000000",
    largest_late_filing_amount_usd: str | Decimal = "10000.000000",
    amendment_count: str | Decimal = "0.000000",
    observed_at: datetime = datetime(2026, 7, 4, 15, 50, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_campaign_finance_feed",),
):
    module = digest()
    return module.PolicyCampaignFinanceFilingLagObservation(
        source_id=source_id,
        market_slug=market_slug,
        jurisdiction=jurisdiction,
        committee_id=committee_id,
        filing_type=filing_type,
        expected_filing_count=(
            expected_filing_count
            if isinstance(expected_filing_count, Decimal)
            else d(expected_filing_count)
        ),
        received_filing_count=(
            received_filing_count
            if isinstance(received_filing_count, Decimal)
            else d(received_filing_count)
        ),
        filing_lag_days=(
            filing_lag_days if isinstance(filing_lag_days, Decimal) else d(filing_lag_days)
        ),
        largest_late_filing_amount_usd=(
            largest_late_filing_amount_usd
            if isinstance(largest_late_filing_amount_usd, Decimal)
            else d(largest_late_filing_amount_usd)
        ),
        amendment_count=(
            amendment_count if isinstance(amendment_count, Decimal) else d(amendment_count)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_policy_campaign_finance_filing_lag_digest(
        rows,
        config=cfg or module.PolicyCampaignFinanceFilingLagDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.PolicyCampaignFinanceFilingLagDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-policy-campaign-finance-filing-lag-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_campaign_finance_filing_lag_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.missing_filing_row_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.amendment_burst_count == d("0.000000")
    assert digest_report.large_late_filing_count == d("0.000000")
    assert digest_report.max_filing_lag_days == d("0.000000")
    assert digest_report.max_late_filing_amount_usd == d("0.000000")
    assert digest_report.average_filing_lag_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("campaign_finance_filing_lag_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.PolicyCampaignFinanceFilingLagReasonCodeCount(
            reason_code="campaign_finance_filing_lag_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_late_large_amended_or_missing_finance_filings_block_policy_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            market_slug="policy-campaign-finance-reporting-arizona",
            jurisdiction="arizona",
            expected_filing_count="2.000000",
            received_filing_count="1.000000",
            filing_lag_days="9.000000",
            largest_late_filing_amount_usd="1500000.000000",
            amendment_count="5.000000",
            observed_at=datetime(
                2026,
                7,
                4,
                11,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-watch",
            market_slug="policy-campaign-finance-reporting-michigan",
            jurisdiction="michigan",
            filing_lag_days="4.000000",
            largest_late_filing_amount_usd="350000.000000",
            amendment_count="2.000000",
        ),
        observation(
            "source-pass",
            market_slug="policy-campaign-finance-reporting-nevada",
            jurisdiction="nevada",
            filing_lag_days="1.000000",
            largest_late_filing_amount_usd="10000.000000",
            amendment_count="0.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_campaign_finance_filing_lag_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.missing_filing_row_count == d("1.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.amendment_burst_count == d("2.000000")
    assert digest_report.large_late_filing_count == d("2.000000")
    assert digest_report.max_filing_lag_days == d("9.000000")
    assert digest_report.max_late_filing_amount_usd == d("1500000.000000")
    assert digest_report.average_filing_lag_risk_score == d("0.571429")
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "policy-campaign-finance-reporting-arizona",
        "policy-campaign-finance-reporting-michigan",
        "policy-campaign-finance-reporting-nevada",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.filing_lag_status == "blocked"
    assert blocked.missing_filing_count == d("1.000000")
    assert blocked.filing_lag_risk_score == d("1.000000")
    assert blocked.observed_at == datetime(2026, 7, 4, 15, 45, tzinfo=UTC)
    assert blocked.source_age_seconds == d("900.000000")
    assert blocked.reason_codes == (
        "campaign_finance_filing_amendment_burst_blocked",
        "campaign_finance_filing_blocked",
        "campaign_finance_filing_large_late_amount_blocked",
        "campaign_finance_filing_late_blocked",
        "campaign_finance_filing_missing_expected_report",
        "campaign_finance_filing_source_fresh",
        "official_campaign_finance_feed",
    )
    assert watched.filing_lag_status == "watch"
    assert watched.filing_lag_risk_score == d("0.571429")
    assert watched.reason_codes == (
        "campaign_finance_filing_amendment_burst_watch",
        "campaign_finance_filing_large_late_amount_watch",
        "campaign_finance_filing_late_watch",
        "campaign_finance_filing_source_fresh",
        "campaign_finance_filing_watch",
        "official_campaign_finance_feed",
    )
    assert passed.filing_lag_status == "pass"
    assert passed.reason_codes == (
        "campaign_finance_filing_below_threshold",
        "campaign_finance_filing_source_fresh",
        "official_campaign_finance_feed",
    )


def test_stale_source_blocks_even_when_finance_metrics_are_below_threshold() -> None:
    digest_report = report(
        observation(
            "source-stale",
            observed_at=datetime(2026, 7, 3, 15, 59, 59, tzinfo=UTC),
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.stale_source_count == d("1.000000")
    assert digest_report.rows[0].filing_lag_status == "blocked"
    assert digest_report.rows[0].source_age_seconds == d("86401.000000")
    assert "campaign_finance_filing_source_stale" in digest_report.rows[0].reason_codes


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="beta-watch",
        filing_lag_days="4.000000",
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        largest_late_filing_amount_usd="1000000.000000",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        filing_lag_days="4.000000",
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
        "campaign_finance_filing_blocked",
        "campaign_finance_filing_large_late_amount_blocked",
        "campaign_finance_filing_late_watch",
        "campaign_finance_filing_source_fresh",
        "campaign_finance_filing_watch",
        "official_campaign_finance_feed",
    )


def test_non_default_thresholds_can_downgrade_moderate_filing_lag_risk() -> None:
    module = digest()
    cfg = module.PolicyCampaignFinanceFilingLagDigestConfig(
        watch_lag_days=d("5.000000"),
        blocked_lag_days=d("10.000000"),
        watch_late_filing_amount_usd=d("500000.000000"),
        blocked_late_filing_amount_usd=d("2000000.000000"),
        watch_amendment_count=d("3.000000"),
        blocked_amendment_count=d("6.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            filing_lag_days="4.000000",
            largest_late_filing_amount_usd="350000.000000",
            amendment_count="2.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_campaign_finance_filing_lag_screening"
    )
    assert digest_report.rows[0].filing_lag_status == "pass"
    assert digest_report.rows[0].filing_lag_risk_score == d("0.400000")
    assert digest_report.rows[0].reason_codes == (
        "campaign_finance_filing_below_threshold",
        "campaign_finance_filing_source_fresh",
        "official_campaign_finance_feed",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="filing_lag_days must be a Decimal"):
        observation(filing_lag_days=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="received_filing_count must not exceed"):
        observation(
            expected_filing_count="1.000000",
            received_filing_count="2.000000",
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 15, 50))
    with pytest.raises(ValueError, match="filing_type must be supported"):
        observation(filing_type="rumor")
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_policy_campaign_finance_filing_lag_digest(
            (),
            config=module.PolicyCampaignFinanceFilingLagDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_lag_days"):
        module.PolicyCampaignFinanceFilingLagDigestConfig(
            watch_lag_days=d("10.000000"),
            blocked_lag_days=d("7.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            observation(
                "source-future",
                observed_at=datetime(2026, 7, 4, 16, 1, tzinfo=UTC),
            ),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="missing_filing_count must match"):
        replace(valid_row, missing_filing_count=d("99.000000"))
    with pytest.raises(ValueError, match="filing_lag_status must match reason_codes"):
        replace(valid_row, reason_codes=("campaign_finance_filing_watch",))

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
        module.PolicyCampaignFinanceFilingLagDigestConfig(paper_only=False)
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

    payload = module.market_research_policy_campaign_finance_filing_lag_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["largest_late_filing_amount_usd"] == "10000.000000"
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
        module.PolicyCampaignFinanceFilingLagDigestConfig(),
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
        "market_research_policy_campaign_finance_filing_lag_digest.py",
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
