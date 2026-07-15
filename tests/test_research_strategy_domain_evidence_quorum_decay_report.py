from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_domain_evidence_quorum_decay_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_domain_evidence_quorum_decay_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 12, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def load_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION
        ),
        "min_domain_count_pass": d("3.000000"),
        "min_domain_count_watch": d("2.000000"),
        "min_independent_evidence_count_pass": d("5.000000"),
        "min_independent_evidence_count_watch": d("3.000000"),
        "min_source_family_count_pass": d("3.000000"),
        "min_source_family_count_watch": d("2.000000"),
        "max_latest_evidence_age_seconds_pass": d("1800.000000"),
        "max_latest_evidence_age_seconds_watch": d("7200.000000"),
        "domain_consensus_score_pass_floor": d("0.800000"),
        "domain_consensus_score_watch_floor": d("0.600000"),
        "contradiction_pressure_watch_ceiling": d("0.250000"),
        "contradiction_pressure_block_ceiling": d("0.500000"),
        "source_authority_score_pass_floor": d("0.750000"),
        "source_authority_score_watch_floor": d("0.500000"),
        "quorum_decay_score_pass_floor": d("0.750000"),
        "quorum_decay_score_watch_floor": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainEvidenceQuorumDecayConfig(**values)


def evidence_input(
    module: Any,
    domain_evidence_key: str = "domain-pass",
    *,
    domain_count: Decimal = d("3.000000"),
    independent_evidence_count: Decimal = d("5.000000"),
    source_family_count: Decimal = d("3.000000"),
    latest_evidence_age_seconds: Decimal = d("600.000000"),
    domain_consensus_score: Decimal = d("0.900000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    source_authority_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyDomainEvidenceQuorumDecayInput(
        domain_evidence_key=domain_evidence_key,
        domain_count=domain_count,
        independent_evidence_count=independent_evidence_count,
        source_family_count=source_family_count,
        latest_evidence_age_seconds=latest_evidence_age_seconds,
        domain_consensus_score=domain_consensus_score,
        contradiction_pressure_score=contradiction_pressure_score,
        source_authority_score=source_authority_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    module: Any,
    *rows: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_domain_evidence_quorum_decay_report(
        rows,
        config=cfg(module) if config is None else config,
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("public_digest")
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def resigned_payload(
    payload: dict[str, Any],
    *path_and_value: object,
) -> dict[str, Any]:
    resigned = deepcopy(payload)
    target: Any = resigned
    *path, value = path_and_value
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    resigned["public_digest"] = canonical_digest(resigned)
    return resigned


def test_domain_evidence_quorum_decay_payload_digest_and_statuses() -> None:
    module = load_module()
    pass_item = evidence_input(module, "domain-pass")
    watch_item = evidence_input(
        module,
        "domain-watch",
        domain_count=d("2.000000"),
        independent_evidence_count=d("3.000000"),
        source_family_count=d("2.000000"),
        latest_evidence_age_seconds=d("3600.000000"),
        domain_consensus_score=d("0.700000"),
        contradiction_pressure_score=d("0.300000"),
        source_authority_score=d("0.650000"),
    )
    block_item = evidence_input(
        module,
        "domain-block",
        domain_count=d("1.000000"),
        independent_evidence_count=d("2.000000"),
        source_family_count=d("1.000000"),
        latest_evidence_age_seconds=d("9000.000000"),
        domain_consensus_score=d("0.500000"),
        contradiction_pressure_score=d("0.600000"),
        source_authority_score=d("0.400000"),
    )

    first = build_report(module, watch_item, block_item, pass_item)
    second = build_report(module, pass_item, watch_item, block_item)

    assert type(first) is module.ResearchStrategyDomainEvidenceQuorumDecayReport
    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION
    )
    assert first.domain_evidence_item_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.domain_quorum_attention_count == d("2.000000")
    assert first.evidence_quorum_attention_count == d("2.000000")
    assert first.source_family_attention_count == d("2.000000")
    assert first.freshness_decay_attention_count == d("2.000000")
    assert first.consensus_support_attention_count == d("2.000000")
    assert first.contradiction_pressure_attention_count == d("2.000000")
    assert first.source_authority_attention_count == d("2.000000")
    assert first.score_attention_count == d("2.000000")
    assert first.mean_quorum_decay_score == d("0.643651")
    assert first.lowest_quorum_decay_score == d("0.338095")
    assert first.highest_contradiction_pressure_score == d("0.600000")
    assert first.reason_codes == (
        "research_strategy_domain_evidence_quorum_decay_domain_quorum_block",
        "research_strategy_domain_evidence_quorum_decay_evidence_quorum_block",
        "research_strategy_domain_evidence_quorum_decay_source_family_block",
        "research_strategy_domain_evidence_quorum_decay_freshness_decay_block",
        "research_strategy_domain_evidence_quorum_decay_consensus_support_block",
        "research_strategy_domain_evidence_quorum_decay_contradiction_pressure_block",
        "research_strategy_domain_evidence_quorum_decay_source_authority_block",
        "research_strategy_domain_evidence_quorum_decay_score_block",
        "research_strategy_domain_evidence_quorum_decay_domain_quorum_watch",
        "research_strategy_domain_evidence_quorum_decay_evidence_quorum_watch",
        "research_strategy_domain_evidence_quorum_decay_source_family_watch",
        "research_strategy_domain_evidence_quorum_decay_freshness_decay_watch",
        "research_strategy_domain_evidence_quorum_decay_consensus_support_watch",
        "research_strategy_domain_evidence_quorum_decay_contradiction_pressure_watch",
        "research_strategy_domain_evidence_quorum_decay_source_authority_watch",
        "research_strategy_domain_evidence_quorum_decay_score_watch",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.aggregate_row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.rows[0].aggregate_row_hash == hashlib.sha256(
        b"domain-block",
    ).hexdigest()
    assert first.rows[0].freshness_decay_score == ZERO
    assert first.rows[0].quorum_decay_score == d("0.338095")
    assert first.rows[1].freshness_decay_score == d("0.500000")
    assert first.rows[1].quorum_decay_score == d("0.640476")
    assert first.rows[2].freshness_decay_score == d("0.916667")
    assert first.rows[2].quorum_decay_score == d("0.952381")
    assert first.rows[2].reason_codes == (
        "research_strategy_domain_evidence_quorum_decay_clear",
    )
    assert not hasattr(first.rows[0], "domain_evidence_key")

    payload = module.research_strategy_domain_evidence_quorum_decay_report_payload(first)
    assert payload == (
        module.research_strategy_domain_evidence_quorum_decay_report_payload(second)
    )
    assert payload["domain_evidence_item_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["quorum_decay_score"] == "0.338095"
    assert payload["public_digest"] == first.public_digest
    assert payload["public_digest"] == canonical_digest(payload)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    payload_text = json.dumps(payload, sort_keys=True)
    assert "domain_evidence_key" not in payload_text
    assert "domain-block" not in payload_text
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)
    assert_payload_has_no_leaked_values(payload)

    digest = module.research_strategy_domain_evidence_quorum_decay_report_digest(first)
    assert digest == first.public_digest
    assert len(digest) == 64
    int(digest, 16)
    module.validate_research_strategy_domain_evidence_quorum_decay_report_digest(first)
    module.validate_research_strategy_domain_evidence_quorum_decay_public_payload(payload)


def test_time_decay_drives_manual_review_priority_and_stable_tie_breaks() -> None:
    module = load_module()
    fresh = evidence_input(
        module,
        "domain-fresh",
        latest_evidence_age_seconds=d("0.000000"),
    )
    stale = evidence_input(
        module,
        "domain-stale",
        latest_evidence_age_seconds=d("7200.000000"),
    )
    tied_a = evidence_input(
        module,
        "domain-tied-a",
        domain_count=d("2.000000"),
        independent_evidence_count=d("3.000000"),
        source_family_count=d("2.000000"),
        latest_evidence_age_seconds=d("3600.000000"),
        domain_consensus_score=d("0.700000"),
        contradiction_pressure_score=d("0.300000"),
        source_authority_score=d("0.650000"),
    )
    tied_b = replace(tied_a, domain_evidence_key="domain-tied-b")

    first = build_report(module, tied_b, fresh, stale, tied_a)
    second = build_report(module, tied_a, stale, tied_b, fresh)

    assert (
        module.research_strategy_domain_evidence_quorum_decay_report_payload(first)
        == module.research_strategy_domain_evidence_quorum_decay_report_payload(second)
    )
    rows_by_hash = {row.aggregate_row_hash: row for row in first.rows}
    fresh_row = rows_by_hash[hashlib.sha256(b"domain-fresh").hexdigest()]
    stale_row = rows_by_hash[hashlib.sha256(b"domain-stale").hexdigest()]
    assert fresh_row.manual_review_priority == "routine"
    assert stale_row.manual_review_priority == "priority"
    assert stale_row.manual_review_priority_score > fresh_row.manual_review_priority_score
    assert first.manual_review_required_count == d("3.000000")
    assert first.highest_manual_review_priority_score == max(
        row.manual_review_priority_score for row in first.rows
    )

    tied_hashes = tuple(
        row.aggregate_row_hash
        for row in first.rows
        if row.aggregate_row_hash
        in {
            hashlib.sha256(b"domain-tied-a").hexdigest(),
            hashlib.sha256(b"domain-tied-b").hexdigest(),
        }
    )
    assert tied_hashes == tuple(sorted(tied_hashes))


def test_decimal_context_raw_bounds_signed_zero_and_non_finite_are_strict() -> None:
    module = load_module()
    baseline = build_report(module, evidence_input(module))
    with localcontext() as hostile_context:
        hostile_context.prec = 6
        hostile_context.rounding = ROUND_DOWN
        under_hostile_context = build_report(module, evidence_input(module))
    assert under_hostile_context == baseline

    for field_name, value, expected_error in (
        ("domain_count", d("-0.0000004"), "nonnegative"),
        ("domain_count", d("-0.000000"), "signed zero"),
        ("domain_consensus_score", d("1.0000004"), "between 0 and 1"),
        ("domain_consensus_score", d("NaN"), "finite"),
        ("domain_consensus_score", d("Infinity"), "finite"),
        ("domain_consensus_score", d("-Infinity"), "finite"),
    ):
        with pytest.raises(ValueError, match=expected_error):
            evidence_input(module, **{field_name: value})

    for field_name, value, expected_error in (
        ("min_domain_count_pass", d("-0.0000004"), "nonnegative"),
        ("min_domain_count_pass", d("-0.000000"), "signed zero"),
        ("quorum_decay_score_pass_floor", d("1.0000004"), "between 0 and 1"),
        ("quorum_decay_score_pass_floor", d("NaN"), "finite"),
    ):
        with pytest.raises(ValueError, match=expected_error):
            cfg(module, **{field_name: value})


def test_all_public_dataclasses_are_frozen_exact_and_non_subclassable() -> None:
    module = load_module()
    report = build_report(module, evidence_input(module))
    public_values = (
        cfg(module),
        evidence_input(module),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in public_values:
        assert is_dataclass(value)
        with pytest.raises(TypeError):
            type(f"{type(value).__name__}Subclass", (type(value),), {})
        first_field = fields(value)[0]
        with pytest.raises(FrozenInstanceError):
            setattr(value, first_field.name, getattr(value, first_field.name))


@pytest.mark.parametrize(
    ("forged_value", "expected_error"),
    (
        (d("NaN"), "finite"),
        (d("-0.000000"), "signed zero"),
        (d("7200"), "six decimal places"),
    ),
)
def test_digest_revalidation_rejects_low_level_config_decimal_tampering(
    forged_value: Decimal,
    expected_error: str,
) -> None:
    module = load_module()
    report = build_report(module, evidence_input(module))
    object.__setattr__(
        report.config,
        "max_latest_evidence_age_seconds_watch",
        forged_value,
    )

    with pytest.raises(ValueError, match=expected_error):
        module.validate_research_strategy_domain_evidence_quorum_decay_report_digest(
            report,
        )


def test_public_payload_requires_exact_canonical_schema_and_sha256() -> None:
    module = load_module()
    payload = module.research_strategy_domain_evidence_quorum_decay_report_payload(
        build_report(module, evidence_input(module)),
    )

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "config",
        "domain_evidence_item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "domain_quorum_attention_count",
        "evidence_quorum_attention_count",
        "source_family_attention_count",
        "freshness_decay_attention_count",
        "consensus_support_attention_count",
        "contradiction_pressure_attention_count",
        "source_authority_attention_count",
        "score_attention_count",
        "manual_review_required_count",
        "mean_quorum_decay_score",
        "lowest_quorum_decay_score",
        "highest_contradiction_pressure_score",
        "highest_manual_review_priority_score",
        "status",
        "public_digest",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "aggregate_row_number",
        "aggregate_row_hash",
        "status",
        "manual_review_priority",
        "domain_count",
        "independent_evidence_count",
        "source_family_count",
        "latest_evidence_age_seconds",
        "freshness_decay_score",
        "domain_consensus_score",
        "contradiction_pressure_score",
        "source_authority_score",
        "quorum_decay_score",
        "manual_review_priority_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["reason_code_counts"][0]) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["config"]) == tuple(
        field.name
        for field in fields(module.ResearchStrategyDomainEvidenceQuorumDecayConfig)
    )
    assert payload["public_digest"] == canonical_digest(payload)
    assert hashlib.sha256(b"domain-pass").hexdigest() == (
        payload["rows"][0]["aggregate_row_hash"]
    )

    invalid_payloads = (
        resigned_payload(payload, "safe_extra", "opaque"),
        resigned_payload(payload, "rows", 0, "safe_extra", "opaque"),
        resigned_payload(payload, "rows", 0, "domain_count", "3"),
        resigned_payload(payload, "generated_at", "2026-07-09T12:45:00Z"),
    )
    missing_top_level = deepcopy(payload)
    missing_top_level.pop("watch_count")
    missing_top_level["public_digest"] = canonical_digest(missing_top_level)
    missing_row_field = deepcopy(payload)
    missing_row_field["rows"][0].pop("source_authority_score")
    missing_row_field["public_digest"] = canonical_digest(missing_row_field)

    for invalid in (*invalid_payloads, missing_top_level, missing_row_field):
        with pytest.raises(ValueError, match="canonical schema|canonical"):
            module.validate_research_strategy_domain_evidence_quorum_decay_public_payload(
                invalid,
            )


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("rows", 0, "freshness_decay_score"), "0.500000"),
        (("rows", 0, "quorum_decay_score"), "0.500000"),
        (("rows", 0, "manual_review_priority_score"), "0.999999"),
        (("rows", 0, "manual_review_priority"), "urgent"),
        (("rows", 0, "status"), "watch"),
        (
            ("rows", 0, "reason_codes"),
            ["research_strategy_domain_evidence_quorum_decay_score_watch"],
        ),
        (("rows", 0, "aggregate_row_number"), "2.000000"),
        (("pass_count",), "0.000000"),
        (("manual_review_required_count",), "1.000000"),
        (("mean_quorum_decay_score",), "0.500000"),
        (("highest_manual_review_priority_score",), "0.500000"),
        (("status",), "watch"),
    ),
)
def test_resigned_payload_recomputes_every_derived_value(
    path: tuple[object, ...],
    value: object,
) -> None:
    module = load_module()
    payload = module.research_strategy_domain_evidence_quorum_decay_report_payload(
        build_report(module, evidence_input(module)),
    )
    resigned = resigned_payload(payload, *path, value)

    with pytest.raises(ValueError, match="must match|canonical sequence"):
        module.validate_research_strategy_domain_evidence_quorum_decay_public_payload(
            resigned,
        )


