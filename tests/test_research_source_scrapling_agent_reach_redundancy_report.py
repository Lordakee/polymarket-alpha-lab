from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import (
    Context,
    Decimal,
    Inexact,
    ROUND_DOWN,
    Rounded,
    localcontext,
)
from hashlib import sha256
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_scrapling_agent_reach_redundancy_report as api
from polymarket_alpha_lab.research_source_scrapling_agent_reach_redundancy_report import (
    ResearchSourceScraplingAgentReachRedundancyConfig,
    ResearchSourceScraplingAgentReachRedundancyInput,
    ResearchSourceScraplingAgentReachRedundancyReport,
    build_research_source_scrapling_agent_reach_redundancy_report,
    validate_research_source_scrapling_agent_reach_redundancy_report_payload,
)


NOW = datetime(2026, 7, 9, tzinfo=UTC)


def _input(
    *,
    private_collection_ref: str = (
        "raw_candidate_id=secret-candidate|market_id=secret-market|"
        "market_slug=private-slug|question=private question|"
        "https://example.invalid/path?token=hidden&wallet=hidden"
    ),
    observed_at: datetime = NOW,
    required_evidence_count: Decimal = Decimal("10.000000"),
    scrapling_evidence_count: Decimal = Decimal("9.000000"),
    agent_reach_evidence_count: Decimal = Decimal("8.000000"),
    overlapping_evidence_count: Decimal = Decimal("8.000000"),
    conflicting_evidence_count: Decimal = Decimal("0.000000"),
    scrapling_confidence_score: Decimal = Decimal("0.900000"),
    agent_reach_confidence_score: Decimal = Decimal("0.860000"),
) -> ResearchSourceScraplingAgentReachRedundancyInput:
    return ResearchSourceScraplingAgentReachRedundancyInput(
        private_collection_ref=private_collection_ref,
        observed_at=observed_at,
        required_evidence_count=required_evidence_count,
        scrapling_evidence_count=scrapling_evidence_count,
        agent_reach_evidence_count=agent_reach_evidence_count,
        overlapping_evidence_count=overlapping_evidence_count,
        conflicting_evidence_count=conflicting_evidence_count,
        scrapling_confidence_score=scrapling_confidence_score,
        agent_reach_confidence_score=agent_reach_confidence_score,
    )


def _report(
    inputs: tuple[ResearchSourceScraplingAgentReachRedundancyInput, ...],
    *,
    config: ResearchSourceScraplingAgentReachRedundancyConfig | None = None,
) -> ResearchSourceScraplingAgentReachRedundancyReport:
    return build_research_source_scrapling_agent_reach_redundancy_report(
        inputs,
        config=config or ResearchSourceScraplingAgentReachRedundancyConfig(),
        generated_at=NOW,
    )


