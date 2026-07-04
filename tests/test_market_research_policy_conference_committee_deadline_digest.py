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


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_policy_conference_committee_deadline_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_conference_committee_deadline_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_policy_conference_committee_deadline_digest_reduces_rows_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.conference.energy-permit",
                condition_id="condition_energy_conference",
                bill_key="bill-energy-permitting",
                committee_key="conference-energy-permitting",
                chamber_pair="house-senate",
                deadline_rule_key="conference-report-deadline",
                conference_deadline_at=GENERATED_AT + timedelta(hours=10),
                last_committee_action_at=GENERATED_AT - timedelta(days=2),
                source_count=d("1.000000"),
                independent_source_count=d("1.000000"),
                confidence=d("0.650000"),
                amendment_conflict_score=d("0.870000"),
                market_relevance_score=d("0.920000"),
                source_config_version="conference-deadline-v2",
            ),
            input_row(
                digest,
                "research.conference.bank-capital",
                condition_id="condition_bank_conference",
                bill_key="bill-bank-capital",
                committee_key="conference-bank-capital",
                chamber_pair="house-senate",
                deadline_rule_key="conference-report-deadline",
                conference_deadline_at=GENERATED_AT + timedelta(hours=30),
                last_committee_action_at=GENERATED_AT - timedelta(hours=2),
                source_count=d("2.000000"),
                independent_source_count=d("2.000000"),
                confidence=d("0.800000"),
                amendment_conflict_score=d("0.650000"),
                market_relevance_score=d("0.640000"),
                source_config_version="conference-deadline-v1",
            ),
            input_row(
                digest,
                "research.conference.consumer-fees",
                condition_id="condition_consumer_conference",
                bill_key="bill-consumer-fees",
                committee_key="conference-consumer-fees",
                chamber_pair="house-senate",
                deadline_rule_key="conference-report-deadline",
                conference_deadline_at=GENERATED_AT + timedelta(days=5),
                last_committee_action_at=GENERATED_AT - timedelta(minutes=30),
                source_count=d("3.000000"),
                independent_source_count=d("3.000000"),
                confidence=d("0.900000"),
                amendment_conflict_score=d("0.200000"),
                market_relevance_score=d("0.210000"),
                source_config_version="conference-deadline-v0",
            ),
            input_row(
                digest,
                "research.conference.expired-tax",
                condition_id="condition_expired_conference",
                bill_key="bill-expired-tax",
                committee_key="conference-expired-tax",
                chamber_pair="house-senate",
                deadline_rule_key="conference-report-deadline",
                conference_deadline_at=GENERATED_AT - timedelta(hours=4),
                last_committee_action_at=GENERATED_AT - timedelta(hours=4),
                source_count=d("2.000000"),
                independent_source_count=d("2.000000"),
                confidence=d("0.800000"),
                amendment_conflict_score=d("0.400000"),
                market_relevance_score=d("0.800000"),
                source_config_version="conference-deadline-v3",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_POLICY_CONFERENCE_COMMITTEE_DEADLINE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_conference_committee_deadline_digest"
    )
    assert summary.input_count == d("4.000000")
    assert summary.row_count == d("4.000000")
    assert summary.ready_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.blocked_count == d("2.000000")
    assert summary.high_amendment_conflict_count == d("2.000000")
    assert summary.high_market_relevance_count == d("3.000000")
    assert summary.near_deadline_count == d("2.000000")
    assert summary.stale_action_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.confidence_gap_count == d("1.000000")
    assert summary.past_deadline_count == d("1.000000")
    assert summary.average_confidence == d("0.787500")
    assert summary.average_amendment_conflict_score == d("0.530000")
    assert summary.average_market_relevance_score == d("0.642500")
    assert summary.average_source_count == d("2.000000")
    assert summary.average_independent_source_count == d("2.000000")
    assert summary.minimum_seconds_until_deadline == d("-14400.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.bill_key, row.research_key) for row in summary.rows) == (
        ("bill-expired-tax", "research.conference.expired-tax"),
        ("bill-energy-permitting", "research.conference.energy-permit"),
        ("bill-bank-capital", "research.conference.bank-capital"),
        ("bill-consumer-fees", "research.conference.consumer-fees"),
    )

    expired = summary.rows[0]
    assert expired.deadline_status == "blocked"
    assert expired.seconds_until_deadline == d("-14400.000000")
    assert expired.action_age_seconds == d("14400.000000")
    assert expired.reason_codes == (
        "market_research_policy_conference_committee_deadline_digest_high_market_relevance",
        "market_research_policy_conference_committee_deadline_digest_past_deadline",
    )

    energy = summary.rows[1]
    assert energy.deadline_status == "blocked"
    assert energy.seconds_until_deadline == d("36000.000000")
    assert energy.action_age_seconds == d("172800.000000")
    assert energy.reason_codes == (
        "market_research_policy_conference_committee_deadline_digest_high_amendment_conflict",
        "market_research_policy_conference_committee_deadline_digest_high_market_relevance",
        "market_research_policy_conference_committee_deadline_digest_near_deadline",
        "market_research_policy_conference_committee_deadline_digest_stale_action",
        "market_research_policy_conference_committee_deadline_digest_thin_sources",
        "market_research_policy_conference_committee_deadline_digest_confidence_gap",
    )

    bank = summary.rows[2]
    assert bank.deadline_status == "watch"
    assert bank.seconds_until_deadline == d("108000.000000")
    assert bank.reason_codes == (
        "market_research_policy_conference_committee_deadline_digest_high_amendment_conflict",
        "market_research_policy_conference_committee_deadline_digest_high_market_relevance",
        "market_research_policy_conference_committee_deadline_digest_near_deadline",
    )

    consumer = summary.rows[3]
    assert consumer.deadline_status == "ready"
    assert consumer.reason_codes == (
        "market_research_policy_conference_committee_deadline_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_"
                "high_amendment_conflict"
            ),
            count=d("2.000000"),
            row_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_"
                "high_market_relevance"
            ),
            count=d("3.000000"),
            row_ratio=d("0.750000"),
        ),
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_"
                "near_deadline"
            ),
            count=d("2.000000"),
            row_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_"
                "stale_action"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_"
                "thin_sources"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_"
                "confidence_gap"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_"
                "past_deadline"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_ready"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.source_config_versions == (
        ("condition_bank_conference", "conference-deadline-v1"),
        ("condition_consumer_conference", "conference-deadline-v0"),
        ("condition_energy_conference", "conference-deadline-v2"),
        ("condition_expired_conference", "conference-deadline-v3"),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "private",
    ):
        assert token not in public


