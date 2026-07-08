from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_resolution_rule_dependency_health_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DEPENDENCY_HEALTH_REPORT_CONFIG_VERSION,
    ResearchEventResolutionRuleDependencyHealthAggregate,
    ResearchEventResolutionRuleDependencyHealthConfig,
    ResearchEventResolutionRuleDependencyHealthReport,
    ResearchEventResolutionRuleDependencyHealthRow,
    build_research_event_resolution_rule_dependency_health_report,
    research_event_resolution_rule_dependency_health_report_payload,
    validate_research_event_resolution_rule_dependency_health_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_rule_dependency_health_report.py"
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def aggregate(
    aggregate_key: str,
    *,
    dependent_rules: str,
    official_rule_observed_at: datetime | None = None,
    ambiguous_rules: str = "0.000000",
    impacted_packets: str = "0.000000",
    manual_urgency: str = "0.000000",
    private_context_values: tuple[str, ...] = (),
) -> ResearchEventResolutionRuleDependencyHealthAggregate:
    return ResearchEventResolutionRuleDependencyHealthAggregate(
        aggregate_key=aggregate_key,
        dependent_rule_count=d(dependent_rules),
        official_rule_observed_at=official_rule_observed_at
        if official_rule_observed_at is not None
        else GENERATED_AT - timedelta(minutes=30),
        ambiguous_rule_count=d(ambiguous_rules),
        impacted_research_packet_count=d(impacted_packets),
        manual_escalation_urgency_score=d(manual_urgency),
        private_context_values=private_context_values,
    )


def report(
    rows: tuple[ResearchEventResolutionRuleDependencyHealthAggregate, ...],
    *,
    config: ResearchEventResolutionRuleDependencyHealthConfig | None = None,
) -> ResearchEventResolutionRuleDependencyHealthReport:
    return build_research_event_resolution_rule_dependency_health_report(
        rows,
        config=config or ResearchEventResolutionRuleDependencyHealthConfig(),
        generated_at=GENERATED_AT,
    )


def test_dependency_health_rolls_up_with_public_row_numbers_and_hashes_only() -> None:
    health_report = report(
        (
            aggregate(
                "alpha-private-key",
                dependent_rules="4.000000",
                ambiguous_rules="0.000000",
                impacted_packets="1.000000",
                manual_urgency="0.100000",
                private_context_values=(
                    "raw-candidate-alpha",
                    "0xmarket-alpha",
                    "will-alpha-resolve",
                    "https://private.example.test/rule",
                    "postgresql://private-host/db",
                    "resolution_table",
                    "token-secret-alpha",
                ),
            ),
            aggregate(
                "beta-private-key",
                dependent_rules="4.000000",
                official_rule_observed_at=GENERATED_AT - timedelta(hours=12),
                ambiguous_rules="1.000000",
                impacted_packets="2.000000",
                manual_urgency="0.550000",
                private_context_values=("raw-candidate-beta", "market-slug-beta"),
            ),
            aggregate(
                "gamma-private-key",
                dependent_rules="5.000000",
                official_rule_observed_at=GENERATED_AT - timedelta(days=3),
                ambiguous_rules="4.000000",
                impacted_packets="6.000000",
                manual_urgency="0.900000",
                private_context_values=("raw-candidate-gamma", "private-token-gamma"),
            ),
        ),
    )

    assert health_report.status == "block"
    assert health_report.aggregate_row_count == d("3.000000")
    assert health_report.dependent_rule_count == d("13.000000")
    assert health_report.ambiguous_rule_count == d("5.000000")
    assert health_report.impacted_research_packet_count == d("9.000000")
    assert health_report.pass_count == ONE
    assert health_report.watch_count == ONE
    assert health_report.block_count == ONE
    assert health_report.average_official_rule_freshness_score == d("0.500000")
    assert health_report.ambiguity_pressure == d("0.384615")
    assert health_report.max_manual_escalation_urgency_score == d("0.900000")
    assert health_report.reason_codes == (
        "ambiguity_pressure_watch",
        "dependency_health_block",
        "health_row_block",
        "impacted_research_packets_block",
        "manual_escalation_urgency_block",
        "official_rule_freshness_block",
    )

    blocked, watched, passed = health_report.rows
    assert tuple(row.aggregate_row_number for row in health_report.rows) == (
        ONE,
        d("2.000000"),
        d("3.000000"),
    )
    assert blocked.aggregate_row_hash == hashlib.sha256(
        b"gamma-private-key",
    ).hexdigest()
    assert watched.aggregate_row_hash == hashlib.sha256(
        b"beta-private-key",
    ).hexdigest()
    assert passed.aggregate_row_hash == hashlib.sha256(
        b"alpha-private-key",
    ).hexdigest()
    assert (blocked.status, watched.status, passed.status) == ("block", "watch", "pass")
    assert blocked.dependent_rule_count == d("5.000000")
    assert blocked.official_rule_age_seconds == d("259200.000000")
    assert blocked.official_rule_freshness_score == ZERO
    assert blocked.ambiguity_pressure == d("0.800000")
    assert blocked.impacted_research_packet_count == d("6.000000")
    assert blocked.manual_escalation_urgency_score == d("0.900000")
    assert blocked.dependency_health_score == d("0.925000")
    assert watched.official_rule_freshness_score == d("0.500000")
    assert watched.ambiguity_pressure == d("0.250000")
    assert watched.dependency_health_score == d("0.425000")
    assert passed.status == "pass"
    assert passed.dependency_health_score == d("0.075000")

    payload = research_event_resolution_rule_dependency_health_report_payload(
        health_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert validate_research_event_resolution_rule_dependency_health_report_payload(payload)
    assert "alpha-private-key" not in encoded
    assert "beta-private-key" not in encoded
    assert "gamma-private-key" not in encoded
    assert "raw-candidate" not in encoded
    assert "0xmarket" not in encoded
    assert "market-slug" not in encoded
    assert "will-alpha-resolve" not in encoded
    assert "private.example.test" not in encoded
    assert "postgresql" not in encoded
    assert "resolution_table" not in encoded
    assert "token-secret" not in encoded
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))


