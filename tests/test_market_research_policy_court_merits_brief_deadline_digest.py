from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_policy_court_merits_brief_deadline_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_court_merits_brief_deadline_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_policy_court_merits_brief_deadline_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_policy_court_merits_brief_deadline_digest_reduces_rows_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.brief.scotus-election",
                brief_deadline_key="scotus-opening-brief",
                condition_id="condition_scotus_election",
                court_key="scotus",
                jurisdiction_key="us",
                docket_key="24a-election",
                case_title="election-procedure-merits",
                policy_domain="elections",
                public_brief_deadline_reference=(
                    "https://court.example/briefs?token=secret-123"
                ),
                brief_party="petitioner",
                merits_brief_deadline_at=GENERATED_AT + timedelta(hours=5),
                last_checked_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("1.000000"),
                policy_impact_score=d("0.830000"),
                brief_readiness_score=d("0.420000"),
                market_relevance_score=d("0.770000"),
                brief_config_version="court-merits-brief-deadline-v1",
            ),
            input_row(
                digest,
                "research.brief.ca5-energy",
                brief_deadline_key="ca5-answering-brief",
                condition_id="condition_ca5_energy",
                court_key="ca5",
                jurisdiction_key="us",
                docket_key="25-1001",
                case_title="energy-rule-merits",
                policy_domain="energy",
                public_brief_deadline_reference="sealed-merits-brief-feed",
                brief_party="respondent",
                merits_brief_deadline_at=GENERATED_AT + timedelta(hours=30),
                last_checked_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(hours=1),
                source_count=d("2.000000"),
                policy_impact_score=d("0.640000"),
                brief_readiness_score=d("0.580000"),
                market_relevance_score=d("0.620000"),
                brief_config_version="court-merits-brief-deadline-v1",
            ),
            input_row(
                digest,
                "research.brief.state-tax",
                brief_deadline_key="ny-reply-brief",
                condition_id="condition_state_tax",
                court_key="ny-court-appeals",
                jurisdiction_key="ny",
                docket_key="tax-2026-07",
                case_title="state-tax-merits",
                policy_domain="tax",
                public_brief_deadline_reference="public-state-court-merits-brief",
                brief_party="reply",
                merits_brief_deadline_at=GENERATED_AT + timedelta(days=4),
                last_checked_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=15),
                source_count=d("3.000000"),
                policy_impact_score=d("0.200000"),
                brief_readiness_score=d("0.900000"),
                market_relevance_score=d("0.210000"),
                brief_config_version="court-merits-brief-deadline-v0",
            ),
            input_row(
                digest,
                "research.brief.old-health",
                brief_deadline_key="dc-health-supplemental-brief",
                condition_id="condition_health",
                court_key="dc-circuit",
                jurisdiction_key="us",
                docket_key="health-2026",
                case_title="health-rule-merits",
                policy_domain="health",
                public_brief_deadline_reference="public-dc-circuit-merits-brief",
                brief_party="amicus",
                merits_brief_deadline_at=GENERATED_AT - timedelta(hours=2),
                last_checked_at=GENERATED_AT - timedelta(hours=30),
                acknowledged_at=GENERATED_AT - timedelta(hours=4),
                source_count=d("2.000000"),
                policy_impact_score=d("0.100000"),
                brief_readiness_score=d("0.700000"),
                market_relevance_score=d("0.180000"),
                brief_config_version="court-merits-brief-deadline-v2",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_POLICY_COURT_MERITS_BRIEF_DEADLINE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_court_merits_brief_deadline_digest"
    )
    assert summary.brief_deadline_count == d("4.000000")
    assert summary.ready_brief_deadline_count == d("1.000000")
    assert summary.watch_brief_deadline_count == d("1.000000")
    assert summary.blocked_brief_deadline_count == d("2.000000")
    assert summary.high_policy_impact_count == d("2.000000")
    assert summary.low_brief_readiness_count == d("2.000000")
    assert summary.high_market_relevance_count == d("2.000000")
    assert summary.near_term_brief_deadline_count == d("2.000000")
    assert summary.stale_deadline_check_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.past_brief_deadline_count == d("1.000000")
    assert summary.average_policy_impact_score == d("0.442500")
    assert summary.average_brief_readiness_score == d("0.650000")
    assert summary.average_market_relevance_score == d("0.445000")
    assert summary.average_source_count == d("2.000000")
    assert summary.minimum_seconds_until_brief_deadline == d("-7200.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.brief_deadline_key, row.research_key) for row in summary.rows) == (
        ("scotus-opening-brief", "research.brief.scotus-election"),
        ("dc-health-supplemental-brief", "research.brief.old-health"),
        ("ca5-answering-brief", "research.brief.ca5-energy"),
        ("ny-reply-brief", "research.brief.state-tax"),
    )

    scotus = summary.rows[0]
    assert scotus.deadline_status == "blocked"
    assert scotus.seconds_until_brief_deadline == d("18000.000000")
    assert scotus.deadline_check_age_seconds == d("14400.000000")
    assert scotus.acknowledgement_lag_seconds is None
    assert scotus.redacted_public_brief_deadline_reference == redacted(
        "https://court.example/briefs?token=secret-123",
    )
    assert scotus.reason_codes == (
        "market_research_policy_court_merits_brief_deadline_digest_high_policy_impact",
        "market_research_policy_court_merits_brief_deadline_digest_low_brief_readiness",
        "market_research_policy_court_merits_brief_deadline_digest_high_market_relevance",
        "market_research_policy_court_merits_brief_deadline_digest_near_term_brief_deadline",
        "market_research_policy_court_merits_brief_deadline_digest_thin_sources",
        "market_research_policy_court_merits_brief_deadline_digest_missing_acknowledgement",
    )

    old_health = summary.rows[1]
    assert old_health.deadline_status == "blocked"
    assert old_health.seconds_until_brief_deadline == d("-7200.000000")
    assert old_health.deadline_check_age_seconds == d("108000.000000")
    assert old_health.acknowledgement_lag_seconds == d("93600.000000")
    assert old_health.reason_codes == (
        "market_research_policy_court_merits_brief_deadline_digest_stale_deadline_check",
        "market_research_policy_court_merits_brief_deadline_digest_past_brief_deadline",
    )

    ca5 = summary.rows[2]
    assert ca5.deadline_status == "watch"
    assert ca5.seconds_until_brief_deadline == d("108000.000000")
    assert ca5.acknowledgement_lag_seconds == d("7200.000000")
    assert ca5.redacted_public_brief_deadline_reference == redacted(
        "sealed-merits-brief-feed",
    )
    assert ca5.reason_codes == (
        "market_research_policy_court_merits_brief_deadline_digest_high_policy_impact",
        "market_research_policy_court_merits_brief_deadline_digest_low_brief_readiness",
        "market_research_policy_court_merits_brief_deadline_digest_high_market_relevance",
        "market_research_policy_court_merits_brief_deadline_digest_near_term_brief_deadline",
    )

    state_tax = summary.rows[3]
    assert state_tax.deadline_status == "ready"
    assert state_tax.reason_codes == (
        "market_research_policy_court_merits_brief_deadline_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_high_policy_impact"
            ),
            count=d("2.000000"),
            brief_deadline_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_low_brief_readiness"
            ),
            count=d("2.000000"),
            brief_deadline_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_high_market_relevance"
            ),
            count=d("2.000000"),
            brief_deadline_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_near_term_brief_deadline"
            ),
            count=d("2.000000"),
            brief_deadline_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_stale_deadline_check"
            ),
            count=d("1.000000"),
            brief_deadline_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_thin_sources"
            ),
            count=d("1.000000"),
            brief_deadline_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_missing_acknowledgement"
            ),
            count=d("1.000000"),
            brief_deadline_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_past_brief_deadline"
            ),
            count=d("1.000000"),
            brief_deadline_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_ready"
            ),
            count=d("1.000000"),
            brief_deadline_ratio=d("0.250000"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.brief_config_versions == (
        ("ca5-answering-brief", "court-merits-brief-deadline-v1"),
        ("dc-health-supplemental-brief", "court-merits-brief-deadline-v2"),
        ("ny-reply-brief", "court-merits-brief-deadline-v0"),
        ("scotus-opening-brief", "court-merits-brief-deadline-v1"),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "court.example",
        "https://",
        "sealed-merits-brief-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_policy_court_merits_brief_deadline_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_court_merits_brief_deadline_digest"
    )
    assert summary.brief_deadline_count == ZERO
    assert summary.ready_brief_deadline_count == ZERO
    assert summary.watch_brief_deadline_count == ZERO
    assert summary.blocked_brief_deadline_count == ZERO
    assert summary.average_policy_impact_score == ZERO
    assert summary.average_brief_readiness_score == ZERO
    assert summary.average_market_relevance_score == ZERO
    assert summary.average_source_count == ZERO
    assert summary.minimum_seconds_until_brief_deadline == ZERO
    assert summary.rows == ()
    assert summary.brief_config_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_court_merits_brief_deadline_digest_no_inputs"
            ),
            count=d("1.000000"),
            brief_deadline_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_court_merits_brief_deadline_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_policy_court_merits_brief_deadline_digest_honors_custom_config_thresholds() -> None:
    digest = digest_module()
    custom_config = config(
        digest,
        near_term_brief_deadline_seconds=d("3600.000000"),
        high_policy_impact_threshold=d("0.900000"),
        low_brief_readiness_threshold=d("0.100000"),
        high_market_relevance_threshold=d("0.900000"),
        min_source_count=d("1.000000"),
    )

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.brief.custom-thresholds",
                merits_brief_deadline_at=GENERATED_AT + timedelta(hours=5),
                source_count=d("1.000000"),
                policy_impact_score=d("0.700000"),
                brief_readiness_score=d("0.700000"),
                market_relevance_score=d("0.700000"),
            ),
        ),
        cfg=custom_config,
    )

    assert summary.digest_status == "ready"
    assert summary.ready_brief_deadline_count == d("1.000000")
    assert summary.watch_brief_deadline_count == ZERO
    assert summary.blocked_brief_deadline_count == ZERO
    assert summary.rows[0].deadline_status == "ready"
    assert summary.rows[0].reason_codes == (
        "market_research_policy_court_merits_brief_deadline_digest_ready",
    )


