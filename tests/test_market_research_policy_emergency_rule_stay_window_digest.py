from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_policy_emergency_rule_stay_window_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_emergency_rule_stay_window_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_emergency_rule_stay_window_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_emergency_rule_stay_window_digest_reduces_rows_and_scores_risk() -> None:
    digest = digest_module()
    sensitive_reference = "https://policy.example/rule-window?token=secret-123"

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.emergency.state-tax",
                market_slug="state-tax-rule-stay-window",
                agency_court_source_id="state-court-tax",
                emergency_rule_reference="public-state-tax-rule-window",
                effective_at=GENERATED_AT + timedelta(days=30),
                response_deadline_at=GENERATED_AT + timedelta(days=20),
                docket_checked_at=GENERATED_AT - timedelta(hours=6),
                stay_motion_status="not_filed",
                injunction_probability_proxy=d("0.120000"),
                affected_jurisdiction_count=d("1.000000"),
                legal_source_count=d("3.000000"),
                upstream_reason_codes=(),
            ),
            input_row(
                digest,
                "research.emergency.energy",
                market_slug="energy-rule-effective-date",
                agency_court_source_id="federal-court-energy",
                emergency_rule_reference=sensitive_reference,
                effective_at=GENERATED_AT + timedelta(days=2),
                response_deadline_at=GENERATED_AT + timedelta(hours=12),
                docket_checked_at=GENERATED_AT - timedelta(days=3),
                stay_motion_status="filed",
                injunction_probability_proxy=d("0.800000"),
                affected_jurisdiction_count=d("4.000000"),
                legal_source_count=d("1.000000"),
                upstream_reason_codes=(
                    "agency_rule_injunction_watch",
                    "court_stay_deadline_blocked",
                ),
            ),
            input_row(
                digest,
                "research.emergency.health",
                market_slug="health-rule-stay-motion",
                agency_court_source_id="district-court-health",
                emergency_rule_reference="public-health-rule-window",
                effective_at=GENERATED_AT + timedelta(days=20),
                response_deadline_at=GENERATED_AT + timedelta(days=6),
                docket_checked_at=GENERATED_AT - timedelta(hours=1),
                stay_motion_status="granted",
                injunction_probability_proxy=d("0.300000"),
                affected_jurisdiction_count=d("2.000000"),
                legal_source_count=d("3.000000"),
                upstream_reason_codes=(),
            ),
            input_row(
                digest,
                "research.emergency.vehicle",
                market_slug="vehicle-rule-response-window",
                agency_court_source_id="agency-vehicle-rule",
                emergency_rule_reference="public-vehicle-rule-window",
                effective_at=GENERATED_AT + timedelta(days=10),
                response_deadline_at=GENERATED_AT + timedelta(days=4),
                docket_checked_at=GENERATED_AT - timedelta(days=1),
                stay_motion_status="anticipated",
                injunction_probability_proxy=d("0.450000"),
                affected_jurisdiction_count=d("3.000000"),
                legal_source_count=d("2.000000"),
                upstream_reason_codes=("agency_rule_injunction_watch",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_POLICY_EMERGENCY_RULE_STAY_WINDOW_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_emergency_rule_stay_window_digest"
    )
    assert summary.rule_count == d("4.000000")
    assert summary.pass_rule_count == d("1.000000")
    assert summary.watch_rule_count == d("1.000000")
    assert summary.blocked_rule_count == d("2.000000")
    assert summary.stay_motion_filed_count == d("1.000000")
    assert summary.stay_motion_granted_count == d("1.000000")
    assert summary.high_injunction_probability_count == d("1.000000")
    assert summary.elevated_injunction_probability_count == d("1.000000")
    assert summary.effective_date_block_count == d("1.000000")
    assert summary.effective_date_watch_count == d("1.000000")
    assert summary.response_deadline_block_count == d("1.000000")
    assert summary.response_deadline_watch_count == d("2.000000")
    assert summary.stale_docket_count == d("1.000000")
    assert summary.thin_legal_source_quorum_count == d("1.000000")
    assert summary.broad_affected_jurisdiction_count == d("2.000000")
    assert summary.upstream_block_count == d("1.000000")
    assert summary.upstream_watch_count == d("2.000000")
    assert summary.risk_score_block_count == d("1.000000")
    assert summary.risk_score_watch_count == d("1.000000")
    assert summary.average_stay_window_risk_score == d("0.413250")
    assert summary.max_stay_window_risk_score == d("0.890000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.row_status, row.market_slug) for row in summary.rows) == (
        ("blocked", "energy-rule-effective-date"),
        ("blocked", "health-rule-stay-motion"),
        ("watch", "vehicle-rule-response-window"),
        ("pass", "state-tax-rule-stay-window"),
    )

    blocked = summary.rows[0]
    assert blocked.days_until_effective_date == d("2.000000")
    assert blocked.days_until_response_deadline == d("0.500000")
    assert blocked.docket_freshness_age_days == d("3.000000")
    assert blocked.legal_source_quorum_count == d("2.000000")
    assert blocked.stay_window_risk_score == d("0.890000")
    assert blocked.redacted_emergency_rule_reference == redacted(sensitive_reference)
    assert blocked.upstream_reason_codes == (
        "agency_rule_injunction_watch",
        "court_stay_deadline_blocked",
    )
    assert blocked.reason_codes == (
        "market_research_policy_emergency_rule_stay_window_digest_high_injunction_probability",
        "market_research_policy_emergency_rule_stay_window_digest_effective_date_block",
        "market_research_policy_emergency_rule_stay_window_digest_response_deadline_block",
        "market_research_policy_emergency_rule_stay_window_digest_thin_legal_source_quorum",
        "market_research_policy_emergency_rule_stay_window_digest_stale_docket",
        "market_research_policy_emergency_rule_stay_window_digest_upstream_block",
        "market_research_policy_emergency_rule_stay_window_digest_risk_score_block",
        "market_research_policy_emergency_rule_stay_window_digest_stay_motion_filed",
        "market_research_policy_emergency_rule_stay_window_digest_broad_affected_jurisdiction",
        "market_research_policy_emergency_rule_stay_window_digest_upstream_watch",
    )

    granted = summary.rows[1]
    assert granted.row_status == "blocked"
    assert granted.reason_codes == (
        "market_research_policy_emergency_rule_stay_window_digest_stay_motion_granted",
        "market_research_policy_emergency_rule_stay_window_digest_response_deadline_watch",
    )
    assert granted.stay_window_risk_score == d("0.295000")

    watch = summary.rows[2]
    assert watch.row_status == "watch"
    assert watch.reason_codes == (
        "market_research_policy_emergency_rule_stay_window_digest_elevated_injunction_probability",
        "market_research_policy_emergency_rule_stay_window_digest_effective_date_watch",
        "market_research_policy_emergency_rule_stay_window_digest_response_deadline_watch",
        "market_research_policy_emergency_rule_stay_window_digest_stay_motion_pending",
        "market_research_policy_emergency_rule_stay_window_digest_broad_affected_jurisdiction",
        "market_research_policy_emergency_rule_stay_window_digest_upstream_watch",
        "market_research_policy_emergency_rule_stay_window_digest_risk_score_watch",
    )

    passing = summary.rows[3]
    assert passing.row_status == "pass"
    assert passing.reason_codes == (
        "market_research_policy_emergency_rule_stay_window_digest_pass",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_high_injunction_probability",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_effective_date_block",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_response_deadline_block",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_stay_motion_granted",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_thin_legal_source_quorum",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_stale_docket",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_upstream_block",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_risk_score_block",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_elevated_injunction_probability",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_effective_date_watch",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_response_deadline_watch",
            count=d("2.000000"),
            rule_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_stay_motion_filed",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_stay_motion_pending",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_broad_affected_jurisdiction",
            count=d("2.000000"),
            rule_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_upstream_watch",
            count=d("2.000000"),
            rule_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_risk_score_watch",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_pass",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.upstream_reason_code_counts == (
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount(
            upstream_reason_code="agency_rule_injunction_watch",
            count=d("2.000000"),
            rule_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount(
            upstream_reason_code="court_stay_deadline_blocked",
            count=d("1.000000"),
            rule_ratio=d("0.250000"),
        ),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "policy.example",
        "https://",
        "token=",
    ):
        assert token not in public


def test_empty_emergency_rule_stay_window_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_emergency_rule_stay_window_digest"
    )
    assert summary.rule_count == ZERO
    assert summary.pass_rule_count == ZERO
    assert summary.watch_rule_count == ZERO
    assert summary.blocked_rule_count == ZERO
    assert summary.average_stay_window_risk_score == ZERO
    assert summary.max_stay_window_risk_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code="market_research_policy_emergency_rule_stay_window_digest_no_inputs",
            count=d("1.000000"),
            rule_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_emergency_rule_stay_window_digest_no_inputs",
    )
    assert summary.upstream_reason_code_counts == ()
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_emergency_rule_stay_window_digest_payload_is_canonical_json_safe() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_policy_emergency_rule_stay_window_digest_payload(
        summary,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["rule_count"] == "1.000000"
    assert payload["average_stay_window_risk_score"] == "0.048000"
    assert payload["rows"][0]["days_until_effective_date"] == "30.000000"
    assert payload["rows"][0]["injunction_probability_proxy"] == "0.120000"
    assert payload["rows"][0]["legal_source_quorum_count"] == "2.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'emergency_rule_reference':" not in repr(payload)
    assert "secret" not in repr(payload).lower()


def test_emergency_rule_stay_window_digest_validates_contracts_and_flags() -> None:
    digest = digest_module()

    assert digest.MarketResearchPolicyEmergencyRuleStayWindowDigestConfig.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyEmergencyRuleStayWindowDigestRow.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyEmergencyRuleStayWindowDigestReport.__dataclass_params__.frozen

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].stay_window_risk_score = d("1.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("emergency-rule-window-v0"))
    with pytest.raises(ValueError, match="effective_date_watch_days"):
        config(digest, effective_date_watch_days=14)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="effective_date_block_days"):
        config(
            digest,
            effective_date_watch_days=d("3.000000"),
            effective_date_block_days=d("4.000000"),
        )
    with pytest.raises(ValueError, match="injunction_probability_watch_threshold"):
        config(digest, injunction_probability_watch_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="injunction_probability_block_threshold"):
        config(
            digest,
            injunction_probability_watch_threshold=d("0.700000"),
            injunction_probability_block_threshold=d("0.650000"),
        )
    with pytest.raises(ValueError, match="risk_score_block_threshold"):
        config(
            digest,
            risk_score_watch_threshold=d("0.700000"),
            risk_score_block_threshold=d("0.650000"),
        )
    with pytest.raises(ValueError, match="market_slug"):
        input_row(digest, market_slug=" wallet-market ")
    with pytest.raises(ValueError, match="agency_court_source_id"):
        input_row(digest, agency_court_source_id="private-source")
    with pytest.raises(ValueError, match="effective_at"):
        input_row(digest, effective_at=datetime(2026, 8, 1, 12, 0))
    with pytest.raises(ValueError, match="docket_checked_at"):
        input_row(
            digest,
            docket_checked_at=_DateTimeSubclass(2026, 7, 4, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="stay_motion_status"):
        input_row(digest, stay_motion_status="pending")
    with pytest.raises(ValueError, match="injunction_probability_proxy"):
        input_row(digest, injunction_probability_proxy=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="affected_jurisdiction_count"):
        input_row(digest, affected_jurisdiction_count=d("1.5"))
    with pytest.raises(ValueError, match="legal_source_count"):
        input_row(digest, legal_source_count=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        input_row(digest, upstream_reason_codes=("watch", "watch"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_policy_emergency_rule_stay_window_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        digest.build_market_research_policy_emergency_rule_stay_window_digest(
            (),
            config=config(digest),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, docket_checked_at=GENERATED_AT + timedelta(seconds=1)),),
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (digest.MarketResearchPolicyEmergencyRuleStayWindowDigestConfig,),
            {},
        )


def test_emergency_rule_stay_window_digest_rejects_duplicates_and_manual_drift() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="duplicate"):
        report(
            digest,
            (
                input_row(
                    digest,
                    market_slug="duplicate-window",
                    agency_court_source_id="duplicate-source",
                ),
                input_row(
                    digest,
                    "research.emergency.duplicate",
                    market_slug="duplicate-window",
                    agency_court_source_id="duplicate-source",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_policy_emergency_rule_stay_window_digest_pass",
                "market_research_policy_emergency_rule_stay_window_digest_high_injunction_probability",
            ),
        )
    with pytest.raises(ValueError, match="row_status"):
        replace(ready, row_status="blocked")
    with pytest.raises(ValueError, match="stay_window_risk_score"):
        replace(ready, stay_window_risk_score=d("0.990000"))
    with pytest.raises(ValueError, match="redacted_emergency_rule_reference"):
        replace(ready, redacted_emergency_rule_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="pass_rule_count"):
        replace(report(digest, (input_row(digest),)), pass_rule_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(
                    digest,
                    "research.emergency.zeta",
                    market_slug="zeta-rule-window",
                    agency_court_source_id="zeta-source",
                ),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(config(digest))
    assert_decimal_public_numeric_fields(input_row(digest))
    assert_decimal_public_numeric_fields(summary)
    assert_decimal_public_numeric_fields(summary.rows[0])
    assert_decimal_public_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_execution_or_mutation_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    allowed_import_roots = {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }
    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "supabase",
        "sqlite3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "fetch",
        "open",
        "read",
        "write",
        "request",
        "urlopen",
        "getenv",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "trade",
    }
    forbidden_source_fragments = (
        "live trading",
        "private_key",
        "api_key",
        "wallet",
        "exchange mutation",
        "database",
        "network",
        "subprocess",
        "requests",
        "httpx",
        "supabase",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] in allowed_import_roots
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attribute_name in attribute_names:
        assert attribute_name not in forbidden_calls
    lowered = source.lower()
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            digest.DEFAULT_MARKET_RESEARCH_POLICY_EMERGENCY_RULE_STAY_WINDOW_DIGEST_CONFIG_VERSION
        ),
        "effective_date_watch_days": d("14.000000"),
        "effective_date_block_days": d("3.000000"),
        "response_deadline_watch_days": d("7.000000"),
        "response_deadline_block_days": d("1.000000"),
        "max_docket_freshness_age_days": d("2.000000"),
        "legal_source_quorum_count": d("2.000000"),
        "broad_affected_jurisdiction_count": d("3.000000"),
        "injunction_probability_watch_threshold": d("0.350000"),
        "injunction_probability_block_threshold": d("0.650000"),
        "risk_score_watch_threshold": d("0.350000"),
        "risk_score_block_threshold": d("0.650000"),
    }
    values.update(overrides)
    return digest.MarketResearchPolicyEmergencyRuleStayWindowDigestConfig(**values)


def input_row(
    digest: Any,
    research_key: str = "research.emergency.state-tax",
    *,
    market_slug: str = "state-tax-rule-stay-window",
    agency_court_source_id: str = "state-court-tax",
    emergency_rule_reference: str = "public-state-tax-rule-window",
    effective_at: datetime | None = None,
    response_deadline_at: datetime | None = None,
    docket_checked_at: datetime | None = None,
    stay_motion_status: str = "not_filed",
    injunction_probability_proxy: Decimal = d("0.120000"),
    affected_jurisdiction_count: Decimal = d("1.000000"),
    legal_source_count: Decimal = d("3.000000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow(
        research_key=research_key,
        market_slug=market_slug,
        agency_court_source_id=agency_court_source_id,
        emergency_rule_reference=emergency_rule_reference,
        effective_at=effective_at or GENERATED_AT + timedelta(days=30),
        response_deadline_at=response_deadline_at or GENERATED_AT + timedelta(days=20),
        docket_checked_at=docket_checked_at or GENERATED_AT - timedelta(hours=6),
        stay_motion_status=stay_motion_status,
        injunction_probability_proxy=injunction_probability_proxy,
        affected_jurisdiction_count=affected_jurisdiction_count,
        legal_source_count=legal_source_count,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    digest: Any,
    rows: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return digest.build_market_research_policy_emergency_rule_stay_window_digest(
        rows,
        config=config(digest),
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
                "days",
                "score",
                "proxy",
            )
        ) and not isinstance(item, (tuple, list, dict)):
            assert type(item) is Decimal, field.name
        assert not isinstance(item, float)
        assert not isinstance(item, int)