def test_resigned_payload_rejects_noncanonical_row_order() -> None:
    module = load_module()
    report = build_report(
        module,
        evidence_input(module, "domain-pass-a"),
        evidence_input(module, "domain-pass-b"),
    )
    payload = module.research_strategy_domain_evidence_quorum_decay_report_payload(report)
    reordered = deepcopy(payload)
    reordered["rows"].reverse()
    reordered["public_digest"] = canonical_digest(reordered)

    with pytest.raises(ValueError, match="canonical sequence"):
        module.validate_research_strategy_domain_evidence_quorum_decay_public_payload(
            reordered,
        )


def test_custom_config_is_signed_and_revalidated_after_resigning() -> None:
    module = load_module()
    strict = cfg(
        module,
        max_latest_evidence_age_seconds_pass=d("600.000000"),
        max_latest_evidence_age_seconds_watch=d("3600.000000"),
        quorum_decay_score_pass_floor=d("0.900000"),
        quorum_decay_score_watch_floor=d("0.700000"),
    )
    report = build_report(
        module,
        evidence_input(
            module,
            latest_evidence_age_seconds=d("1800.000000"),
        ),
        config=strict,
    )
    payload = module.research_strategy_domain_evidence_quorum_decay_report_payload(report)

    assert report.config == strict
    assert payload["config"]["max_latest_evidence_age_seconds_pass"] == "600.000000"
    assert payload["config"]["max_latest_evidence_age_seconds_watch"] == "3600.000000"
    assert report.rows[0].freshness_decay_score == d("0.500000")
    assert report.rows[0].status == "watch"

    forged = resigned_payload(
        payload,
        "config",
        "max_latest_evidence_age_seconds_watch",
        "7200.000000",
    )
    with pytest.raises(ValueError, match="freshness_decay_score|must match"):
        module.validate_research_strategy_domain_evidence_quorum_decay_public_payload(
            forged,
        )


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    module = load_module()

    report = build_report(module)

    assert report.status == "block"
    assert report.domain_evidence_item_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.mean_quorum_decay_score == ZERO
    assert report.lowest_quorum_decay_score == ZERO
    assert report.highest_contradiction_pressure_score == ZERO
    assert report.reason_codes == (
        "research_strategy_domain_evidence_quorum_decay_no_inputs",
    )
    assert report.reason_code_counts == (
        module.ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount(
            reason_code="research_strategy_domain_evidence_quorum_decay_no_inputs",
            count=ONE,
        ),
    )
    assert report.rows == ()


