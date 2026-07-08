from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_information_risk_register_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def report_module():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_strategy_information_risk_register_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    candidate_label: str = "candidate-pass",
    *,
    research_area: str = "macro-policy",
    evidence_as_of: datetime = datetime(2026, 7, 8, 6, 0, tzinfo=UTC),
    evidence_age_hours: str | Decimal = "6.000000",
    aggregate_evidence_count: str | Decimal = "5.000000",
    aggregate_source_count: str | Decimal = "4.000000",
    source_reliability_score: str | Decimal = "0.950000",
    contradiction_pressure: str | Decimal = "0.050000",
    ambiguity_score: str | Decimal = "0.100000",
    team_disagreement_ratio: str | Decimal = "0.050000",
    cost_input_quality_score: str | Decimal = "0.900000",
    upstream_reason_codes: tuple[str, ...] = ("public_research_packet",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = report_module()
    return module.ResearchStrategyInformationRiskRegisterInput(
        candidate_label=candidate_label,
        research_area=research_area,
        evidence_as_of=evidence_as_of,
        evidence_age_hours=(
            evidence_age_hours
            if isinstance(evidence_age_hours, Decimal)
            else d(evidence_age_hours)
        ),
        aggregate_evidence_count=(
            aggregate_evidence_count
            if isinstance(aggregate_evidence_count, Decimal)
            else d(aggregate_evidence_count)
        ),
        aggregate_source_count=(
            aggregate_source_count
            if isinstance(aggregate_source_count, Decimal)
            else d(aggregate_source_count)
        ),
        source_reliability_score=(
            source_reliability_score
            if isinstance(source_reliability_score, Decimal)
            else d(source_reliability_score)
        ),
        contradiction_pressure=(
            contradiction_pressure
            if isinstance(contradiction_pressure, Decimal)
            else d(contradiction_pressure)
        ),
        ambiguity_score=(
            ambiguity_score
            if isinstance(ambiguity_score, Decimal)
            else d(ambiguity_score)
        ),
        team_disagreement_ratio=(
            team_disagreement_ratio
            if isinstance(team_disagreement_ratio, Decimal)
            else d(team_disagreement_ratio)
        ),
        cost_input_quality_score=(
            cost_input_quality_score
            if isinstance(cost_input_quality_score, Decimal)
            else d(cost_input_quality_score)
        ),
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**kwargs: object):
    module = report_module()
    return module.ResearchStrategyInformationRiskRegisterConfig(**kwargs)


def report(*rows: object, cfg: object | None = None):
    module = report_module()
    return module.build_research_strategy_information_risk_register_report(
        rows,
        config=(
            cfg
            if cfg is not None
            else module.ResearchStrategyInformationRiskRegisterConfig()
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def block_candidate():
    return candidate(
        "candidate-block",
        research_area="election-resolution",
        evidence_as_of=datetime(2026, 7, 6, 4, 0, tzinfo=timezone(timedelta(hours=-4))),
        evidence_age_hours="104.000000",
        aggregate_evidence_count="1.000000",
        aggregate_source_count="1.000000",
        source_reliability_score="0.250000",
        contradiction_pressure="0.750000",
        ambiguity_score="0.700000",
        team_disagreement_ratio="0.600000",
        cost_input_quality_score="0.300000",
        upstream_reason_codes=(
            "public_record_lag",
            "cost_model_gap",
            "public_record_lag",
        ),
    )


def watch_candidate():
    return candidate(
        "candidate-watch",
        evidence_age_hours="36.000000",
        aggregate_evidence_count="2.000000",
        aggregate_source_count="2.000000",
        source_reliability_score="0.650000",
        contradiction_pressure="0.300000",
        ambiguity_score="0.400000",
        team_disagreement_ratio="0.300000",
        cost_input_quality_score="0.600000",
        upstream_reason_codes=("cross_check_pending",),
    )


def test_empty_input_returns_report_only_blocked_register() -> None:
    module = report_module()

    risk_report = report()

    assert isinstance(
        risk_report,
        module.ResearchStrategyInformationRiskRegisterReport,
    )
    assert is_dataclass(risk_report)
    assert risk_report.__dataclass_params__.frozen
    assert risk_report.generated_at == GENERATED_AT
    assert risk_report.generated_at.tzinfo is UTC
    assert risk_report.config_version == (
        "research-strategy-information-risk-register-report-v0"
    )
    assert risk_report.register_status == "block"
    assert risk_report.next_step == (
        "block_report_only_research_strategy_information_risk_register"
    )
    assert risk_report.input_count == d("0.000000")
    assert risk_report.row_count == d("0.000000")
    assert risk_report.pass_count == d("0.000000")
    assert risk_report.watch_count == d("0.000000")
    assert risk_report.block_count == d("0.000000")
    assert risk_report.information_risk_score == d("0.000000")
    assert risk_report.rows == ()
    assert risk_report.reason_codes == ("information_risk_register_empty",)
    assert risk_report.reason_code_counts == (
        module.ResearchStrategyInformationRiskRegisterReasonCodeCount(
            reason_code="information_risk_register_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert risk_report.paper_only is True
    assert risk_report.report_only is True
    assert risk_report.readonly is True


def test_block_watch_and_pass_candidates_build_public_safe_register() -> None:
    risk_report = report(block_candidate(), watch_candidate(), candidate())

    assert risk_report.register_status == "block"
    assert risk_report.next_step == (
        "block_report_only_research_strategy_information_risk_register"
    )
    assert risk_report.input_count == d("3.000000")
    assert risk_report.row_count == d("3.000000")
    assert risk_report.block_count == d("1.000000")
    assert risk_report.watch_count == d("1.000000")
    assert risk_report.pass_count == d("1.000000")
    assert risk_report.evidence_freshness_risk_count == d("2.000000")
    assert risk_report.low_source_reliability_count == d("2.000000")
    assert risk_report.contradiction_pressure_count == d("2.000000")
    assert risk_report.ambiguity_count == d("2.000000")
    assert risk_report.team_disagreement_count == d("2.000000")
    assert risk_report.low_cost_input_quality_count == d("2.000000")
    assert risk_report.thin_evidence_count == d("1.000000")
    assert risk_report.thin_source_count == d("1.000000")
    assert risk_report.max_evidence_age_hours == d("104.000000")
    assert risk_report.min_source_reliability_score == d("0.250000")
    assert risk_report.max_contradiction_pressure == d("0.750000")
    assert risk_report.max_ambiguity_score == d("0.700000")
    assert risk_report.max_team_disagreement_ratio == d("0.600000")
    assert risk_report.min_cost_input_quality_score == d("0.300000")
    assert risk_report.information_risk_score == d("0.500000")

    assert tuple(row.candidate_label for row in risk_report.rows) == (
        "candidate-block",
        "candidate-watch",
        "candidate-pass",
    )

    blocked, watched, passed = risk_report.rows
    assert blocked.information_risk_status == "block"
    assert blocked.evidence_as_of == datetime(2026, 7, 6, 8, 0, tzinfo=UTC)
    assert blocked.risk_score == d("1.000000")
    assert blocked.upstream_reason_codes == (
        "cost_model_gap",
        "public_record_lag",
    )
    assert blocked.reason_codes == (
        "information_risk_evidence_freshness_block",
        "information_risk_source_reliability_block",
        "information_risk_contradiction_pressure_block",
        "information_risk_ambiguity_block",
        "information_risk_team_disagreement_block",
        "information_risk_cost_input_quality_block",
        "information_risk_thin_aggregate_evidence",
        "information_risk_thin_aggregate_sources",
    )
    assert watched.information_risk_status == "watch"
    assert watched.risk_score == d("0.500000")
    assert watched.reason_codes == (
        "information_risk_evidence_freshness_watch",
        "information_risk_source_reliability_watch",
        "information_risk_contradiction_pressure_watch",
        "information_risk_ambiguity_watch",
        "information_risk_team_disagreement_watch",
        "information_risk_cost_input_quality_watch",
    )
    assert passed.information_risk_status == "pass"
    assert passed.reason_codes == ("information_risk_register_pass",)
    assert risk_report.reason_codes == (
        "information_risk_evidence_freshness_block",
        "information_risk_evidence_freshness_watch",
        "information_risk_source_reliability_block",
        "information_risk_source_reliability_watch",
        "information_risk_contradiction_pressure_block",
        "information_risk_contradiction_pressure_watch",
        "information_risk_ambiguity_block",
        "information_risk_ambiguity_watch",
        "information_risk_team_disagreement_block",
        "information_risk_team_disagreement_watch",
        "information_risk_cost_input_quality_block",
        "information_risk_cost_input_quality_watch",
        "information_risk_thin_aggregate_evidence",
        "information_risk_thin_aggregate_sources",
        "information_risk_register_watch_present",
    )
    assert risk_report.reason_code_counts[-1] == (
        report_module().ResearchStrategyInformationRiskRegisterReasonCodeCount(
            reason_code="information_risk_register_watch_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_non_default_thresholds_can_clear_moderate_information_risk() -> None:
    cfg = config(
        watch_evidence_age_hours=d("48.000000"),
        block_evidence_age_hours=d("120.000000"),
        watch_min_source_reliability_score=d("0.600000"),
        block_min_source_reliability_score=d("0.200000"),
        watch_contradiction_pressure=d("0.350000"),
        block_contradiction_pressure=d("0.800000"),
        watch_ambiguity_score=d("0.450000"),
        block_ambiguity_score=d("0.800000"),
        watch_team_disagreement_ratio=d("0.350000"),
        block_team_disagreement_ratio=d("0.800000"),
        watch_min_cost_input_quality_score=d("0.550000"),
        block_min_cost_input_quality_score=d("0.200000"),
    )

    risk_report = report(watch_candidate(), cfg=cfg)

    assert risk_report.register_status == "pass"
    assert risk_report.rows[0].information_risk_status == "pass"
    assert risk_report.rows[0].reason_codes == ("information_risk_register_pass",)
    assert risk_report.reason_codes == ("information_risk_register_clear",)
    assert risk_report.information_risk_score == d("0.000000")


def test_rows_reason_codes_payload_and_digest_are_deterministic() -> None:
    first = watch_candidate()
    second = block_candidate()
    third = candidate("candidate-a-pass")

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.candidate_label for row in forward.rows) == (
        "candidate-block",
        "candidate-watch",
        "candidate-a-pass",
    )
    for row in forward.rows:
        assert len(row.reason_codes) == len(set(row.reason_codes))
    assert forward.reason_code_counts == tuple(
        sorted(
            forward.reason_code_counts,
            key=lambda item: forward.reason_codes.index(item.reason_code),
        ),
    )

    module = report_module()
    payload = module.research_strategy_information_risk_register_report_payload(forward)
    reverse_payload = module.research_strategy_information_risk_register_report_payload(
        reverse,
    )
    assert payload == reverse_payload
    assert json.dumps(payload, sort_keys=True)
    assert module.research_strategy_information_risk_register_report_digest(
        forward,
    ) == module.research_strategy_information_risk_register_report_digest(reverse)


def test_validation_frozen_dataclasses_decimal_inputs_and_hard_flags() -> None:
    module = report_module()
    row = candidate("candidate-frozen")
    risk_report = report(row)

    with pytest.raises(FrozenInstanceError):
        row.candidate_label = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.register_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadInput",
            (module.ResearchStrategyInformationRiskRegisterInput,),
            {},
        )
    with pytest.raises(ValueError, match="evidence_as_of must be timezone-aware"):
        candidate("bad-time", evidence_as_of=datetime(2026, 7, 8, 6, 0))
    with pytest.raises(ValueError, match="evidence_age_hours must be a Decimal"):
        candidate(
            "bad-decimal",
            evidence_age_hours=_DecimalSubclass("6.000000"),
        )
    with pytest.raises(ValueError, match="candidate_label must be a plain str"):
        candidate(_StringSubclass("bad-string"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_strategy_information_risk_register_report(
            (row,),
            config=module.ResearchStrategyInformationRiskRegisterConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="inputs must contain"):
        report("not-an-input")
    with pytest.raises(ValueError, match="duplicate candidate_label"):
        report(candidate("candidate-dupe"), candidate("candidate-dupe"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate("bad-flags", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="watch_evidence_age_hours"):
        config(
            watch_evidence_age_hours=d("90.000000"),
            block_evidence_age_hours=d("80.000000"),
        )
    with pytest.raises(ValueError, match="block_min_source_reliability_score"):
        config(
            watch_min_source_reliability_score=d("0.400000"),
            block_min_source_reliability_score=d("0.500000"),
        )

    valid_row = risk_report.rows[0]
    with pytest.raises(ValueError, match="risk_score must match"):
        replace(valid_row, risk_score=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "information_risk_register_pass",
                "information_risk_evidence_freshness_watch",
            ),
        )


def test_payload_uses_six_decimal_strings_and_public_safe_contract() -> None:
    module = report_module()
    risk_report = report(block_candidate(), watch_candidate(), candidate())

    payload = module.research_strategy_information_risk_register_report_payload(
        risk_report,
    )
    digest = module.research_strategy_information_risk_register_report_digest(
        risk_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["register_status"] == "block"
    assert payload["input_count"] == "3.000000"
    assert payload["information_risk_score"] == "0.500000"
    assert payload["rows"][0]["candidate_label"] == "candidate-block"
    assert payload["rows"][0]["evidence_age_hours"] == "104.000000"
    assert payload["rows"][0]["source_reliability_score"] == "0.250000"
    assert payload["rows"][0]["evidence_as_of"] == "2026-07-06T08:00:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.333333"
    assert len(digest) == 64
    assert int(digest, 16) >= 0

    forbidden_key_fragments = (
        "event_id",
        "event_slug",
        "market_id",
        "market_slug",
        "source_id",
        "source_url",
        "source_uri",
        "raw_identifier",
    )
    forbidden_value_fragments = (
        "buy",
        "sell",
        "position sizing",
        "private_key",
        "wallet",
        "auth_token",
    )

    def walk_payload(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert not any(fragment in lowered for fragment in forbidden_key_fragments)
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            if isinstance(value, str):
                lowered_value = value.lower()
                assert not any(
                    fragment in lowered_value
                    for fragment in forbidden_value_fragments
                )

    walk_payload(payload)

    for public_record in (
        module.ResearchStrategyInformationRiskRegisterConfig(),
        candidate("candidate-dataclass"),
        risk_report.rows[0],
        risk_report.reason_code_counts[0],
        risk_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_module_has_no_forbidden_side_effect_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
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
        "sqlite",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "auth_token",
        "authentication",
        "buy",
        "sell",
        "position sizing",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "trade",
        "live_execution",
        "urlopen",
        "connect(",
        "execute(",
        "event_id",
        "market_slug",
        "source_id",
        "source_url",
    ):
        assert forbidden not in source.lower()
