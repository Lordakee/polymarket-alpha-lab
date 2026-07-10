from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_team_specialist_thesis_divergence_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_team_specialist_thesis_divergence_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 9, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_THESIS_DIVERGENCE_CONFIG_VERSION
        ),
        "specialist_gap_weight": d("0.400000"),
        "consensus_gap_weight": d("0.250000"),
        "evidence_gap_weight": d("0.200000"),
        "resolution_gap_weight": d("0.150000"),
        "pass_specialist_gap_ceiling": d("0.100000"),
        "block_specialist_gap_floor": d("0.300000"),
        "pass_consensus_gap_ceiling": d("0.150000"),
        "block_consensus_gap_floor": d("0.350000"),
        "pass_evidence_gap_ceiling": d("0.200000"),
        "block_evidence_gap_floor": d("0.500000"),
        "pass_resolution_gap_ceiling": d("0.200000"),
        "block_resolution_gap_floor": d("0.500000"),
        "pass_divergence_score_ceiling": d("0.150000"),
        "block_divergence_score_floor": d("0.350000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamSpecialistThesisDivergenceConfig(**values)


def thesis_input(thesis_ref: str = "private-thesis-alpha", **overrides: object) -> Any:
    module = api()
    values = {
        "thesis_ref": thesis_ref,
        "team_code": "macro-team",
        "lead_specialist_code": "rates-lead",
        "challenger_specialist_code": "policy-review",
        "lead_thesis_probability": d("0.620000"),
        "challenger_thesis_probability": d("0.570000"),
        "team_consensus_probability": d("0.600000"),
        "evidence_alignment_score": d("0.900000"),
        "resolution_rule_clarity_score": d("0.900000"),
        "observed_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.ResearchStrategyTeamSpecialistThesisDivergenceInput(**values)


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return api().build_research_strategy_team_specialist_thesis_divergence_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def payload_digest(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "public_digest"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def row_digest(row: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in row.items() if key != "validation_digest"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def assert_decimal_surfaces(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if type(field_value) in (bool, str, datetime, tuple):
            continue
        assert type(field_value) is not int
        assert type(field_value) is not float
        if field.name.endswith(("_count", "_score", "_gap", "_probability", "_ratio")):
            assert type(field_value) is Decimal


def test_builds_team_specialist_thesis_divergence_report_for_review() -> None:
    module = api()
    built = report(
        thesis_input(
            "raw-candidate-alpha-market-id-slug-question-source-url-token-wallet",
            lead_thesis_probability=d("0.900000"),
            challenger_thesis_probability=d("0.500000"),
            team_consensus_probability=d("0.550000"),
            evidence_alignment_score=d("0.400000"),
            resolution_rule_clarity_score=d("0.450000"),
        ),
        thesis_input(
            "private-thesis-watch",
            lead_thesis_probability=d("0.720000"),
            challenger_thesis_probability=d("0.560000"),
            team_consensus_probability=d("0.650000"),
            evidence_alignment_score=d("0.760000"),
            resolution_rule_clarity_score=d("0.850000"),
        ),
        thesis_input("private-thesis-pass"),
    )

    assert type(built) is module.ResearchStrategyTeamSpecialistThesisDivergenceReport
    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_THESIS_DIVERGENCE_CONFIG_VERSION
    )
    assert built.report_status == "block"
    assert built.thesis_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_thesis_divergence_score == d("0.223167")
    assert built.max_thesis_divergence_score == d("0.450000")
    assert built.max_specialist_probability_gap == d("0.400000")
    assert built.max_consensus_gap == d("0.350000")
    assert built.reason_codes == (
        "specialist_probability_gap_block",
        "team_consensus_gap_block",
        "evidence_alignment_gap_block",
        "resolution_rule_gap_block",
        "thesis_divergence_score_block",
        "specialist_probability_gap_watch",
        "evidence_alignment_gap_watch",
        "thesis_divergence_score_watch",
        "specialist_thesis_divergence_pass",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert_digest(built.public_digest)
    assert_decimal_surfaces(built)

    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    blocked, watched, passed = built.rows
    assert blocked.thesis_digest.startswith("sha256:")
    assert "raw-candidate-alpha" not in blocked.thesis_digest
    assert blocked.specialist_probability_gap == d("0.400000")
    assert blocked.lead_consensus_gap == d("0.350000")
    assert blocked.challenger_consensus_gap == d("0.050000")
    assert blocked.max_consensus_gap == d("0.350000")
    assert blocked.evidence_alignment_gap == d("0.600000")
    assert blocked.resolution_rule_gap == d("0.550000")
    assert blocked.thesis_divergence_score == d("0.450000")
    assert blocked.reason_codes == (
        "specialist_probability_gap_block",
        "team_consensus_gap_block",
        "evidence_alignment_gap_block",
        "resolution_rule_gap_block",
        "thesis_divergence_score_block",
    )
    assert_digest(blocked.validation_digest)

    assert watched.status == "watch"
    assert watched.specialist_probability_gap == d("0.160000")
    assert watched.max_consensus_gap == d("0.090000")
    assert watched.evidence_alignment_gap == d("0.240000")
    assert watched.resolution_rule_gap == d("0.150000")
    assert watched.thesis_divergence_score == d("0.157000")
    assert watched.reason_codes == (
        "specialist_probability_gap_watch",
        "evidence_alignment_gap_watch",
        "thesis_divergence_score_watch",
    )

    assert passed.status == "pass"
    assert passed.specialist_probability_gap == d("0.050000")
    assert passed.max_consensus_gap == d("0.030000")
    assert passed.evidence_alignment_gap == d("0.100000")
    assert passed.resolution_rule_gap == d("0.100000")
    assert passed.thesis_divergence_score == d("0.062500")
    assert passed.reason_codes == ("specialist_thesis_divergence_pass",)


def test_payload_is_deterministic_redacted_decimal_only_and_digest_validated() -> None:
    module = api()
    first = report(
        thesis_input("private-thesis-pass"),
        thesis_input(
            "candidate://market-123/slug/question?source=https://example.invalid",
            lead_thesis_probability=d("0.720000"),
            challenger_thesis_probability=d("0.560000"),
            team_consensus_probability=d("0.650000"),
            evidence_alignment_score=d("0.760000"),
            resolution_rule_clarity_score=d("0.850000"),
        ),
    )
    second = report(
        thesis_input(
            "candidate://market-123/slug/question?source=https://example.invalid",
            lead_thesis_probability=d("0.720000"),
            challenger_thesis_probability=d("0.560000"),
            team_consensus_probability=d("0.650000"),
            evidence_alignment_score=d("0.760000"),
            resolution_rule_clarity_score=d("0.850000"),
        ),
        thesis_input("private-thesis-pass"),
    )

    assert second.public_digest == first.public_digest
    assert (
        module.research_strategy_team_specialist_thesis_divergence_report_digest(first)
        == first.public_digest
    )
    payload = (
        module.research_strategy_team_specialist_thesis_divergence_report_payload(first)
    )
    payload_again = (
        module.research_strategy_team_specialist_thesis_divergence_report_payload(first)
    )

    assert payload == payload_again
    assert payload == first.payload
    assert payload["generated_at"] == "2026-07-09T09:30:00+00:00"
    assert payload["config"] == {
        "config_version": (
            "research-strategy-team-specialist-thesis-divergence-report-v1"
        ),
        "specialist_gap_weight": "0.400000",
        "consensus_gap_weight": "0.250000",
        "evidence_gap_weight": "0.200000",
        "resolution_gap_weight": "0.150000",
        "pass_specialist_gap_ceiling": "0.100000",
        "block_specialist_gap_floor": "0.300000",
        "pass_consensus_gap_ceiling": "0.150000",
        "block_consensus_gap_floor": "0.350000",
        "pass_evidence_gap_ceiling": "0.200000",
        "block_evidence_gap_floor": "0.500000",
        "pass_resolution_gap_ceiling": "0.200000",
        "block_resolution_gap_floor": "0.500000",
        "pass_divergence_score_ceiling": "0.150000",
        "block_divergence_score_floor": "0.350000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert payload["thesis_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["thesis_digest"].startswith("sha256:")
    assert payload["rows"][0]["validation_digest"] == first.rows[0].validation_digest
    assert payload["public_digest"] == first.public_digest
    assert_no_raw_ids_or_decision_surfaces(payload)
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(type(value) is int for value in walk_values(payload))

    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert "private-thesis-pass" not in encoded
    assert "candidate://market-123" not in encoded
    assert "example.invalid" not in encoded

    tampered = dict(payload)
    tampered["report_status"] = "pass"
    with pytest.raises(ValueError, match="public_digest"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="validation_digest"):
        replace(first.rows[0], validation_digest="0" * 64)

    with pytest.raises(ValueError, match="public_digest"):
        replace(first, public_digest="0" * 64)


def test_empty_input_is_pass_report_only_without_decision_surfaces() -> None:
    module = api()
    empty = report()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        empty,
    )

    assert empty.report_status == "pass"
    assert empty.thesis_count == ZERO
    assert empty.rows == ()
    assert empty.reason_codes == ("no_specialist_thesis_divergence_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount(
            reason_code="no_specialist_thesis_divergence_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert payload["rows"] == []
    assert_no_raw_ids_or_decision_surfaces(payload)


def test_validation_guards_freezing_decimal_only_statuses_and_flags() -> None:
    module = api()
    cfg = config()
    item = thesis_input()
    built = report(item, cfg=cfg)

    for cls_name in (
        "ResearchStrategyTeamSpecialistThesisDivergenceConfig",
        "ResearchStrategyTeamSpecialistThesisDivergenceInput",
        "ResearchStrategyTeamSpecialistThesisDivergenceRow",
        "ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount",
        "ResearchStrategyTeamSpecialistThesisDivergenceReport",
    ):
        assert is_dataclass(getattr(module, cls_name))

    with pytest.raises(FrozenInstanceError):
        built.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].thesis_divergence_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="lead_thesis_probability"):
        thesis_input(lead_thesis_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="specialist_gap_weight"):
        config(specialist_gap_weight=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_alignment_score"):
        thesis_input(evidence_alignment_score=d("1.000001"))
    with pytest.raises(ValueError, match="challenger_thesis_probability"):
        thesis_input(challenger_thesis_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(thesis_input(), generated_at=datetime(2026, 7, 9, 9, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            thesis_input(),
            generated_at=datetime(2026, 7, 9, 9, 30, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(thesis_input(), generated_at=_DateTimeSubclass(2026, 7, 9, 9, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="thesis_ref values must be unique"):
        report(thesis_input("dup"), thesis_input("dup"))
    with pytest.raises(ValueError, match="paper_only"):
        thesis_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="review")
    with pytest.raises(ValueError, match="weights must sum"):
        config(resolution_gap_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_specialist_gap_ceiling"):
        config(
            pass_specialist_gap_ceiling=d("0.350000"),
            block_specialist_gap_floor=d("0.300000"),
        )
    with pytest.raises(ValueError, match="count.*whole"):
        module.ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount(
            reason_code="specialist_thesis_divergence_pass",
            count=d("0.500000"),
            row_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="count must be a Decimal"):
        module.ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount(
            reason_code="specialist_thesis_divergence_pass",
            count=1,  # type: ignore[arg-type]
            row_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="pass_count must be a Decimal"):
        replace(built, pass_count=1)
    with pytest.raises(ValueError, match="thesis_divergence_score must be a Decimal"):
        replace(built.rows[0], thesis_divergence_score=0.5)

    for value in (cfg, item, built, *built.rows, *built.reason_code_counts):
        assert_decimal_surfaces(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True


def test_public_frozen_dataclasses_reject_subclassing() -> None:
    module = api()

    for public_type in (
        module.ResearchStrategyTeamSpecialistThesisDivergenceConfig,
        module.ResearchStrategyTeamSpecialistThesisDivergenceInput,
        module.ResearchStrategyTeamSpecialistThesisDivergenceRow,
        module.ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount,
        module.ResearchStrategyTeamSpecialistThesisDivergenceReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})


def test_decimal_surfaces_reject_signed_zero() -> None:
    module = api()
    built = report(thesis_input())

    with pytest.raises(ValueError, match="pass_specialist_gap_ceiling.*signed zero"):
        config(pass_specialist_gap_ceiling=d("-0.000000"))
    with pytest.raises(ValueError, match="lead_thesis_probability.*signed zero"):
        thesis_input(lead_thesis_probability=d("-0.0000004"))
    with pytest.raises(ValueError, match="count.*signed zero"):
        module.ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount(
            reason_code="specialist_thesis_divergence_pass",
            count=d("-0.000000"),
            row_ratio=d("0.000000"),
        )
    with pytest.raises(
        ValueError,
        match="average_thesis_divergence_score.*signed zero",
    ):
        replace(built, average_thesis_divergence_score=d("-0.000000"))
    with pytest.raises(ValueError, match="specialist_probability_gap.*signed zero"):
        replace(built.rows[0], specialist_probability_gap=d("-0.000000"))


def test_build_rejects_observation_after_generated_at() -> None:
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            thesis_input(observed_at=GENERATED_AT + timedelta(microseconds=1)),
        )


def test_public_payload_rejects_leaks_status_mutation_and_numeric_types() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )
    assert_no_raw_ids_or_decision_surfaces(payload)

    unsafe_payloads = (
        {**payload, "raw_candidate_id": "abc"},
        {**payload, "candidate_id": "abc"},
        {**payload, "market_id": "abc"},
        {**payload, "market_slug": "abc"},
        {**payload, "slug": "abc"},
        {**payload, "question": "abc"},
        {**payload, "source_url": "https://example.test/path"},
        {**payload, "source_text": "raw"},
        {**payload, "storage": "postgres://example.test/db"},
        {**payload, "dsn": "postgres://example.test/db"},
        {**payload, "table_name": "abc"},
        {**payload, "token": "secret"},
        {**payload, "wallet": "abc"},
        {**payload, "order": "abc"},
        {**payload, "trade": "abc"},
        {**payload, "live": "abc"},
        {**payload, "sizing": "abc"},
        {**payload, "recommendation": "abc"},
    )
    for unsafe in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_team_specialist_thesis_divergence_report_payload(
                unsafe,
            )

    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            {**payload, "thesis_count": 1},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            {**payload, "average_thesis_divergence_score": 1.0},
        )
    with pytest.raises(ValueError, match="status"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            {**payload, "report_status": "review"},
        )
    forged_payload = {**payload, "candidate": "raw-candidate-alpha"}
    forged_payload["public_digest"] = payload_digest(forged_payload)
    with pytest.raises(ValueError, match="unexpected|unsafe"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_payload,
        )
    forged_row_payload = dict(payload)
    forged_rows = [dict(row) for row in payload["rows"]]
    forged_rows[0]["candidate"] = "raw-candidate-row"
    forged_rows[0]["validation_digest"] = row_digest(forged_rows[0])
    forged_row_payload["rows"] = forged_rows
    forged_row_payload["public_digest"] = payload_digest(forged_row_payload)
    with pytest.raises(ValueError, match="unexpected|unsafe"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_row_payload,
        )
    with pytest.raises(ValueError, match="unsafe"):
        thesis_input(team_code="market_slug-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        thesis_input(lead_specialist_code="https://example.test/raw")


def test_public_payload_rejects_resigned_signed_zero() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )
    forged = {**payload, "watch_count": "-0.000000"}
    forged["public_digest"] = payload_digest(forged)

    with pytest.raises(ValueError, match="watch_count.*signed zero"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged,
        )


def test_public_payload_rejects_noncanonical_json_types_without_coercion() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )
    invalid_values = (
        (
            "thesis_count",
            Decimal("1.000000"),
            "thesis_count must be a canonical Decimal string",
        ),
        (
            "generated_at",
            GENERATED_AT,
            "generated_at must be a canonical UTC datetime string",
        ),
        (
            "reason_codes",
            tuple(payload["reason_codes"]),
            "reason_codes must be a non-empty list",
        ),
        (
            "rows",
            tuple(payload["rows"]),
            "rows must be a list",
        ),
    )

    for field_name, invalid_value, error_match in invalid_values:
        forged = {**payload, field_name: invalid_value}
        with pytest.raises(ValueError, match=error_match):
            module.research_strategy_team_specialist_thesis_divergence_report_payload(
                forged,
            )


def test_public_payload_requires_exact_nested_schemas() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )

    missing_report_field = json.loads(json.dumps(payload))
    del missing_report_field["max_consensus_gap"]
    missing_report_field["public_digest"] = payload_digest(missing_report_field)
    with pytest.raises(ValueError, match="public payload contains unexpected fields"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            missing_report_field,
        )

    missing_config_field = json.loads(json.dumps(payload))
    del missing_config_field["config"]["specialist_gap_weight"]
    missing_config_field["public_digest"] = payload_digest(missing_config_field)
    with pytest.raises(ValueError, match="config payload contains unexpected fields"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            missing_config_field,
        )

    missing_row_field = json.loads(json.dumps(payload))
    del missing_row_field["rows"][0]["lead_consensus_gap"]
    missing_row_field["rows"][0]["validation_digest"] = row_digest(
        missing_row_field["rows"][0],
    )
    missing_row_field["public_digest"] = payload_digest(missing_row_field)
    with pytest.raises(ValueError, match="row payload contains unexpected fields"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            missing_row_field,
        )

    missing_reason_count_field = json.loads(json.dumps(payload))
    del missing_reason_count_field["reason_code_counts"][0]["row_ratio"]
    missing_reason_count_field["public_digest"] = payload_digest(
        missing_reason_count_field,
    )
    with pytest.raises(
        ValueError,
        match="reason code count payload contains unexpected fields",
    ):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            missing_reason_count_field,
        )


def test_public_payload_rejects_fully_resigned_derived_mutations() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )

    report_mutations = (
        ("report_status", "watch", "report_status"),
        ("pass_count", "0.000000", "pass_count"),
        (
            "average_thesis_divergence_score",
            "0.900000",
            "average_thesis_divergence_score",
        ),
        (
            "reason_codes",
            ["specialist_probability_gap_watch"],
            "reason_codes",
        ),
    )
    for field_name, forged_value, error_match in report_mutations:
        forged = json.loads(json.dumps(payload))
        forged[field_name] = forged_value
        forged["public_digest"] = payload_digest(forged)
        with pytest.raises(ValueError, match=error_match):
            module.research_strategy_team_specialist_thesis_divergence_report_payload(
                forged,
            )

    forged_row_status = json.loads(json.dumps(payload))
    forged_row_status["rows"][0]["status"] = "watch"
    forged_row_status["rows"][0]["validation_digest"] = row_digest(
        forged_row_status["rows"][0],
    )
    forged_row_status["public_digest"] = payload_digest(forged_row_status)
    with pytest.raises(ValueError, match="status must match reason_codes"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_row_status,
        )

    forged_reason_ratio = json.loads(json.dumps(payload))
    forged_reason_ratio["reason_code_counts"][0]["row_ratio"] = "0.500000"
    forged_reason_ratio["public_digest"] = payload_digest(forged_reason_ratio)
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_reason_ratio,
        )


def test_public_payload_rejects_nested_phase_one_flag_downgrades() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )
    nested_mutations = (
        ("config", 0, "paper_only"),
        ("rows", 0, "report_only"),
        ("reason_code_counts", 0, "readonly"),
    )

    for container_name, item_index, flag_name in nested_mutations:
        forged = json.loads(json.dumps(payload))
        container = forged[container_name]
        target = container if type(container) is dict else container[item_index]
        target[flag_name] = False
        if container_name == "rows":
            target["validation_digest"] = row_digest(target)
        forged["public_digest"] = payload_digest(forged)
        with pytest.raises(ValueError, match=flag_name):
            module.research_strategy_team_specialist_thesis_divergence_report_payload(
                forged,
            )


def test_public_payload_rejects_resigned_observation_after_generated_at() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )
    forged = dict(payload)
    forged_rows = [dict(row) for row in payload["rows"]]
    forged_rows[0]["observed_at"] = (
        GENERATED_AT + timedelta(microseconds=1)
    ).isoformat()
    forged_rows[0]["validation_digest"] = row_digest(forged_rows[0])
    forged["rows"] = forged_rows
    forged["public_digest"] = payload_digest(forged)

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged,
        )