def test_policy_court_merits_brief_deadline_digest_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_policy_court_merits_brief_deadline_digest_payload(
        summary,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["brief_deadline_count"] == "1.000000"
    assert payload["average_policy_impact_score"] == "0.200000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["seconds_until_brief_deadline"] == "345600.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_brief_deadline_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_policy_court_merits_brief_deadline_digest_validates_contracts_and_flags() -> None:
    digest = digest_module()

    assert (
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestConfig
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestInputRow
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestRow
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestReport
        .__dataclass_params__
        .frozen
    )

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("court-merits-brief-v0"))
    with pytest.raises(ValueError, match="near_term_brief_deadline_seconds"):
        config(
            digest,
            near_term_brief_deadline_seconds=_DecimalSubclass("172800.000000"),
        )
    with pytest.raises(ValueError, match="high_policy_impact_threshold"):
        config(digest, high_policy_impact_threshold=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=" bad")
    with pytest.raises(ValueError, match="case_title"):
        input_row(digest, case_title="private-docket-title")
    with pytest.raises(ValueError, match="merits_brief_deadline_at"):
        input_row(digest, merits_brief_deadline_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="last_checked_at"):
        input_row(
            digest,
            last_checked_at=_DateTimeSubclass(2026, 7, 4, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="policy_impact_score"):
        input_row(digest, policy_impact_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="brief_readiness_score"):
        input_row(digest, brief_readiness_score=d("1.000001"))
    with pytest.raises(ValueError, match="market_relevance_score"):
        input_row(digest, market_relevance_score=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, last_checked_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_policy_court_merits_brief_deadline_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestConfig,),
            {},
        )