def test_empty_report_blocks_with_hard_flags_and_valid_digest() -> None:
    empty_report = report(())
    payload = research_event_resolution_rule_dependency_health_report_payload(empty_report)

    assert type(empty_report) is ResearchEventResolutionRuleDependencyHealthReport
    assert empty_report.status == "block"
    assert empty_report.rows == ()
    assert empty_report.aggregate_row_count == ZERO
    assert empty_report.dependent_rule_count == ZERO
    assert empty_report.average_official_rule_freshness_score == ZERO
    assert empty_report.ambiguity_pressure == ZERO
    assert empty_report.max_manual_escalation_urgency_score == ZERO
    assert empty_report.reason_codes == ("no_resolution_rule_dependency_health_rows",)
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(empty_report.derived_validation_digest) == 64
    int(empty_report.derived_validation_digest, 16)


def test_validation_rejects_bad_numerics_flags_statuses_and_public_payloads() -> None:
    with pytest.raises(ValueError, match="watch_ambiguity_pressure"):
        ResearchEventResolutionRuleDependencyHealthConfig(
            watch_ambiguity_pressure=0.25,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="manual_escalation_urgency"):
        ResearchEventResolutionRuleDependencyHealthConfig(
            watch_manual_escalation_urgency_score=DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="block_impacted_research_packet_count"):
        ResearchEventResolutionRuleDependencyHealthConfig(
            watch_impacted_research_packet_count=d("5.000000"),
            block_impacted_research_packet_count=d("5.000000"),
        )
    with pytest.raises(ValueError, match="dependent_rule_count"):
        aggregate("bad-count", dependent_rules="1.500000")
    with pytest.raises(ValueError, match="ambiguous_rule_count"):
        aggregate(
            "bad-ambiguity",
            dependent_rules="1.000000",
            ambiguous_rules="2.000000",
        )
    with pytest.raises(ValueError, match="private_context_values"):
        aggregate(
            "bad-context",
            dependent_rules="1.000000",
            private_context_values=("candidate",),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(aggregate("bad-flag", dependent_rules="1.000000"), paper_only=False)
    with pytest.raises(ValueError, match="official_rule_observed_at"):
        report(
            (
                aggregate(
                    "future-row",
                    dependent_rules="1.000000",
                    official_rule_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )

    populated = report((aggregate("valid-row", dependent_rules="1.000000"),))
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="review")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)

    payload = research_event_resolution_rule_dependency_health_report_payload(populated)
    payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_event_resolution_rule_dependency_health_report_payload(payload)
    with pytest.raises(ValueError, match="unsafe public surface"):
        validate_research_event_resolution_rule_dependency_health_report_payload(
            {
                "market_" + "id": "secret",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
            },
        )


def test_public_dataclasses_are_frozen_decimal_only_and_source_has_no_live_surfaces() -> None:
    health_report = report((aggregate("single-row", dependent_rules="1.000000"),))
    public_classes = (
        ResearchEventResolutionRuleDependencyHealthConfig,
        ResearchEventResolutionRuleDependencyHealthAggregate,
        ResearchEventResolutionRuleDependencyHealthRow,
        ResearchEventResolutionRuleDependencyHealthReport,
    )

    assert all(is_dataclass(public_class) for public_class in public_classes)
    assert all(public_class.__dataclass_params__.frozen is True for public_class in public_classes)
    for public_class in public_classes:
        for field in fields(public_class):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_pressure")
                or field.name.endswith("_seconds")
                or field.name.endswith("_number")
            ):
                assert field.type in (Decimal, "Decimal")

    with pytest.raises(FrozenInstanceError):
        health_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        health_report.rows[0].status = "watch"  # type: ignore[misc]

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "private_token",
        "wallet",
        "order",
        "trading",
        "sizing",
        "recommendation",
    )
    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
