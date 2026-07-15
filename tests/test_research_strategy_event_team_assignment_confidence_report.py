from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_strategy_event_team_assignment_confidence_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    return api().ResearchStrategyEventTeamAssignmentConfidenceConfig(**overrides)


def assignment(
    suffix: str,
    *,
    domain_label: str = "macro.rates",
    assigned_team_label: str = "team_macro",
    assignment_confidence_score: Decimal = d("0.900000"),
    evidence_coverage_score: Decimal = d("0.850000"),
    independence_score: Decimal = d("0.800000"),
    team_domain_fit_score: Decimal = d("0.900000"),
    workload_headroom_score: Decimal = d("0.750000"),
    calibration_memory_score: Decimal = d("0.850000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = (),
):
    return api().ResearchStrategyEventTeamAssignmentConfidenceInput(
        raw_candidate_id=f"raw-candidate-{suffix}",
        raw_market_id=f"raw-market-{suffix}",
        market_slug=f"market-slug-{suffix}",
        market_question=f"Will private question {suffix} stay hidden?",
        source_url=f"https://example.test/{suffix}?token=super-secret",
        source_text=f"private source text {suffix} with wallet order trade terms",
        domain_label=domain_label,
        assigned_team_label=assigned_team_label,
        assignment_confidence_score=assignment_confidence_score,
        evidence_coverage_score=evidence_coverage_score,
        independence_score=independence_score,
        team_domain_fit_score=team_domain_fit_score,
        workload_headroom_score=workload_headroom_score,
        calibration_memory_score=calibration_memory_score,
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_research_strategy_event_team_assignment_confidence_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_assignment_confidence_scores_events_and_validates_payload_digest() -> None:
    rows = (
        assignment("alpha"),
        assignment(
            "beta",
            domain_label="crypto",
            assigned_team_label="team_crypto",
            assignment_confidence_score=d("0.650000"),
            evidence_coverage_score=d("0.600000"),
            independence_score=d("0.700000"),
            team_domain_fit_score=d("0.650000"),
            workload_headroom_score=d("0.500000"),
            calibration_memory_score=d("0.600000"),
        ),
        assignment(
            "gamma",
            domain_label="sports.soccer",
            assigned_team_label="team_soccer",
            assignment_confidence_score=d("0.400000"),
            evidence_coverage_score=d("0.300000"),
            independence_score=d("0.350000"),
            team_domain_fit_score=d("0.450000"),
            workload_headroom_score=d("0.200000"),
            calibration_memory_score=d("0.300000"),
            reason_codes=("manual_review_gap",),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().ASSIGNMENT_CONFIDENCE_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_assignment_confidence_block"
    assert report.event_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.avg_confidence_score == d("0.597222")
    assert report.avg_evidence_coverage_score == d("0.583333")
    assert report.avg_team_domain_fit_score == d("0.666667")
    assert report.max_confidence_shortfall_score == d("0.416667")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.assignment_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert blocked.confidence_score == d("0.333333")
    assert blocked.confidence_shortfall_score == d("0.416667")
    assert blocked.reason_codes == (
        "assignment_confidence_block",
        "assignment_confidence_score_block",
        "evidence_coverage_block",
        "independence_block",
        "team_domain_fit_block",
        "workload_headroom_block",
        "calibration_memory_block",
        "input_manual_review_gap",
    )
    assert watched.confidence_score == d("0.616667")
    assert watched.reason_codes == (
        "assignment_confidence_watch",
        "assignment_confidence_score_watch",
        "evidence_coverage_watch",
        "team_domain_fit_watch",
        "workload_headroom_watch",
        "calibration_memory_watch",
    )
    assert passed.confidence_score == d("0.841667")
    assert passed.confidence_shortfall_score == d("0.000000")
    assert passed.reason_codes == ("assignment_confidence_pass",)

    payload = api().research_strategy_event_team_assignment_confidence_report_payload(
        report,
    )
    reversed_payload = (
        api().research_strategy_event_team_assignment_confidence_report_payload(
            reversed_report,
        )
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["confidence_score"] == "0.333333"
    assert (
        api().research_strategy_event_team_assignment_confidence_report_digest(report)
        == payload["derived_validation_digest"]
    )
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_assignment_confidence_is_report_only_public_safe_and_decimal_strict() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVENT_TEAM_ASSIGNMENT_CONFIDENCE_CONFIG_VERSION",
        "ASSIGNMENT_CONFIDENCE_STATUSES",
        "ResearchStrategyEventTeamAssignmentConfidenceConfig",
        "ResearchStrategyEventTeamAssignmentConfidenceInput",
        "ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount",
        "ResearchStrategyEventTeamAssignmentConfidenceReport",
        "ResearchStrategyEventTeamAssignmentConfidenceRow",
        "build_research_strategy_event_team_assignment_confidence_report",
        "research_strategy_event_team_assignment_confidence_report_digest",
        "research_strategy_event_team_assignment_confidence_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    empty = build_report()
    assert empty.status == "pass"
    assert empty.paper_queue_action == "paper_assignment_confidence_monitor"
    assert empty.reason_codes == ("assignment_confidence_no_events",)
    assert empty.event_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_code_counts == ()

    populated = build_report(assignment("safe"))
    for value in (
        config(),
        assignment("other"),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_rank")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="assignment_confidence_score must be a Decimal"):
        assignment("float-score", assignment_confidence_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="assignment_confidence_score must be a Decimal"):
        assignment("subclass-score", assignment_confidence_score=DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        assignment("naive-time", observed_at=datetime(2026, 7, 9, 10, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            assignment("tz"),
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="raw event keys must be unique"):
        build_report(assignment("dup"), assignment("dup"))
    with pytest.raises(ValueError, match="domain_label"):
        assignment("bad-domain", domain_label="market_slug")
    with pytest.raises(ValueError, match="min_watch_confidence_score"):
        config(
            min_pass_confidence_score=d("0.600000"),
            min_watch_confidence_score=d("0.700000"),
        )

    payload = module.research_strategy_event_team_assignment_confidence_report_payload(
        populated,
    )
    public = repr(payload).lower()
    forbidden = (
        "raw-candidate",
        "raw-market",
        "market-slug",
        "private question",
        "example.test",
        "super-secret",
        "source text",
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "live",
    )
    for token_value in forbidden:
        assert token_value not in public


def test_assignment_confidence_rejects_payload_leaks_and_digest_tampering() -> None:
    module = api()
    report = build_report(
        assignment(
            "sensitive",
            domain_label="weather",
            assignment_confidence_score=d("0.700000"),
            evidence_coverage_score=d("0.500000"),
        ),
    )
    payload = module.research_strategy_event_team_assignment_confidence_report_payload(
        report,
    )

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_event_team_assignment_confidence_report_payload(tampered)

    numeric = dict(payload)
    numeric["event_count"] = 1
    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        module.research_strategy_event_team_assignment_confidence_report_payload(numeric)

    for unsafe_key, unsafe_value in (
        ("candidate_id", "opaque"),
        ("market_slug", "will-fed-cut-rates"),
        ("question", "Will this resolve yes?"),
        ("source_url", "https://example.test/item"),
        ("source_text", "private source text"),
        ("dsn", "postgres://example"),
        ("wallet", "0xabc"),
        ("order_ticket", "abc"),
        ("trade", "filled"),
        ("sizing", "100"),
        ("recommendation", "buy"),
    ):
        leaked = dict(payload)
        leaked[unsafe_key] = unsafe_value
        leaked["derived_validation_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_event_team_assignment_confidence_report_payload(
                leaked,
            )


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