def test_policy_court_merits_brief_deadline_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, brief_deadline_key="duplicate-brief"),
                input_row(
                    digest,
                    "research.brief.duplicate-2",
                    brief_deadline_key="duplicate-brief",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_policy_court_merits_brief_deadline_digest_ready",
                "market_research_policy_court_merits_brief_deadline_digest_past_brief_deadline",
            ),
        )
    with pytest.raises(ValueError, match="deadline_status"):
        replace(ready, deadline_status="blocked")
    with pytest.raises(ValueError, match="redacted_public_brief_deadline_reference"):
        replace(
            ready,
            redacted_public_brief_deadline_reference="https://host?token=secret",
        )

    with pytest.raises(ValueError, match="ready_brief_deadline_count"):
        replace(report(digest, (input_row(digest),)), ready_brief_deadline_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(
                    digest,
                    "research.brief.z",
                    brief_deadline_key="z-brief",
                    court_key="z-court",
                ),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_count_ratio_score_and_seconds_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(
        digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestConfig(),
    )
    assert_decimal_public_numeric_fields(input_row(digest))
    assert_decimal_public_numeric_fields(summary)
    assert_decimal_public_numeric_fields(summary.rows[0])
    assert_decimal_public_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
        "subprocess",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "account",
        "advice",
    ):
        assert forbidden not in source.lower()


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            digest.DEFAULT_MARKET_RESEARCH_POLICY_COURT_MERITS_BRIEF_DEADLINE_DIGEST_CONFIG_VERSION
        ),
        "near_term_brief_deadline_seconds": d("172800.000000"),
        "stale_deadline_check_seconds": d("86400.000000"),
        "high_policy_impact_threshold": d("0.600000"),
        "low_brief_readiness_threshold": d("0.600000"),
        "high_market_relevance_threshold": d("0.600000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestConfig(**values)


def input_row(
    digest: Any,
    research_key: str = "research.brief.state-tax",
    *,
    brief_deadline_key: str = "ny-reply-brief",
    condition_id: str = "condition_state_tax",
    court_key: str = "ny-court-appeals",
    jurisdiction_key: str = "ny",
    docket_key: str = "tax-2026-07",
    case_title: str = "state-tax-merits",
    policy_domain: str = "tax",
    public_brief_deadline_reference: str = "public-state-court-merits-brief",
    brief_party: str = "reply",
    merits_brief_deadline_at: datetime | None = None,
    last_checked_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    policy_impact_score: Decimal = d("0.200000"),
    brief_readiness_score: Decimal = d("0.900000"),
    market_relevance_score: Decimal = d("0.210000"),
    brief_config_version: str = "court-merits-brief-deadline-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchPolicyCourtMeritsBriefDeadlineDigestInputRow(
        research_key=research_key,
        brief_deadline_key=brief_deadline_key,
        condition_id=condition_id,
        court_key=court_key,
        jurisdiction_key=jurisdiction_key,
        docket_key=docket_key,
        case_title=case_title,
        policy_domain=policy_domain,
        public_brief_deadline_reference=public_brief_deadline_reference,
        brief_party=brief_party,
        merits_brief_deadline_at=(
            merits_brief_deadline_at
            if merits_brief_deadline_at is not None
            else GENERATED_AT + timedelta(days=4)
        ),
        last_checked_at=(
            last_checked_at
            if last_checked_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        acknowledged_at=(
            acknowledged_at
            if acknowledged_at is not _UNSET
            else GENERATED_AT - timedelta(minutes=15)
        ),
        source_count=source_count,
        policy_impact_score=policy_impact_score,
        brief_readiness_score=brief_readiness_score,
        market_relevance_score=market_relevance_score,
        brief_config_version=brief_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    digest: Any,
    rows: tuple[Any, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return digest.build_market_research_policy_court_merits_brief_deadline_digest(
        rows,
        config=cfg or config(digest),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        output: list[Any] = []
        for item in value.values():
            output.extend(walk_values(item))
        return tuple(output)
    if isinstance(value, list):
        output = []
        for item in value:
            output.extend(walk_values(item))
        return tuple(output)
    return (value,)


def assert_decimal_public_numeric_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, bool):
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "ratio",
                "score",
                "seconds",
                "threshold",
            )
        ) and not isinstance(item, (tuple, list, dict)):
            assert type(item) is Decimal
        assert not isinstance(item, float)
        assert not isinstance(item, int)