def test_pass_report_uses_decimal_payload_stable_digest_and_private_ref_redaction() -> None:
    report = _report(
        (
            _input(private_collection_ref="private-a"),
            _input(
                private_collection_ref=(
                    "raw_market_id=secret-2|source_url=https://example.invalid/other"
                ),
                required_evidence_count=Decimal("5.000000"),
                scrapling_evidence_count=Decimal("5.000000"),
                agent_reach_evidence_count=Decimal("5.000000"),
                overlapping_evidence_count=Decimal("4.000000"),
                scrapling_confidence_score=Decimal("0.950000"),
                agent_reach_confidence_score=Decimal("0.940000"),
            ),
        ),
    )
    same_report = _report(
        (
            _input(
                private_collection_ref="changed-private-b",
                required_evidence_count=Decimal("5.000000"),
                scrapling_evidence_count=Decimal("5.000000"),
                agent_reach_evidence_count=Decimal("5.000000"),
                overlapping_evidence_count=Decimal("4.000000"),
                scrapling_confidence_score=Decimal("0.950000"),
                agent_reach_confidence_score=Decimal("0.940000"),
            ),
            _input(private_collection_ref="changed-private-a"),
        ),
    )
    changed_report = _report((_input(overlapping_evidence_count=Decimal("7.000000")),))

    assert report.status == "pass"
    assert report.reason_codes == ("scrapling_agent_reach_redundancy_pass",)
    assert report.input_count == Decimal("2.000000")
    assert report.row_count == Decimal("2.000000")
    assert report.required_evidence_count == Decimal("15.000000")
    assert report.overlapping_evidence_count == Decimal("12.000000")
    assert report.aggregate_redundant_coverage_ratio == Decimal("0.800000")
    assert report.average_tool_agreement_score == Decimal("0.921000")
    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert report.derived_validation_digest != changed_report.derived_validation_digest

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert validate_research_source_scrapling_agent_reach_redundancy_report_payload(payload)
    assert payload["input_count"] == "2.000000"
    assert payload["aggregate_redundant_coverage_ratio"] == "0.800000"
    assert payload["rows"][0]["row_index"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest

    rendered = json.dumps(payload, sort_keys=True)
    for forbidden_fragment in (
        "secret-candidate",
        "secret-market",
        "private-slug",
        "private question",
        "https://",
        "example.invalid",
        "hidden",
        "private-a",
        "changed-private",
    ):
        assert forbidden_fragment not in rendered
    _assert_no_decimal_objects(payload)
    _assert_no_public_numbers(report)


@pytest.mark.parametrize(
    "caller_context",
    (
        Context(prec=6),
        Context(prec=28, rounding=ROUND_DOWN),
        Context(prec=28, traps=[Inexact, Rounded]),
    ),
    ids=("low-precision", "different-rounding", "arithmetic-traps"),
)
def test_report_build_payload_validation_and_digest_ignore_caller_decimal_context(
    caller_context: Context,
) -> None:
    def build_report() -> ResearchSourceScraplingAgentReachRedundancyReport:
        return _report(
            (
                _input(
                    private_collection_ref="private-context-a",
                    required_evidence_count=Decimal("7.000000"),
                    scrapling_evidence_count=Decimal("6.000000"),
                    agent_reach_evidence_count=Decimal("5.000000"),
                    overlapping_evidence_count=Decimal("4.000000"),
                    conflicting_evidence_count=Decimal("1.000000"),
                    scrapling_confidence_score=Decimal("0.876543"),
                    agent_reach_confidence_score=Decimal("0.234567"),
                ),
                _input(
                    private_collection_ref="private-context-b",
                    required_evidence_count=Decimal("11.000000"),
                    scrapling_evidence_count=Decimal("10.000000"),
                    agent_reach_evidence_count=Decimal("7.000000"),
                    overlapping_evidence_count=Decimal("6.000000"),
                    conflicting_evidence_count=Decimal("2.000000"),
                    scrapling_confidence_score=Decimal("0.765432"),
                    agent_reach_confidence_score=Decimal("0.345678"),
                ),
            ),
        )

    expected_report = build_report()
    expected_payload = expected_report.payload
    expected_digest = (
        api.research_source_scrapling_agent_reach_redundancy_report_digest(
            expected_report,
        )
    )

    with localcontext(caller_context):
        actual_report = build_report()
        actual_payload = actual_report.payload
        actual_payload_valid = (
            validate_research_source_scrapling_agent_reach_redundancy_report_payload(
                actual_payload,
            )
        )
        expected_payload_valid = (
            validate_research_source_scrapling_agent_reach_redundancy_report_payload(
                expected_payload,
            )
        )
        actual_digest = (
            api.research_source_scrapling_agent_reach_redundancy_report_digest(
                actual_report,
            )
        )

    assert actual_report == expected_report
    assert actual_payload == expected_payload
    assert actual_payload_valid
    assert expected_payload_valid
    assert actual_digest == expected_digest


def test_watch_and_block_reports_use_fixed_reason_order() -> None:
    watch_report = _report(
        (
            _input(
                scrapling_evidence_count=Decimal("7.000000"),
                agent_reach_evidence_count=Decimal("6.000000"),
                overlapping_evidence_count=Decimal("5.000000"),
                conflicting_evidence_count=Decimal("1.000000"),
                scrapling_confidence_score=Decimal("0.900000"),
                agent_reach_confidence_score=Decimal("0.720000"),
            ),
        ),
    )
    block_report = _report(
        (
            _input(
                scrapling_evidence_count=Decimal("2.000000"),
                agent_reach_evidence_count=Decimal("8.000000"),
                overlapping_evidence_count=Decimal("2.000000"),
                conflicting_evidence_count=Decimal("1.000000"),
                scrapling_confidence_score=Decimal("0.900000"),
                agent_reach_confidence_score=Decimal("0.400000"),
            ),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "redundant_coverage_below_pass_threshold",
        "conflict_ratio_above_pass_threshold",
        "confidence_gap_above_pass_threshold",
        "tool_agreement_below_pass_threshold",
    )
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].reason_codes == (
        "redundant_coverage_below_watch_threshold",
        "coverage_gap_above_watch_threshold",
        "conflict_ratio_above_watch_threshold",
        "confidence_gap_above_watch_threshold",
        "tool_agreement_below_watch_threshold",
    )


def test_empty_input_blocks_with_zero_decimal_scores() -> None:
    report = _report(())

    assert report.status == "block"
    assert report.reason_codes == ("scrapling_agent_reach_redundancy_no_inputs",)
    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.required_evidence_count == Decimal("0.000000")
    assert report.aggregate_redundant_coverage_ratio == Decimal("0.000000")
    assert report.average_tool_agreement_score == Decimal("0.000000")
    assert report.reason_code_counts[0].reason_code == (
        "scrapling_agent_reach_redundancy_no_inputs"
    )
    assert report.reason_code_counts[0].count == Decimal("1.000000")
    assert report.rows == ()


def test_dataclasses_flags_digest_decimal_only_safe_surface_and_no_io_imports() -> None:
    report = _report((_input(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceScraplingAgentReachRedundancyConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceScraplingAgentReachRedundancyConfig(paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        _input(required_evidence_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report.payload
    broken_payload = dict(payload)
    broken_payload["aggregate_redundant_coverage_ratio"] = "0.100000"
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        broken_payload,
    )

    forbidden_terms = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchSourceScraplingAgentReachRedundancyConfig,
        ResearchSourceScraplingAgentReachRedundancyInput,
        ResearchSourceScraplingAgentReachRedundancyReport,
    ):
        for field in fields(cls):
            if field.name == "private_collection_ref":
                continue
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

    source_path = Path(api.__file__)
    tree = ast.parse(source_path.read_text())
    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def test_public_payload_validator_rejects_resigned_schema_drift() -> None:
    payload = _report((_input(),)).payload

    with_extra = _payload_with_matching_digest(payload, unexpected_safe_field="safe")
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        with_extra,
    )

    missing_rows = dict(payload)
    missing_rows.pop("rows")
    missing_rows = _payload_with_matching_digest(missing_rows)
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        missing_rows,
    )

    false_flags = _payload_with_matching_digest(payload, paper_only=False)
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        false_flags,
    )

    noncanonical_decimal = _payload_with_matching_digest(payload, input_count="1")
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        noncanonical_decimal,
    )


