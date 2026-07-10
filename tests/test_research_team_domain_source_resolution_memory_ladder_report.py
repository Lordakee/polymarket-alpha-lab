from __future__ import annotations

import ast
import hashlib
import importlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_team_domain_source_resolution_memory_ladder_report",
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
    return module.ResearchTeamDomainSourceResolutionMemoryLadderConfig(**overrides)


def input_row(
    domain_label: str,
    team_label: str,
    source_family_label: str,
    *,
    resolution_memory_count: Decimal = d("120.000000"),
    verified_resolution_memory_count: Decimal = d("114.000000"),
    source_resolution_score: Decimal = d("0.920000"),
    memory_age_seconds: Decimal = d("3600.000000"),
    ladder_depth_count: Decimal = d("4.000000"),
    contradiction_ratio: Decimal = d("0.020000"),
    observed_at: datetime = OBSERVED_AT,
):
    module = api()
    return module.ResearchTeamDomainSourceResolutionMemoryLadderInput(
        domain_label=domain_label,
        team_label=team_label,
        source_family_label=source_family_label,
        resolution_memory_count=resolution_memory_count,
        verified_resolution_memory_count=verified_resolution_memory_count,
        source_resolution_score=source_resolution_score,
        memory_age_seconds=memory_age_seconds,
        ladder_depth_count=ladder_depth_count,
        contradiction_ratio=contradiction_ratio,
        observed_at=observed_at,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_source_resolution_memory_ladder_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_source_resolution_memory_ladder_scores_rows_and_digest() -> None:
    rows = (
        input_row("sports_results", "team_outcome_review", "official_results"),
        input_row(
            "macro_policy",
            "team_policy_review",
            "agency_releases",
            resolution_memory_count=d("20.000000"),
            verified_resolution_memory_count=d("8.000000"),
            source_resolution_score=d("0.450000"),
            memory_age_seconds=d("900000.000000"),
            ladder_depth_count=d("1.000000"),
            contradiction_ratio=d("0.400000"),
        ),
        input_row(
            "weather_events",
            "team_forecast_review",
            "agency_bulletins",
            resolution_memory_count=d("80.000000"),
            verified_resolution_memory_count=d("60.000000"),
            source_resolution_score=d("0.680000"),
            memory_age_seconds=d("172800.000000"),
            ladder_depth_count=d("2.500000"),
            contradiction_ratio=d("0.150000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.report_mode == "paper_source_resolution_memory_ladder_block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.watch_block_ratio == d("0.666667")
    assert report.min_memory_coverage_ratio == d("0.400000")
    assert report.min_ladder_depth_ratio == d("0.333333")
    assert report.min_source_resolution_score == d("0.450000")
    assert report.min_resolution_memory_ladder_score == d("0.356667")
    assert report.max_memory_age_seconds == d("900000.000000")
    assert report.max_contradiction_ratio == d("0.400000")
    assert report.max_memory_ladder_pressure_score == d("1.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.resolution_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.domain_label == "macro_policy"
    assert blocked.memory_coverage_ratio == d("0.400000")
    assert blocked.ladder_depth_ratio == d("0.333333")
    assert blocked.memory_ladder_pressure_score == d("1.000000")
    assert blocked.memory_staleness_ratio == d("1.000000")
    assert blocked.reason_codes == (
        "source_resolution_memory_coverage_block",
        "source_resolution_score_block",
        "source_resolution_memory_staleness_block",
        "source_resolution_ladder_depth_block",
        "source_resolution_contradiction_block",
    )
    assert watched.resolution_memory_ladder_score == d("0.765524")
    assert watched.reason_codes == (
        "source_resolution_memory_coverage_watch",
        "source_resolution_score_watch",
        "source_resolution_memory_staleness_watch",
        "source_resolution_ladder_depth_watch",
        "source_resolution_contradiction_watch",
    )
    assert passed.resolution_memory_ladder_score == d("0.968810")
    assert passed.reason_codes == ("source_resolution_memory_ladder_pass",)
    assert (
        api().ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount(
            reason_code="source_resolution_memory_staleness_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
        in report.reason_code_counts
    )

    payload = api().research_team_domain_source_resolution_memory_ladder_report_payload(
        report,
    )
    reversed_payload = (
        api().research_team_domain_source_resolution_memory_ladder_report_payload(
            reversed_report,
        )
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["memory_ladder_pressure_score"] == "1.000000"
    assert _float_paths(payload) == ()
    assert _int_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_source_resolution_memory_ladder_is_report_only_public_safe() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_CONFIG_VERSION",
        "RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_STATUSES",
        "ResearchTeamDomainSourceResolutionMemoryLadderConfig",
        "ResearchTeamDomainSourceResolutionMemoryLadderInput",
        "ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount",
        "ResearchTeamDomainSourceResolutionMemoryLadderReport",
        "ResearchTeamDomainSourceResolutionMemoryLadderRow",
        "build_research_team_domain_source_resolution_memory_ladder_report",
        "research_team_domain_source_resolution_memory_ladder_report_digest",
        "research_team_domain_source_resolution_memory_ladder_report_payload",
        "validate_research_team_domain_source_resolution_memory_ladder_report_digest",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen

    empty = build_report()
    assert empty.status == "pass"
    assert empty.report_mode == "paper_source_resolution_memory_ladder_monitor"
    assert empty.reason_codes == ("source_resolution_memory_ladder_empty",)
    assert empty.input_count == ZERO
    assert empty.row_count == ZERO
    assert empty.reason_code_counts == ()
    assert empty.rows == ()

    populated = build_report(
        input_row("sports_results", "team_outcome_review", "official_results"),
    )
    for value in (
        populated,
        *populated.rows,
        *populated.reason_code_counts,
        config(),
        input_row("macro_policy", "team_policy_review", "agency_releases"),
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
            if field.name.endswith(("_count", "_ratio", "_score", "_seconds", "_rank")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="source_resolution_score must be a Decimal"):
        input_row(
            "macro_policy",
            "team_policy_review",
            "agency_releases",
            source_resolution_score=0.5,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        input_row(
            "macro_policy",
            "team_policy_review",
            "agency_releases",
            observed_at=datetime(2026, 7, 9, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            input_row("macro_policy", "team_policy_review", "agency_releases"),
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="team-domain-source labels must be unique"):
        build_report(
            input_row("macro_policy", "team_policy_review", "agency_releases"),
            input_row("macro_policy", "team_policy_review", "agency_releases"),
        )
    with pytest.raises(ValueError, match="source_resolution_score"):
        input_row(
            "macro_policy",
            "team_policy_review",
            "agency_releases",
            source_resolution_score=d("1.100000"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        input_row("market_slug", "team_policy_review", "agency_releases")
    with pytest.raises(ValueError, match="verified_resolution_memory_count"):
        input_row(
            "macro_policy",
            "team_policy_review",
            "agency_releases",
            resolution_memory_count=d("10.000000"),
            verified_resolution_memory_count=d("11.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_memory_coverage_ratio"):
        config(
            min_pass_memory_coverage_ratio=d("0.700000"),
            min_watch_memory_coverage_ratio=d("0.900000"),
        )

    payload = module.research_team_domain_source_resolution_memory_ladder_report_payload(
        populated,
    )
    assert (
        module.research_team_domain_source_resolution_memory_ladder_report_digest(
            populated,
        )
        == payload["derived_validation_digest"]
    )
    assert module.validate_research_team_domain_source_resolution_memory_ladder_report_digest(
        payload,
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate",
        "market",
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
        "recommendation",
    ):
        assert forbidden not in encoded
    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "source_text",
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
            module.research_team_domain_source_resolution_memory_ladder_report_payload(
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


def test_payload_validation_rejects_tampering_and_public_leaks() -> None:
    module = api()
    report = build_report(
        input_row("sports_results", "team_outcome_review", "official_results"),
    )
    row = report.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            source_resolution_score=d("0.700000"),
            derived_validation_digest=row.derived_validation_digest,
        )

    payload = module.research_team_domain_source_resolution_memory_ladder_report_payload(
        report,
    )

    tampered = dict(payload)
    tampered["status"] = "clear"
    tampered["derived_validation_digest"] = canonical_digest(tampered)
    with pytest.raises(ValueError, match="status"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            tampered,
        )

    leaked = dict(payload)
    leaked["rows"] = [dict(payload["rows"][0])]
    leaked["rows"][0]["domain_label"] = "candidate_ref"
    leaked["rows"][0]["derived_validation_digest"] = _row_digest(leaked["rows"][0])
    leaked["derived_validation_digest"] = canonical_digest(leaked)
    with pytest.raises(ValueError, match="public aggregate labels"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            leaked,
        )

    numeric = dict(payload)
    numeric["input_count"] = 1
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            numeric,
        )


def test_public_payload_rejects_noncanonical_json_values() -> None:
    module = api()
    payload = module.research_team_domain_source_resolution_memory_ladder_report_payload(
        build_report(
            input_row("sports_results", "team_outcome_review", "official_results"),
        ),
    )

    raw_decimal = dict(payload)
    raw_decimal["input_count"] = d("1.000000")
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            raw_decimal,
        )

    raw_datetime = dict(payload)
    raw_datetime["generated_at"] = GENERATED_AT
    with pytest.raises(ValueError, match="JSON primitives"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            raw_datetime,
        )

    tuple_rows = dict(payload)
    tuple_rows["rows"] = tuple(payload["rows"])
    with pytest.raises(ValueError, match="JSON primitives"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            tuple_rows,
        )

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["input_count"] = "1"
    noncanonical_decimal["derived_validation_digest"] = canonical_digest(
        noncanonical_decimal,
    )
    with pytest.raises(ValueError, match="canonical decimal string"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            noncanonical_decimal,
        )


def test_public_payload_rejects_recomputed_semantic_forgeries() -> None:
    module = api()
    payload = module.research_team_domain_source_resolution_memory_ladder_report_payload(
        build_report(
            input_row("sports_results", "team_outcome_review", "official_results"),
        ),
    )

    bad_report_count = dict(payload)
    bad_report_count["pass_count"] = "9.000000"
    bad_report_count["derived_validation_digest"] = canonical_digest(bad_report_count)
    with pytest.raises(ValueError, match="pass_count must match rows"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            bad_report_count,
        )

    bad_row_metric = deepcopy(payload)
    bad_row_metric["rows"][0]["resolution_memory_ladder_score"] = "0.500000"
    bad_row_metric["rows"][0]["derived_validation_digest"] = _row_digest(
        bad_row_metric["rows"][0],
    )
    bad_row_metric["derived_validation_digest"] = canonical_digest(bad_row_metric)
    with pytest.raises(ValueError, match="resolution_memory_ladder_score must match"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            bad_row_metric,
        )

    bad_row_flag = deepcopy(payload)
    bad_row_flag["rows"][0]["readonly"] = False
    bad_row_flag["rows"][0]["derived_validation_digest"] = _row_digest(
        bad_row_flag["rows"][0],
    )
    bad_row_flag["derived_validation_digest"] = canonical_digest(bad_row_flag)
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            bad_row_flag,
        )


def test_public_payload_rejects_recomputed_signed_zero_forgery() -> None:
    module = api()
    payload = module.research_team_domain_source_resolution_memory_ladder_report_payload(
        build_report(
            input_row("sports_results", "team_outcome_review", "official_results"),
        ),
    )

    signed_zero = dict(payload)
    signed_zero["watch_block_ratio"] = "-0.000000"
    signed_zero["derived_validation_digest"] = canonical_digest(signed_zero)

    with pytest.raises(ValueError, match="canonical decimal string"):
        module.research_team_domain_source_resolution_memory_ladder_report_payload(
            signed_zero,
        )


def test_derived_invariants_counts_and_final_types_are_strict() -> None:
    module = api()
    report = build_report(
        input_row("sports_results", "team_outcome_review", "official_results"),
    )
    row = report.rows[0]

    with pytest.raises(ValueError, match="resolution_memory_ladder_score must match"):
        replace(
            row,
            resolution_memory_ladder_score=d("0.500000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="status must match"):
        replace(
            row,
            status="watch",
            reason_codes=("source_resolution_memory_coverage_watch",),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="resolution_rank must match row order"):
        replace(
            report,
            rows=(
                replace(
                    row,
                    resolution_rank=d("2.000000"),
                    derived_validation_digest="",
                ),
            ),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="supported config version"):
        replace(
            report,
            config_version="research-team-domain-source-resolution-memory-ladder-report-v2",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="whole Decimal"):
        input_row(
            "sports_results",
            "team_outcome_review",
            "official_results",
            resolution_memory_count=d("1.500000"),
            verified_resolution_memory_count=d("1.000000"),
        )

    for public_class in (
        module.ResearchTeamDomainSourceResolutionMemoryLadderConfig,
        module.ResearchTeamDomainSourceResolutionMemoryLadderInput,
        module.ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount,
        module.ResearchTeamDomainSourceResolutionMemoryLadderReport,
        module.ResearchTeamDomainSourceResolutionMemoryLadderRow,
    ):
        with pytest.raises(TypeError):

            class InvalidSubclass(public_class):
                pass


def test_valid_custom_config_remains_supported_and_payload_is_self_consistent() -> None:
    custom_config = config(
        max_pass_memory_age_seconds=d("1800.000000"),
        max_watch_memory_age_seconds=d("7200.000000"),
        target_ladder_depth_count=d("8.000000"),
        min_pass_ladder_depth_ratio=d("0.400000"),
        min_watch_ladder_depth_ratio=d("0.200000"),
    )

    report = build_report(
        input_row("sports_results", "team_outcome_review", "official_results"),
        cfg=custom_config,
    )
    payload = api().research_team_domain_source_resolution_memory_ladder_report_payload(
        report,
    )

    assert report.rows[0].memory_staleness_ratio == d("0.500000")
    assert report.rows[0].ladder_depth_ratio == d("0.500000")
    assert report.rows[0].status == "watch"
    assert payload["derived_validation_digest"] == canonical_digest(payload)


def test_module_has_no_execution_persistence_or_advice_surface() -> None:
    module = api()
    module_source = module.__loader__.get_source(module.__name__)
    assert module_source is not None
    tree = ast.parse(module_source)
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            called_names.add(getattr(node.func, "attr", getattr(node.func, "id", "")))

    assert imported_roots.isdisjoint(
        {
            "asyncpg",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
            "web3",
        },
    )
    assert called_names.isdisjoint(
        {
            "connect",
            "execute",
            "executemany",
            "open",
            "request",
            "send",
            "write",
            "write_bytes",
            "write_text",
        },
    )

    forbidden_surface_terms = {
        "auth",
        "client",
        "database",
        "dsn",
        "live",
        "order",
        "recommendation",
        "sizing",
        "table",
        "token",
        "trade",
        "wallet",
    }
    for exported_name in module.__all__:
        assert not any(term in exported_name.lower() for term in forbidden_surface_terms)
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            for field in fields(exported):
                assert not any(
                    term in field.name.lower() for term in forbidden_surface_terms
                )


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


def _int_paths(value: object, prefix: str = "$") -> tuple[str, ...]:
    if type(value) is int:
        return (prefix,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_int_paths(item, f"{prefix}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_int_paths(item, f"{prefix}[{index}]"))
        return tuple(paths)
    return ()
