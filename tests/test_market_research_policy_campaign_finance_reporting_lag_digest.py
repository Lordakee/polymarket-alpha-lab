from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType

import pytest

from polymarket_alpha_lab.market_research_policy_campaign_finance_reporting_lag_digest import (
    DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION,
    MarketResearchPolicyCampaignFinanceReportingLagDigestConfig,
    MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow,
    MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
    MarketResearchPolicyCampaignFinanceReportingLagDigestReport,
    MarketResearchPolicyCampaignFinanceReportingLagDigestRow,
    build_market_research_policy_campaign_finance_reporting_lag_digest,
    market_research_policy_campaign_finance_reporting_lag_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


_UNSET = object()


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchPolicyCampaignFinanceReportingLagDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION
        ),
        "max_ready_reporting_lag_seconds": d("86400.000000"),
        "max_watch_reporting_lag_seconds": d("259200.000000"),
        "min_public_source_count": d("2.000000"),
        "materiality_watch_threshold": d("0.150000"),
        "materiality_block_threshold": d("0.350000"),
    }
    values.update(overrides)
    return MarketResearchPolicyCampaignFinanceReportingLagDigestConfig(**values)


def filing_row(
    research_id: str = "research.campaign_finance.ready",
    *,
    condition_id: str = "condition_campaign_finance_ready",
    committee_id: str = "committee_alpha",
    filing_type: str = "quarterly_report",
    reporting_period_end_at: datetime | None = None,
    filing_due_at: datetime | None = None,
    filing_published_at: datetime | None | object = _UNSET,
    source_observed_at: datetime | None = None,
    public_source_reference: str = "public-fec-campaign-finance-report",
    public_source_count: Decimal = d("3.000000"),
    disclosure_amount_usd: Decimal = d("125000.000000"),
    estimated_probability_impact: Decimal = d("0.040000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow:
    due_at = filing_due_at or GENERATED_AT - timedelta(days=3)
    return MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow(
        research_id=research_id,
        condition_id=condition_id,
        committee_id=committee_id,
        filing_type=filing_type,
        reporting_period_end_at=(
            reporting_period_end_at or GENERATED_AT - timedelta(days=33)
        ),
        filing_due_at=due_at,
        filing_published_at=(
            due_at + timedelta(hours=12)
            if filing_published_at is _UNSET
            else filing_published_at
        ),
        source_observed_at=source_observed_at or GENERATED_AT - timedelta(hours=6),
        public_source_reference=public_source_reference,
        public_source_count=public_source_count,
        disclosure_amount_usd=disclosure_amount_usd,
        estimated_probability_impact=estimated_probability_impact,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow, ...],
    *,
    cfg: MarketResearchPolicyCampaignFinanceReportingLagDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPolicyCampaignFinanceReportingLagDigestReport:
    return build_market_research_policy_campaign_finance_reporting_lag_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload(value: object) -> tuple[object, ...]:
    if isinstance(value, MappingProxyType):
        return tuple(item for child in value.values() for item in walk_payload(child))
    if isinstance(value, tuple):
        return tuple(item for child in value for item in walk_payload(child))
    return (value,)


def assert_public_numerics_are_decimal(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if isinstance(field_value, bool):
                continue
            if field.name.endswith(
                ("count", "ratio", "seconds", "usd", "impact"),
            ):
                assert type(field_value) is Decimal, field.name
                assert field_value.as_tuple().exponent == -6, field.name
            assert_public_numerics_are_decimal(field_value)
    elif isinstance(value, tuple):
        for item in value:
            assert_public_numerics_are_decimal(item)


def test_campaign_finance_reporting_lag_digest_reduces_and_ranks_rows() -> None:
    summary = report(
        (
            filing_row(
                "research.campaign_finance.ready",
                condition_id="condition_campaign_finance_ready",
                committee_id="committee_ready",
                filing_due_at=GENERATED_AT - timedelta(days=2),
                filing_published_at=GENERATED_AT - timedelta(days=1, hours=18),
                source_observed_at=GENERATED_AT.astimezone(
                    timezone(timedelta(hours=-4)),
                )
                - timedelta(hours=5),
                public_source_reference="public-fec-campaign-finance-ready-report",
                disclosure_amount_usd=d("250000.000000"),
                estimated_probability_impact=d("0.050000"),
            ),
            filing_row(
                "research.campaign_finance.lagged",
                condition_id="condition_campaign_finance_lagged",
                committee_id="committee_lagged",
                filing_type="monthly_report",
                filing_due_at=GENERATED_AT - timedelta(days=7),
                filing_published_at=GENERATED_AT - timedelta(days=2),
                source_observed_at=GENERATED_AT - timedelta(hours=4),
                public_source_reference=(
                    "https://www.fec.gov/data/committee/private-source-token"
                ),
                public_source_count=d("1.000000"),
                disclosure_amount_usd=d("1000000.000000"),
                estimated_probability_impact=d("0.420000"),
            ),
            filing_row(
                "research.campaign_finance.missing",
                condition_id="condition_campaign_finance_missing",
                committee_id="committee_missing",
                filing_type="pre_primary_report",
                filing_due_at=GENERATED_AT - timedelta(days=5),
                filing_published_at=None,
                source_observed_at=GENERATED_AT - timedelta(hours=3),
                public_source_reference="public-fec-campaign-finance-missing-report",
                public_source_count=d("2.000000"),
                disclosure_amount_usd=d("0.000000"),
                estimated_probability_impact=d("0.200000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchPolicyCampaignFinanceReportingLagDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_policy_campaign_finance_reporting_lag_digest"
    )
    assert summary.filing_count == d("3.000000")
    assert summary.ready_filing_count == d("1.000000")
    assert summary.watch_filing_count == d("0.000000")
    assert summary.blocked_filing_count == d("2.000000")
    assert summary.missing_filing_count == d("1.000000")
    assert summary.lagged_filing_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.material_filing_count == d("2.000000")
    assert summary.average_reporting_lag_seconds == d("295200.000000")
    assert summary.max_reporting_lag_seconds == d("432000.000000")
    assert summary.average_probability_impact == d("0.223333")
    assert summary.average_public_source_count == d("2.000000")
    assert tuple(row.research_id for row in summary.rows) == (
        "research.campaign_finance.lagged",
        "research.campaign_finance.missing",
        "research.campaign_finance.ready",
    )

    lagged = summary.rows[0]
    assert lagged.lag_status == "blocked"
    assert lagged.reporting_lag_seconds == d("432000.000000")
    assert lagged.source_age_seconds == d("14400.000000")
    assert lagged.redacted_public_source_reference == "sha256:09c94ef0e7e2"
    assert lagged.reason_codes == (
        "market_research_policy_campaign_finance_reporting_lag_digest_reporting_lag_block",
        "market_research_policy_campaign_finance_reporting_lag_digest_thin_sources",
        "market_research_policy_campaign_finance_reporting_lag_digest_material_block",
    )
    assert summary.rows[1].reason_codes == (
        "market_research_policy_campaign_finance_reporting_lag_digest_missing_filing",
        "market_research_policy_campaign_finance_reporting_lag_digest_material_watch",
    )
    assert summary.rows[2].lag_status == "ready"
    assert summary.rows[2].redacted_public_source_reference == (
        "public-fec-campaign-finance-ready-report"
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.reason_code_counts == (
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_"
                "reporting_lag_block"
            ),
            count=d("1.000000"),
            filing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_"
                "missing_filing"
            ),
            count=d("1.000000"),
            filing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_"
                "thin_sources"
            ),
            count=d("1.000000"),
            filing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_"
                "material_block"
            ),
            count=d("1.000000"),
            filing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_"
                "material_watch"
            ),
            count=d("1.000000"),
            filing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_ready"
            ),
            count=d("1.000000"),
            filing_ratio=d("0.333333"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in summary.rows)
    assert all(
        count.paper_only and count.report_only and count.readonly
        for count in summary.reason_code_counts
    )
    assert_public_numerics_are_decimal(summary)

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "ready"  # type: ignore[misc]

    payload = market_research_policy_campaign_finance_reporting_lag_digest_payload(summary)
    assert isinstance(payload, MappingProxyType)
    assert isinstance(payload["rows"], tuple)
    assert isinstance(payload["rows"][0], MappingProxyType)
    assert payload["filing_count"] == "3.000000"
    assert payload["average_probability_impact"] == "0.223333"
    assert payload["rows"][0]["reporting_lag_seconds"] == "432000.000000"
    assert payload["reason_code_counts"][0]["filing_ratio"] == "0.333333"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(item, Decimal) for item in walk_payload(payload))
    assert not any(isinstance(item, float) for item in walk_payload(payload))
    with pytest.raises(TypeError):
        payload["filing_count"] = "0.000000"  # type: ignore[index]


def test_campaign_finance_reporting_lag_digest_empty_input_is_blocked() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_policy_campaign_finance_reporting_lag_digest"
    )
    assert summary.filing_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_policy_campaign_finance_reporting_lag_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_no_inputs"
            ),
            count=d("1.000000"),
            filing_ratio=d("1.000000"),
        ),
    )


