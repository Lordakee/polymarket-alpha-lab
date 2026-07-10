from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_team_domain_review_readiness_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_review_readiness_report.py"
)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_digest(payload)


def config(**overrides: object) -> Any:
    module = api()
    return module.ResearchTeamDomainReviewReadinessConfig(**overrides)


def input_row(
    domain_category: str,
    team_label: str,
    *,
    calibration_score: Decimal = d("0.900000"),
    memory_refreshed_at: datetime = GENERATED_AT - timedelta(hours=1),
    evidence_coverage_score: Decimal = d("0.950000"),
    workload_ratio: Decimal = d("0.200000"),
    correction_follow_through_score: Decimal = d("0.900000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchTeamDomainReviewReadinessInput(
        domain_category=domain_category,
        team_label=team_label,
        calibration_score=calibration_score,
        memory_refreshed_at=memory_refreshed_at,
        evidence_coverage_score=evidence_coverage_score,
        workload_ratio=workload_ratio,
        correction_follow_through_score=correction_follow_through_score,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_team_domain_review_readiness_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_domain_review_readiness_scores_required_domains_and_digest_deterministically() -> None:
    rows = (
        input_row("politics", "policy_team"),
        input_row(
            "crypto",
            "onchain_team",
            calibration_score=d("0.650000"),
            memory_refreshed_at=GENERATED_AT - timedelta(days=10),
            evidence_coverage_score=d("0.650000"),
            workload_ratio=d("0.750000"),
            correction_follow_through_score=d("0.650000"),
        ),
        input_row(
            "equities",
            "index_team",
            calibration_score=d("0.400000"),
            memory_refreshed_at=GENERATED_AT - timedelta(days=40),
            evidence_coverage_score=d("0.300000"),
            workload_ratio=d("0.950000"),
            correction_follow_through_score=d("0.400000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().PUBLIC_DOMAIN_CATEGORIES == (
        "politics",
        "crypto",
        "equities",
        "commodities",
        "football",
        "basketball",
        "other",
    )
    assert api().PUBLIC_REVIEW_READINESS_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.domain_count == d("7.000000")
    assert report.observed_domain_count == d("3.000000")
    assert report.missing_domain_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("5.000000")
    assert report.average_readiness_score == d("0.244722")
    assert report.weakest_readiness_score == d("0.000000")

    by_domain = {row.domain_category: row for row in report.rows}
    assert set(by_domain) == set(api().PUBLIC_DOMAIN_CATEGORIES)
    assert by_domain["politics"].status == "pass"
    assert by_domain["politics"].readiness_score == d("0.909722")
    assert by_domain["politics"].reason_codes == ("domain_review_readiness_pass",)
    assert by_domain["crypto"].status == "watch"
    assert by_domain["crypto"].memory_freshness_score == d("0.666667")
    assert by_domain["crypto"].workload_health_score == d("0.250000")
    assert by_domain["crypto"].reason_codes == (
        "domain_review_readiness_calibration_watch",
        "domain_review_readiness_memory_freshness_watch",
        "domain_review_readiness_coverage_watch",
        "domain_review_readiness_workload_watch",
        "domain_review_readiness_correction_follow_through_watch",
    )
    assert by_domain["equities"].status == "block"
    assert by_domain["equities"].memory_freshness_score == d("0.000000")
    assert by_domain["equities"].reason_codes == (
        "domain_review_readiness_calibration_block",
        "domain_review_readiness_memory_freshness_block",
        "domain_review_readiness_coverage_block",
        "domain_review_readiness_workload_block",
        "domain_review_readiness_correction_follow_through_block",
    )
    assert by_domain["basketball"].status == "block"
    assert by_domain["basketball"].reason_codes == (
        "domain_review_readiness_missing_domain",
    )

    payload = api().research_team_domain_review_readiness_report_payload(report)
    reversed_payload = api().research_team_domain_review_readiness_report_payload(
        reversed_report,
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][-1]["domain_category"] == "politics"
    assert _float_or_int_paths(payload) == ()
    assert not any(isinstance(value, Decimal) for value in _walk(payload))
    json.dumps(payload, sort_keys=True)


def test_report_contract_is_frozen_decimal_only_and_flag_hardened() -> None:
    module = api()
    report = build_report(input_row("politics", "policy_team"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_READINESS_CONFIG_VERSION",
        "PUBLIC_DOMAIN_CATEGORIES",
        "PUBLIC_REVIEW_READINESS_STATUSES",
        "ResearchTeamDomainReviewReadinessConfig",
        "ResearchTeamDomainReviewReadinessInput",
        "ResearchTeamDomainReviewReadinessReport",
        "ResearchTeamDomainReviewReadinessRow",
        "build_research_team_domain_review_readiness_report",
        "research_team_domain_review_readiness_report_digest",
        "research_team_domain_review_readiness_report_payload",
        "validate_research_team_domain_review_readiness_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    empty = build_report()
    assert empty.status == "block"
    assert empty.reason_codes == (
        "domain_review_readiness_no_inputs",
        "domain_review_readiness_block_present",
        "domain_review_readiness_missing_domain_present",
    )
    assert empty.rows and len(empty.rows) == 7

    for value in (config(), input_row("politics", "policy_team"), report, *report.rows):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="calibration_score must be a Decimal"):
        input_row("politics", "policy_team", calibration_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_coverage_score must be a Decimal"):
        input_row(
            "politics",
            "policy_team",
            evidence_coverage_score=DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="memory_refreshed_at must be UTC-aware"):
        input_row(
            "politics",
            "policy_team",
            memory_refreshed_at=datetime(2026, 7, 8, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            input_row("politics", "policy_team"),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
        )
    with pytest.raises(ValueError, match="domain team labels must be unique"):
        build_report(
            input_row("politics", "policy_team"),
            input_row("politics", "policy_team"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        input_row("politics", "market_slug_team")


def test_dataclass_and_public_payload_schemas_are_exact() -> None:
    module = api()
    expected_config_fields = (
        "config_version",
        "max_watch_memory_age_seconds",
        "min_pass_calibration_score",
        "min_watch_calibration_score",
        "min_pass_memory_freshness_score",
        "min_watch_memory_freshness_score",
        "min_pass_evidence_coverage_score",
        "min_watch_evidence_coverage_score",
        "min_pass_workload_health_score",
        "min_watch_workload_health_score",
        "min_pass_correction_follow_through_score",
        "min_watch_correction_follow_through_score",
        "paper_only",
        "report_only",
        "readonly",
    )
    expected_input_fields = (
        "domain_category",
        "team_label",
        "calibration_score",
        "memory_refreshed_at",
        "evidence_coverage_score",
        "workload_ratio",
        "correction_follow_through_score",
        "observed_at",
        "paper_only",
        "report_only",
        "readonly",
    )
    expected_row_fields = (
        "domain_category",
        "status",
        "team_count",
        "readiness_score",
        "calibration_score",
        "memory_freshness_score",
        "evidence_coverage_score",
        "workload_health_score",
        "correction_follow_through_score",
        "newest_memory_age_seconds",
        "oldest_memory_age_seconds",
        "newest_observation_age_seconds",
        "oldest_observation_age_seconds",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    expected_report_fields = (
        "generated_at",
        "config_version",
        "domain_count",
        "observed_domain_count",
        "missing_domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_readiness_score",
        "weakest_readiness_score",
        "average_calibration_score",
        "average_memory_freshness_score",
        "average_evidence_coverage_score",
        "average_workload_health_score",
        "average_correction_follow_through_score",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )

    assert tuple(
        field.name
        for field in fields(module.ResearchTeamDomainReviewReadinessConfig)
    ) == expected_config_fields
    assert tuple(
        field.name
        for field in fields(module.ResearchTeamDomainReviewReadinessInput)
    ) == expected_input_fields
    assert tuple(
        field.name
        for field in fields(module.ResearchTeamDomainReviewReadinessRow)
    ) == expected_row_fields
    assert tuple(
        field.name
        for field in fields(module.ResearchTeamDomainReviewReadinessReport)
    ) == expected_report_fields

    report = build_report(input_row("politics", "policy_team"))
    payload = module.research_team_domain_review_readiness_report_payload(report)
    assert tuple(payload) == expected_report_fields
    assert all(tuple(row) == expected_row_fields for row in payload["rows"])


def test_exported_dataclasses_are_final_and_frozen() -> None:
    module = api()
    values = (
        config(),
        input_row("politics", "policy_team"),
        build_report(input_row("politics", "policy_team")),
    )
    values += values[-1].rows

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.readonly = False

    for base in (
        module.ResearchTeamDomainReviewReadinessConfig,
        module.ResearchTeamDomainReviewReadinessInput,
        module.ResearchTeamDomainReviewReadinessRow,
        module.ResearchTeamDomainReviewReadinessReport,
    ):
        with pytest.raises(TypeError, match="subclass is not allowed"):
            type(f"Forged{base.__name__}", (base,), {})


@pytest.mark.parametrize("invalid_value", ("-0.0000001", "1.0000001"))
def test_ratio_bounds_are_checked_before_decimal_quantization(
    invalid_value: str,
) -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        input_row(
            "politics",
            "policy_team",
            calibration_score=d(invalid_value),
        )


def test_count_integrality_is_checked_before_decimal_quantization() -> None:
    report = build_report(input_row("politics", "policy_team"))
    politics = next(
        row for row in report.rows if row.domain_category == "politics"
    )

    with pytest.raises(ValueError, match="integer Decimal"):
        replace(politics, team_count=d("1.0000001"))


def test_nonnegative_age_bounds_are_checked_before_decimal_quantization() -> None:
    report = build_report(input_row("politics", "policy_team"))
    politics = next(
        row for row in report.rows if row.domain_category == "politics"
    )

    with pytest.raises(ValueError, match="nonnegative"):
        replace(
            politics,
            newest_observation_age_seconds=d("-0.0000001"),
        )


def test_signed_zero_is_canonicalized_in_memory_and_rejected_in_payloads() -> None:
    module = api()
    item = input_row(
        "politics",
        "policy_team",
        workload_ratio=d("-0.000000"),
    )
    report = build_report(item)

    for value in (item, report, *report.rows):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if type(field_value) is Decimal and field_value.is_zero():
                assert field_value.is_signed() is False

    payload = module.research_team_domain_review_readiness_report_payload(report)
    payload["missing_domain_count"] = "-0.000000"
    resign(payload)
    with pytest.raises(ValueError, match="canonical Decimal string"):
        module.validate_research_team_domain_review_readiness_public_payload(
            payload,
        )


def test_elapsed_seconds_preserve_decimal_microsecond_precision() -> None:
    report = build_report(
        input_row(
            "politics",
            "policy_team",
            memory_refreshed_at=GENERATED_AT - timedelta(seconds=1, microseconds=500000),
            observed_at=GENERATED_AT - timedelta(microseconds=250000),
        ),
    )
    politics = next(
        row for row in report.rows if row.domain_category == "politics"
    )

    assert politics.newest_memory_age_seconds == d("1.500000")
    assert politics.oldest_memory_age_seconds == d("1.500000")
    assert politics.newest_observation_age_seconds == d("0.250000")
    assert politics.oldest_observation_age_seconds == d("0.250000")


def test_row_rejects_derived_reason_status_forgery() -> None:
    report = build_report(input_row("politics", "policy_team"))
    politics = next(
        row for row in report.rows if row.domain_category == "politics"
    )

    with pytest.raises(
        ValueError,
        match="reason_codes are inconsistent with component scores",
    ):
        replace(
            politics,
            status="block",
            reason_codes=("domain_review_readiness_calibration_block",),
        )


@pytest.mark.parametrize(
    ("oldest_field", "forged_value"),
    (
        ("oldest_memory_age_seconds", "7200.000000"),
        ("oldest_observation_age_seconds", "600.000000"),
    ),
)
def test_re_signed_payload_rejects_single_team_age_extrema_forgery(
    oldest_field: str,
    forged_value: str,
) -> None:
    module = api()
    payload = module.research_team_domain_review_readiness_report_payload(
        build_report(input_row("politics", "policy_team")),
    )
    politics = next(
        row for row in payload["rows"] if row["domain_category"] == "politics"
    )
    politics[oldest_field] = forged_value
    payload["derived_validation_digest"] = canonical_digest(payload)

    with pytest.raises(ValueError, match="single-team .* ages must match"):
        module.validate_research_team_domain_review_readiness_public_payload(
            payload,
        )


def test_re_signed_payload_rejects_memory_score_outside_age_count_bounds() -> None:
    module = api()
    payload = module.research_team_domain_review_readiness_report_payload(
        build_report(input_row("politics", "policy_team")),
    )
    politics = next(
        row for row in payload["rows"] if row["domain_category"] == "politics"
    )
    politics["team_count"] = "2.000000"
    politics["oldest_memory_age_seconds"] = "7200.000000"
    payload["derived_validation_digest"] = canonical_digest(payload)

    with pytest.raises(
        ValueError,
        match="memory_freshness_score is inconsistent with memory ages",
    ):
        module.validate_research_team_domain_review_readiness_public_payload(
            payload,
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("domain_count", "8.000000"),
        ("observed_domain_count", "2.000000"),
        ("missing_domain_count", "5.000000"),
        ("pass_count", "0.000000"),
        ("watch_count", "1.000000"),
        ("block_count", "5.000000"),
        ("average_readiness_score", "0.500000"),
        ("weakest_readiness_score", "0.100000"),
        ("average_calibration_score", "0.500000"),
        ("average_memory_freshness_score", "0.500000"),
        ("average_evidence_coverage_score", "0.500000"),
        ("average_workload_health_score", "0.500000"),
        ("average_correction_follow_through_score", "0.500000"),
        ("status", "watch"),
        (
            "reason_codes",
            ["domain_review_readiness_watch_present"],
        ),
    ),
)
def test_re_signed_payload_rejects_derived_report_forgeries(
    field_name: str,
    forged_value: object,
) -> None:
    module = api()
    payload = module.research_team_domain_review_readiness_report_payload(
        build_report(input_row("politics", "policy_team")),
    )
    payload[field_name] = forged_value
    resign(payload)

    with pytest.raises(ValueError, match=field_name):
        module.validate_research_team_domain_review_readiness_public_payload(
            payload,
        )


@pytest.mark.parametrize(
    ("forged_values", "error_match"),
    (
        ({"status": "block"}, "status is inconsistent with reason_codes"),
        (
            {
                "status": "watch",
                "reason_codes": ["domain_review_readiness_calibration_watch"],
            },
            "reason_codes are inconsistent with component scores",
        ),
        (
            {"readiness_score": "0.100000"},
            "readiness_score is inconsistent with component scores",
        ),
        (
            {
                "status": "watch",
                "readiness_score": "0.810000",
                "memory_freshness_score": "0.500000",
                "reason_codes": ["domain_review_readiness_memory_freshness_watch"],
            },
            "memory_freshness_score is inconsistent with memory ages",
        ),
    ),
)
def test_re_signed_payload_rejects_derived_row_forgeries(
    forged_values: dict[str, object],
    error_match: str,
) -> None:
    module = api()
    payload = module.research_team_domain_review_readiness_report_payload(
        build_report(input_row("politics", "policy_team")),
    )
    politics = next(
        row for row in payload["rows"] if row["domain_category"] == "politics"
    )
    politics.update(forged_values)
    resign(payload)

    with pytest.raises(ValueError, match=error_match):
        module.validate_research_team_domain_review_readiness_public_payload(
            payload,
        )


def test_public_payload_validator_rejects_identifier_evidence_and_live_surface_leaks() -> None:
    module = api()
    report = build_report(input_row("politics", "policy_team"))
    payload = module.research_team_domain_review_readiness_report_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.research_team_domain_review_readiness_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    module.validate_research_team_domain_review_readiness_public_payload(payload)

    for unsafe_key in (
        "candidate_id",
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
        "position_sizing",
    ):
        forged_payload = dict(payload)
        forged_payload[unsafe_key] = "public_aggregate"
        forged_payload["derived_validation_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match="unsafe|public aggregate"):
            module.research_team_domain_review_readiness_report_payload(forged_payload)

    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_team_domain_review_readiness_public_payload(
            {**payload, "domain_count": 1},
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_research_team_domain_review_readiness_public_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_team_domain_review_readiness_public_payload(
            {**payload, "status": "watch"},
        )

    public_json = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "policy_team",
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in public_json


def test_public_payload_validator_enforces_exact_canonical_schema() -> None:
    module = api()
    payload = module.research_team_domain_review_readiness_report_payload(
        build_report(input_row("politics", "policy_team")),
    )

    invalid_payloads: list[dict[str, Any]] = []

    extra_top_level = deepcopy(payload)
    extra_top_level["summary_label"] = "aggregate"
    invalid_payloads.append(extra_top_level)

    missing_top_level = deepcopy(payload)
    missing_top_level.pop("average_calibration_score")
    invalid_payloads.append(missing_top_level)

    extra_row_field = deepcopy(payload)
    extra_row_field["rows"][0]["summary_label"] = "aggregate"
    invalid_payloads.append(extra_row_field)

    missing_row_field = deepcopy(payload)
    missing_row_field["rows"][0].pop("team_count")
    invalid_payloads.append(missing_row_field)

    noncanonical_decimal = deepcopy(payload)
    noncanonical_decimal["domain_count"] = "7"
    invalid_payloads.append(noncanonical_decimal)

    noncanonical_datetime = deepcopy(payload)
    noncanonical_datetime["generated_at"] = "2026-07-08T12:00:00Z"
    invalid_payloads.append(noncanonical_datetime)

    noncanonical_reason_container = deepcopy(payload)
    noncanonical_reason_container["reason_codes"] = tuple(
        noncanonical_reason_container["reason_codes"],
    )
    invalid_payloads.append(noncanonical_reason_container)

    inconsistent_count = deepcopy(payload)
    inconsistent_count["domain_count"] = "8.000000"
    invalid_payloads.append(inconsistent_count)

    noncanonical_row_order = deepcopy(payload)
    noncanonical_row_order["rows"] = list(reversed(noncanonical_row_order["rows"]))
    invalid_payloads.append(noncanonical_row_order)

    downgraded_nested_flag = deepcopy(payload)
    downgraded_nested_flag["rows"][0]["readonly"] = False
    invalid_payloads.append(downgraded_nested_flag)

    unsupported_config = deepcopy(payload)
    unsupported_config["config_version"] = "research-team-domain-review-readiness-report-v1"
    invalid_payloads.append(unsupported_config)

    for invalid_payload in invalid_payloads:
        invalid_payload["derived_validation_digest"] = canonical_digest(invalid_payload)
        with pytest.raises(ValueError):
            module.validate_research_team_domain_review_readiness_public_payload(
                invalid_payload,
            )


def test_module_scope_is_pure_in_memory_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "subprocess",
        "socket",
        "open(",
        "getenv",
        "environ",
        "postgres",
        "://",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "append_order",
                "authenticate",
                "cancel",
                "connect",
                "execute",
                "executemany",
                "open",
                "persist",
                "place",
                "request",
                "recommend",
                "save",
                "send",
                "post",
                "put",
                "patch",
                "place_order",
                "submit_order",
                "cancel_order",
                "touch",
                "trade",
                "unlink",
                "write",
                "write_bytes",
                "write_text",
            }

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }
    assert not imported_roots.intersection(
        {
            "aiohttp",
            "httpx",
            "os",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "subprocess",
            "supabase",
            "urllib",
        },
    )


def _walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in _walk(nested))
    return (value,)


def _float_or_int_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if type(value) in (float, int):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_or_int_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_or_int_paths(nested, child))
        return tuple(paths)
    return ()