def test_decimal_datetime_flags_and_frozen_dataclasses() -> None:
    module = load_module()

    report = build_report(
        module,
        evidence_input(module),
        generated_at=datetime(
            2026,
            7,
            9,
            8,
            45,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )
    assert report.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="min_domain_count_pass"):
        cfg(module, min_domain_count_pass=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_consensus_score_pass_floor"):
        cfg(module, domain_consensus_score_pass_floor=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="min_domain_count_pass"):
        cfg(module, min_domain_count_pass=d("1.000000"))
    with pytest.raises(ValueError, match="max_latest_evidence_age_seconds_pass"):
        cfg(module, max_latest_evidence_age_seconds_pass=d("7200.000000"))
    with pytest.raises(ValueError, match="contradiction_pressure_watch_ceiling"):
        cfg(module, contradiction_pressure_watch_ceiling=d("0.600000"))
    with pytest.raises(ValueError, match="domain_count"):
        evidence_input(module, domain_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_consensus_score"):
        evidence_input(module, domain_consensus_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        cfg(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence_input(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence_input(module, readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            module,
            evidence_input(module),
            generated_at=datetime(2026, 7, 9, 12, 45),
        )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_STATUSES",
        "ResearchStrategyDomainEvidenceQuorumDecayConfig",
        "ResearchStrategyDomainEvidenceQuorumDecayInput",
        "ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount",
        "ResearchStrategyDomainEvidenceQuorumDecayReport",
        "ResearchStrategyDomainEvidenceQuorumDecayRow",
        "build_research_strategy_domain_evidence_quorum_decay_report",
        "research_strategy_domain_evidence_quorum_decay_report_digest",
        "research_strategy_domain_evidence_quorum_decay_report_payload",
        "validate_research_strategy_domain_evidence_quorum_decay_public_payload",
        "validate_research_strategy_domain_evidence_quorum_decay_report_digest",
    )
    assert is_dataclass(cfg(module))
    assert is_dataclass(evidence_input(module))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    for value in (cfg(module), evidence_input(module), report, *report.rows):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                assert item_value is True
                continue
            if item.name.endswith(("_count", "_score", "_seconds")):
                assert type(item_value) is Decimal

    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchStrategyDomainEvidenceQuorumDecayConfig,), {})
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        cfg(module).min_independent_evidence_count_pass = d("4.000000")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="block")
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)


