from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_resolution_claim_trace_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_claim_trace_coverage": d("0.800000"),
        "block_claim_trace_coverage": d("0.500000"),
        "min_resolution_clause_coverage": d("0.800000"),
        "block_resolution_clause_coverage": d("0.500000"),
        "trace_watch_age_seconds": d("3600.000000"),
        "trace_block_age_seconds": d("7200.000000"),
        "min_source_authority_score": d("0.800000"),
        "block_source_authority_score": d("0.500000"),
        "contradiction_watch_pressure": d("0.300000"),
        "contradiction_block_pressure": d("0.600000"),
        "min_independent_source_count": d("2.000000"),
        "block_independent_source_count": d("1.000000"),
        "missing_trace_link_watch_count": d("1.000000"),
        "missing_trace_link_block_count": d("2.000000"),
        "deadline_watch_proximity_seconds": d("43200.000000"),
        "deadline_block_proximity_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceResolutionClaimTraceGapConfig(**values)


def trace_input(
    claim_trace_key: str,
    resolution_scope: str,
    evidence_family: str,
    *,
    observed_seconds_ago: int = 1200,
    deadline_seconds_from_now: int = 172800,
    claim_trace_coverage: Decimal = d("0.900000"),
    resolution_clause_coverage: Decimal = d("0.900000"),
    source_authority_score: Decimal = d("0.900000"),
    contradiction_pressure: Decimal = d("0.100000"),
    independent_source_count: Decimal = d("3.000000"),
    missing_trace_link_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceResolutionClaimTraceGapInput(
        claim_trace_key=claim_trace_key,
        resolution_scope=resolution_scope,
        evidence_family=evidence_family,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        resolution_deadline_at=GENERATED_AT + timedelta(seconds=deadline_seconds_from_now),
        claim_trace_coverage=claim_trace_coverage,
        resolution_clause_coverage=resolution_clause_coverage,
        source_authority_score=source_authority_score,
        contradiction_pressure=contradiction_pressure,
        independent_source_count=independent_source_count,
        missing_trace_link_count=missing_trace_link_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_resolution_claim_trace_gap_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def direct_report_with_rows(report: Any, rows: tuple[Any, ...]) -> Any:
    module = api()
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["rows"] = rows
    values["derived_validation_digest"] = ""
    return module.ResearchSourceResolutionClaimTraceGapReport(**values)


def test_claim_trace_gap_report_blocks_material_resolution_trace_gaps() -> None:
    report = build_report(
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "official.feed",
            observed_seconds_ago=10800,
            deadline_seconds_from_now=3600,
            claim_trace_coverage=d("0.400000"),
            resolution_clause_coverage=d("0.300000"),
            source_authority_score=d("0.400000"),
            contradiction_pressure=d("0.800000"),
            independent_source_count=d("1.000000"),
            missing_trace_link_count=d("2.000000"),
        ),
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "archive.feed",
            observed_seconds_ago=9000,
            deadline_seconds_from_now=3600,
            claim_trace_coverage=d("0.600000"),
            resolution_clause_coverage=d("0.500000"),
            source_authority_score=d("0.600000"),
            contradiction_pressure=d("0.500000"),
            independent_source_count=d("1.000000"),
            missing_trace_link_count=d("1.000000"),
        ),
        trace_input("trace.verification", "verification.criteria", "official.feed"),
    )

    assert report.status == "block"
    assert report.claim_trace_count == d("2.000000")
    assert report.evidence_count == d("3.000000")
    assert report.pass_claim_trace_count == d("1.000000")
    assert report.watch_claim_trace_count == d("0.000000")
    assert report.block_claim_trace_count == d("1.000000")
    assert report.low_claim_trace_coverage_count == d("1.000000")
    assert report.low_resolution_clause_coverage_count == d("1.000000")
    assert report.stale_trace_count == d("1.000000")
    assert report.low_source_authority_count == d("1.000000")
    assert report.contradiction_pressure_count == d("1.000000")
    assert report.low_independent_source_count == d("1.000000")
    assert report.missing_trace_link_count == d("1.000000")
    assert report.deadline_pressure_count == d("1.000000")
    assert report.highest_claim_trace_gap_score == d("0.727083")
    assert report.nearest_deadline_seconds == d("3600.000000")
    assert report.reason_codes == (
        "claim_trace_coverage_block",
        "resolution_clause_coverage_block",
        "stale_claim_trace_block",
        "low_source_authority_block",
        "contradiction_pressure_block",
        "low_independent_source_block",
        "missing_trace_link_block",
        "deadline_proximity_block",
    )

    assert tuple(row.claim_trace_key for row in report.rows) == (
        "trace.settlement",
        "trace.verification",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.resolution_scope == "settlement.criteria"
    assert blocked.evidence_family_count == d("2.000000")
    assert blocked.latest_trace_age_seconds == d("9000.000000")
    assert blocked.average_claim_trace_coverage == d("0.500000")
    assert blocked.average_resolution_clause_coverage == d("0.400000")
    assert blocked.average_source_authority_score == d("0.500000")
    assert blocked.contradiction_pressure == d("0.800000")
    assert blocked.independent_source_count == d("1.000000")
    assert blocked.missing_trace_link_count == d("2.000000")
    assert blocked.deadline_proximity_seconds == d("3600.000000")
    assert blocked.claim_trace_gap_score == d("0.727083")
    assert blocked.reason_codes == report.reason_codes

    passed = report.rows[1]
    assert passed.status == "pass"
    assert passed.reason_codes == ("resolution_claim_trace_gap_clear",)
    assert passed.claim_trace_gap_score == d("0.070833")
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_watch_thresholds_report_claim_trace_pressure_without_blocking() -> None:
    report = build_report(
        trace_input(
            "trace.weather",
            "weather.criteria",
            "official.bulletin",
            observed_seconds_ago=5400,
            deadline_seconds_from_now=21600,
            claim_trace_coverage=d("0.650000"),
            resolution_clause_coverage=d("0.700000"),
            source_authority_score=d("0.650000"),
            contradiction_pressure=d("0.350000"),
            independent_source_count=d("1.500000"),
            missing_trace_link_count=d("1.000000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_claim_trace_count == d("1.000000")
    assert report.block_claim_trace_count == d("0.000000")
    assert report.reason_codes == (
        "claim_trace_coverage_watch",
        "resolution_clause_coverage_watch",
        "stale_claim_trace_watch",
        "low_source_authority_watch",
        "contradiction_pressure_watch",
        "low_independent_source_watch",
        "missing_trace_link_watch",
        "deadline_proximity_watch",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == report.reason_codes


def test_payload_digest_is_deterministic_decimal_string_only_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        trace_input("trace.verification", "verification.criteria", "official.feed"),
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "official.feed",
            observed_seconds_ago=10800,
            deadline_seconds_from_now=3600,
            claim_trace_coverage=d("0.400000"),
            resolution_clause_coverage=d("0.300000"),
            source_authority_score=d("0.400000"),
            contradiction_pressure=d("0.800000"),
            independent_source_count=d("1.000000"),
            missing_trace_link_count=d("2.000000"),
        ),
    )
    report_b = build_report(
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "official.feed",
            observed_seconds_ago=10800,
            deadline_seconds_from_now=3600,
            claim_trace_coverage=d("0.400000"),
            resolution_clause_coverage=d("0.300000"),
            source_authority_score=d("0.400000"),
            contradiction_pressure=d("0.800000"),
            independent_source_count=d("1.000000"),
            missing_trace_link_count=d("2.000000"),
        ),
        trace_input("trace.verification", "verification.criteria", "official.feed"),
    )

    payload_a = module.research_source_resolution_claim_trace_gap_report_payload(report_a)
    payload_b = module.research_source_resolution_claim_trace_gap_report_payload(report_b)
    digest_a = module.research_source_resolution_claim_trace_gap_report_digest(report_a)
    digest_b = module.research_source_resolution_claim_trace_gap_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["claim_trace_count"] == "2.000000"
    assert payload_a["rows"][0]["claim_trace_gap_score"] >= payload_a["rows"][1][
        "claim_trace_gap_score"
    ]
    assert len(digest_a) == 64
    int(digest_a, 16)
    json.dumps(payload_a, sort_keys=True)
    assert_no_float_values(payload_a)

    unsafe_keys = {
        "api_key",
        "auth_token",
        "authentication_url",
        "authorization_header",
        "bet_size",
        "execution_plan",
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "notional",
        "password",
        "position_size",
        "recommendation",
        "recommended_action",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "sizing_rule",
        "stake",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_url",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_resolution_claim_trace_gap_report_digest(report_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_flags_statuses_decimal_only_and_safe_scope() -> None:
    module = api()

    with pytest.raises(ValueError, match="min_claim_trace_coverage must be a Decimal"):
        config(min_claim_trace_coverage=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="claim_trace_coverage must be a Decimal"):
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "official.feed",
            claim_trace_coverage=0.9,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="missing_trace_link_count must be a Decimal"):
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "official.feed",
            missing_trace_link_count=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "official.feed",
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        trace_input(
            "trace.settlement",
            "settlement.criteria",
            "official.feed",
            readonly=False,
        )
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(build_report(trace_input("trace.ok", "settlement.criteria", "official.feed")), status="clear")
    with pytest.raises(ValueError, match="must not be in the future"):
        build_report(
            trace_input(
                "trace.future",
                "settlement.criteria",
                "official.feed",
                observed_seconds_ago=-1,
            ),
        )
    with pytest.raises(ValueError, match="contains unsafe text"):
        trace_input("candidate-123", "settlement.criteria", "official.feed")
    with pytest.raises(ValueError, match="contains unsafe text"):
        trace_input("trace.ok", "market_slug", "official.feed")
    with pytest.raises(ValueError, match="contains unsafe text"):
        trace_input("trace.ok", "settlement.criteria", "https://example.test/source")
    with pytest.raises(ValueError, match="contains unsafe text"):
        trace_input("trace.ok", "settlement.criteria", "authentication.feed")
    with pytest.raises(ValueError, match="contains unsafe text"):
        trace_input("trace.ok", "execution-plan", "official.feed")
    with pytest.raises(ValueError, match="contains unsafe text"):
        trace_input("trace.ok", "settlement.criteria", "position_size.feed")
    with pytest.raises(ValueError, match="contains unsafe text"):
        trace_input("trace.ok", "settlement.criteria", "recommendation.feed")

    report = build_report(trace_input("trace.ok", "settlement.criteria", "official.feed"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().min_claim_trace_coverage = d("0.900000")

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
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
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "scrap",
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


def assert_no_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
    else:
        assert type(value) is not float


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "api-key",
        "api_key",
        "auth-token",
        "auth_token",
        "authentication",
        "authorization",
        "bearer",
        "bet-size",
        "bet_size",
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate_",
        "execution",
        "market-",
        "market_",
        "notional",
        "password",
        "position-size",
        "position_size",
        "recommendation",
        "recommended",
        "sizing",
        "stake",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "slug",
        "live",
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


def test_decimal_context_raw_bounds_signed_zero_and_exact_scale_are_hardened() -> None:
    module = api()
    baseline = build_report(
        trace_input(
            "trace.alpha",
            "settlement.criteria",
            "official.feed",
            observed_seconds_ago=7200,
            deadline_seconds_from_now=7200,
            claim_trace_coverage=d("0.500000"),
            resolution_clause_coverage=d("0.500000"),
            source_authority_score=d("0.500000"),
            contradiction_pressure=d("0.600000"),
            independent_source_count=d("1.000000"),
            missing_trace_link_count=d("2.000000"),
        ),
    )
    baseline_payload = module.research_source_resolution_claim_trace_gap_report_payload(
        baseline,
    )

    with localcontext(Context(prec=6, rounding=ROUND_DOWN)):
        constrained = build_report(
            trace_input(
                "trace.alpha",
                "settlement.criteria",
                "official.feed",
                observed_seconds_ago=7200,
                deadline_seconds_from_now=7200,
                claim_trace_coverage=d("0.500000"),
                resolution_clause_coverage=d("0.500000"),
                source_authority_score=d("0.500000"),
                contradiction_pressure=d("0.600000"),
                independent_source_count=d("1.000000"),
                missing_trace_link_count=d("2.000000"),
            ),
        )
        constrained_payload = (
            module.research_source_resolution_claim_trace_gap_report_payload(
                constrained,
            )
        )
    assert constrained_payload == baseline_payload

    for field_name in (
        "claim_trace_coverage",
        "resolution_clause_coverage",
        "source_authority_score",
        "contradiction_pressure",
        "independent_source_count",
        "missing_trace_link_count",
    ):
        with pytest.raises(ValueError, match=f"{field_name} must not be signed zero"):
            trace_input(
                "trace.zero",
                "settlement.criteria",
                "official.feed",
                **{field_name: d("-0.000000")},
            )

    for field_name in (
        "min_claim_trace_coverage",
        "block_claim_trace_coverage",
        "trace_watch_age_seconds",
        "missing_trace_link_watch_count",
    ):
        with pytest.raises(ValueError, match=f"{field_name} must use six decimal places"):
            config(**{field_name: d("0.8000000")})

    with pytest.raises(ValueError, match="claim_trace_coverage must use six decimal places"):
        trace_input(
            "trace.scale",
            "settlement.criteria",
            "official.feed",
            claim_trace_coverage=d("0.8"),
        )
    with pytest.raises(ValueError, match="claim_trace_coverage must be between zero and one"):
        trace_input(
            "trace.raw.low",
            "settlement.criteria",
            "official.feed",
            claim_trace_coverage=d("-0.0000004"),
        )
    with pytest.raises(ValueError, match="claim_trace_coverage must be between zero and one"):
        trace_input(
            "trace.raw.high",
            "settlement.criteria",
            "official.feed",
            claim_trace_coverage=d("1.0000004"),
        )


def test_dataclasses_are_final_exact_type_and_revalidate_object_setattr_tampering() -> None:
    module = api()
    dataclass_types = (
        module.ResearchSourceResolutionClaimTraceGapConfig,
        module.ResearchSourceResolutionClaimTraceGapInput,
        module.ResearchSourceResolutionClaimTraceGapRow,
        module.ResearchSourceResolutionClaimTraceGapReport,
    )
    for dataclass_type in dataclass_types:
        with pytest.raises(TypeError, match="subclass"):
            type(f"{dataclass_type.__name__}Subclass", (dataclass_type,), {})

    tampered_config = config()
    object.__setattr__(tampered_config, "block_claim_trace_coverage", d("0.900000"))
    with pytest.raises(ValueError, match="block_claim_trace_coverage"):
        build_report(
            trace_input("trace.config", "settlement.criteria", "official.feed"),
            cfg=tampered_config,
        )

    tampered_input = trace_input(
        "trace.input",
        "settlement.criteria",
        "official.feed",
    )
    object.__setattr__(tampered_input, "claim_trace_coverage", d("0.8000000"))
    with pytest.raises(ValueError, match="claim_trace_coverage must use six decimal places"):
        build_report(tampered_input)

    report = build_report(trace_input("trace.row", "settlement.criteria", "official.feed"))
    tampered_row = replace(report.rows[0])
    object.__setattr__(tampered_row, "evidence_family_count", d("0.000000"))
    with pytest.raises(ValueError, match="evidence_family_count"):
        direct_report_with_rows(report, (tampered_row,))


def test_public_mapping_requires_exact_schema_key_order_and_lowercase_sha256() -> None:
    module = api()
    payload = module.research_source_resolution_claim_trace_gap_report_payload(
        build_report(trace_input("trace.schema", "settlement.criteria", "official.feed")),
    )

    assert module.research_source_resolution_claim_trace_gap_report_payload(payload) == payload
    assert (
        module.research_source_resolution_claim_trace_gap_report_digest(payload)
        == payload["derived_validation_digest"]
    )
    module.validate_research_source_resolution_claim_trace_gap_report_digest(payload)

    missing_field = json.loads(json.dumps(payload))
    missing_field.pop("status")
    resign(missing_field)
    with pytest.raises(ValueError, match="exact public fields"):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            missing_field,
        )

    wrong_order = dict(reversed(tuple(payload.items())))
    wrong_order["derived_validation_digest"] = canonical_digest(wrong_order)
    with pytest.raises(ValueError, match="canonical field order"):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            wrong_order,
        )

    row_missing_field = json.loads(json.dumps(payload))
    row_missing_field["rows"][0].pop("status")
    resign(row_missing_field)
    with pytest.raises(ValueError, match="exact public fields"):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            row_missing_field,
        )

    tuple_reason_codes = json.loads(json.dumps(payload))
    tuple_reason_codes["reason_codes"] = tuple(tuple_reason_codes["reason_codes"])
    with pytest.raises(ValueError, match="canonical|public list"):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            tuple_reason_codes,
        )

    decimal_numeric = json.loads(json.dumps(payload))
    decimal_numeric["claim_trace_count"] = d(decimal_numeric["claim_trace_count"])
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            decimal_numeric,
        )

    uppercase_sha = json.loads(json.dumps(payload))
    uppercase_sha["derived_validation_digest"] = uppercase_sha[
        "derived_validation_digest"
    ].upper()
    with pytest.raises(ValueError, match="lowercase|SHA-256"):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            uppercase_sha,
        )