def test_public_payload_revalidates_canonical_values_and_derived_invariants() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )

    forged_count = {**payload, "thesis_count": "999.000000"}
    forged_count["public_digest"] = payload_digest(forged_count)
    with pytest.raises(ValueError, match="thesis_count"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_count,
        )

    noncanonical_count = {**payload, "thesis_count": "1"}
    noncanonical_count["public_digest"] = payload_digest(noncanonical_count)
    with pytest.raises(ValueError, match="canonical Decimal string"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            noncanonical_count,
        )

    unsupported_config = {**payload, "config_version": "unsupported-report-version"}
    unsupported_config["public_digest"] = payload_digest(unsupported_config)
    with pytest.raises(ValueError, match="supported config version"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            unsupported_config,
        )

    invalid_timestamp = {**payload, "generated_at": "not-a-timestamp"}
    invalid_timestamp["public_digest"] = payload_digest(invalid_timestamp)
    with pytest.raises(ValueError, match="generated_at"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            invalid_timestamp,
        )

    forged_row_payload = dict(payload)
    forged_rows = [dict(row) for row in payload["rows"]]
    forged_rows[0]["specialist_probability_gap"] = "0.900000"
    forged_rows[0]["validation_digest"] = row_digest(forged_rows[0])
    forged_row_payload["rows"] = forged_rows
    forged_row_payload["public_digest"] = payload_digest(forged_row_payload)
    with pytest.raises(ValueError, match="specialist_probability_gap"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_row_payload,
        )

    forged_reason_counts = dict(payload)
    reason_code_counts = [dict(item) for item in payload["reason_code_counts"]]
    reason_code_counts[0]["count"] = "999.000000"
    forged_reason_counts["reason_code_counts"] = reason_code_counts
    forged_reason_counts["public_digest"] = payload_digest(forged_reason_counts)
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_reason_counts,
        )

    duplicated_rows = dict(payload)
    duplicated_rows["rows"] = [dict(payload["rows"][0]), dict(payload["rows"][0])]
    duplicated_rows["thesis_count"] = "2.000000"
    duplicated_rows["pass_count"] = "2.000000"
    duplicated_reason_counts = [
        {**item, "count": "2.000000"} for item in payload["reason_code_counts"]
    ]
    duplicated_rows["reason_code_counts"] = duplicated_reason_counts
    duplicated_rows["public_digest"] = payload_digest(duplicated_rows)
    with pytest.raises(ValueError, match="thesis_digest values must be unique"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            duplicated_rows,
        )