def test_public_dataclasses_are_slotted_final_and_exact() -> None:
    module = load_module()
    public_types = (
        module.ResearchStrategyDomainEvidenceQuorumDecayConfig,
        module.ResearchStrategyDomainEvidenceQuorumDecayInput,
        module.ResearchStrategyDomainEvidenceQuorumDecayRow,
        module.ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount,
        module.ResearchStrategyDomainEvidenceQuorumDecayReport,
    )

    for public_type in public_types:
        assert getattr(public_type, "__final__", False) is True
        assert public_type.__slots__ == tuple(
            field.name for field in fields(public_type)
        )
        assert "__dict__" not in public_type.__slots__
        with pytest.raises(TypeError):
            type(f"{public_type.__name__}Subclass", (public_type,), {})


def test_build_revalidates_mutated_config_and_input_before_scoring() -> None:
    module = load_module()
    mutated_config = cfg(module)
    object.__setattr__(mutated_config, "min_domain_count_pass", d("1.000000"))
    with pytest.raises(ValueError, match="min_domain_count_pass"):
        build_report(module, evidence_input(module), config=mutated_config)

    mutated_input = evidence_input(module)
    object.__setattr__(mutated_input, "domain_count", 3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_count"):
        build_report(module, mutated_input)


def test_digest_revalidation_rechecks_canonical_nested_collections() -> None:
    module = load_module()
    report = build_report(
        module,
        evidence_input(module, "domain-a"),
        evidence_input(module, "domain-b"),
    )
    object.__setattr__(
        report.rows[1],
        "aggregate_row_hash",
        report.rows[0].aggregate_row_hash,
    )
    object.__setattr__(
        report,
        "public_digest",
        module._computed_report_digest(report),
    )

    with pytest.raises(ValueError, match="duplicate aggregate_row_hash"):
        module.validate_research_strategy_domain_evidence_quorum_decay_report_digest(
            report,
        )


def test_status_threshold_boundaries_are_inclusive_until_next_level() -> None:
    module = load_module()
    assert build_report(
        module,
        evidence_input(
            module,
            domain_count=d("2.000000"),
            independent_evidence_count=d("3.000000"),
            source_family_count=d("2.000000"),
            latest_evidence_age_seconds=d("1800.000000"),
            domain_consensus_score=d("0.600000"),
            contradiction_pressure_score=d("0.250000"),
            source_authority_score=d("0.500000"),
        ),
    ).rows[0].status == "watch"
    assert build_report(
        module,
        evidence_input(
            module,
            latest_evidence_age_seconds=d("7200.000001"),
        ),
    ).rows[0].status == "block"


def test_public_payload_prevents_identifier_source_secret_and_execution_leaks() -> None:
    module = load_module()
    report = build_report(module, evidence_input(module))
    payload = module.research_strategy_domain_evidence_quorum_decay_report_payload(report)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "position_size",
        "recommendation",
    }
    keys = {
        field.name
        for cls in (type(evidence_input(module)), type(report), type(report.rows[0]))
        for field in fields(cls)
    }
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload)

    for unsafe_value in (
        "candidate-123",
        "market_slug",
        "Will this question resolve?",
        "https://example.invalid/source",
        "source_text",
        "private-team-alpha",
        "team_key",
        "private-source-alpha",
        "source_id",
        "source_name",
        "postgres://local.example/db",
        "wallet_token",
        "live order trade recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe text"):
            evidence_input(module, unsafe_value)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation"},
        {"private_team_key": "opaque"},
        {"source_name": "opaque"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_strategy_domain_evidence_quorum_decay_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "public_digest": payload["public_digest"],
                },
            )


def test_module_scope_is_pure_report_only_without_external_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "submit_order",
                "place_order",
                "recommend",
                "size_position",
            }

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "position_size",
        "recommendation",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