@pytest.mark.parametrize(
    ("field_path", "forged_value", "error_match"),
    (
        (("rows", 0, "status"), "pass", "status|reason_codes"),
        (
            ("rows", 0, "reason_codes"),
            ["resolution_claim_trace_gap_clear"],
            "reason_codes",
        ),
        (("rows", 0, "claim_trace_gap_score"), "0.000000", "claim_trace_gap_score"),
        (("rows", 0, "evidence_count"), "2.000000", "evidence_count"),
        ("block_claim_trace_count", "0.000000", "block_claim_trace_count|status"),
        (
            "low_claim_trace_coverage_count",
            "0.000000",
            "low_claim_trace_coverage_count",
        ),
        ("highest_claim_trace_gap_score", "0.000000", "highest_claim_trace_gap_score"),
        ("status", "pass", "status"),
        (("reason_codes",), ["resolution_claim_trace_gap_clear"], "reason_codes"),
    ),
)
def test_public_mapping_rejects_resigned_forged_trace_gap_derived_fields(
    field_path: str | tuple[object, ...],
    forged_value: object,
    error_match: str,
) -> None:
    module = api()
    payload = module.research_source_resolution_claim_trace_gap_report_payload(
        build_report(
            trace_input(
                "trace.blocked",
                "settlement.criteria",
                "official.feed",
                observed_seconds_ago=9000,
                deadline_seconds_from_now=3600,
                claim_trace_coverage=d("0.400000"),
                resolution_clause_coverage=d("0.300000"),
                source_authority_score=d("0.400000"),
                contradiction_pressure=d("0.800000"),
                independent_source_count=d("1.000000"),
                missing_trace_link_count=d("2.000000"),
            ),
        ),
    )
    forged = json.loads(json.dumps(payload))
    path = (field_path,) if isinstance(field_path, str) else field_path
    target = forged
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = forged_value  # type: ignore[index]
    resign(forged)

    with pytest.raises(ValueError, match=error_match):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            forged,
        )


def test_public_mapping_rejects_resigned_row_order_and_preserves_tie_breaks() -> None:
    module = api()
    report = build_report(
        trace_input("trace.beta", "settlement.criteria", "official.feed"),
        trace_input("trace.alpha", "settlement.criteria", "official.feed"),
    )
    payload = module.research_source_resolution_claim_trace_gap_report_payload(report)

    assert tuple(row["claim_trace_key"] for row in payload["rows"]) == (
        "trace.alpha",
        "trace.beta",
    )

    reversed_rows = json.loads(json.dumps(payload))
    reversed_rows["rows"].reverse()
    resign(reversed_rows)
    with pytest.raises(ValueError, match="deterministic|sort"):
        module.validate_research_source_resolution_claim_trace_gap_report_digest(
            reversed_rows,
        )
