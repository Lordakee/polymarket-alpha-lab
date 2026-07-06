from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.market_research_policy_debate_mic_rule_change_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_debate_mic_rule_change_digest.py",
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


def test_policy_debate_mic_rule_change_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_policy_debate_mic_rule_change_digest_reduces_rows_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.debate.mic.mayor",
                condition_id="condition_mayor_mic_rule",
                jurisdiction="nyc",
                debate_id="debate_mayor_1",
                broadcaster="public-broadcast",
                rule_change_kind="rebuttal-window",
                public_rule_reference="public-city-debate-rule",
                rule_announced_at=GENERATED_AT - timedelta(days=15),
                debate_scheduled_at=GENERATED_AT + timedelta(days=5),
                last_verified_at=GENERATED_AT - timedelta(minutes=45),
                acknowledged_at=GENERATED_AT - timedelta(minutes=30),
                source_count=d("3.000000"),
                implementation_uncertainty_score=d("0.200000"),
                candidate_impact_score=d("0.250000"),
                outcome_relevance_score=d("0.210000"),
                format_disruption_score=d("0.300000"),
                rule_config_version="debate-mic-rule-v0",
            ),
            input_row(
                digest,
                "research.debate.mic.open",
                condition_id="condition_open_mic_rule",
                jurisdiction="us-az",
                debate_id="debate_senate_primary",
                broadcaster="state-public-tv",
                rule_change_kind="open-mic",
                public_rule_reference="public-open-mic-format-rule",
                rule_announced_at=GENERATED_AT - timedelta(days=1),
                debate_scheduled_at=GENERATED_AT + timedelta(days=1),
                last_verified_at=GENERATED_AT - timedelta(hours=30),
                acknowledged_at=GENERATED_AT - timedelta(hours=6),
                source_count=d("2.000000"),
                implementation_uncertainty_score=d("0.650000"),
                candidate_impact_score=d("0.800000"),
                outcome_relevance_score=d("0.700000"),
                format_disruption_score=d("0.780000"),
                rule_config_version="debate-mic-rule-v3",
            ),
            input_row(
                digest,
                "research.debate.mic.cross",
                condition_id="condition_cross_talk_rule",
                jurisdiction="us-mi",
                debate_id="debate_governor_2026",
                broadcaster="public-affairs-network",
                rule_change_kind="cross-talk",
                public_rule_reference="sealed-cross-talk-format-calendar",
                rule_announced_at=GENERATED_AT - timedelta(days=2),
                debate_scheduled_at=GENERATED_AT + timedelta(days=10),
                last_verified_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(hours=1),
                source_count=d("2.000000"),
                implementation_uncertainty_score=d("0.650000"),
                candidate_impact_score=d("0.500000"),
                outcome_relevance_score=d("0.620000"),
                format_disruption_score=d("0.550000"),
                rule_config_version="debate-mic-rule-v1",
            ),
            input_row(
                digest,
                "research.debate.mic.muted",
                condition_id="condition_muted_mic_rule",
                jurisdiction="us-pa",
                debate_id="debate_senate_general",
                broadcaster="public-election-forum",
                rule_change_kind="muted-mic",
                public_rule_reference=(
                    "https://debates.example/mic-rule?token=secret-123"
                ),
                rule_announced_at=GENERATED_AT - timedelta(hours=8),
                debate_scheduled_at=GENERATED_AT + timedelta(days=1),
                last_verified_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_count=d("1.000000"),
                implementation_uncertainty_score=d("0.850000"),
                candidate_impact_score=d("0.700000"),
                outcome_relevance_score=d("0.900000"),
                format_disruption_score=d("0.950000"),
                rule_config_version="debate-mic-rule-v2",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_POLICY_DEBATE_MIC_RULE_CHANGE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_debate_mic_rule_change_digest"
    )
    assert summary.rule_change_count == d("4.000000")
    assert summary.pass_rule_change_count == d("1.000000")
    assert summary.watch_rule_change_count == d("1.000000")
    assert summary.blocked_rule_change_count == d("2.000000")
    assert summary.muted_mic_rule_change_count == d("1.000000")
    assert summary.open_mic_rule_change_count == d("1.000000")
    assert summary.cross_talk_rule_change_count == d("1.000000")
    assert summary.late_rule_change_count == d("3.000000")
    assert summary.high_implementation_uncertainty_count == d("3.000000")
    assert summary.high_candidate_impact_count == d("2.000000")
    assert summary.high_outcome_relevance_count == d("3.000000")
    assert summary.high_format_disruption_count == d("2.000000")
    assert summary.stale_verification_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.average_implementation_uncertainty_score == d("0.587500")
    assert summary.average_candidate_impact_score == d("0.562500")
    assert summary.average_outcome_relevance_score == d("0.607500")
    assert summary.average_format_disruption_score == d("0.645000")
    assert summary.average_source_count == d("2.000000")
    assert summary.minimum_rule_change_lead_seconds == d("115200.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.jurisdiction, row.research_id) for row in summary.rows) == (
        ("us-pa", "research.debate.mic.muted"),
        ("us-az", "research.debate.mic.open"),
        ("us-mi", "research.debate.mic.cross"),
        ("nyc", "research.debate.mic.mayor"),
    )

    muted = summary.rows[0]
    assert muted.screening_status == "blocked"
    assert muted.rule_change_lead_seconds == d("115200.000000")
    assert muted.seconds_until_debate == d("86400.000000")
    assert muted.verification_age_seconds == d("18000.000000")
    assert muted.acknowledgement_lag_seconds is None
    assert muted.redacted_public_rule_reference == redacted(
        "https://debates.example/mic-rule?token=secret-123",
    )
    assert muted.reason_codes == (
        "market_research_policy_debate_mic_rule_change_digest_high_implementation_uncertainty",
        "market_research_policy_debate_mic_rule_change_digest_high_candidate_impact",
        "market_research_policy_debate_mic_rule_change_digest_high_outcome_relevance",
        "market_research_policy_debate_mic_rule_change_digest_high_format_disruption",
        "market_research_policy_debate_mic_rule_change_digest_late_rule_change",
        "market_research_policy_debate_mic_rule_change_digest_muted_mic_rule_change",
        "market_research_policy_debate_mic_rule_change_digest_thin_sources",
        "market_research_policy_debate_mic_rule_change_digest_missing_acknowledgement",
    )

    open_mic = summary.rows[1]
    assert open_mic.screening_status == "blocked"
    assert open_mic.rule_change_lead_seconds == d("172800.000000")
    assert open_mic.acknowledgement_lag_seconds == d("86400.000000")
    assert open_mic.reason_codes == (
        "market_research_policy_debate_mic_rule_change_digest_high_implementation_uncertainty",
        "market_research_policy_debate_mic_rule_change_digest_high_candidate_impact",
        "market_research_policy_debate_mic_rule_change_digest_high_outcome_relevance",
        "market_research_policy_debate_mic_rule_change_digest_high_format_disruption",
        "market_research_policy_debate_mic_rule_change_digest_late_rule_change",
        "market_research_policy_debate_mic_rule_change_digest_open_mic_rule_change",
        "market_research_policy_debate_mic_rule_change_digest_stale_verification",
    )

    cross_talk = summary.rows[2]
    assert cross_talk.screening_status == "watch"
    assert cross_talk.rule_change_lead_seconds == d("1036800.000000")
    assert cross_talk.reason_codes == (
        "market_research_policy_debate_mic_rule_change_digest_high_implementation_uncertainty",
        "market_research_policy_debate_mic_rule_change_digest_high_outcome_relevance",
        "market_research_policy_debate_mic_rule_change_digest_late_rule_change",
        "market_research_policy_debate_mic_rule_change_digest_cross_talk_rule_change",
    )

    mayor = summary.rows[3]
    assert mayor.screening_status == "pass"
    assert mayor.reason_codes == (
        "market_research_policy_debate_mic_rule_change_digest_pass",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_high_implementation_uncertainty"
            ),
            count=d("3.000000"),
            rule_change_ratio=d("0.750000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_high_candidate_impact"
            ),
            count=d("2.000000"),
            rule_change_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_high_outcome_relevance"
            ),
            count=d("3.000000"),
            rule_change_ratio=d("0.750000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_high_format_disruption"
            ),
            count=d("2.000000"),
            rule_change_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_late_rule_change"
            ),
            count=d("3.000000"),
            rule_change_ratio=d("0.750000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_muted_mic_rule_change"
            ),
            count=d("1.000000"),
            rule_change_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_open_mic_rule_change"
            ),
            count=d("1.000000"),
            rule_change_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_cross_talk_rule_change"
            ),
            count=d("1.000000"),
            rule_change_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_stale_verification"
            ),
            count=d("1.000000"),
            rule_change_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_thin_sources"
            ),
            count=d("1.000000"),
            rule_change_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_missing_acknowledgement"
            ),
            count=d("1.000000"),
            rule_change_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code="market_research_policy_debate_mic_rule_change_digest_pass",
            count=d("1.000000"),
            rule_change_ratio=d("0.250000"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.rule_config_versions == (
        ("condition_cross_talk_rule", "debate-mic-rule-v1"),
        ("condition_mayor_mic_rule", "debate-mic-rule-v0"),
        ("condition_muted_mic_rule", "debate-mic-rule-v2"),
        ("condition_open_mic_rule", "debate-mic-rule-v3"),
    )

    public = repr(summary).lower()
    for token in (
        "secret-123",
        "debates.example",
        "https://",
        "sealed-cross-talk-format-calendar",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_policy_debate_mic_rule_change_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_debate_mic_rule_change_digest"
    )
    assert summary.rule_change_count == ZERO
    assert summary.pass_rule_change_count == ZERO
    assert summary.watch_rule_change_count == ZERO
    assert summary.blocked_rule_change_count == ZERO
    assert summary.average_implementation_uncertainty_score == ZERO
    assert summary.average_candidate_impact_score == ZERO
    assert summary.average_outcome_relevance_score == ZERO
    assert summary.average_format_disruption_score == ZERO
    assert summary.average_source_count == ZERO
    assert summary.minimum_rule_change_lead_seconds == ZERO
    assert summary.rows == ()
    assert summary.rule_config_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_debate_mic_rule_change_digest_no_inputs"
            ),
            count=d("1.000000"),
            rule_change_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_debate_mic_rule_change_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_policy_debate_mic_rule_change_digest_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_policy_debate_mic_rule_change_digest_payload(
        summary,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["rule_change_count"] == "1.000000"
    assert payload["average_implementation_uncertainty_score"] == "0.200000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["rule_change_lead_seconds"] == "1728000.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_rule_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_policy_debate_mic_rule_change_digest_validates_contracts_and_flags() -> None:
    digest = digest_module()

    public_dataclasses = (
        digest.MarketResearchPolicyDebateMicRuleChangeDigestConfig,
        digest.MarketResearchPolicyDebateMicRuleChangeDigestInputRow,
        digest.MarketResearchPolicyDebateMicRuleChangeDigestRow,
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReasonCodeCount,
        digest.MarketResearchPolicyDebateMicRuleChangeDigestReport,
    )
    for public_dataclass in public_dataclasses:
        assert is_dataclass(public_dataclass)
        assert public_dataclass.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Bad{public_dataclass.__name__}", (public_dataclass,), {})

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("debate-mic-rule-v0"))
    with pytest.raises(ValueError, match="late_rule_change_window_seconds"):
        config(digest, late_rule_change_window_seconds=_DecimalSubclass("604800.000000"))
    with pytest.raises(ValueError, match="high_format_disruption_threshold"):
        config(digest, high_format_disruption_threshold=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_id"):
        input_row(digest, research_id=" bad")
    with pytest.raises(ValueError, match="debate_id"):
        input_row(digest, debate_id="")
    with pytest.raises(ValueError, match="rule_change_kind"):
        input_row(digest, rule_change_kind="stage-lighting")
    with pytest.raises(ValueError, match="rule_announced_at"):
        input_row(digest, rule_announced_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="last_verified_at"):
        input_row(
            digest,
            last_verified_at=_DateTimeSubclass(2026, 7, 4, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="implementation_uncertainty_score"):
        input_row(digest, implementation_uncertainty_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate_impact_score"):
        input_row(digest, candidate_impact_score=d("1.000001"))
    with pytest.raises(ValueError, match="outcome_relevance_score"):
        input_row(digest, outcome_relevance_score=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, last_verified_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_policy_debate_mic_rule_change_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_policy_debate_mic_rule_change_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, condition_id="duplicate-condition"),
                input_row(
                    digest,
                    "research.debate.mic.duplicate-2",
                    condition_id="duplicate-condition",
                ),
            ),
        )

    pass_row = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            pass_row,
            reason_codes=(
                "market_research_policy_debate_mic_rule_change_digest_pass",
                "market_research_policy_debate_mic_rule_change_digest_late_rule_change",
            ),
        )
    with pytest.raises(ValueError, match="screening_status"):
        replace(pass_row, screening_status="blocked")
    with pytest.raises(ValueError, match="redacted_public_rule_reference"):
        replace(pass_row, redacted_public_rule_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="pass_rule_change_count"):
        replace(report(digest, (input_row(digest),)), pass_rule_change_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(digest, "research.debate.mic.z", condition_id="z-condition"),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_count_ratio_score_and_seconds_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(
        digest.MarketResearchPolicyDebateMicRuleChangeDigestConfig(),
    )
    assert_decimal_public_numeric_fields(input_row(digest))
    assert_decimal_public_numeric_fields(summary)
    assert_decimal_public_numeric_fields(summary.rows[0])
    assert_decimal_public_numeric_fields(summary.reason_code_counts[0])


def test_policy_debate_mic_rule_change_payload_revalidates_tampering() -> None:
    digest = digest_module()

    summary = report(digest, (input_row(digest),))
    object.__setattr__(
        summary,
        "generated_at",
        GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )
    with pytest.raises(ValueError, match="generated_at"):
        digest.market_research_policy_debate_mic_rule_change_digest_payload(summary)

    summary = report(digest, (input_row(digest),))
    object.__setattr__(summary.rows[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        digest.market_research_policy_debate_mic_rule_change_digest_payload(summary)

    summary = report(digest, (input_row(digest),))
    object.__setattr__(summary.rows[0], "source_count", Decimal("3"))
    with pytest.raises(ValueError, match="source_count"):
        digest.market_research_policy_debate_mic_rule_change_digest_payload(summary)


def test_module_has_no_asdict_or_io_store_execution_surfaces() -> None:
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
            if node.module == "dataclasses":
                assert all(alias.name != "asdict" for alias in node.names)
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
        "asdict",
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
        "wallet",
        "broker",
        "account",
        "sign",
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
        "submit_" + "order",
        "cancel_" + "order",
        "account",
        "advice",
        "market_" + "slug",
        "payload_" + "json",
    ):
        assert forbidden not in source.lower()


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            digest.DEFAULT_MARKET_RESEARCH_POLICY_DEBATE_MIC_RULE_CHANGE_DIGEST_CONFIG_VERSION
        ),
        "late_rule_change_window_seconds": d("604800.000000"),
        "stale_verification_seconds": d("86400.000000"),
        "high_implementation_uncertainty_threshold": d("0.600000"),
        "high_candidate_impact_threshold": d("0.600000"),
        "high_outcome_relevance_threshold": d("0.600000"),
        "high_format_disruption_threshold": d("0.600000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchPolicyDebateMicRuleChangeDigestConfig(**values)


def input_row(
    digest: Any,
    research_id: str = "research.debate.mic.mayor",
    *,
    condition_id: str = "condition_mayor_mic_rule",
    jurisdiction: str = "nyc",
    debate_id: str = "debate_mayor_1",
    broadcaster: str = "public-broadcast",
    rule_change_kind: str = "rebuttal-window",
    public_rule_reference: str = "public-city-debate-rule",
    rule_announced_at: datetime | None = None,
    debate_scheduled_at: datetime | None = None,
    last_verified_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    implementation_uncertainty_score: Decimal = d("0.200000"),
    candidate_impact_score: Decimal = d("0.250000"),
    outcome_relevance_score: Decimal = d("0.210000"),
    format_disruption_score: Decimal = d("0.300000"),
    rule_config_version: str = "debate-mic-rule-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchPolicyDebateMicRuleChangeDigestInputRow(
        research_id=research_id,
        condition_id=condition_id,
        jurisdiction=jurisdiction,
        debate_id=debate_id,
        broadcaster=broadcaster,
        rule_change_kind=rule_change_kind,
        public_rule_reference=public_rule_reference,
        rule_announced_at=(
            rule_announced_at
            if rule_announced_at is not None
            else GENERATED_AT - timedelta(days=15)
        ),
        debate_scheduled_at=(
            debate_scheduled_at
            if debate_scheduled_at is not None
            else GENERATED_AT + timedelta(days=5)
        ),
        last_verified_at=(
            last_verified_at
            if last_verified_at is not None
            else GENERATED_AT - timedelta(minutes=45)
        ),
        acknowledged_at=(
            acknowledged_at
            if acknowledged_at is not _UNSET
            else GENERATED_AT - timedelta(minutes=30)
        ),
        source_count=source_count,
        implementation_uncertainty_score=implementation_uncertainty_score,
        candidate_impact_score=candidate_impact_score,
        outcome_relevance_score=outcome_relevance_score,
        format_disruption_score=format_disruption_score,
        rule_config_version=rule_config_version,
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
    return digest.build_market_research_policy_debate_mic_rule_change_digest(
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
    if isinstance(value, tuple):
        output = []
        for item in value:
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
            )
        ) and not isinstance(item, tuple):
            assert type(item) is Decimal
        assert not isinstance(item, float)
        assert not isinstance(item, int)
