from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_freshness_reliability"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_freshness_reliability.py"
)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-source-freshness-reliability-test-v0",
        "watch_stale_after_seconds": d("3600.000000"),
        "blocked_stale_after_seconds": d("7200.000000"),
        "reliability_watch_below": d("0.800000"),
        "reliability_block_below": d("0.500000"),
        "independence_watch_below": d("0.700000"),
        "independence_block_below": d("0.400000"),
        "conflict_watch_count": d("1.000000"),
        "conflict_block_count": d("3.000000"),
        "conflict_penalty_per_conflict": d("0.050000"),
        "max_conflict_penalty": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceFreshnessReliabilityConfig(**values)


def evidence(
    source_id: str,
    *,
    source_kind: str = "official",
    observed_at: datetime | None = None,
    latest_source_at: datetime | None = None,
    reliability_score: Decimal = d("0.950000"),
    independence_score: Decimal = d("0.900000"),
    conflict_count: Decimal = d("0.000000"),
    is_official_or_primary: bool = True,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceEvidence(
        source_id=source_id,
        source_kind=source_kind,
        observed_at=observed_at or ago(minutes=5),
        latest_source_at=latest_source_at or ago(minutes=5),
        reliability_score=reliability_score,
        independence_score=independence_score,
        conflict_count=conflict_count,
        is_official_or_primary=is_official_or_primary,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*values: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_source_freshness_reliability_report(
        values,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload contains float")
    if isinstance(value, dict):
        for key, item in value.items():
            assert_no_float_values(key)
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_official_primary_current_source_passes_with_decimal_scores() -> None:
    module = api()
    digest = report(
        evidence(
            "official-election-source",
            source_kind="official",
            reliability_score=d("0.960000"),
            independence_score=d("0.920000"),
            reason_codes=("research_packet_manual_review",),
        ),
        evidence(
            "primary-box-score",
            source_kind="primary",
            reliability_score=d("0.900000"),
            independence_score=d("0.820000"),
            latest_source_at=ago(minutes=10),
        ),
    )

    assert digest.status == "pass"
    assert digest.reason_codes == (
        "research_source_freshness_reliability_pass",
        "research_packet_manual_review",
    )
    assert digest.evidence_count == d("2.000000")
    assert digest.pass_count == d("2.000000")
    assert digest.watch_count == d("0.000000")
    assert digest.blocked_count == d("0.000000")
    assert digest.stale_source_count == d("0.000000")
    assert digest.conflict_source_count == d("0.000000")
    assert digest.official_or_primary_count == d("2.000000")
    assert digest.min_decision_score == d("0.860000")
    assert digest.max_source_age_seconds == d("600.000000")
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    assert tuple(row.source_id for row in digest.rows) == (
        "official-election-source",
        "primary-box-score",
    )
    assert digest.rows[0].status == "pass"
    assert digest.rows[0].source_age_seconds == d("300.000000")
    assert digest.rows[0].conflict_penalty_score == d("0.000000")
    assert digest.rows[0].decision_score == d("0.940000")
    assert digest.rows[0].reason_codes == (
        "research_source_freshness_reliability_pass",
        "research_packet_manual_review",
    )

    counts = {item.reason_code: item.count for item in digest.reason_code_counts}
    assert counts == {
        "research_source_freshness_reliability_pass": d("2.000000"),
        "research_packet_manual_review": d("1.000000"),
    }

    payload = module.research_source_freshness_reliability_report_payload(digest)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["evidence_count"] == "2.000000"
    assert payload["min_decision_score"] == "0.860000"
    assert payload["reason_code_counts"][0]["count"] == "2.000000"
    assert payload["rows"][0]["decision_score"] == "0.940000"
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_stale_sources_escalate_from_watch_to_blocked() -> None:
    digest = report(
        evidence(
            "stale-watch-source",
            latest_source_at=ago(minutes=90),
        ),
        evidence(
            "stale-block-source",
            latest_source_at=ago(hours=3),
        ),
    )

    assert digest.status == "blocked"
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.stale_source_count == d("2.000000")
    assert tuple(row.source_id for row in digest.rows) == (
        "stale-block-source",
        "stale-watch-source",
    )
    assert digest.rows[0].status == "blocked"
    assert digest.rows[0].source_age_seconds == d("10800.000000")
    assert digest.rows[0].reason_codes == (
        "research_source_freshness_reliability_stale_block",
    )
    assert digest.rows[1].status == "watch"
    assert digest.rows[1].source_age_seconds == d("5400.000000")
    assert digest.rows[1].reason_codes == (
        "research_source_freshness_reliability_stale_watch",
    )


def test_conflicts_apply_penalties_and_drive_watch_or_blocked_statuses() -> None:
    digest = report(
        evidence(
            "conflict-watch-source",
            conflict_count=d("2.000000"),
            reliability_score=d("0.900000"),
            independence_score=d("0.900000"),
        ),
        evidence(
            "conflict-block-source",
            conflict_count=d("3.000000"),
            reliability_score=d("0.900000"),
            independence_score=d("0.900000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.conflict_source_count == d("2.000000")
    assert tuple(row.source_id for row in digest.rows) == (
        "conflict-block-source",
        "conflict-watch-source",
    )
    assert digest.rows[0].status == "blocked"
    assert digest.rows[0].conflict_penalty_score == d("0.150000")
    assert digest.rows[0].decision_score == d("0.750000")
    assert digest.rows[0].reason_codes == (
        "research_source_freshness_reliability_conflict_block",
    )
    assert digest.rows[1].status == "watch"
    assert digest.rows[1].conflict_penalty_score == d("0.100000")
    assert digest.rows[1].decision_score == d("0.800000")
    assert digest.rows[1].reason_codes == (
        "research_source_freshness_reliability_conflict_watch",
    )


def test_deterministic_sorting_status_counts_and_reason_counts() -> None:
    digest = report(
        evidence("pass-source", source_kind="primary"),
        evidence(
            "watch-secondary",
            source_kind="secondary",
            is_official_or_primary=False,
            reason_codes=("source_packet_annotation",),
        ),
        evidence(
            "blocked-reliability",
            reliability_score=d("0.400000"),
            independence_score=d("0.900000"),
        ),
        evidence(
            "watch-reliability",
            reliability_score=d("0.700000"),
            independence_score=d("0.900000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("2.000000")
    assert digest.blocked_count == d("1.000000")
    assert tuple(row.source_id for row in digest.rows) == (
        "blocked-reliability",
        "watch-reliability",
        "watch-secondary",
        "pass-source",
    )
    assert digest.reason_codes == (
        "research_source_freshness_reliability_reliability_block",
        "research_source_freshness_reliability_reliability_watch",
        "research_source_freshness_reliability_non_primary",
        "research_source_freshness_reliability_pass",
        "source_packet_annotation",
    )
    assert tuple((item.reason_code, item.count, item.row_ratio) for item in digest.reason_code_counts) == (
        (
            "research_source_freshness_reliability_reliability_block",
            d("1.000000"),
            d("0.250000"),
        ),
        (
            "research_source_freshness_reliability_reliability_watch",
            d("1.000000"),
            d("0.250000"),
        ),
        (
            "research_source_freshness_reliability_non_primary",
            d("1.000000"),
            d("0.250000"),
        ),
        (
            "research_source_freshness_reliability_pass",
            d("1.000000"),
            d("0.250000"),
        ),
        ("source_packet_annotation", d("1.000000"), d("0.250000")),
    )


def test_utc_normalization_validation_hard_flags_and_public_values() -> None:
    module = api()
    local_generated_at = datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    local_observed_at = datetime(2026, 7, 7, 7, 50, tzinfo=timezone(timedelta(hours=-4)))
    local_latest_at = datetime(2026, 7, 7, 7, 45, tzinfo=timezone(timedelta(hours=-4)))

    digest = report(
        evidence(
            "timezone-source",
            observed_at=local_observed_at,
            latest_source_at=local_latest_at,
        ),
        generated_at=local_generated_at,
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.rows[0].observed_at == datetime(2026, 7, 7, 11, 50, tzinfo=UTC)
    assert digest.rows[0].latest_source_at == datetime(2026, 7, 7, 11, 45, tzinfo=UTC)
    assert digest.rows[0].observed_age_seconds == d("600.000000")
    assert digest.rows[0].source_age_seconds == d("900.000000")

    with pytest.raises(FrozenInstanceError):
        digest.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence("flag-source"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(evidence("naive-generated"), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        evidence("naive-observed", observed_at=datetime(2026, 7, 7, 11, 55))
    with pytest.raises(ValueError, match="latest_source_at must be <= observed_at"):
        evidence(
            "future-source-time",
            observed_at=ago(minutes=10),
            latest_source_at=ago(minutes=5),
        )
    with pytest.raises(ValueError, match="observed_at must be <= generated_at"):
        report(evidence("future-observed", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="source_id values must be unique"):
        report(evidence("duplicate-source"), evidence("duplicate-source"))
    with pytest.raises(ValueError, match="reliability_score must be a Decimal"):
        evidence("float-reliability", reliability_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflict_count must be integral"):
        evidence("fractional-conflicts", conflict_count=d("1.500000"))
    with pytest.raises(ValueError, match="source_kind must be known"):
        evidence("unknown-kind", source_kind="blog")
    with pytest.raises(ValueError, match="unsafe public value"):
        evidence(f"{'wal'}{'let'}-source")
    with pytest.raises(ValueError, match="unsafe public value"):
        evidence("reason-source", reason_codes=(f"source_{'tok'}{'en'}_note",))

    rebuilt_row = module.ResearchSourceFreshnessReliabilityRow(**field_values(digest.rows[0]))
    rebuilt_report = module.ResearchSourceFreshnessReliabilityReport(**field_values(digest))
    assert rebuilt_row == digest.rows[0]
    assert rebuilt_report == digest

    for instance in (config(), evidence("decimal-source"), digest, digest.rows[0]):
        for field in fields(instance):
            if (
                field.name.endswith("_score")
                or field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                value = getattr(instance, field.name)
                assert type(value) is Decimal, (field.name, value)


def test_pure_boundary_module_surface_has_no_runtime_clients_or_floats() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "network",
        "persistence",
        "supabase",
        "requests",
        "http",
        "socket",
        "subprocess",
        "env",
        "cli",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert module_exports(tree) == (
        "DEFAULT_RESEARCH_SOURCE_FRESHNESS_RELIABILITY_CONFIG_VERSION",
        "SOURCE_KINDS",
        "ROW_STATUSES",
        "REPORT_STATUSES",
        "ResearchSourceFreshnessReliabilityConfig",
        "ResearchSourceEvidence",
        "ResearchSourceFreshnessReliabilityReasonCodeCount",
        "ResearchSourceFreshnessReliabilityReport",
        "ResearchSourceFreshnessReliabilityRow",
        "build_research_source_freshness_reliability_report",
        "research_source_freshness_reliability_report_payload",
    )
    assert set(imported_modules(tree)) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
    }
    normalized_names = {
        normalize_identifier(name)
        for name in collected_names(tree)
        if normalize_identifier(name) != "readonly"
    }
    for fragment in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert not any(fragment in name for name in normalized_names), fragment
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "__import__",
                "compile",
                "eval",
                "exec",
                "float",
                "input",
                "open",
                "print",
            }


def module_exports(tree: ast.Module) -> tuple[str, ...]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return tuple(ast.literal_eval(node.value))
    raise AssertionError("__all__ not found")


def imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def collected_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
