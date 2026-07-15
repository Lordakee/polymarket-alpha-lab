from __future__ import annotations

import ast
import hashlib
import importlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from itertools import permutations
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_cross_team_memory_decay_router_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_cross_team_memory_decay_router_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
QUANT = Decimal("0.000001")

REPORT_FIELD_ORDER = (
    "generated_at",
    "config_version",
    "config",
    "status",
    "snapshot_count",
    "route_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_memory_health_score",
    "lowest_memory_health_score",
    "highest_memory_decay_ratio",
    "highest_memory_age_seconds",
    "highest_decay_pressure_score",
    "lowest_cross_group_alignment_score",
    "lowest_reuse_confidence_score",
    "highest_handoff_gap_score",
    "reason_codes",
    "reason_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
CONFIG_FIELD_ORDER = (
    "config_version",
    "fresh_memory_age_seconds",
    "stale_memory_age_seconds",
    "min_pass_memory_health_score",
    "min_watch_memory_health_score",
    "min_pass_memory_retention_score",
    "min_watch_memory_retention_score",
    "min_pass_cross_group_alignment_score",
    "min_watch_cross_group_alignment_score",
    "min_pass_reuse_confidence_score",
    "min_watch_reuse_confidence_score",
    "max_pass_decay_pressure_score",
    "max_watch_decay_pressure_score",
    "max_pass_handoff_gap_score",
    "max_watch_handoff_gap_score",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_FIELD_ORDER = (
    "aggregate_row_number",
    "route_digest",
    "lead_group_digest",
    "peer_group_digest",
    "status",
    "baseline_memory_score",
    "current_memory_score",
    "memory_retention_score",
    "memory_decay_ratio",
    "memory_age_seconds",
    "memory_age_pressure_score",
    "decay_pressure_score",
    "cross_group_alignment_score",
    "reuse_confidence_score",
    "handoff_gap_score",
    "memory_health_score",
    "observed_at",
    "last_memory_refresh_at",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_COUNT_FIELD_ORDER = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _TupleSubclass(tuple):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "cross-team memory decay router report module is missing"
    return importlib.import_module(MODULE_NAME)


def config(mod: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            mod.DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ),
        "fresh_memory_age_seconds": d("3600.000000"),
        "stale_memory_age_seconds": d("86400.000000"),
        "min_pass_memory_health_score": d("0.700000"),
        "min_watch_memory_health_score": d("0.500000"),
        "min_pass_memory_retention_score": d("0.750000"),
        "min_watch_memory_retention_score": d("0.500000"),
        "min_pass_cross_group_alignment_score": d("0.700000"),
        "min_watch_cross_group_alignment_score": d("0.500000"),
        "min_pass_reuse_confidence_score": d("0.700000"),
        "min_watch_reuse_confidence_score": d("0.500000"),
        "max_pass_decay_pressure_score": d("0.200000"),
        "max_watch_decay_pressure_score": d("0.450000"),
        "max_pass_handoff_gap_score": d("0.200000"),
        "max_watch_handoff_gap_score": d("0.450000"),
    }
    values.update(overrides)
    return mod.ResearchStrategyCrossTeamMemoryDecayRouterConfig(**values)


def snapshot(
    mod: Any,
    route_ref: str = "route-ref:alpha?candidate=hidden&market_id=secret",
    lead_group_ref: str = "lead-group:alpha?wallet=hidden",
    peer_group_ref: str = "peer-group:beta?token=hidden",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    last_memory_refresh_at: datetime = GENERATED_AT - timedelta(minutes=30),
    baseline_memory_score: Decimal = d("0.900000"),
    current_memory_score: Decimal = d("0.855000"),
    cross_group_alignment_score: Decimal = d("0.900000"),
    reuse_confidence_score: Decimal = d("0.880000"),
    handoff_gap_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = ("cross_team_memory_snapshot_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return mod.ResearchStrategyCrossTeamMemoryDecayRouterSnapshot(
        route_ref=route_ref,
        lead_group_ref=lead_group_ref,
        peer_group_ref=peer_group_ref,
        observed_at=observed_at,
        last_memory_refresh_at=last_memory_refresh_at,
        baseline_memory_score=baseline_memory_score,
        current_memory_score=current_memory_score,
        cross_group_alignment_score=cross_group_alignment_score,
        reuse_confidence_score=reuse_confidence_score,
        handoff_gap_score=handoff_gap_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    mod: Any,
    *items: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return mod.build_research_strategy_cross_team_memory_decay_router_report(
        items,
        config=cfg or config(mod),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_digest(payload)


def resign_row_payload(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_digest(payload)


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for key, item in value.items():
            values.append(key)
            values.extend(walk_payload(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload(item))
        return tuple(values)
    return (value,)


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"raw numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def assert_no_forbidden_public_payload_surface(payload: dict[str, Any]) -> None:
    encoded_values = " ".join(str(value).lower() for value in walk_payload(payload))
    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "live",
        "sizing",
        "recommend",
        "private",
    )
    assert not any(fragment in encoded_values for fragment in forbidden_fragments)


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"} or item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_score",
                "_seconds",
                "_number",
            ),
        ):
            assert type(item) is Decimal


def classify_isolated_driver(
    mod: Any,
    **overrides: Decimal,
) -> tuple[str, tuple[str, ...]]:
    values = {
        "memory_health_score": d("0.700000"),
        "memory_retention_score": d("0.750000"),
        "memory_age_seconds": d("3600.000000"),
        "memory_decay_ratio": d("0.200000"),
        "decay_pressure_score": d("0.200000"),
        "cross_group_alignment_score": d("0.700000"),
        "reuse_confidence_score": d("0.700000"),
        "handoff_gap_score": d("0.200000"),
        "config": config(mod),
    }
    values.update(overrides)
    status = mod._row_status(**values)
    reason_codes = mod._row_reason_codes_from_values(
        status=status,
        upstream_reason_codes=(mod.REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,),
        **values,
    )
    return status, reason_codes


def schema_object(payload: dict[str, Any], target: str) -> dict[str, Any]:
    if target == "report":
        return payload
    if target == "config":
        return payload["config"]
    if target == "row":
        return payload["rows"][0]
    if target == "reason_count":
        return payload["reason_counts"][0]
    raise AssertionError(f"unsupported schema target: {target}")


def replace_schema_object(
    payload: dict[str, Any],
    target: str,
    replacement: object,
) -> dict[str, Any]:
    if target == "report":
        assert type(replacement) is dict
        return replacement
    if target == "config":
        payload["config"] = replacement
    elif target == "row":
        payload["rows"][0] = replacement
    elif target == "reason_count":
        payload["reason_counts"][0] = replacement
    else:
        raise AssertionError(f"unsupported schema target: {target}")
    return payload


def qualified_name(node: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        owner = qualified_name(node.value, aliases)
        return f"{owner}.{node.attr}" if owner else node.attr
    if isinstance(node, ast.Call):
        return qualified_name(node.func, aliases)
    return ""


def forbidden_io_surfaces(source: str) -> set[str]:
    tree = ast.parse(source)
    aliases: dict[str, str] = {}
    findings: set[str] = set()
    forbidden_roots = {
        "aiohttp",
        "asyncio",
        "http",
        "httpx",
        "importlib",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    path_methods = {
        "chmod",
        "mkdir",
        "open",
        "read_bytes",
        "read_text",
        "rename",
        "replace",
        "rmdir",
        "symlink_to",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }
    execution_calls = {
        "__import__",
        "eval",
        "exec",
        "open",
        "os.popen",
        "os.spawnl",
        "os.spawnlp",
        "os.system",
        "socket.create_connection",
        "socket.socket",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
        "subprocess.run",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound_name = alias.asname or alias.name.split(".", 1)[0]
                aliases[bound_name] = alias.name
                if alias.name.split(".", 1)[0] in forbidden_roots:
                    findings.add(f"import:{alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".", 1)[0]
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
            if root in forbidden_roots:
                findings.add(f"import:{node.module}")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = qualified_name(node.func, aliases)
        root = name.split(".", 1)[0]
        if name in execution_calls or root in forbidden_roots:
            findings.add(f"call:{name}")
        if isinstance(node.func, ast.Attribute) and node.func.attr in path_methods:
            owner = qualified_name(node.func.value, aliases)
            if owner == "pathlib.Path" or owner.startswith("pathlib.Path."):
                findings.add(f"path:{name}")
        if name == "getattr" and len(node.args) >= 2:
            owner = qualified_name(node.args[0], aliases)
            attribute = node.args[1]
            attribute_name = (
                attribute.value
                if isinstance(attribute, ast.Constant)
                and type(attribute.value) is str
                else None
            )
            if (
                owner.split(".", 1)[0] in forbidden_roots
                or attribute_name in execution_calls
                or attribute_name in path_methods
                or attribute_name in {
                    "create_connection",
                    "import_module",
                    "open_connection",
                    "request",
                    "send",
                    "system",
                    "urlopen",
                }
            ):
                findings.add(f"getattr:{owner}.{attribute_name}")
    return findings


DRIVER_THRESHOLD_CASES = (
    ("health-pass-minus", "memory_health_score", "0.699999", "watch", "memory_health_watch"),
    ("health-pass-equal", "memory_health_score", "0.700000", "pass", None),
    ("health-pass-plus", "memory_health_score", "0.700001", "pass", None),
    ("health-watch-minus", "memory_health_score", "0.499999", "block", "memory_health_block"),
    ("health-watch-equal", "memory_health_score", "0.500000", "watch", "memory_health_watch"),
    ("health-watch-plus", "memory_health_score", "0.500001", "watch", "memory_health_watch"),
    (
        "retention-pass-minus",
        "memory_retention_score",
        "0.749999",
        "watch",
        "memory_retention_watch",
    ),
    ("retention-pass-equal", "memory_retention_score", "0.750000", "pass", None),
    ("retention-pass-plus", "memory_retention_score", "0.750001", "pass", None),
    (
        "retention-watch-minus",
        "memory_retention_score",
        "0.499999",
        "block",
        "memory_retention_block",
    ),
    (
        "retention-watch-equal",
        "memory_retention_score",
        "0.500000",
        "watch",
        "memory_retention_watch",
    ),
    (
        "retention-watch-plus",
        "memory_retention_score",
        "0.500001",
        "watch",
        "memory_retention_watch",
    ),
    ("age-pass-minus", "memory_age_seconds", "3599.999999", "pass", None),
    ("age-pass-equal", "memory_age_seconds", "3600.000000", "pass", None),
    ("age-pass-plus", "memory_age_seconds", "3600.000001", "watch", "memory_age_watch"),
    ("age-block-minus", "memory_age_seconds", "86399.999999", "watch", "memory_age_watch"),
    ("age-block-equal", "memory_age_seconds", "86400.000000", "block", "memory_age_block"),
    ("age-block-plus", "memory_age_seconds", "86400.000001", "block", "memory_age_block"),
    ("decay-pass-minus", "memory_decay_ratio", "0.199999", "pass", None),
    ("decay-pass-equal", "memory_decay_ratio", "0.200000", "pass", None),
    ("decay-pass-plus", "memory_decay_ratio", "0.200001", "watch", "memory_decay_watch"),
    ("decay-block-minus", "memory_decay_ratio", "0.449999", "watch", "memory_decay_watch"),
    ("decay-block-equal", "memory_decay_ratio", "0.450000", "watch", "memory_decay_watch"),
    ("decay-block-plus", "memory_decay_ratio", "0.450001", "block", "memory_decay_block"),
    (
        "pressure-pass-minus",
        "decay_pressure_score",
        "0.199999",
        "pass",
        None,
    ),
    ("pressure-pass-equal", "decay_pressure_score", "0.200000", "pass", None),
    (
        "pressure-pass-plus",
        "decay_pressure_score",
        "0.200001",
        "watch",
        "decay_pressure_watch",
    ),
    (
        "pressure-block-minus",
        "decay_pressure_score",
        "0.449999",
        "watch",
        "decay_pressure_watch",
    ),
    (
        "pressure-block-equal",
        "decay_pressure_score",
        "0.450000",
        "watch",
        "decay_pressure_watch",
    ),
    (
        "pressure-block-plus",
        "decay_pressure_score",
        "0.450001",
        "block",
        "decay_pressure_block",
    ),
    (
        "alignment-pass-minus",
        "cross_group_alignment_score",
        "0.699999",
        "watch",
        "cross_group_alignment_watch",
    ),
    ("alignment-pass-equal", "cross_group_alignment_score", "0.700000", "pass", None),
    ("alignment-pass-plus", "cross_group_alignment_score", "0.700001", "pass", None),
    (
        "alignment-watch-minus",
        "cross_group_alignment_score",
        "0.499999",
        "block",
        "cross_group_alignment_block",
    ),
    (
        "alignment-watch-equal",
        "cross_group_alignment_score",
        "0.500000",
        "watch",
        "cross_group_alignment_watch",
    ),
    (
        "alignment-watch-plus",
        "cross_group_alignment_score",
        "0.500001",
        "watch",
        "cross_group_alignment_watch",
    ),
    (
        "reuse-pass-minus",
        "reuse_confidence_score",
        "0.699999",
        "watch",
        "reuse_confidence_watch",
    ),
    ("reuse-pass-equal", "reuse_confidence_score", "0.700000", "pass", None),
    ("reuse-pass-plus", "reuse_confidence_score", "0.700001", "pass", None),
    (
        "reuse-watch-minus",
        "reuse_confidence_score",
        "0.499999",
        "block",
        "reuse_confidence_block",
    ),
    (
        "reuse-watch-equal",
        "reuse_confidence_score",
        "0.500000",
        "watch",
        "reuse_confidence_watch",
    ),
    (
        "reuse-watch-plus",
        "reuse_confidence_score",
        "0.500001",
        "watch",
        "reuse_confidence_watch",
    ),
    ("handoff-pass-minus", "handoff_gap_score", "0.199999", "pass", None),
    ("handoff-pass-equal", "handoff_gap_score", "0.200000", "pass", None),
    ("handoff-pass-plus", "handoff_gap_score", "0.200001", "watch", "handoff_gap_watch"),
    ("handoff-block-minus", "handoff_gap_score", "0.449999", "watch", "handoff_gap_watch"),
    ("handoff-block-equal", "handoff_gap_score", "0.450000", "watch", "handoff_gap_watch"),
    ("handoff-block-plus", "handoff_gap_score", "0.450001", "block", "handoff_gap_block"),
)


@pytest.mark.parametrize(
    ("case_id", "field_name", "raw_value", "expected_status", "expected_reason"),
    DRIVER_THRESHOLD_CASES,
    ids=tuple(case[0] for case in DRIVER_THRESHOLD_CASES),
)
def test_driver_thresholds_are_isolated_at_equal_and_one_quantum(
    case_id: str,
    field_name: str,
    raw_value: str,
    expected_status: str,
    expected_reason: str | None,
) -> None:
    del case_id
    mod = module()
    status, reason_codes = classify_isolated_driver(
        mod,
        **{field_name: d(raw_value)},
    )

    assert status == expected_status
    if expected_reason is None:
        assert reason_codes == (
            mod.REASON_ROW_PASS,
            mod.REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,
        )
    else:
        assert reason_codes == (
            mod.REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,
            expected_reason,
        )


@pytest.mark.parametrize(
    ("overrides", "error_pattern"),
    (
        (
            {
                "min_pass_memory_health_score": d("0.5000004"),
                "min_watch_memory_health_score": d("0.50000049"),
            },
            "min_pass_memory_health_score",
        ),
        (
            {
                "min_pass_memory_retention_score": d("0.5000004"),
                "min_watch_memory_retention_score": d("0.50000049"),
            },
            "min_pass_memory_retention_score",
        ),
        (
            {
                "min_pass_cross_group_alignment_score": d("0.5000004"),
                "min_watch_cross_group_alignment_score": d("0.50000049"),
            },
            "min_pass_cross_group_alignment_score",
        ),
        (
            {
                "min_pass_reuse_confidence_score": d("0.5000004"),
                "min_watch_reuse_confidence_score": d("0.50000049"),
            },
            "min_pass_reuse_confidence_score",
        ),
        (
            {
                "max_pass_decay_pressure_score": d("0.45000049"),
                "max_watch_decay_pressure_score": d("0.4500004"),
            },
            "max_pass_decay_pressure_score",
        ),
        (
            {
                "max_pass_handoff_gap_score": d("0.45000049"),
                "max_watch_handoff_gap_score": d("0.4500004"),
            },
            "max_pass_handoff_gap_score",
        ),
        (
            {
                "fresh_memory_age_seconds": d("3600.00000049"),
                "stale_memory_age_seconds": d("3600.0000004"),
            },
            "fresh_memory_age_seconds",
        ),
    ),
)
def test_config_compares_raw_threshold_pairs_before_quantization(
    overrides: dict[str, Decimal],
    error_pattern: str,
) -> None:
    mod = module()

    with pytest.raises(ValueError, match=error_pattern):
        config(mod, **overrides)


def test_public_payload_locks_all_canonical_field_orders() -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )

    assert tuple(public_payload) == REPORT_FIELD_ORDER
    assert tuple(public_payload["config"]) == CONFIG_FIELD_ORDER
    assert tuple(public_payload["rows"][0]) == ROW_FIELD_ORDER
    assert tuple(public_payload["reason_counts"][0]) == REASON_COUNT_FIELD_ORDER


@pytest.mark.parametrize(
    ("target", "field_order", "error_pattern"),
    (
        ("report", REPORT_FIELD_ORDER, "payload"),
        ("config", CONFIG_FIELD_ORDER, r"payload\.config"),
        ("row", ROW_FIELD_ORDER, r"payload\.rows\[0\]"),
        (
            "reason_count",
            REASON_COUNT_FIELD_ORDER,
            r"payload\.reason_counts\[0\]",
        ),
    ),
)
def test_public_payload_rejects_missing_unknown_and_reordered_schema_fields(
    target: str,
    field_order: tuple[str, ...],
    error_pattern: str,
) -> None:
    mod = module()
    original = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )

    for mutation in ("missing", "unknown", "reordered"):
        tampered = deepcopy(original)
        target_object = schema_object(tampered, target)
        if mutation == "missing":
            target_object.pop(field_order[0])
        elif mutation == "unknown":
            target_object["safe_extension"] = "pass"
        else:
            replacement = dict(reversed(tuple(target_object.items())))
            tampered = replace_schema_object(tampered, target, replacement)
        resign_payload(tampered)

        with pytest.raises(ValueError, match=error_pattern):
            mod.research_strategy_cross_team_memory_decay_router_report_payload(
                tampered,
            )


@pytest.mark.parametrize(
    ("target", "error_pattern"),
    (
        ("report", "public payload must be a JSON object"),
        ("config", r"payload\.config must be a JSON object"),
        ("row", r"payload\.rows\[0\] must be a JSON object"),
        (
            "reason_count",
            r"payload\.reason_counts\[0\] must be a JSON object",
        ),
    ),
)
def test_public_payload_rejects_wrong_schema_object_types(
    target: str,
    error_pattern: str,
) -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )
    replacement = list(schema_object(public_payload, target).values())
    if target == "report":
        invalid_payload: object = replacement
    else:
        invalid_payload = replace_schema_object(
            deepcopy(public_payload),
            target,
            replacement,
        )
        resign_payload(invalid_payload)

    with pytest.raises(ValueError, match=error_pattern):
        mod.validate_research_strategy_cross_team_memory_decay_router_report_public_payload(
            invalid_payload,
        )


@pytest.mark.parametrize(
    ("field_name", "lower_value", "higher_value"),
    (
        ("status", "block", "watch"),
        ("memory_health_score", d("0.700000"), d("0.800000")),
        ("route_digest", "sha256:0", "sha256:1"),
        ("lead_group_digest", "sha256:0", "sha256:1"),
        ("peer_group_digest", "sha256:0", "sha256:1"),
        ("baseline_memory_score", d("0.700000"), d("0.800000")),
        ("current_memory_score", d("0.700000"), d("0.800000")),
        (
            "observed_at",
            GENERATED_AT - timedelta(minutes=2),
            GENERATED_AT - timedelta(minutes=1),
        ),
        (
            "last_memory_refresh_at",
            GENERATED_AT - timedelta(hours=2),
            GENERATED_AT - timedelta(hours=1),
        ),
        ("memory_retention_score", d("0.700000"), d("0.800000")),
        ("memory_decay_ratio", d("0.100000"), d("0.200000")),
        ("memory_age_seconds", d("1.000000"), d("2.000000")),
        ("memory_age_pressure_score", d("0.100000"), d("0.200000")),
        ("decay_pressure_score", d("0.100000"), d("0.200000")),
        ("cross_group_alignment_score", d("0.700000"), d("0.800000")),
        ("reuse_confidence_score", d("0.700000"), d("0.800000")),
        ("handoff_gap_score", d("0.100000"), d("0.200000")),
        ("reason_codes", ("a",), ("b",)),
    ),
)
def test_sort_key_uses_every_subsequent_field(
    field_name: str,
    lower_value: object,
    higher_value: object,
) -> None:
    mod = module()
    base = {
        "status": "pass",
        "memory_health_score": d("0.700000"),
        "route_digest": "sha256:0",
        "lead_group_digest": "sha256:0",
        "peer_group_digest": "sha256:0",
        "baseline_memory_score": d("0.700000"),
        "current_memory_score": d("0.700000"),
        "observed_at": GENERATED_AT - timedelta(minutes=2),
        "last_memory_refresh_at": GENERATED_AT - timedelta(hours=2),
        "memory_retention_score": d("0.700000"),
        "memory_decay_ratio": d("0.100000"),
        "memory_age_seconds": d("1.000000"),
        "memory_age_pressure_score": d("0.100000"),
        "decay_pressure_score": d("0.100000"),
        "cross_group_alignment_score": d("0.700000"),
        "reuse_confidence_score": d("0.700000"),
        "handoff_gap_score": d("0.100000"),
        "reason_codes": ("a",),
    }
    lower = dict(base)
    higher = dict(base)
    lower[field_name] = lower_value
    higher[field_name] = higher_value

    assert mod._row_part_sort_key(lower) < mod._row_part_sort_key(higher)


def test_report_is_invariant_under_every_input_permutation() -> None:
    mod = module()
    items = (
        snapshot(
            mod,
            "route-ref:shared",
            "lead-group:shared",
            "peer-group:shared",
            observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        snapshot(
            mod,
            "route-ref:shared",
            "lead-group:shared",
            "peer-group:shared",
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        snapshot(
            mod,
            "route-ref:shared",
            "lead-group:shared",
            "peer-group:shared",
            observed_at=GENERATED_AT - timedelta(minutes=10),
        ),
    )

    payloads = tuple(
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            report(mod, *ordered),
        )
        for ordered in permutations(items)
    )

    assert all(payload == payloads[0] for payload in payloads)


def test_resigned_rows_reject_noncanonical_sort_after_renumbering() -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(
            mod,
            snapshot(
                mod,
                "route-ref:shared",
                "lead-group:shared",
                "peer-group:shared",
                observed_at=GENERATED_AT - timedelta(minutes=20),
            ),
            snapshot(
                mod,
                "route-ref:shared",
                "lead-group:shared",
                "peer-group:shared",
                observed_at=GENERATED_AT - timedelta(minutes=10),
            ),
        ),
    )
    public_payload["rows"].reverse()
    for index, row_payload in enumerate(public_payload["rows"], start=1):
        row_payload["aggregate_row_number"] = f"{index}.000000"
        resign_row_payload(row_payload)
    resign_payload(public_payload)

    with pytest.raises(ValueError, match="canonical report ordering"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            public_payload,
        )


def test_resigned_row_derived_field_tamper_matrix() -> None:
    mod = module()
    original = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )
    mutations = (
        ("aggregate_row_number", "2.000000", "aggregate_row_number"),
        ("status", "watch", "status must match reason_codes"),
        ("memory_retention_score", "0.940000", "memory_retention_score"),
        ("memory_decay_ratio", "0.060000", "memory_decay_ratio"),
        ("memory_age_seconds", "1801.000000", "memory_age_seconds"),
        (
            "memory_age_pressure_score",
            "0.100000",
            "memory_age_pressure_score",
        ),
        ("decay_pressure_score", "0.100000", "decay_pressure_score"),
        ("memory_health_score", "0.900000", "memory_health_score"),
        (
            "reason_codes",
            [
                "cross_team_memory_snapshot_ready",
                "memory_health_watch",
            ],
            "status must match reason_codes",
        ),
    )

    for field_name, value, error_pattern in mutations:
        tampered = deepcopy(original)
        tampered["rows"][0][field_name] = value
        resign_row_payload(tampered["rows"][0])
        resign_payload(tampered)

        with pytest.raises(ValueError, match=error_pattern):
            mod.research_strategy_cross_team_memory_decay_router_report_payload(
                tampered,
            )


def test_resigned_report_derived_field_tamper_matrix() -> None:
    mod = module()
    original = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )
    mutations = (
        ("status", "watch", "status"),
        ("snapshot_count", "2.000000", "snapshot_count"),
        ("route_count", "2.000000", "route_count"),
        ("pass_count", "0.000000", "pass_count"),
        ("watch_count", "1.000000", "watch_count"),
        ("block_count", "1.000000", "block_count"),
        (
            "average_memory_health_score",
            "0.000000",
            "average_memory_health_score",
        ),
        ("lowest_memory_health_score", "0.000000", "lowest_memory_health_score"),
        ("highest_memory_decay_ratio", "0.000000", "highest_memory_decay_ratio"),
        ("highest_memory_age_seconds", "0.000000", "highest_memory_age_seconds"),
        (
            "highest_decay_pressure_score",
            "0.000000",
            "highest_decay_pressure_score",
        ),
        (
            "lowest_cross_group_alignment_score",
            "0.000000",
            "lowest_cross_group_alignment_score",
        ),
        (
            "lowest_reuse_confidence_score",
            "0.000000",
            "lowest_reuse_confidence_score",
        ),
        ("highest_handoff_gap_score", "0.000000", "highest_handoff_gap_score"),
        (
            "reason_codes",
            [
                "cross_team_memory_decay_router_report_watch",
                "cross_team_memory_decay_router_pass",
                "cross_team_memory_snapshot_ready",
            ],
            "reason_codes",
        ),
    )

    for field_name, value, error_pattern in mutations:
        tampered = deepcopy(original)
        tampered[field_name] = value
        resign_payload(tampered)

        with pytest.raises(ValueError, match=error_pattern):
            mod.research_strategy_cross_team_memory_decay_router_report_payload(
                tampered,
            )

    for field_name, value in (
        ("count", "2.000000"),
        ("row_ratio", "0.500000"),
    ):
        tampered = deepcopy(original)
        tampered["reason_counts"][0][field_name] = value
        resign_payload(tampered)

        with pytest.raises(ValueError, match="reason_counts"):
            mod.research_strategy_cross_team_memory_decay_router_report_payload(
                tampered,
            )


@pytest.mark.parametrize(
    "invalid_value",
    (
        d("-0"),
        d("-0.000000"),
        d("NaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_every_decimal_field_rejects_signed_zero_and_non_finite(
    invalid_value: Decimal,
) -> None:
    mod = module()
    summary = report(mod, snapshot(mod))
    targets = (
        (
            "config",
            config(mod),
            CONFIG_FIELD_ORDER[1:15],
        ),
        (
            "snapshot",
            snapshot(mod),
            (
                "baseline_memory_score",
                "current_memory_score",
                "cross_group_alignment_score",
                "reuse_confidence_score",
                "handoff_gap_score",
            ),
        ),
        (
            "row",
            summary.rows[0],
            (
                "aggregate_row_number",
                "baseline_memory_score",
                "current_memory_score",
                "memory_retention_score",
                "memory_decay_ratio",
                "memory_age_seconds",
                "memory_age_pressure_score",
                "decay_pressure_score",
                "cross_group_alignment_score",
                "reuse_confidence_score",
                "handoff_gap_score",
                "memory_health_score",
            ),
        ),
        (
            "reason_count",
            summary.reason_counts[0],
            ("count", "row_ratio"),
        ),
        (
            "report",
            summary,
            (
                "snapshot_count",
                "route_count",
                "pass_count",
                "watch_count",
                "block_count",
                "average_memory_health_score",
                "lowest_memory_health_score",
                "highest_memory_decay_ratio",
                "highest_memory_age_seconds",
                "highest_decay_pressure_score",
                "lowest_cross_group_alignment_score",
                "lowest_reuse_confidence_score",
                "highest_handoff_gap_score",
            ),
        ),
    )

    for _label, value, field_names in targets:
        for field_name in field_names:
            with pytest.raises(
                ValueError,
                match="signed zero|finite",
            ):
                replace(value, **{field_name: invalid_value})


def test_decimal_categories_enforce_raw_bounds_before_quantization() -> None:
    mod = module()
    summary = report(mod, snapshot(mod))

    with pytest.raises(ValueError, match="between 0 and 1"):
        config(mod, min_pass_memory_health_score=d("1.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        snapshot(mod, handoff_gap_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="greater than 0"):
        snapshot(mod, baseline_memory_score=d("0.0000004"))
    with pytest.raises(ValueError, match="positive after quantization"):
        config(mod, fresh_memory_age_seconds=d("0.0000004"))
    with pytest.raises(ValueError, match="non-negative"):
        replace(summary.rows[0], memory_age_seconds=d("-0.0000004"))
    with pytest.raises(ValueError, match="integral Decimal count"):
        replace(summary.rows[0], aggregate_row_number=d("1.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        replace(summary, average_memory_health_score=d("1.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        replace(summary.reason_counts[0], row_ratio=d("-0.0000004"))


def test_snapshot_compares_raw_current_and_baseline_before_quantization() -> None:
    mod = module()

    with pytest.raises(
        ValueError,
        match="current_memory_score must not exceed baseline_memory_score",
    ):
        snapshot(
            mod,
            baseline_memory_score=d("0.5000004"),
            current_memory_score=d("0.50000049"),
        )


def test_public_row_retains_sources_and_rejects_coordinated_derived_resign() -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )
    row_payload = public_payload["rows"][0]

    assert row_payload["baseline_memory_score"] == "0.900000"
    assert row_payload["current_memory_score"] == "0.855000"

    row_payload["status"] = "watch"
    row_payload["memory_retention_score"] = "0.700000"
    row_payload["memory_decay_ratio"] = "0.300000"
    row_payload["decay_pressure_score"] = "0.150000"
    row_payload["memory_health_score"] = "0.847000"
    row_payload["reason_codes"] = [
        "cross_team_memory_snapshot_ready",
        "memory_retention_watch",
        "memory_decay_watch",
    ]
    resign_row_payload(row_payload)
    public_payload["status"] = "watch"
    public_payload["pass_count"] = "0.000000"
    public_payload["watch_count"] = "1.000000"
    public_payload["average_memory_health_score"] = "0.847000"
    public_payload["lowest_memory_health_score"] = "0.847000"
    public_payload["highest_memory_decay_ratio"] = "0.300000"
    public_payload["highest_decay_pressure_score"] = "0.150000"
    public_payload["reason_codes"] = [
        "cross_team_memory_decay_router_report_watch",
        "memory_retention_watch",
        "memory_decay_watch",
        "cross_team_memory_snapshot_ready",
    ]
    reason_count_template = {
        "count": "1.000000",
        "row_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    public_payload["reason_counts"] = [
        {
            "reason_code": "memory_retention_watch",
            **reason_count_template,
        },
        {
            "reason_code": "memory_decay_watch",
            **reason_count_template,
        },
        {
            "reason_code": "cross_team_memory_snapshot_ready",
            **reason_count_template,
        },
    ]
    resign_payload(public_payload)

    with pytest.raises(ValueError, match="memory_retention_score"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            public_payload,
        )


def test_public_payload_properties_revalidate_object_setattr_tampering() -> None:
    mod = module()
    row_summary = report(mod, snapshot(mod))
    object.__setattr__(
        row_summary.rows[0],
        "memory_health_score",
        d("0.000000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _ = row_summary.rows[0].public_payload

    report_summary = report(mod, snapshot(mod))
    object.__setattr__(report_summary, "status", "watch")
    with pytest.raises(ValueError, match="status|derived_validation_digest"):
        _ = report_summary.public_payload

    privacy_summary = report(mod, snapshot(mod))
    object.__setattr__(
        privacy_summary.rows[0],
        "route_digest",
        "candidate=secret",
    )
    with pytest.raises(ValueError, match="route_digest|unsafe|derived_validation_digest"):
        _ = privacy_summary.rows[0].public_payload


def test_upstream_reason_codes_are_canonical_for_snapshot_row_report_and_digest() -> None:
    mod = module()
    canonical = (
        mod.REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,
        mod.REASON_CROSS_GROUP_MEMORY_REVIEW_REQUESTED,
        mod.REASON_MEMORY_DECAY_ROUTER_REVIEW_REQUESTED,
    )
    reversed_codes = tuple(reversed(canonical))
    canonical_snapshot = snapshot(
        mod,
        reason_codes=canonical,
    )
    reversed_snapshot = snapshot(
        mod,
        reason_codes=reversed_codes,
    )

    assert canonical_snapshot.reason_codes == canonical
    assert reversed_snapshot.reason_codes == canonical

    canonical_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, canonical_snapshot),
    )
    reversed_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, reversed_snapshot),
    )
    assert reversed_payload == canonical_payload

    tampered = deepcopy(canonical_payload)
    tampered["rows"][0]["reason_codes"] = [
        mod.REASON_ROW_PASS,
        *reversed_codes,
    ]
    resign_row_payload(tampered["rows"][0])
    resign_payload(tampered)
    with pytest.raises(
        ValueError,
        match="canonical|reason_codes|derived_validation_digest",
    ):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            tampered,
        )


def test_multirow_report_is_independent_of_hostile_decimal_context() -> None:
    mod = module()
    items = (
        snapshot(mod),
        snapshot(
            mod,
            "route-ref:watch",
            "lead-group:watch",
            "peer-group:watch",
            last_memory_refresh_at=GENERATED_AT - timedelta(hours=12),
            current_memory_score=d("0.630000"),
            cross_group_alignment_score=d("0.620000"),
            reuse_confidence_score=d("0.660000"),
            handoff_gap_score=d("0.300000"),
        ),
        snapshot(
            mod,
            "route-ref:block",
            "lead-group:block",
            "peer-group:block",
            last_memory_refresh_at=GENERATED_AT - timedelta(days=2),
            baseline_memory_score=d("1.000000"),
            current_memory_score=d("0.420000"),
            cross_group_alignment_score=d("0.440000"),
            reuse_confidence_score=d("0.400000"),
            handoff_gap_score=d("0.700000"),
        ),
    )
    expected = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, *items),
    )
    hostile_context = Context(prec=3, rounding=ROUND_DOWN)
    hostile_context.traps[Inexact] = True
    hostile_context.traps[Rounded] = True

    with localcontext(hostile_context):
        actual = mod.research_strategy_cross_team_memory_decay_router_report_payload(
            report(mod, *items),
        )

    assert actual == expected


@pytest.mark.parametrize(
    "source",
    (
        "import os as harmless\nharmless.system('true')",
        "from pathlib import Path as P\nP('x').read_text()",
        "from pathlib import Path as P\nP('x').write_text('x')",
        "import subprocess as sp\nsp.run(['true'])",
        "from socket import create_connection as dial\ndial(('example.com', 80))",
        "import requests as client\nclient.get('https://example.com')",
        "import importlib as loader\nloader.import_module('os')",
        "__import__('socket')",
        "import os as provider\ngetattr(provider, 'system')('true')",
        "getattr(__builtins__, '__import__')('os')",
        (
            "import httpx as hx\n"
            "async def fetch():\n"
            "    async with hx.AsyncClient() as client:\n"
            "        await client.get('https://example.com')"
        ),
        (
            "import asyncio as aio\n"
            "async def fetch():\n"
            "    await aio.open_connection('example.com', 80)"
        ),
    ),
)
def test_ast_no_io_detector_covers_alias_dynamic_and_async_surfaces(
    source: str,
) -> None:
    assert forbidden_io_surfaces(source)


def test_module_ast_has_no_alias_dynamic_path_execution_or_network_surfaces() -> None:
    assert forbidden_io_surfaces(MODULE_PATH.read_text(encoding="utf-8")) == set()


def test_scores_cross_team_memory_decay_router_pass_watch_and_block() -> None:
    mod = module()
    summary = report(
        mod,
        snapshot(
            mod,
            "route-ref:block?candidate=raw&market=secret",
            "lead-group:block?wallet=hidden",
            "peer-group:block?token=hidden",
            last_memory_refresh_at=GENERATED_AT - timedelta(days=2),
            baseline_memory_score=d("1.000000"),
            current_memory_score=d("0.420000"),
            cross_group_alignment_score=d("0.440000"),
            reuse_confidence_score=d("0.400000"),
            handoff_gap_score=d("0.700000"),
            reason_codes=("cross_group_memory_review_requested",),
        ),
        snapshot(
            mod,
            "route-ref:watch?market_slug=hidden-question",
            "lead-group:watch",
            "peer-group:watch",
            last_memory_refresh_at=GENERATED_AT - timedelta(hours=12),
            baseline_memory_score=d("0.900000"),
            current_memory_score=d("0.630000"),
            cross_group_alignment_score=d("0.620000"),
            reuse_confidence_score=d("0.660000"),
            handoff_gap_score=d("0.300000"),
            reason_codes=("memory_decay_router_review_requested",),
        ),
        snapshot(mod),
    )

    assert mod.RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(summary)
    assert type(summary) is mod.ResearchStrategyCrossTeamMemoryDecayRouterReport
    assert summary.status == "block"
    assert summary.snapshot_count == d("3.000000")
    assert summary.route_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_memory_health_score == d("0.633949")
    assert summary.lowest_memory_health_score == d("0.325000")
    assert summary.highest_memory_decay_ratio == d("0.580000")
    assert summary.highest_memory_age_seconds == d("172800.000000")
    assert summary.highest_decay_pressure_score == d("0.742000")
    assert summary.lowest_cross_group_alignment_score == d("0.440000")
    assert summary.lowest_reuse_confidence_score == d("0.400000")
    assert summary.highest_handoff_gap_score == d("0.700000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked, watched, passed = summary.rows
    assert type(blocked) is mod.ResearchStrategyCrossTeamMemoryDecayRouterRow
    assert blocked.aggregate_row_number == d("1.000000")
    assert blocked.memory_retention_score == d("0.420000")
    assert blocked.memory_decay_ratio == d("0.580000")
    assert blocked.memory_age_seconds == d("172800.000000")
    assert blocked.memory_age_pressure_score == d("1.000000")
    assert blocked.decay_pressure_score == d("0.742000")
    assert blocked.memory_health_score == d("0.325000")
    assert blocked.reason_codes == (
        "cross_group_memory_review_requested",
        "memory_health_block",
        "memory_retention_block",
        "memory_age_block",
        "memory_decay_block",
        "decay_pressure_block",
        "cross_group_alignment_block",
        "reuse_confidence_block",
        "handoff_gap_block",
    )

    assert watched.aggregate_row_number == d("2.000000")
    assert watched.memory_retention_score == d("0.700000")
    assert watched.memory_decay_ratio == d("0.300000")
    assert watched.memory_age_seconds == d("43200.000000")
    assert watched.memory_age_pressure_score == d("0.478261")
    assert watched.decay_pressure_score == d("0.353478")
    assert watched.memory_health_score == d("0.642348")
    assert watched.reason_codes == (
        "memory_decay_router_review_requested",
        "memory_health_watch",
        "memory_retention_watch",
        "memory_age_watch",
        "memory_decay_watch",
        "decay_pressure_watch",
        "cross_group_alignment_watch",
        "reuse_confidence_watch",
        "handoff_gap_watch",
    )

    assert passed.aggregate_row_number == d("3.000000")
    assert passed.memory_retention_score == d("0.950000")
    assert passed.memory_decay_ratio == d("0.050000")
    assert passed.memory_age_pressure_score == d("0.000000")
    assert passed.decay_pressure_score == d("0.050000")
    assert passed.memory_health_score == d("0.934500")
    assert passed.reason_codes == (
        "cross_team_memory_decay_router_pass",
        "cross_team_memory_snapshot_ready",
    )
    assert passed.route_digest.startswith("sha256:")
    assert len(passed.route_digest) == 71
    assert len(passed.derived_validation_digest) == 64

    counts = {item.reason_code: item for item in summary.reason_counts}
    assert counts["memory_health_block"] == (
        mod.ResearchStrategyCrossTeamMemoryDecayRouterReasonCount(
            reason_code="memory_health_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_empty_report_is_report_only_block() -> None:
    mod = module()
    summary = report(mod)

    assert summary.status == "block"
    assert summary.snapshot_count == ZERO
    assert summary.route_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_memory_health_score == ZERO
    assert summary.lowest_memory_health_score == ZERO
    assert summary.highest_memory_decay_ratio == ZERO
    assert summary.highest_memory_age_seconds == ZERO
    assert summary.highest_decay_pressure_score == ZERO
    assert summary.lowest_cross_group_alignment_score == ZERO
    assert summary.lowest_reuse_confidence_score == ZERO
    assert summary.highest_handoff_gap_score == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "cross_team_memory_decay_router_report_block",
        "cross_team_memory_decay_router_no_snapshots",
    )
    assert summary.reason_counts == (
        mod.ResearchStrategyCrossTeamMemoryDecayRouterReasonCount(
            reason_code="cross_team_memory_decay_router_no_snapshots",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_public_payload_is_deterministic_digest_bound_and_leak_free() -> None:
    mod = module()
    first = report(
        mod,
        snapshot(mod, "route-ref:one?candidate=raw", "lead:one", "peer:one"),
        snapshot(mod, "route-ref:two?market=raw", "lead:two", "peer:two"),
    )
    second = report(
        mod,
        snapshot(mod, "route-ref:two?market=raw", "lead:two", "peer:two"),
        snapshot(mod, "route-ref:one?candidate=raw", "lead:one", "peer:one"),
    )

    first_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        first,
    )
    second_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert first.derived_validation_digest == canonical_digest(first_payload)
    assert mod.research_strategy_cross_team_memory_decay_router_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(tampered)


def test_exports_strict_public_payload_validator() -> None:
    mod = module()
    validator = getattr(
        mod,
        "validate_research_strategy_cross_team_memory_decay_router_report_public_payload",
        None,
    )
    assert callable(validator)

    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )
    assert validator(public_payload) is None


def test_public_payload_rejects_unknown_missing_and_wrongly_typed_schema() -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )

    invalid_payloads: list[tuple[dict[str, Any], str]] = []

    unknown_report_field = deepcopy(public_payload)
    unknown_report_field["safe_extension"] = "pass"
    resign_payload(unknown_report_field)
    invalid_payloads.append((unknown_report_field, "payload fields"))

    missing_report_field = deepcopy(public_payload)
    missing_report_field.pop("status")
    resign_payload(missing_report_field)
    invalid_payloads.append((missing_report_field, "payload fields"))

    wrong_rows_container = deepcopy(public_payload)
    wrong_rows_container["rows"] = tuple(wrong_rows_container["rows"])
    resign_payload(wrong_rows_container)
    invalid_payloads.append((wrong_rows_container, "payload.rows"))

    unknown_row_field = deepcopy(public_payload)
    unknown_row_field["rows"][0]["safe_extension"] = "pass"
    resign_payload(unknown_row_field)
    invalid_payloads.append((unknown_row_field, r"payload.rows\[0\] fields"))

    missing_reason_count_field = deepcopy(public_payload)
    missing_reason_count_field["reason_counts"][0].pop("row_ratio")
    resign_payload(missing_reason_count_field)
    invalid_payloads.append(
        (
            missing_reason_count_field,
            r"payload.reason_counts\[0\] fields",
        ),
    )

    for invalid_payload, error_pattern in invalid_payloads:
        with pytest.raises(ValueError, match=error_pattern):
            mod.research_strategy_cross_team_memory_decay_router_report_payload(
                invalid_payload,
            )


def test_public_payload_revalidates_nested_integrity_flags_and_derived_values() -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )

    stale_row_digest = deepcopy(public_payload)
    stale_row_digest["rows"][0]["memory_health_score"] = "0.000000"
    resign_payload(stale_row_digest)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            stale_row_digest,
        )

    downgraded_nested_flag = deepcopy(public_payload)
    downgraded_nested_flag["rows"][0]["readonly"] = False
    resign_payload(downgraded_nested_flag)
    with pytest.raises(ValueError, match="readonly"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            downgraded_nested_flag,
        )

    recomputed_summary_metric = deepcopy(public_payload)
    recomputed_summary_metric["average_memory_health_score"] = "0.000000"
    resign_payload(recomputed_summary_metric)
    with pytest.raises(ValueError, match="average_memory_health_score"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            recomputed_summary_metric,
        )

    recomputed_reason_count = deepcopy(public_payload)
    recomputed_reason_count["reason_counts"][0]["count"] = "9.000000"
    resign_payload(recomputed_reason_count)
    with pytest.raises(ValueError, match="reason_counts"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            recomputed_reason_count,
        )


def test_public_payload_rejects_forged_resigned_reason_status_rollups() -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )

    forged = deepcopy(public_payload)
    forged["rows"][0]["reason_codes"].append("memory_health_watch")
    resign_row_payload(forged["rows"][0])
    forged["reason_codes"].insert(1, "memory_health_watch")
    forged_reason_count = deepcopy(forged["reason_counts"][0])
    forged_reason_count["reason_code"] = "memory_health_watch"
    forged["reason_counts"].insert(0, forged_reason_count)
    resign_payload(forged)

    with pytest.raises(ValueError, match="status must match reason_codes"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(forged)


def test_report_digest_rejects_mutated_nested_row_before_resigning() -> None:
    mod = module()
    summary = report(mod, snapshot(mod))
    object.__setattr__(summary.rows[0], "route_digest", f"sha256:{'0' * 64}")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        mod.research_strategy_cross_team_memory_decay_router_report_digest(summary)


def test_report_requires_exact_tuple_containers() -> None:
    mod = module()
    summary = report(mod, snapshot(mod))

    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(summary, rows=_TupleSubclass(summary.rows))
    with pytest.raises(ValueError, match="reason_counts must be a tuple"):
        replace(summary, reason_counts=_TupleSubclass(summary.reason_counts))


def test_memory_age_seconds_uses_exact_decimal_arithmetic_for_large_ranges() -> None:
    mod = module()
    generated_at = datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)
    summary = report(
        mod,
        snapshot(
            mod,
            observed_at=generated_at,
            last_memory_refresh_at=datetime(1, 1, 1, 0, 0, 0, 1, tzinfo=UTC),
        ),
        generated_at=generated_at,
    )

    assert summary.rows[0].memory_age_seconds == d("315537897599.999998")


def test_decimal_arithmetic_is_independent_of_ambient_context() -> None:
    mod = module()
    expected = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )

    with localcontext() as ctx:
        ctx.prec = 6
        ctx.rounding = ROUND_DOWN
        actual = mod.research_strategy_cross_team_memory_decay_router_report_payload(
            report(mod, snapshot(mod)),
        )

    assert actual == expected