def test_public_payload_revalidates_policy_derived_score_and_reason_codes() -> None:
    module = api()
    payload = module.research_strategy_team_specialist_thesis_divergence_report_payload(
        report(thesis_input()),
    )

    forged_score = dict(payload)
    score_rows = [dict(row) for row in payload["rows"]]
    score_rows[0]["thesis_divergence_score"] = "0.900000"
    score_rows[0]["validation_digest"] = row_digest(score_rows[0])
    forged_score["rows"] = score_rows
    forged_score["average_thesis_divergence_score"] = "0.900000"
    forged_score["max_thesis_divergence_score"] = "0.900000"
    forged_score["public_digest"] = payload_digest(forged_score)
    with pytest.raises(ValueError, match="thesis_divergence_score"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_score,
        )

    forged_reasons = dict(payload)
    reason_rows = [dict(row) for row in payload["rows"]]
    reason_rows[0]["status"] = "watch"
    reason_rows[0]["reason_codes"] = ["specialist_probability_gap_watch"]
    reason_rows[0]["validation_digest"] = row_digest(reason_rows[0])
    forged_reasons["rows"] = reason_rows
    forged_reasons["report_status"] = "watch"
    forged_reasons["pass_count"] = "0.000000"
    forged_reasons["watch_count"] = "1.000000"
    forged_reasons["reason_codes"] = ["specialist_probability_gap_watch"]
    forged_reasons["reason_code_counts"] = [
        {
            **payload["reason_code_counts"][0],
            "reason_code": "specialist_probability_gap_watch",
        },
    ]
    forged_reasons["public_digest"] = payload_digest(forged_reasons)
    with pytest.raises(ValueError, match="reason_codes"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_reasons,
        )

    forged_config = dict(payload)
    config_payload = dict(payload["config"])
    config_payload["unexpected"] = "field"
    forged_config["config"] = config_payload
    forged_config["public_digest"] = payload_digest(forged_config)
    with pytest.raises(ValueError, match="config payload.*unexpected"):
        module.research_strategy_team_specialist_thesis_divergence_report_payload(
            forged_config,
        )


