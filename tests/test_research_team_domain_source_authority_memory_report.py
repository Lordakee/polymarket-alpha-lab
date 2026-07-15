from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import (
    DefaultContext,
    Decimal,
    Inexact,
    InvalidOperation,
    ROUND_DOWN,
    localcontext,
)
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_source_authority_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    return module.ResearchTeamDomainSourceAuthorityMemoryConfig(**overrides)


def input_row(
    domain_label: str,
    team_label: str,
    authority_family_label: str,
    *,
    authority_memory_count: Decimal = d("150.000000"),
    verified_authority_memory_count: Decimal = d("140.000000"),
    authority_score: Decimal = d("0.920000"),
    memory_age_seconds: Decimal = d("3600.000000"),
    contradiction_ratio: Decimal = d("0.020000"),
    observed_at: datetime = OBSERVED_AT,
):
    module = api()
    return module.ResearchTeamDomainSourceAuthorityMemoryInput(
        domain_label=domain_label,
        team_label=team_label,
        authority_family_label=authority_family_label,
        authority_memory_count=authority_memory_count,
        verified_authority_memory_count=verified_authority_memory_count,
        authority_score=authority_score,
        memory_age_seconds=memory_age_seconds,
        contradiction_ratio=contradiction_ratio,
        observed_at=observed_at,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_source_authority_memory_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_team_domain_authority_memory_scores_rows_and_digest() -> None:
    rows = (
        input_row("sports_tennis", "team_match_results", "official_results"),
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_memory_count=d("20.000000"),
            verified_authority_memory_count=d("10.000000"),
            authority_score=d("0.450000"),
            memory_age_seconds=d("900000.000000"),
            contradiction_ratio=d("0.400000"),
        ),
        input_row(
            "weather_extremes",
            "team_forecast_models",
            "agency_bulletins",
            authority_memory_count=d("80.000000"),
            verified_authority_memory_count=d("60.000000"),
            authority_score=d("0.700000"),
            memory_age_seconds=d("172800.000000"),
            contradiction_ratio=d("0.150000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.report_mode == "paper_authority_memory_block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.watch_block_ratio == d("0.666667")
    assert report.min_memory_coverage_ratio == d("0.500000")
    assert report.min_authority_score == d("0.450000")
    assert report.max_memory_age_seconds == d("900000.000000")
    assert report.max_contradiction_ratio == d("0.400000")
    assert report.max_authority_pressure_score == d("1.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.authority_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.domain_label == "macro_rates"
    assert blocked.memory_coverage_ratio == d("0.500000")
    assert blocked.authority_pressure_score == d("1.000000")
    assert blocked.memory_staleness_ratio == d("1.000000")
    assert blocked.reason_codes == (
        "source_authority_memory_coverage_block",
        "source_authority_score_block",
        "source_authority_memory_staleness_block",
        "source_authority_contradiction_block",
    )
    assert watched.authority_pressure_score == d("0.750000")
    assert watched.reason_codes == (
        "source_authority_memory_coverage_watch",
        "source_authority_score_watch",
        "source_authority_memory_staleness_watch",
        "source_authority_contradiction_watch",
    )
    assert passed.reason_codes == ("source_authority_memory_pass",)
    assert (
        api().ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount(
            reason_code="source_authority_memory_staleness_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
        in report.reason_code_counts
    )

    payload = api().research_team_domain_source_authority_memory_report_payload(report)
    reversed_payload = (
        api().research_team_domain_source_authority_memory_report_payload(
            reversed_report,
        )
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["authority_pressure_score"] == "1.000000"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_team_domain_authority_memory_is_report_only_public_safe() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_CONFIG_VERSION",
        "RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_STATUSES",
        "ResearchTeamDomainSourceAuthorityMemoryConfig",
        "ResearchTeamDomainSourceAuthorityMemoryInput",
        "ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount",
        "ResearchTeamDomainSourceAuthorityMemoryReport",
        "ResearchTeamDomainSourceAuthorityMemoryRow",
        "build_research_team_domain_source_authority_memory_report",
        "research_team_domain_source_authority_memory_report_digest",
        "research_team_domain_source_authority_memory_report_payload",
        "validate_research_team_domain_source_authority_memory_report_digest",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    empty = build_report()
    assert empty.status == "pass"
    assert empty.report_mode == "paper_authority_memory_monitor"
    assert empty.reason_codes == ("source_authority_memory_empty",)
    assert empty.input_count == ZERO
    assert empty.row_count == ZERO
    assert empty.reason_code_counts == ()
    assert empty.rows == ()

    populated = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    for value in (
        populated,
        *populated.rows,
        *populated.reason_code_counts,
        config(),
        input_row("macro_rates", "team_policy_events", "central_bank_filings"),
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item is None:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_score=0.5,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            observed_at=datetime(2026, 7, 9, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            input_row("macro_rates", "team_policy_events", "central_bank_filings"),
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="team-domain-authority labels must be unique"):
        build_report(
            input_row("macro_rates", "team_policy_events", "central_bank_filings"),
            input_row("macro_rates", "team_policy_events", "central_bank_filings"),
        )
    with pytest.raises(ValueError, match="authority_score"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_score=d("1.100000"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        input_row("macro_market_ref", "team_policy_events", "central_bank_filings")
    with pytest.raises(ValueError, match="verified_authority_memory_count"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_memory_count=d("10.000000"),
            verified_authority_memory_count=d("11.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_memory_coverage_ratio"):
        config(
            min_pass_memory_coverage_ratio=d("0.700000"),
            min_watch_memory_coverage_ratio=d("0.900000"),
        )

    payload = module.research_team_domain_source_authority_memory_report_payload(
        populated,
    )
    assert module.research_team_domain_source_authority_memory_report_digest(populated) == (
        payload["derived_validation_digest"]
    )
    assert module.validate_research_team_domain_source_authority_memory_report_digest(
        payload,
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "wallet_ref",
        "order_ref",
        "trade_ref",
        "sizing_model",
        "recommendation",
    ):
        forged_payload = dict(payload)
        forged_payload[unsafe_key] = "public_aggregate"
        forged_payload["derived_validation_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match="public aggregate labels"):
            module.research_team_domain_source_authority_memory_report_payload(
                forged_payload,
            )

    module_source = module.__loader__.get_source(module.__name__)
    assert module_source is not None
    tree = ast.parse(module_source)
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


def test_payload_validation_rejects_tampering_and_public_leaks() -> None:
    module = api()
    report = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    row = report.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            authority_score=d("0.700000"),
            derived_validation_digest=row.derived_validation_digest,
        )

    payload = module.research_team_domain_source_authority_memory_report_payload(report)

    tampered = dict(payload)
    tampered["status"] = "clear"
    tampered["derived_validation_digest"] = canonical_digest(tampered)
    with pytest.raises(ValueError, match="status"):
        module.research_team_domain_source_authority_memory_report_payload(tampered)

    leaked = dict(payload)
    leaked["rows"] = [dict(payload["rows"][0])]
    leaked["rows"][0]["domain_label"] = "market_slug"
    leaked["rows"][0]["derived_validation_digest"] = _row_digest(leaked["rows"][0])
    leaked["derived_validation_digest"] = canonical_digest(leaked)
    with pytest.raises(ValueError, match="public aggregate labels"):
        module.research_team_domain_source_authority_memory_report_payload(leaked)

    numeric = dict(payload)
    numeric["input_count"] = 1
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_source_authority_memory_report_payload(numeric)


def test_public_labels_reject_authentication_and_personal_identifiers() -> None:
    for private_label in (
        "account_session",
        "password_reset",
        "oauth_bearer",
        "user_email",
        "phone_number",
        "ip_address",
    ):
        with pytest.raises(ValueError, match="public aggregate labels"):
            input_row(private_label, "team_public", "authority_public")


def test_public_mapping_requires_exact_json_payload_types() -> None:
    module = api()
    payload = module.research_team_domain_source_authority_memory_report_payload(
        build_report(
            input_row("sports_tennis", "team_match_results", "official_results"),
        ),
    )

    decimal_value = json.loads(json.dumps(payload))
    decimal_value["input_count"] = d("1.000000")
    datetime_value = json.loads(json.dumps(payload))
    datetime_value["generated_at"] = GENERATED_AT
    tuple_value = json.loads(json.dumps(payload))
    tuple_value["reason_codes"] = tuple(tuple_value["reason_codes"])

    for forged in (decimal_value, datetime_value, tuple_value):
        with pytest.raises(ValueError, match="public payload"):
            module.research_team_domain_source_authority_memory_report_payload(forged)


def test_raw_decimal_bounds_signed_zero_and_ambient_context_are_safe() -> None:
    module = api()

    with pytest.raises(ValueError, match="authority_score.*between 0 and 1"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_score=d("-0.0000004"),
        )
    with pytest.raises(ValueError, match="authority_score.*between 0 and 1"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_score=d("1.0000004"),
        )
    with pytest.raises(ValueError, match="authority_score.*signed zero"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_score=d("-0.000000"),
        )

    built = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    with pytest.raises(ValueError, match="authority_memory_count.*nonnegative"):
        replace(built.rows[0], authority_memory_count=d("-0.0000004"))
    with pytest.raises(ValueError, match="authority_rank.*whole count"):
        replace(built.rows[0], authority_rank=d("1.0000004"))

    signed_zero_payload = json.loads(
        json.dumps(module.research_team_domain_source_authority_memory_report_payload(built)),
    )
    signed_zero_payload["rows"][0]["authority_pressure_score"] = "-0.000000"
    signed_zero_payload["derived_validation_digest"] = canonical_digest(signed_zero_payload)
    with pytest.raises(ValueError, match="signed zero"):
        module.research_team_domain_source_authority_memory_report_payload(
            signed_zero_payload,
        )

    with localcontext() as ambient:
        ambient.prec = 4
        ambient.rounding = ROUND_DOWN
        ambient.traps[InvalidOperation] = True
        actual = build_report(
            input_row(
                "macro_rates",
                "team_policy_events",
                "central_bank_filings",
                authority_memory_count=d("3.000000"),
                verified_authority_memory_count=d("2.000000"),
            ),
        )

    assert actual.rows[0].memory_coverage_ratio == d("0.666667")


def test_authority_memory_counts_must_be_whole_decimals() -> None:
    with pytest.raises(ValueError, match="authority_memory_count must be a whole count"):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            authority_memory_count=d("150.500000"),
        )
    with pytest.raises(
        ValueError,
        match="verified_authority_memory_count must be a whole count",
    ):
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_filings",
            verified_authority_memory_count=d("140.500000"),
        )


def test_ambient_decimal_context_cannot_change_pressure_ordering() -> None:
    lower_pressure = input_row(
        "alpha_domain",
        "team_alpha",
        "family_alpha",
        authority_score=d("0.678000"),
    )
    higher_pressure = input_row(
        "zeta_domain",
        "team_zeta",
        "family_zeta",
        authority_score=d("0.672000"),
    )

    with localcontext() as ambient:
        ambient.prec = 1
        ambient.rounding = ROUND_DOWN
        report = build_report(lower_pressure, higher_pressure)

    assert tuple(row.domain_label for row in report.rows) == (
        "zeta_domain",
        "alpha_domain",
    )


def test_decimal_calculations_do_not_trust_a_mutable_context_template() -> None:
    module = api()
    original_context = module.DECIMAL_CONTEXT
    module.DECIMAL_CONTEXT = original_context.copy()
    module.DECIMAL_CONTEXT.prec = 4
    module.DECIMAL_CONTEXT.rounding = ROUND_DOWN
    try:
        report = build_report(
            input_row(
                "macro_rates",
                "team_policy_events",
                "central_bank_filings",
                authority_memory_count=d("3.000000"),
                verified_authority_memory_count=d("2.000000"),
            ),
        )
    finally:
        module.DECIMAL_CONTEXT = original_context

    assert report.rows[0].memory_coverage_ratio == d("0.666667")


def test_decimal_calculations_do_not_inherit_mutable_default_context() -> None:
    original_context = DefaultContext.copy()
    DefaultContext.Emax = 4
    DefaultContext.traps[Inexact] = True
    try:
        report = build_report(
            input_row(
                "macro_rates",
                "team_policy_events",
                "central_bank_filings",
                authority_memory_count=d("3.000000"),
                verified_authority_memory_count=d("2.000000"),
            ),
        )
    finally:
        DefaultContext.prec = original_context.prec
        DefaultContext.rounding = original_context.rounding
        DefaultContext.Emin = original_context.Emin
        DefaultContext.Emax = original_context.Emax
        DefaultContext.capitals = original_context.capitals
        DefaultContext.clamp = original_context.clamp
        DefaultContext.clear_flags()
        for signal, enabled in original_context.flags.items():
            DefaultContext.flags[signal] = enabled
        for signal, enabled in original_context.traps.items():
            DefaultContext.traps[signal] = enabled

    assert report.rows[0].memory_coverage_ratio == d("0.666667")


def test_resigned_payload_rederives_rows_aggregates_and_reason_counts() -> None:
    module = api()
    built = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    payload = module.research_team_domain_source_authority_memory_report_payload(built)

    forged_row = json.loads(json.dumps(payload))
    forged_row["rows"][0]["authority_score"] = "0.700000"
    forged_row["rows"][0]["derived_validation_digest"] = _row_digest(
        forged_row["rows"][0],
    )
    forged_row["derived_validation_digest"] = canonical_digest(forged_row)
    with pytest.raises(
        ValueError,
        match="authority_pressure_score|status|reason_codes",
    ):
        module.research_team_domain_source_authority_memory_report_payload(forged_row)

    forged_aggregate = json.loads(json.dumps(payload))
    forged_aggregate["pass_count"] = "2.000000"
    forged_aggregate["derived_validation_digest"] = canonical_digest(forged_aggregate)
    with pytest.raises(ValueError, match="pass_count"):
        module.research_team_domain_source_authority_memory_report_payload(
            forged_aggregate,
        )

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["count"] = "2.000000"
    forged_reason_count["derived_validation_digest"] = canonical_digest(
        forged_reason_count,
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_team_domain_source_authority_memory_report_payload(
            forged_reason_count,
        )


def test_resigned_payload_rejects_duplicate_reason_codes_explicitly() -> None:
    module = api()
    payload = module.research_team_domain_source_authority_memory_report_payload(
        build_report(
            input_row("sports_tennis", "team_match_results", "official_results"),
        ),
    )
    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["reason_codes"].append(
        forged["rows"][0]["reason_codes"][0],
    )
    forged["rows"][0]["derived_validation_digest"] = _row_digest(
        forged["rows"][0],
    )
    forged["derived_validation_digest"] = canonical_digest(forged)

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.research_team_domain_source_authority_memory_report_payload(forged)


def test_resigned_payload_rejects_observations_after_report_as_of() -> None:
    module = api()
    payload = module.research_team_domain_source_authority_memory_report_payload(
        build_report(
            input_row("sports_tennis", "team_match_results", "official_results"),
        ),
    )
    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["observed_at"] = "2026-07-09T12:00:00.000001+00:00"
    forged["rows"][0]["derived_validation_digest"] = _row_digest(
        forged["rows"][0],
    )
    forged["derived_validation_digest"] = canonical_digest(forged)

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.research_team_domain_source_authority_memory_report_payload(forged)


def test_public_dataclass_and_payload_schemas_are_exact_ordered_and_final() -> None:
    module = api()
    built = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    expected_fields = {
        module.ResearchTeamDomainSourceAuthorityMemoryConfig: (
            "config_version",
            "min_pass_memory_coverage_ratio",
            "min_watch_memory_coverage_ratio",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
            "max_pass_contradiction_ratio",
            "max_watch_contradiction_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSourceAuthorityMemoryInput: (
            "domain_label",
            "team_label",
            "authority_family_label",
            "authority_memory_count",
            "verified_authority_memory_count",
            "authority_score",
            "memory_age_seconds",
            "contradiction_ratio",
            "observed_at",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSourceAuthorityMemoryRow: (
            "authority_rank",
            "domain_label",
            "team_label",
            "authority_family_label",
            "status",
            "authority_pressure_score",
            "authority_memory_count",
            "verified_authority_memory_count",
            "memory_coverage_ratio",
            "authority_score",
            "memory_age_seconds",
            "memory_staleness_ratio",
            "contradiction_ratio",
            "observed_at",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount: (
            "reason_code",
            "count",
            "row_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSourceAuthorityMemoryReport: (
            "generated_at",
            "config_version",
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "watch_block_ratio",
            "min_memory_coverage_ratio",
            "min_authority_score",
            "max_memory_age_seconds",
            "max_contradiction_ratio",
            "max_authority_pressure_score",
            "status",
            "report_mode",
            "reason_codes",
            "reason_code_counts",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    for cls, schema in expected_fields.items():
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(cls)) == schema
        with pytest.raises(TypeError, match="subclass|subclassed"):
            type(f"Invalid{cls.__name__}", (cls,), {})

    payload = module.research_team_domain_source_authority_memory_report_payload(built)
    assert tuple(payload) == expected_fields[type(built)]
    assert tuple(payload["rows"][0]) == expected_fields[type(built.rows[0])]
    assert tuple(payload["reason_code_counts"][0]) == expected_fields[
        type(built.reason_code_counts[0])
    ]

    reversed_report = dict(reversed(tuple(payload.items())))
    reversed_report["derived_validation_digest"] = canonical_digest(reversed_report)
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_source_authority_memory_report_payload(
            reversed_report,
        )

    reversed_row = json.loads(json.dumps(payload))
    reversed_row["rows"][0] = dict(reversed(tuple(reversed_row["rows"][0].items())))
    reversed_row["rows"][0]["derived_validation_digest"] = _row_digest(
        reversed_row["rows"][0],
    )
    reversed_row["derived_validation_digest"] = canonical_digest(reversed_row)
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_source_authority_memory_report_payload(reversed_row)

    reversed_reason_count = json.loads(json.dumps(payload))
    reversed_reason_count["reason_code_counts"][0] = dict(
        reversed(tuple(reversed_reason_count["reason_code_counts"][0].items())),
    )
    reversed_reason_count["derived_validation_digest"] = canonical_digest(
        reversed_reason_count,
    )
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_source_authority_memory_report_payload(
            reversed_reason_count,
        )


def test_report_dataclass_requires_the_supported_config_version() -> None:
    report = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )

    with pytest.raises(ValueError, match="config_version must be the supported"):
        replace(
            report,
            config_version="research-team-domain-source-authority-memory-report-v2",
            derived_validation_digest="",
        )


def test_final_dataclasses_cannot_be_subclassed_through_a_noncooperative_mixin() -> None:
    module = api()

    class NonCooperativeMixin:
        def __init_subclass__(cls, **kwargs: object) -> None:
            del kwargs

    for dataclass_type in (
        module.ResearchTeamDomainSourceAuthorityMemoryConfig,
        module.ResearchTeamDomainSourceAuthorityMemoryInput,
        module.ResearchTeamDomainSourceAuthorityMemoryRow,
        module.ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount,
        module.ResearchTeamDomainSourceAuthorityMemoryReport,
    ):
        with pytest.raises(TypeError, match="subclass"):
            type(
                f"Invalid{dataclass_type.__name__}",
                (NonCooperativeMixin, dataclass_type),
                {},
            )


def test_digest_fields_reject_none_instead_of_treating_it_as_automatic() -> None:
    report = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )

    with pytest.raises(ValueError, match="derived_validation_digest must be a string"):
        replace(report.rows[0], derived_validation_digest=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="derived_validation_digest must be a string"):
        replace(report, derived_validation_digest=None)  # type: ignore[arg-type]


def test_object_setattr_tampering_of_config_and_inputs_is_revalidated() -> None:
    tampered_config = config()
    object.__setattr__(
        tampered_config,
        "min_watch_authority_score",
        d("-0.100000"),
    )
    with pytest.raises(ValueError, match="min_watch_authority_score.*between 0 and 1"):
        build_report(
            input_row("sports_tennis", "team_match_results", "official_results"),
            cfg=tampered_config,
        )

    tampered_input = input_row(
        "macro_rates",
        "team_policy_events",
        "central_bank_filings",
    )
    object.__setattr__(
        tampered_input,
        "observed_at",
        datetime(2026, 7, 9, 11, 45),
    )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        build_report(tampered_input)


def test_object_setattr_tampering_of_nested_rows_and_reason_counts_is_revalidated() -> None:
    module = api()

    row_tampered = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    object.__setattr__(row_tampered.rows[0], "authority_score", d("0.700000"))
    row_payload = module._json_ready(asdict(row_tampered.rows[0]))
    object.__setattr__(
        row_tampered.rows[0],
        "derived_validation_digest",
        _row_digest(row_payload),
    )
    report_payload = module._json_ready(asdict(row_tampered))
    object.__setattr__(
        row_tampered,
        "derived_validation_digest",
        canonical_digest(report_payload),
    )
    with pytest.raises(
        ValueError,
        match="authority_pressure_score|status|reason_codes",
    ):
        module.research_team_domain_source_authority_memory_report_payload(
            row_tampered,
        )

    reason_count_tampered = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    object.__setattr__(
        reason_count_tampered.reason_code_counts[0],
        "count",
        d("2.000000"),
    )
    report_payload = module._json_ready(asdict(reason_count_tampered))
    object.__setattr__(
        reason_count_tampered,
        "derived_validation_digest",
        canonical_digest(report_payload),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_team_domain_source_authority_memory_report_payload(
            reason_count_tampered,
        )


def test_report_construction_revalidates_nested_hard_flags() -> None:
    tampered = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    object.__setattr__(tampered.rows[0], "readonly", False)

    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(tampered, derived_validation_digest="")


def test_report_construction_revalidates_nested_row_digest() -> None:
    tampered = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    object.__setattr__(
        tampered.rows[0],
        "observed_at",
        OBSERVED_AT - timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(tampered, derived_validation_digest="")


def test_report_construction_revalidates_nested_row_semantics() -> None:
    module = api()
    tampered = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    object.__setattr__(
        tampered.rows[0],
        "verified_authority_memory_count",
        d("130.000000"),
    )
    row_payload = module._json_ready(asdict(tampered.rows[0]))
    object.__setattr__(
        tampered.rows[0],
        "derived_validation_digest",
        _row_digest(row_payload),
    )

    with pytest.raises(ValueError, match="memory_coverage_ratio must match"):
        replace(tampered, derived_validation_digest="")


def test_report_construction_rejects_resigned_impossible_status_pressure() -> None:
    module = api()
    tampered = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    object.__setattr__(
        tampered.rows[0],
        "authority_pressure_score",
        d("0.500000"),
    )
    row_payload = module._json_ready(asdict(tampered.rows[0]))
    object.__setattr__(
        tampered.rows[0],
        "derived_validation_digest",
        _row_digest(row_payload),
    )

    with pytest.raises(
        ValueError,
        match="authority_pressure_score must be zero for pass rows",
    ):
        replace(
            tampered,
            max_authority_pressure_score=d("0.500000"),
            derived_validation_digest="",
        )


def test_row_construction_rejects_resigned_reason_status_conflict() -> None:
    module = api()
    row = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    ).rows[0]
    object.__setattr__(row, "status", "watch")
    row_payload = module._json_ready(asdict(row))
    object.__setattr__(row, "derived_validation_digest", _row_digest(row_payload))

    with pytest.raises(ValueError, match="status must match reason code severity"):
        replace(row)


def test_report_construction_revalidates_rows_before_sorting() -> None:
    module = api()
    tampered = build_report(
        input_row("sports_tennis", "team_match_results", "official_results"),
    )
    object.__setattr__(tampered.rows[0], "status", "forged")
    row_payload = module._json_ready(asdict(tampered.rows[0]))
    object.__setattr__(
        tampered.rows[0],
        "derived_validation_digest",
        _row_digest(row_payload),
    )

    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(tampered, derived_validation_digest="")


def test_deterministic_tie_breaks_and_resigned_row_order_are_canonical() -> None:
    module = api()
    tied_rows = (
        input_row("beta_domain", "team_b", "family_b"),
        input_row("alpha_domain", "team_b", "family_b"),
        input_row("alpha_domain", "team_a", "family_b"),
        input_row("alpha_domain", "team_a", "family_a"),
    )

    forward = build_report(*tied_rows)
    reversed_report = build_report(*reversed(tied_rows))

    assert tuple(
        (row.domain_label, row.team_label, row.authority_family_label)
        for row in forward.rows
    ) == (
        ("alpha_domain", "team_a", "family_a"),
        ("alpha_domain", "team_a", "family_b"),
        ("alpha_domain", "team_b", "family_b"),
        ("beta_domain", "team_b", "family_b"),
    )
    assert (
        module.research_team_domain_source_authority_memory_report_payload(forward)
        == module.research_team_domain_source_authority_memory_report_payload(
            reversed_report,
        )
    )

    payload = module.research_team_domain_source_authority_memory_report_payload(
        forward,
    )
    forged_order = json.loads(json.dumps(payload))
    forged_order["rows"] = list(reversed(forged_order["rows"]))
    forged_order["derived_validation_digest"] = canonical_digest(forged_order)
    with pytest.raises(ValueError, match="canonical|derived_validation_digest"):
        module.research_team_domain_source_authority_memory_report_payload(
            forged_order,
        )


def test_resigned_payload_rejects_noncanonical_authority_ranks() -> None:
    module = api()
    payload = module.research_team_domain_source_authority_memory_report_payload(
        build_report(
            input_row("sports_tennis", "team_match_results", "official_results"),
        ),
    )
    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["authority_rank"] = "2.000000"
    forged["rows"][0]["derived_validation_digest"] = _row_digest(
        forged["rows"][0],
    )
    forged["derived_validation_digest"] = canonical_digest(forged)

    with pytest.raises(ValueError, match="authority_rank must match canonical row order"):
        module.research_team_domain_source_authority_memory_report_payload(forged)


def _row_digest(row_payload: dict[str, Any]) -> str:
    unsigned = dict(row_payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _float_paths(value: object, prefix: str = "$") -> tuple[str, ...]:
    if type(value) is float:
        return (prefix,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{prefix}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{prefix}[{index}]"))
        return tuple(paths)
    return ()