def test_campaign_finance_reporting_lag_digest_rejects_subclasses_and_noncanonical_inputs() -> None:
    assert is_dataclass(MarketResearchPolicyCampaignFinanceReportingLagDigestConfig)
    assert is_dataclass(MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow)
    assert is_dataclass(MarketResearchPolicyCampaignFinanceReportingLagDigestRow)
    assert is_dataclass(
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
    )
    assert is_dataclass(MarketResearchPolicyCampaignFinanceReportingLagDigestReport)

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(MarketResearchPolicyCampaignFinanceReportingLagDigestConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class InputSubclass(MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class RowSubclass(MarketResearchPolicyCampaignFinanceReportingLagDigestRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class CountSubclass(
            MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ReportSubclass(MarketResearchPolicyCampaignFinanceReportingLagDigestReport):
            pass

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("campaign-finance-v0"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported-campaign-finance-v0")
    with pytest.raises(ValueError, match="max_ready_reporting_lag_seconds"):
        config(max_ready_reporting_lag_seconds=d("86400"))
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=Decimal("2.0"))
    with pytest.raises(ValueError, match="materiality_block_threshold"):
        config(
            materiality_watch_threshold=d("0.500000"),
            materiality_block_threshold=d("0.400000"),
        )
    with pytest.raises(ValueError, match="research_id"):
        filing_row(research_id=_StringSubclass("research.bad"))
    with pytest.raises(ValueError, match="reporting_period_end_at"):
        filing_row(reporting_period_end_at=datetime(2026, 7, 1, 12, 0))
    with pytest.raises(ValueError, match="source_observed_at"):
        filing_row(
            source_observed_at=_DateTimeSubclass(2026, 7, 5, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_source_count"):
        filing_row(public_source_count=d("2"))
    with pytest.raises(ValueError, match="disclosure_amount_usd"):
        filing_row(disclosure_amount_usd=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="estimated_probability_impact"):
        filing_row(estimated_probability_impact=d("0.100"))
    with pytest.raises(ValueError, match="paper_only"):
        filing_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(filing_row(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(filing_row(), readonly=False)


def test_campaign_finance_reporting_lag_digest_rejects_future_source_and_list_inputs() -> None:
    with pytest.raises(ValueError, match="input rows must be a tuple"):
        build_market_research_policy_campaign_finance_reporting_lag_digest(
            [filing_row()],  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source_observed_at"):
        report((filing_row(source_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    tampered_input = filing_row()
    object.__setattr__(tampered_input, "public_source_count", Decimal("2"))
    with pytest.raises(ValueError, match="public_source_count"):
        report((tampered_input,))
    with pytest.raises(ValueError, match="filing_published_at"):
        report(
            (
                filing_row(
                    filing_published_at=GENERATED_AT + timedelta(seconds=1),
                    source_observed_at=GENERATED_AT + timedelta(hours=1),
                ),
            ),
        )

    valid_summary = report((filing_row(),))
    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(valid_summary, rows=list(valid_summary.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(
            valid_summary,
            reason_code_counts=list(valid_summary.reason_code_counts),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(valid_summary, reason_codes=list(valid_summary.reason_codes))  # type: ignore[arg-type]


def test_campaign_finance_reporting_lag_digest_reconciles_reason_counts() -> None:
    summary = report((filing_row(),))
    ready_row = summary.rows[0]

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_finance_reporting_lag_digest_ready"
            ),
            count=ZERO,
            filing_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())
    with pytest.raises(ValueError, match="filing_count"):
        replace(summary, filing_count=d("2.000000"))
    with pytest.raises(ValueError, match="config_version"):
        replace(summary, config_version="unsupported-campaign-finance-v0")
    with pytest.raises(ValueError, match="lag_status"):
        replace(ready_row, lag_status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready_row,
            reason_codes=(
                "market_research_policy_campaign_finance_reporting_lag_digest_ready",
                "market_research_policy_campaign_finance_reporting_lag_digest_thin_sources",
            ),
        )


def test_campaign_finance_reporting_lag_payload_revalidates_nested_dataclasses_and_utc_times() -> None:
    summary = report((filing_row(),))

    object.__setattr__(
        summary,
        "generated_at",
        GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        market_research_policy_campaign_finance_reporting_lag_digest_payload(summary)

    nested_flag_summary = report((filing_row(),))
    object.__setattr__(nested_flag_summary.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_policy_campaign_finance_reporting_lag_digest_payload(
            nested_flag_summary,
        )

    nested_decimal_summary = report((filing_row(),))
    object.__setattr__(
        nested_decimal_summary.rows[0],
        "source_age_seconds",
        Decimal("1"),
    )
    with pytest.raises(ValueError, match="source_age_seconds"):
        market_research_policy_campaign_finance_reporting_lag_digest_payload(
            nested_decimal_summary,
        )


def test_campaign_finance_reporting_lag_digest_has_no_live_io_or_forbidden_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_policy_campaign_finance_reporting_lag_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    for token in (
        "dataclasses.asdict",
        "payload_json",
        "market_slug",
        "question",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
        "private_key",
        "wallet",
        "sqlite",
        "postgres",
        "redis",
    ):
        assert token not in lowered

    allowed_import_roots = {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "types",
        "typing",
    }
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "psycopg",
        "psycopg2",
        "supabase",
        "sqlite3",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_import_roots
                assert root not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".")[0]
            assert root in allowed_import_roots
            assert root not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