@pytest.mark.parametrize(
    "field_name,value",
    (
        ("team_code", "buy-now"),
        ("lead_specialist_code", "sell-review"),
        ("challenger_specialist_code", "execution-desk"),
    ),
)
def test_public_codes_reject_decision_and_execution_surfaces(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        thesis_input(**{field_name: value})


def test_module_scope_is_report_only_readonly_and_public_api_is_narrow() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    banned_imports = {
        "aiohttp",
        "asyncio",
        "boto3",
        "http",
        "httpx",
        "mysql",
        "os",
        "pathlib",
        "pickle",
        "psycopg",
        "redis",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_public_field_fragments = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
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
        "live",
        "position",
        "sizing",
        "recommend",
    )

    public_field_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            public_field_names.append(node.target.id.casefold())
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    assert not any(
        fragment in field_name
        for fragment in forbidden_public_field_fragments
        for field_name in public_field_names
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_THESIS_DIVERGENCE_CONFIG_VERSION",
        "ResearchStrategyTeamSpecialistThesisDivergenceConfig",
        "ResearchStrategyTeamSpecialistThesisDivergenceInput",
        "ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount",
        "ResearchStrategyTeamSpecialistThesisDivergenceReport",
        "ResearchStrategyTeamSpecialistThesisDivergenceRow",
        "build_research_strategy_team_specialist_thesis_divergence_report",
        "research_strategy_team_specialist_thesis_divergence_report_digest",
        "research_strategy_team_specialist_thesis_divergence_report_payload",
    )


def assert_no_raw_ids_or_decision_surfaces(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True, allow_nan=False).casefold()
    for forbidden in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "raw-candidate",
        "market-123",
        "slug",
        "question",
        "source_url",
        "source_text",
        "https://",
        "example.invalid",
        "postgres://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live trading",
        "sizing",
        "recommendation",
        "buy",
        "sell",
    ):
        assert forbidden not in rendered
