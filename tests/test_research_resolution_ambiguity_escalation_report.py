from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_ambiguity_escalation_report import (
    PUBLIC_STATUSES,
    ResearchResolutionAmbiguityEscalationConfig,
    ResearchResolutionAmbiguityEscalationInput,
    ResearchResolutionAmbiguityEscalationReasonCodeCount,
    ResearchResolutionAmbiguityEscalationReport,
    ResearchResolutionAmbiguityEscalationRow,
    build_research_resolution_ambiguity_escalation_report,
    research_resolution_ambiguity_escalation_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedAmbiguityShape:
    resolution_area: str
    affected_market_count: Decimal
    rule_ambiguity_score: Decimal
    source_disagreement_score: Decimal
    authoritative_evidence_age_seconds: Decimal
    manual_review_item_count: Decimal
    available_reviewer_count: Decimal
    seconds_until_required_recheck: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionAmbiguityEscalationConfig:
    values = {
        "fresh_authoritative_evidence_age_seconds": d("3600"),
        "stale_authoritative_evidence_age_seconds": d("86400"),
        "manual_review_capacity_per_reviewer": d("4"),
        "comfortable_recheck_window_seconds": d("86400"),
        "watch_escalation_pressure": d("0.350000"),
        "block_escalation_pressure": d("0.700000"),
        "rule_ambiguity_weight": d("0.250000"),
        "source_disagreement_weight": d("0.250000"),
        "stale_authoritative_evidence_weight": d("0.200000"),
        "manual_review_burden_weight": d("0.150000"),
        "recheck_urgency_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchResolutionAmbiguityEscalationConfig(**values)


def ambiguity_item(
    resolution_area: str = "weather",
    *,
    affected_market_count: Decimal = d("3"),
    rule_ambiguity_score: Decimal = d("0.100000"),
    source_disagreement_score: Decimal = d("0.050000"),
    authoritative_evidence_age_seconds: Decimal = d("1800"),
    manual_review_item_count: Decimal = d("1"),
    available_reviewer_count: Decimal = d("4"),
    seconds_until_required_recheck: Decimal = d("172800"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionAmbiguityEscalationInput:
    return ResearchResolutionAmbiguityEscalationInput(
        resolution_area=resolution_area,
        affected_market_count=affected_market_count,
        rule_ambiguity_score=rule_ambiguity_score,
        source_disagreement_score=source_disagreement_score,
        authoritative_evidence_age_seconds=authoritative_evidence_age_seconds,
        manual_review_item_count=manual_review_item_count,
        available_reviewer_count=available_reviewer_count,
        seconds_until_required_recheck=seconds_until_required_recheck,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionAmbiguityEscalationConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionAmbiguityEscalationReport:
    return build_research_resolution_ambiguity_escalation_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def public_payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_input_returns_block_report_only_ambiguity_escalation() -> None:
    ambiguity_report = report(())

    assert type(ambiguity_report) is ResearchResolutionAmbiguityEscalationReport
    assert ambiguity_report.generated_at == GENERATED_AT
    assert ambiguity_report.config_version == "research-resolution-ambiguity-escalation-v0"
    assert ambiguity_report.resolution_area_count == d("0")
    assert ambiguity_report.affected_market_count == d("0")
    assert ambiguity_report.pass_count == d("0")
    assert ambiguity_report.watch_count == d("0")
    assert ambiguity_report.block_count == d("0")
    assert ambiguity_report.average_escalation_pressure is None
    assert ambiguity_report.max_authoritative_evidence_age_seconds == d("0.000000")
    assert ambiguity_report.status == "block"
    assert ambiguity_report.reason_codes == ("no_resolution_ambiguity_inputs",)
    assert ambiguity_report.reason_code_counts == (
        ResearchResolutionAmbiguityEscalationReasonCodeCount(
            reason_code="no_resolution_ambiguity_inputs",
            count=d("1"),
        ),
    )
    assert ambiguity_report.rows == ()
    assert len(ambiguity_report.derived_validation_digest) == 64
    assert ambiguity_report.paper_only is True
    assert ambiguity_report.report_only is True
    assert ambiguity_report.readonly is True


def test_report_scores_rule_source_staleness_manual_burden_and_recheck_urgency() -> None:
    ambiguity_report = report(
        (
            ambiguity_item(
                "sports",
                affected_market_count=d("4"),
                rule_ambiguity_score=d("0.900000"),
                source_disagreement_score=d("0.800000"),
                authoritative_evidence_age_seconds=d("172800"),
                manual_review_item_count=d("12"),
                available_reviewer_count=d("1"),
                seconds_until_required_recheck=d("0"),
                reason_codes=("committee_escalation",),
            ),
            ambiguity_item(
                "macro_rates",
                affected_market_count=d("2"),
                rule_ambiguity_score=d("0.500000"),
                source_disagreement_score=d("0.400000"),
                authoritative_evidence_age_seconds=d("43200"),
                manual_review_item_count=d("6"),
                available_reviewer_count=d("3"),
                seconds_until_required_recheck=d("43200"),
            ),
            ambiguity_item("weather"),
        ),
    )

    assert PUBLIC_STATUSES == ("pass", "watch", "block")
    assert ambiguity_report.status == "block"
    assert ambiguity_report.resolution_area_count == d("3")
    assert ambiguity_report.affected_market_count == d("9")
    assert ambiguity_report.pass_count == d("1")
    assert ambiguity_report.watch_count == d("1")
    assert ambiguity_report.block_count == d("1")
    assert ambiguity_report.average_escalation_pressure == d("0.482292")
    assert ambiguity_report.max_authoritative_evidence_age_seconds == d("172800.000000")

    assert tuple(row.resolution_area for row in ambiguity_report.rows) == (
        "macro_rates",
        "sports",
        "weather",
    )
    watch_row, block_row, pass_row = ambiguity_report.rows
    assert type(block_row) is ResearchResolutionAmbiguityEscalationRow
    assert pass_row.stale_authoritative_evidence_pressure == d("0.000000")
    assert pass_row.manual_review_burden == d("0.062500")
    assert pass_row.recheck_urgency == d("0.000000")
    assert pass_row.escalation_pressure == d("0.046875")
    assert pass_row.status == "pass"
    assert watch_row.stale_authoritative_evidence_pressure == d("0.500000")
    assert watch_row.manual_review_burden == d("0.500000")
    assert watch_row.recheck_urgency == d("0.500000")
    assert watch_row.escalation_pressure == d("0.475000")
    assert watch_row.status == "watch"
    assert block_row.stale_authoritative_evidence_pressure == d("1.000000")
    assert block_row.manual_review_burden == d("1.000000")
    assert block_row.recheck_urgency == d("1.000000")
    assert block_row.escalation_pressure == d("0.925000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "authoritative_evidence_stale",
        "input_committee_escalation",
        "manual_review_burden_block",
        "recheck_urgency_block",
        "resolution_ambiguity_escalation_block",
        "rule_ambiguity_block",
        "source_disagreement_block",
    )
    assert ambiguity_report.reason_code_counts == tuple(
        sorted(ambiguity_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedAmbiguityShape(
            resolution_area="macro_rates",
            affected_market_count=d("2"),
            rule_ambiguity_score=d("0.500000"),
            source_disagreement_score=d("0.400000"),
            authoritative_evidence_age_seconds=d("43200"),
            manual_review_item_count=d("6"),
            available_reviewer_count=d("3"),
            seconds_until_required_recheck=d("43200"),
            reason_codes=("manual_review_queue",),
        ),
        ambiguity_item("weather"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_resolution_ambiguity_escalation_report_payload(first_report)
    second_payload = research_resolution_ambiguity_escalation_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["escalation_pressure"] == "0.475000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "market_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "source_reference",
            "raw_market",
            "raw_source",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="rule_ambiguity_weight"):
        config(rule_ambiguity_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_escalation_pressure"):
        config(block_escalation_pressure=d("0.300000"))
    with pytest.raises(ValueError, match="fresh_authoritative_evidence_age_seconds"):
        config(fresh_authoritative_evidence_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_disagreement_weight"):
        config(source_disagreement_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((ambiguity_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (ambiguity_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="resolution_area"):
        ambiguity_item(resolution_area="market_slug_like")
    with pytest.raises(ValueError, match="resolution_area"):
        ambiguity_item(resolution_area="question text")
    with pytest.raises(ValueError, match="rule_ambiguity_score"):
        ambiguity_item(rule_ambiguity_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="affected_market_count"):
        ambiguity_item(affected_market_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchResolutionAmbiguityEscalationInput(
            resolution_area="weather",
            affected_market_count=d("1"),
            rule_ambiguity_score=d("0.100000"),
            source_disagreement_score=d("0.050000"),
            authoritative_evidence_age_seconds=d("1800"),
            manual_review_item_count=d("1"),
            available_reviewer_count=d("1"),
            seconds_until_required_recheck=d("3600"),
            paper_only=False,
        )
    bad_payload = research_resolution_ambiguity_escalation_report_payload(report((ambiguity_item(),)))
    bad_payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        research_resolution_ambiguity_escalation_report_payload(bad_payload)


@pytest.mark.parametrize(
    ("unsafe_key", "unsafe_value"),
    (
        ("candidate_id", "candidate_123"),
        ("candidate_ids", ["candidate_123"]),
        ("raw_candidate", "candidate_123"),
        ("question", "will this resolve yes"),
        ("database_dsn", "postgres://readonly.invalid/reporting"),
        ("table_name", "resolution_markets"),
        ("position_size", "1.000000"),
        ("recommendation", "watch"),
    ),
)
def test_public_dict_payload_rejects_raw_private_and_action_surfaces(
    unsafe_key: str,
    unsafe_value: object,
) -> None:
    payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        unsafe_key: unsafe_value,
    }

    with pytest.raises(ValueError, match="unsafe|action"):
        research_resolution_ambiguity_escalation_report_payload(payload)


@pytest.mark.parametrize("bad_numeric", (1, 0.5))
def test_public_dict_payload_rejects_non_decimal_numeric_values(
    bad_numeric: object,
) -> None:
    payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "safe_metric": bad_numeric,
    }

    with pytest.raises(ValueError, match="numeric|float"):
        research_resolution_ambiguity_escalation_report_payload(payload)


def test_public_dict_payload_requires_validation_digest() -> None:
    payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_resolution_ambiguity_escalation_report_payload(payload)


def test_public_dict_payload_serializes_decimal_values_as_strings() -> None:
    payload_without_digest = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "safe_metric": "1.500000",
    }
    payload = research_resolution_ambiguity_escalation_report_payload(
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "safe_metric": d("1.500000"),
            "derived_validation_digest": public_payload_digest(payload_without_digest),
        },
    )

    assert payload["safe_metric"] == "1.500000"


def test_report_objects_are_frozen_and_module_has_no_live_surfaces() -> None:
    ambiguity_report = report((ambiguity_item(),))

    with pytest.raises(FrozenInstanceError):
        ambiguity_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        replace(ambiguity_report.rows[0]).status = "block"  # type: ignore[misc]

    module_text = Path(
        "src/polymarket_alpha_lab/research_resolution_ambiguity_escalation_report.py",
    ).read_text(encoding="utf-8").lower()
    assert "requests" not in module_text
    assert "psycopg" not in module_text
    assert "supabase" not in module_text
    assert "websocket" not in module_text
    assert "wallet" not in module_text
    assert "private_key" not in module_text
    assert "api_key" not in module_text
    assert "place_order" not in module_text
    assert "live_trading" not in module_text


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_payload_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_payload_values(child))
    return (value,)
