from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_market_specificity_digest import (
    DEFAULT_PROBABILITY_EVENT_MARKET_SPECIFICITY_DIGEST_CONFIG_VERSION,
    ProbabilityEventMarketSpecificityDigestConfig,
    ProbabilityEventMarketSpecificityDigestFacts,
    ProbabilityEventMarketSpecificityDigestReasonCodeCount,
    ProbabilityEventMarketSpecificityDigestReport,
    ProbabilityEventMarketSpecificityDigestRow,
    build_probability_event_market_specificity_digest,
    probability_event_market_specificity_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_market_specificity_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ProbabilityEventMarketSpecificityDigestConfig:
    values = {
        "config_version": (
            DEFAULT_PROBABILITY_EVENT_MARKET_SPECIFICITY_DIGEST_CONFIG_VERSION
        ),
        "question_specificity_pass_score": d("0.800000"),
        "question_specificity_block_score": d("0.500000"),
        "time_clarity_pass_score": d("0.800000"),
        "time_clarity_block_score": d("0.500000"),
        "measurable_threshold_pass_score": d("0.800000"),
        "measurable_threshold_block_score": d("0.500000"),
        "revision_risk_watch_score": d("0.500000"),
        "revision_risk_block_score": d("0.800000"),
        "dispute_risk_watch_score": d("0.500000"),
        "dispute_risk_block_score": d("0.800000"),
        "min_exact_outcome_label_count": d("2.000000"),
    }
    values.update(overrides)
    return ProbabilityEventMarketSpecificityDigestConfig(**values)


def facts(
    redacted_public_reference: str = "market-alpha-redacted",
    *,
    question_specificity_score: Decimal = d("0.950000"),
    resolution_source_reference: str | None = "resolution-source-redacted",
    outcome_labels: tuple[str, ...] = ("No", "Yes"),
    close_time_clarity_score: Decimal = d("1.000000"),
    resolution_time_clarity_score: Decimal = d("0.950000"),
    measurable_threshold_score: Decimal = d("0.900000"),
    ambiguity_flags: tuple[str, ...] = (),
    revision_risk_score: Decimal = d("0.100000"),
    dispute_risk_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventMarketSpecificityDigestFacts:
    return ProbabilityEventMarketSpecificityDigestFacts(
        redacted_public_reference=redacted_public_reference,
        question_specificity_score=question_specificity_score,
        resolution_source_reference=resolution_source_reference,
        outcome_labels=outcome_labels,
        close_time_clarity_score=close_time_clarity_score,
        resolution_time_clarity_score=resolution_time_clarity_score,
        measurable_threshold_score=measurable_threshold_score,
        ambiguity_flags=ambiguity_flags,
        revision_risk_score=revision_risk_score,
        dispute_risk_score=dispute_risk_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ProbabilityEventMarketSpecificityDigestFacts,
    cfg: ProbabilityEventMarketSpecificityDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ProbabilityEventMarketSpecificityDigestReport:
    return build_probability_event_market_specificity_digest(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if isinstance(value, (Decimal, datetime, float)):
        pytest.fail(f"payload contains runtime-only value: {value!r}")
    if type(value) is int:
        pytest.fail(f"payload contains int instead of Decimal string: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert "raw_question" not in lowered_key
            assert "market_slug" not in lowered_key
            assert "market_id" not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_specific_event_passes_with_public_decimal_payload() -> None:
    digest = report(facts("market-clear-redacted"))

    assert isinstance(digest, ProbabilityEventMarketSpecificityDigestReport)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == (
        DEFAULT_PROBABILITY_EVENT_MARKET_SPECIFICITY_DIGEST_CONFIG_VERSION
    )
    assert digest.status == "pass"
    assert digest.market_count == d("1.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.missing_outcome_label_count == ZERO
    assert digest.missing_resolution_source_count == ZERO
    assert digest.ambiguity_flag_count == ZERO
    assert digest.revision_or_dispute_risk_count == ZERO
    assert digest.reason_codes == ("probability_event_market_specificity_passed",)
    assert digest.reason_code_counts == (
        ProbabilityEventMarketSpecificityDigestReasonCodeCount(
            "probability_event_market_specificity_passed",
            d("1.000000"),
        ),
    )

    row = digest.market_rows[0]
    assert isinstance(row, ProbabilityEventMarketSpecificityDigestRow)
    assert row.redacted_public_reference == "market-clear-redacted"
    assert row.status == "pass"
    assert row.outcome_label_count == d("2.000000")
    assert row.outcome_labels == ("No", "Yes")
    assert row.reason_codes == ("probability_event_market_specificity_passed",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    payload = probability_event_market_specificity_digest_payload(digest)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["market_count"] == "1.000000"
    assert payload["market_rows"][0]["question_specificity_score"] == "0.950000"
    assert payload["market_rows"][0]["outcome_label_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "market_slug" not in json.dumps(payload, sort_keys=True)
    assert "market_id" not in json.dumps(payload, sort_keys=True)
    assert "raw_question" not in json.dumps(payload, sort_keys=True)
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_vague_question_watches_without_blocking() -> None:
    digest = report(
        facts(
            "market-vague-redacted",
            question_specificity_score=d("0.650000"),
        ),
    )

    assert digest.status == "watch"
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == ZERO
    assert digest.reason_codes == (
        "probability_event_market_specificity_question_vague_watch",
    )
    assert digest.market_rows[0].status == "watch"
    assert digest.market_rows[0].reason_codes == (
        "probability_event_market_specificity_question_vague_watch",
    )


def test_ambiguity_and_revision_dispute_risk_block_analysis() -> None:
    digest = report(
        facts(
            "market-ambiguous-redacted",
            ambiguity_flags=("ambiguous_settlement_boundary",),
            revision_risk_score=d("0.900000"),
            dispute_risk_score=d("0.850000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.blocked_count == d("1.000000")
    assert digest.ambiguity_flag_count == d("1.000000")
    assert digest.revision_or_dispute_risk_count == d("1.000000")
    assert digest.reason_codes == (
        "probability_event_market_specificity_ambiguity_flagged_blocked",
        "probability_event_market_specificity_dispute_risk_blocked",
        "probability_event_market_specificity_revision_risk_blocked",
    )
    assert digest.market_rows[0].status == "blocked"


def test_missing_outcome_labels_block_with_aggregate_count() -> None:
    digest = report(facts("market-no-outcomes-redacted", outcome_labels=()))

    assert digest.status == "blocked"
    assert digest.missing_outcome_label_count == d("1.000000")
    assert digest.reason_codes == (
        "probability_event_market_specificity_outcome_labels_missing_blocked",
    )
    assert digest.market_rows[0].outcome_labels == ()
    assert digest.market_rows[0].outcome_label_count == ZERO


def test_missing_resolution_source_blocks_with_aggregate_count() -> None:
    digest = report(
        facts("market-no-source-redacted", resolution_source_reference=None),
    )

    assert digest.status == "blocked"
    assert digest.missing_resolution_source_count == d("1.000000")
    assert digest.reason_codes == (
        "probability_event_market_specificity_resolution_source_missing_blocked",
    )
    assert digest.market_rows[0].resolution_source_reference is None


def test_deterministic_sorting_and_reason_code_counts() -> None:
    digest = report(
        facts("market-zeta-redacted"),
        facts(
            "market-beta-redacted",
            resolution_source_reference=None,
        ),
        facts(
            "market-alpha-redacted",
            question_specificity_score=d("0.650000"),
        ),
    )

    assert tuple(row.redacted_public_reference for row in digest.market_rows) == (
        "market-beta-redacted",
        "market-alpha-redacted",
        "market-zeta-redacted",
    )
    assert tuple(row.status for row in digest.market_rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert digest.reason_codes == (
        "probability_event_market_specificity_question_vague_watch",
        "probability_event_market_specificity_resolution_source_missing_blocked",
    )
    assert digest.reason_code_counts == (
        ProbabilityEventMarketSpecificityDigestReasonCodeCount(
            "probability_event_market_specificity_passed",
            d("1.000000"),
        ),
        ProbabilityEventMarketSpecificityDigestReasonCodeCount(
            "probability_event_market_specificity_question_vague_watch",
            d("1.000000"),
        ),
        ProbabilityEventMarketSpecificityDigestReasonCodeCount(
            "probability_event_market_specificity_resolution_source_missing_blocked",
            d("1.000000"),
        ),
    )


def test_hard_flags_frozen_dataclasses_and_datetime_validation() -> None:
    digest = report(facts("market-flags-redacted"))

    for public_type in (
        ProbabilityEventMarketSpecificityDigestConfig,
        ProbabilityEventMarketSpecificityDigestFacts,
        ProbabilityEventMarketSpecificityDigestRow,
        ProbabilityEventMarketSpecificityDigestReasonCodeCount,
        ProbabilityEventMarketSpecificityDigestReport,
    ):
        assert is_dataclass(public_type)

    for public_record in (
        config(),
        facts("market-record-redacted"),
        digest.market_rows[0],
        digest.reason_code_counts[0],
        digest,
    ):
        assert public_record.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        digest.status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        facts("market-flag-false-redacted", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(facts("market-flag-report-redacted"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)

    generated_at = datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    assert report(facts(), generated_at=generated_at).generated_at == GENERATED_AT
    with pytest.raises(ValueError, match="generated_at"):
        report(facts(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            facts(),
            generated_at=datetime(2026, 7, 7, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(facts(), generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))


def test_no_floats_or_int_public_numbers_are_accepted_or_emitted() -> None:
    with pytest.raises(ValueError, match="question_specificity_score"):
        facts(question_specificity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="revision_risk_score"):
        facts(revision_risk_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="question_specificity_pass_score"):
        config(question_specificity_pass_score=0.8)
    with pytest.raises(ValueError, match="dispute_risk_score"):
        facts(dispute_risk_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="revision_risk_score"):
        facts(revision_risk_score=Decimal("NaN"))

    digest = report(facts("market-decimal-redacted"))
    for item in (digest, *digest.market_rows, *digest.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
    assert_no_runtime_numbers(probability_event_market_specificity_digest_payload(digest))


def test_unsafe_and_unredacted_public_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="redacted"):
        facts(redacted_public_reference="market-alpha")
    with pytest.raises(ValueError, match="redacted"):
        facts(resolution_source_reference="source-0xabc-redacted")
    with pytest.raises(ValueError, match="unsafe"):
        facts(redacted_public_reference="market-wallet-redacted")
    with pytest.raises(ValueError, match="unsafe"):
        facts(outcome_labels=("Cancel", "Yes"))
    with pytest.raises(ValueError, match="canonical"):
        facts(ambiguity_flags=("ambiguous_z", "ambiguous_a"))
    with pytest.raises(ValueError, match="duplicate"):
        facts(outcome_labels=("Yes", "Yes"))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            facts("market-dupe-redacted"),
            facts("market-dupe-redacted"),
        )

    digest = report(facts("market-tamper-redacted"))
    object.__setattr__(
        digest.market_rows[0],
        "redacted_public_reference",
        "market-wallet-redacted",
    )
    with pytest.raises(ValueError, match="unsafe"):
        probability_event_market_specificity_digest_payload(digest)


def test_pure_boundary_has_no_io_network_or_mutation_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "network",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "market_slug",
        "market_id",
        "raw_question",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