@pytest.mark.parametrize(
    ("overrides", "error_match"),
    (
        (
            {"required_evidence_count": Decimal("Infinity")},
            "finite",
        ),
        (
            {"scrapling_confidence_score": Decimal("NaN")},
            "finite",
        ),
    ),
    ids=("infinite-count", "nan-probability"),
)
def test_input_rejects_non_finite_decimals(
    overrides: dict[str, Decimal],
    error_match: str,
) -> None:
    with pytest.raises(ValueError, match=error_match):
        _input(**overrides)


@pytest.mark.parametrize(
    ("overrides", "error_match"),
    (
        (
            {"scrapling_confidence_score": Decimal("1.000001")},
            "between zero and one",
        ),
        (
            {"agent_reach_confidence_score": Decimal("-0.000001")},
            "between zero and one",
        ),
        (
            {"scrapling_evidence_count": Decimal("-1.000000")},
            "nonnegative",
        ),
        (
            {
                "scrapling_evidence_count": Decimal("3.000000"),
                "overlapping_evidence_count": Decimal("4.000000"),
            },
            "must not exceed Scrapling count",
        ),
    ),
    ids=(
        "probability-above-one",
        "probability-below-zero",
        "negative-count",
        "overlap-above-source-count",
    ),
)
def test_input_rejects_raw_domain_and_evidence_count_violations(
    overrides: dict[str, Decimal],
    error_match: str,
) -> None:
    with pytest.raises(ValueError, match=error_match):
        _input(**overrides)


@pytest.mark.parametrize(
    ("overrides", "error_match"),
    (
        (
            {"min_redundant_coverage_pass_ratio": Decimal("Infinity")},
            "finite",
        ),
        (
            {"max_conflict_ratio_pass_ratio": Decimal("NaN")},
            "finite",
        ),
        (
            {"min_tool_agreement_pass_score": Decimal("1.000001")},
            "between zero and one",
        ),
        (
            {"max_confidence_gap_pass_ratio": Decimal("-0.000001")},
            "between zero and one",
        ),
    ),
    ids=(
        "infinite-config-probability",
        "nan-config-probability",
        "config-probability-above-one",
        "config-probability-below-zero",
    ),
)
def test_config_rejects_non_finite_and_out_of_domain_probabilities(
    overrides: dict[str, Decimal],
    error_match: str,
) -> None:
    with pytest.raises(ValueError, match=error_match):
        ResearchSourceScraplingAgentReachRedundancyConfig(**overrides)


def test_signed_zero_is_rejected_before_decimal_quantization() -> None:
    with pytest.raises(ValueError, match="signed zero"):
        _input(
            scrapling_evidence_count=Decimal("-0.000000"),
            overlapping_evidence_count=Decimal("0.000000"),
        )

    with pytest.raises(ValueError, match="signed zero"):
        _input(scrapling_confidence_score=Decimal("-0.0000004"))

    with pytest.raises(ValueError, match="signed zero"):
        ResearchSourceScraplingAgentReachRedundancyConfig(
            coverage_balance_weight=Decimal("-0.000000"),
            redundant_coverage_weight=Decimal("0.515714"),
        )