def test_decimal_inputs_apply_raw_bounds_before_quantization() -> None:
    mod = module()

    with pytest.raises(ValueError, match="between 0 and 1"):
        config(mod, min_pass_memory_health_score=d("1.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        snapshot(mod, handoff_gap_score=d("-0.0000004"))


@pytest.mark.parametrize(
    "invalid_value",
    (
        d("-0"),
        d("-0.000000"),
        d("NaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_decimal_inputs_reject_signed_zero_and_non_finite_values(
    invalid_value: Decimal,
) -> None:
    mod = module()

    with pytest.raises(ValueError, match="signed zero|finite"):
        snapshot(mod, current_memory_score=invalid_value)


def test_reason_code_containers_require_exact_tuples() -> None:
    mod = module()

    with pytest.raises(ValueError, match="tuple"):
        snapshot(mod, reason_codes=["cross_team_memory_snapshot_ready"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="tuple"):
        snapshot(
            mod,
            reason_codes=_TupleSubclass(("cross_team_memory_snapshot_ready",)),
        )


def test_stable_sort_uses_complete_row_tie_breakers() -> None:
    mod = module()
    first_snapshot = snapshot(
        mod,
        route_ref="route-ref:shared",
        lead_group_ref="lead-group:first",
        peer_group_ref="peer-group:first",
    )
    second_snapshot = snapshot(
        mod,
        route_ref="route-ref:shared",
        lead_group_ref="lead-group:second",
        peer_group_ref="peer-group:second",
    )

    first = report(mod, first_snapshot, second_snapshot)
    second = report(mod, second_snapshot, first_snapshot)

    first_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        first,
    )
    second_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        second,
    )
    assert first_payload == second_payload
    assert tuple(row.lead_group_digest for row in first.rows) == tuple(
        sorted(row.lead_group_digest for row in first.rows),
    )


def test_public_payload_embeds_config_for_full_derived_revalidation() -> None:
    mod = module()
    cfg = config(
        mod,
        fresh_memory_age_seconds=d("1800.000000"),
        stale_memory_age_seconds=d("7200.000000"),
    )
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(
            mod,
            snapshot(
                mod,
                last_memory_refresh_at=GENERATED_AT - timedelta(hours=1),
            ),
            cfg=cfg,
        ),
    )

    assert public_payload["config"] == {
        "config_version": (
            mod.DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ),
        "fresh_memory_age_seconds": "1800.000000",
        "stale_memory_age_seconds": "7200.000000",
        "min_pass_memory_health_score": "0.700000",
        "min_watch_memory_health_score": "0.500000",
        "min_pass_memory_retention_score": "0.750000",
        "min_watch_memory_retention_score": "0.500000",
        "min_pass_cross_group_alignment_score": "0.700000",
        "min_watch_cross_group_alignment_score": "0.500000",
        "min_pass_reuse_confidence_score": "0.700000",
        "min_watch_reuse_confidence_score": "0.500000",
        "max_pass_decay_pressure_score": "0.200000",
        "max_watch_decay_pressure_score": "0.450000",
        "max_pass_handoff_gap_score": "0.200000",
        "max_watch_handoff_gap_score": "0.450000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert public_payload["config_version"] == public_payload["config"]["config_version"]
    assert (
        mod.validate_research_strategy_cross_team_memory_decay_router_report_public_payload(
            public_payload,
        )
        is None
    )


def test_fully_resigned_payload_recomputes_memory_age_pressure() -> None:
    mod = module()
    forged = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )
    row = forged["rows"][0]
    row["memory_age_pressure_score"] = "0.100000"
    row["decay_pressure_score"] = "0.080000"
    row["memory_health_score"] = "0.914500"
    resign_row_payload(row)
    forged["average_memory_health_score"] = "0.914500"
    forged["lowest_memory_health_score"] = "0.914500"
    forged["highest_decay_pressure_score"] = "0.080000"
    resign_payload(forged)

    with pytest.raises(ValueError, match="memory_age_pressure_score"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(forged)


def test_public_payload_requires_canonical_decimal_and_datetime_strings() -> None:
    mod = module()
    public_payload = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod, snapshot(mod)),
    )

    noncanonical_decimal = deepcopy(public_payload)
    noncanonical_decimal["average_memory_health_score"] = "0.7"
    resign_payload(noncanonical_decimal)
    with pytest.raises(ValueError, match="canonical"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            noncanonical_decimal,
        )

    invalid_decimal = deepcopy(public_payload)
    invalid_decimal["average_memory_health_score"] = "not-a-decimal"
    resign_payload(invalid_decimal)
    with pytest.raises(ValueError, match="Decimal"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            invalid_decimal,
        )

    extreme_decimal = deepcopy(public_payload)
    extreme_decimal["average_memory_health_score"] = "1E+999999"
    resign_payload(extreme_decimal)
    with pytest.raises(ValueError, match="Decimal"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            extreme_decimal,
        )

    negative_zero = mod.research_strategy_cross_team_memory_decay_router_report_payload(
        report(mod),
    )
    negative_zero["snapshot_count"] = "-0.000000"
    resign_payload(negative_zero)
    with pytest.raises(ValueError, match="canonical"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            negative_zero,
        )

    noncanonical_datetime = deepcopy(public_payload)
    noncanonical_datetime["generated_at"] = "2026-07-09T12:00:00Z"
    resign_payload(noncanonical_datetime)
    with pytest.raises(ValueError, match="canonical"):
        mod.research_strategy_cross_team_memory_decay_router_report_payload(
            noncanonical_datetime,
        )


def test_rejects_non_decimal_subclasses_bad_times_and_false_flags() -> None:
    mod = module()

    with pytest.raises(ValueError, match="Decimal"):
        config(mod, min_pass_memory_health_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(mod, paper_only=False)
    with pytest.raises(ValueError, match="datetime"):
        snapshot(mod, observed_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="baseline_memory_score"):
        snapshot(mod, baseline_memory_score=d("0.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        snapshot(mod, reason_codes=("candidate_id_leak",))
    with pytest.raises(ValueError, match="last_memory_refresh_at"):
        report(
            mod,
            snapshot(
                mod,
                last_memory_refresh_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


def test_dataclasses_are_frozen_final_decimal_only_and_readonly() -> None:
    mod = module()
    summary = report(mod, snapshot(mod))

    public_values = (
        config(mod),
        snapshot(mod),
        summary,
        *summary.rows,
        *summary.reason_counts,
    )
    for value in public_values:
        assert is_dataclass(value)
        assert_decimal_public_fields(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReportSubclass(mod.ResearchStrategyCrossTeamMemoryDecayRouterReport):
            pass


def test_public_dataclasses_are_slotted_and_final_exact_types() -> None:
    mod = module()
    summary = report(mod, snapshot(mod))
    public_types = (
        mod.ResearchStrategyCrossTeamMemoryDecayRouterConfig,
        mod.ResearchStrategyCrossTeamMemoryDecayRouterSnapshot,
        mod.ResearchStrategyCrossTeamMemoryDecayRouterRow,
        mod.ResearchStrategyCrossTeamMemoryDecayRouterReasonCount,
        mod.ResearchStrategyCrossTeamMemoryDecayRouterReport,
    )

    for public_type in public_types:
        assert getattr(public_type, "__final__", False) is True
        assert hasattr(public_type, "__slots__")

    for value in (
        config(mod),
        snapshot(mod),
        summary,
        *summary.rows,
        *summary.reason_counts,
    ):
        assert not hasattr(value, "__dict__")


def test_builder_revalidates_tampered_config_and_snapshot_inputs() -> None:
    mod = module()

    tampered_config = config(mod)
    object.__setattr__(tampered_config, "min_watch_memory_health_score", d("NaN"))
    with pytest.raises(ValueError, match="min_watch_memory_health_score.*finite"):
        report(mod, snapshot(mod), cfg=tampered_config)

    tampered_snapshot = snapshot(
        mod,
    )
    object.__setattr__(
        tampered_snapshot,
        "reason_codes",
        (
            mod.REASON_MEMORY_DECAY_ROUTER_REVIEW_REQUESTED,
            mod.REASON_CROSS_GROUP_MEMORY_REVIEW_REQUESTED,
            mod.REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,
        ),
    )
    with pytest.raises(ValueError, match="reason_codes must be canonical"):
        report(mod, tampered_snapshot)


def test_row_public_payload_revalidates_tampered_container_types() -> None:
    mod = module()
    summary = report(mod, snapshot(mod))
    row = summary.rows[0]
    object.__setattr__(row, "reason_codes", list(row.reason_codes))
    object.__setattr__(
        row,
        "derived_validation_digest",
        mod._payload_digest(mod._row_payload(row, include_digest=False)),
    )

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _ = row.public_payload


def test_module_has_no_runtime_external_or_execution_surfaces() -> None:
    mod = module()
    tree = ast.parse(MODULE_PATH.read_text())
    imports: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert imports.isdisjoint(
        {
            "ccxt",
            "httpx",
            "pandas",
            "pathlib",
            "polars",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "subprocess",
            "supabase",
            "urllib",
            "web3",
        },
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not float_constants
    assert not any(
        fragment in exported_name.lower()
        for exported_name in mod.__all__
        for fragment in (
            "auth",
            "execute",
            "live",
            "order",
            "persist",
            "recommend",
            "sizing",
            "trade",
            "wallet",
        )
    )
    assert set(mod.RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_STATUSES) == {
        "pass",
        "watch",
        "block",
    }