def test_empty_policy_conference_committee_deadline_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_conference_committee_deadline_digest"
    )
    assert summary.input_count == ZERO
    assert summary.row_count == ZERO
    assert summary.ready_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.blocked_count == ZERO
    assert summary.average_confidence == ZERO
    assert summary.average_amendment_conflict_score == ZERO
    assert summary.average_market_relevance_score == ZERO
    assert summary.average_source_count == ZERO
    assert summary.average_independent_source_count == ZERO
    assert summary.minimum_seconds_until_deadline == ZERO
    assert summary.rows == ()
    assert summary.source_config_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_conference_committee_deadline_digest_no_inputs"
            ),
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_conference_committee_deadline_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_policy_conference_committee_deadline_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_policy_conference_committee_deadline_digest_payload(
        summary,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["row_count"] == "1.000000"
    assert payload["average_confidence"] == "0.900000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["seconds_until_deadline"] == "432000.000000"
    assert payload["rows"][0]["conference_deadline_at"] == (
        "2026-07-09T16:00:00+00:00"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(
        isinstance(value, int) and not isinstance(value, bool)
        for value in walk_values(payload)
    )


def test_policy_conference_committee_deadline_validates_contracts_and_flags() -> None:
    digest = digest_module()

    assert (
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyConferenceCommitteeDeadlineInputRow
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestRow
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestReport
        .__dataclass_params__
        .frozen
    )

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("conference-deadline-v0"))
    with pytest.raises(ValueError, match="near_deadline_seconds"):
        config(digest, near_deadline_seconds=_DecimalSubclass("172800.000000"))
    with pytest.raises(ValueError, match="high_amendment_conflict_threshold"):
        config(digest, high_amendment_conflict_threshold=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=" bad")
    with pytest.raises(ValueError, match="bill_key"):
        input_row(digest, bill_key="private-bill")
    with pytest.raises(ValueError, match="conference_deadline_at"):
        input_row(digest, conference_deadline_at=datetime(2026, 7, 9, 16, 0))
    with pytest.raises(ValueError, match="last_committee_action_at"):
        input_row(
            digest,
            last_committee_action_at=_DateTimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="independent_source_count"):
        input_row(digest, independent_source_count=d("4.000000"))
    with pytest.raises(ValueError, match="confidence"):
        input_row(digest, confidence=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="amendment_conflict_score"):
        input_row(digest, amendment_conflict_score=d("1.000001"))
    with pytest.raises(ValueError, match="market_relevance_score"):
        input_row(digest, market_relevance_score=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (
                input_row(
                    digest,
                    last_committee_action_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_policy_conference_committee_deadline_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        digest.build_market_research_policy_conference_committee_deadline_digest(
            (),
            config=config(digest),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig,),
            {},
        )


def test_policy_conference_committee_deadline_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, condition_id="duplicate-condition"),
                input_row(
                    digest,
                    "research.conference.duplicate-2",
                    condition_id="duplicate-condition",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_policy_conference_committee_deadline_digest_ready",
                "market_research_policy_conference_committee_deadline_digest_past_deadline",
            ),
        )
    with pytest.raises(ValueError, match="deadline_status"):
        replace(ready, deadline_status="blocked")

    with pytest.raises(ValueError, match="ready_count"):
        replace(report(digest, (input_row(digest),)), ready_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(digest, "research.conference.z", condition_id="z-condition"),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_count_ratio_score_and_seconds_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(
        digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig(),
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


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            digest.DEFAULT_MARKET_RESEARCH_POLICY_CONFERENCE_COMMITTEE_DEADLINE_DIGEST_CONFIG_VERSION
        ),
        "near_deadline_seconds": d("172800.000000"),
        "stale_action_seconds": d("86400.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_confidence": d("0.700000"),
        "high_amendment_conflict_threshold": d("0.600000"),
        "high_market_relevance_threshold": d("0.600000"),
    }
    values.update(overrides)
    return digest.MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig(
        **values,
    )


def input_row(
    digest: Any,
    research_key: str = "research.conference.consumer-fees",
    *,
    condition_id: str = "condition_consumer_conference",
    bill_key: str = "bill-consumer-fees",
    committee_key: str = "conference-consumer-fees",
    chamber_pair: str = "house-senate",
    deadline_rule_key: str = "conference-report-deadline",
    conference_deadline_at: datetime | None = None,
    last_committee_action_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.900000"),
    amendment_conflict_score: Decimal = d("0.200000"),
    market_relevance_score: Decimal = d("0.210000"),
    source_config_version: str = "conference-deadline-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchPolicyConferenceCommitteeDeadlineInputRow(
        research_key=research_key,
        condition_id=condition_id,
        bill_key=bill_key,
        committee_key=committee_key,
        chamber_pair=chamber_pair,
        deadline_rule_key=deadline_rule_key,
        conference_deadline_at=(
            conference_deadline_at
            if conference_deadline_at is not None
            else GENERATED_AT + timedelta(days=5)
        ),
        last_committee_action_at=(
            last_committee_action_at
            if last_committee_action_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        source_count=source_count,
        independent_source_count=independent_source_count,
        confidence=confidence,
        amendment_conflict_score=amendment_conflict_score,
        market_relevance_score=market_relevance_score,
        source_config_version=source_config_version,
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
    return digest.build_market_research_policy_conference_committee_deadline_digest(
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
                "score",
                "seconds",
            )
        ) and not isinstance(item, (tuple, list, dict)):
            assert type(item) is Decimal
        assert not isinstance(item, float)
        assert not isinstance(item, int)