def test_payload_is_canonical_json_and_carries_the_effective_config() -> None:
    config = ResearchSourceScraplingAgentReachRedundancyConfig(
        min_tool_agreement_pass_score=Decimal("0.950000"),
    )
    payload = _report((_input(),), config=config).payload

    assert payload["config"]["min_tool_agreement_pass_score"] == "0.950000"
    assert payload["config_version"] == payload["config"]["config_version"]
    assert payload["rows"][0]["scrapling_confidence_score"] == "0.900000"
    assert payload["rows"][0]["agent_reach_confidence_score"] == "0.860000"

    decimal_payload = dict(payload)
    decimal_payload["input_count"] = Decimal("1.000000")
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        decimal_payload,
    )

    tuple_payload = dict(payload)
    tuple_payload["rows"] = tuple(payload["rows"])
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        tuple_payload,
    )


def test_resigned_payload_rederives_row_score_status_reasons_and_report_counts() -> None:
    payload = json.loads(json.dumps(_report((_input(),)).payload))
    row = payload["rows"][0]
    row["tool_agreement_score"] = "0.100000"
    row["status"] = "block"
    row["reason_codes"] = ["tool_agreement_below_watch_threshold"]
    payload["average_tool_agreement_score"] = "0.100000"
    payload["pass_count"] = "0.000000"
    payload["block_count"] = "1.000000"
    payload["status"] = "block"
    payload["reason_codes"] = ["tool_agreement_below_watch_threshold"]
    payload["reason_code_counts"] = [
        {
            "reason_code": "tool_agreement_below_watch_threshold",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    resigned = _payload_with_matching_digest(payload)

    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        resigned,
    )


def test_resigned_payload_rederives_confidence_gap_and_effective_config_logic() -> None:
    report = _report(
        (_input(),),
        config=ResearchSourceScraplingAgentReachRedundancyConfig(
            min_tool_agreement_pass_score=Decimal("0.850000"),
        ),
    )
    confidence_tamper = json.loads(json.dumps(report.payload))
    confidence_tamper["rows"][0]["agent_reach_confidence_score"] = "0.100000"
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        _payload_with_matching_digest(confidence_tamper),
    )

    config_tamper = json.loads(json.dumps(report.payload))
    config_tamper["config"]["min_tool_agreement_pass_score"] = "0.950000"
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        _payload_with_matching_digest(config_tamper),
    )


def test_resigned_payload_rederives_rank_and_reason_code_occurrence_counts() -> None:
    repeated_watch = _report(
        (
            _input(
                private_collection_ref="private-a",
                scrapling_evidence_count=Decimal("7.000000"),
                agent_reach_evidence_count=Decimal("6.000000"),
                overlapping_evidence_count=Decimal("5.000000"),
                conflicting_evidence_count=Decimal("1.000000"),
                scrapling_confidence_score=Decimal("0.900000"),
                agent_reach_confidence_score=Decimal("0.720000"),
            ),
            _input(
                private_collection_ref="private-b",
                scrapling_evidence_count=Decimal("7.000000"),
                agent_reach_evidence_count=Decimal("6.000000"),
                overlapping_evidence_count=Decimal("5.000000"),
                conflicting_evidence_count=Decimal("1.000000"),
                scrapling_confidence_score=Decimal("0.900000"),
                agent_reach_confidence_score=Decimal("0.720000"),
            ),
        ),
    )
    counts = {
        item.reason_code: item.count for item in repeated_watch.reason_code_counts
    }
    assert counts["redundant_coverage_below_pass_threshold"] == Decimal("2.000000")
    assert counts["conflict_ratio_above_pass_threshold"] == Decimal("2.000000")

    rank_tamper = json.loads(json.dumps(repeated_watch.payload))
    rank_tamper["rows"][0]["row_index"] = "2.000000"
    rank_tamper["rows"][1]["row_index"] = "1.000000"
    assert not validate_research_source_scrapling_agent_reach_redundancy_report_payload(
        _payload_with_matching_digest(rank_tamper),
    )


def _payload_with_matching_digest(
    payload: dict[str, object],
    **overrides: object,
) -> dict[str, object]:
    resigned = dict(payload)
    resigned.update(overrides)
    resigned.pop("derived_validation_digest", None)
    canonical_payload = json.dumps(
        resigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    resigned["derived_validation_digest"] = sha256(
        canonical_payload.encode("utf-8"),
    ).hexdigest()
    return resigned


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_public_numbers(getattr(value, field.name))
