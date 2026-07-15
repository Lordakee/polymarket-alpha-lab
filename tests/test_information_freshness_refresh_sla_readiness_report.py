from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.information_freshness_refresh_sla_readiness_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "information_freshness_refresh_sla_readiness_report.py"
)
GENERATED_AT = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    values: dict[str, object] = {
        "config_version": "information-freshness-refresh-sla-readiness-test-v0",
        "market_data_stale_after_seconds": d("120.000000"),
        "external_evidence_stale_after_seconds": d("3600.000000"),
        "research_packet_stale_after_seconds": d("7200.000000"),
        "market_data_latency_sla_seconds": d("15.000000"),
        "external_evidence_latency_sla_seconds": d("300.000000"),
        "research_packet_latency_sla_seconds": d("900.000000"),
    }
    values.update(overrides)
    return module().InformationFreshnessRefreshSlaReadinessConfig(**values)


def item(
    information_id: str,
    *,
    information_surface: str = "market_data",
    age_seconds: Decimal = d("60.000000"),
    latency_seconds: Decimal = d("5.000000"),
    upstream_refresh_sla_breached: bool = False,
    required_for_recommendation: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module().InformationFreshnessRefreshSlaReadinessItem(
        information_id=information_id,
        information_surface=information_surface,
        age_seconds=age_seconds,
        latency_seconds=latency_seconds,
        upstream_refresh_sla_breached=upstream_refresh_sla_breached,
        required_for_recommendation=required_for_recommendation,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any) -> Any:
    return module().build_information_freshness_refresh_sla_readiness_report(
        items,
        config=config(),
        generated_at=GENERATED_AT,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk_payload_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk_payload_values(child))
    return (value,)


def assert_payload_has_no_public_numbers(value: object) -> None:
    values = walk_payload_values(value)
    assert not any(type(payload_value) is float for payload_value in values)
    assert not any(type(payload_value) is int for payload_value in values)
    assert not any(type(payload_value) is Decimal for payload_value in values)


def recompute_payload_digest(payload: dict[str, object]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    canonical = json.dumps(
        payload_without_digest,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(
        ("information_freshness_refresh_sla_readiness|" + canonical).encode("utf-8"),
    ).hexdigest()


def test_builds_readiness_report_that_blocks_stale_recommendation_inputs() -> None:
    report = build_report(
        item("market-pass"),
        item(
            "market-stale",
            information_surface="market_data",
            age_seconds=d("121.000000"),
        ),
        item(
            "evidence-latency",
            information_surface="external_evidence",
            age_seconds=d("600.000000"),
            latency_seconds=d("301.000000"),
        ),
        item(
            "packet-upstream-breach",
            information_surface="research_packet",
            age_seconds=d("60.000000"),
            latency_seconds=d("30.000000"),
            upstream_refresh_sla_breached=True,
        ),
        item(
            "evidence-watch",
            information_surface="external_evidence",
            age_seconds=d("3600.000001"),
            required_for_recommendation=False,
        ),
    )

    assert type(report) is module().InformationFreshnessRefreshSlaReadinessReport
    assert report.generated_at == GENERATED_AT
    assert report.readiness_status == "blocked"
    assert report.recommendation_gate == "block_report_only_stale_information_recommendation"
    assert report.information_count == d("5.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("3.000000")
    assert report.required_information_count == d("4.000000")
    assert report.blocking_required_information_count == d("3.000000")
    assert report.stale_information_count == d("2.000000")
    assert report.latency_sla_breach_count == d("1.000000")
    assert report.upstream_refresh_sla_breach_count == d("1.000000")
    assert report.issue_ratio == d("0.800000")
    assert report.required_block_ratio == d("0.750000")
    assert report.max_age_seconds == d("3600.000001")
    assert report.max_latency_seconds == d("301.000000")
    assert report.reason_codes == (
        "required_information_blocked",
        "market_data_stale",
        "external_evidence_stale",
        "external_evidence_latency_sla_breached",
        "research_packet_refresh_sla_breached",
    )
    assert tuple(row.information_id for row in report.rows) == (
        "market-stale",
        "evidence-latency",
        "packet-upstream-breach",
        "evidence-watch",
        "market-pass",
    )
    assert tuple(row.readiness_status for row in report.rows) == (
        "blocked",
        "blocked",
        "blocked",
        "watch",
        "pass",
    )
    assert report.rows[0].reason_codes == (
        "required_information_blocked",
        "market_data_stale",
    )
    assert report.rows[1].reason_codes == (
        "required_information_blocked",
        "external_evidence_latency_sla_breached",
    )
    assert report.rows[2].reason_codes == (
        "required_information_blocked",
        "research_packet_refresh_sla_breached",
    )
    assert report.rows[3].reason_codes == ("external_evidence_stale",)
    assert report.rows[4].reason_codes == ("information_freshness_refresh_sla_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_blocks_as_missing_information_readiness_evidence() -> None:
    report = build_report()

    assert report.readiness_status == "blocked"
    assert report.recommendation_gate == "block_report_only_stale_information_recommendation"
    assert report.information_count == d("0.000000")
    assert report.issue_ratio == d("0.000000")
    assert report.required_block_ratio == d("0.000000")
    assert report.max_age_seconds == d("0.000000")
    assert report.max_latency_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("no_information_freshness_inputs",)


def test_report_snapshots_complete_effective_config_for_replay() -> None:
    api = module()
    source_config = config(
        market_data_stale_after_seconds=d("121.000000"),
        external_evidence_stale_after_seconds=d("3601.000000"),
        research_packet_stale_after_seconds=d("7201.000000"),
        market_data_latency_sla_seconds=d("16.000000"),
        external_evidence_latency_sla_seconds=d("301.000000"),
        research_packet_latency_sla_seconds=d("901.000000"),
    )
    report = api.build_information_freshness_refresh_sla_readiness_report(
        (item("snapshot", information_surface="market_data"),),
        config=source_config,
        generated_at=GENERATED_AT,
    )

    assert report.effective_config == source_config
    assert report.effective_config is not source_config
    payload = api.information_freshness_refresh_sla_readiness_report_payload(report)
    assert payload["effective_config"] == {
        "config_version": "information-freshness-refresh-sla-readiness-test-v0",
        "market_data_stale_after_seconds": "121.000000",
        "external_evidence_stale_after_seconds": "3601.000000",
        "research_packet_stale_after_seconds": "7201.000000",
        "market_data_latency_sla_seconds": "16.000000",
        "external_evidence_latency_sla_seconds": "301.000000",
        "research_packet_latency_sla_seconds": "901.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    object.__setattr__(
        source_config,
        "market_data_stale_after_seconds",
        d("999.000000"),
    )
    assert report.effective_config.market_data_stale_after_seconds == d("121.000000")


def test_rehashed_payload_cannot_promote_stale_row_by_rewriting_row_threshold() -> None:
    api = module()
    report = build_report(item("threshold-forgery", age_seconds=d("121.000000")))
    payload = json.loads(
        json.dumps(
            api.information_freshness_refresh_sla_readiness_report_payload(report),
        ),
    )
    row = payload["rows"][0]

    row["stale_after_seconds"] = "1000.000000"
    row["readiness_status"] = "pass"
    row["reason_codes"] = ["information_freshness_refresh_sla_ready"]
    payload.update(
        {
            "readiness_status": "pass",
            "recommendation_gate": "allow_report_only_information_freshness_readiness",
            "pass_count": "1.000000",
            "blocked_count": "0.000000",
            "blocking_required_information_count": "0.000000",
            "stale_information_count": "0.000000",
            "issue_ratio": "0.000000",
            "required_block_ratio": "0.000000",
            "reason_codes": ["information_freshness_refresh_sla_ready"],
        },
    )
    payload["derived_validation_digest"] = recompute_payload_digest(payload)

    with pytest.raises(ValueError, match="stale_after_seconds must match effective_config"):
        api.information_freshness_refresh_sla_readiness_report_payload(payload)


def test_payload_is_json_safe_decimal_string_only_and_tamper_evident() -> None:
    api = module()
    report = build_report(item("payload-pass"))
    payload = api.information_freshness_refresh_sla_readiness_report_payload(report)
    same_payload = api.information_freshness_refresh_sla_readiness_report_payload(payload)

    assert payload == same_payload
    assert payload["information_count"] == "1.000000"
    assert payload["issue_ratio"] == "0.000000"
    assert payload["rows"][0]["age_seconds"] == "60.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert same_payload is not payload
    assert same_payload["rows"] is not payload["rows"]
    assert same_payload["rows"][0] is not payload["rows"][0]
    _assert_json_payload_is_deeply_immutable(payload)
    _assert_json_payload_is_deeply_immutable(same_payload)
    assert_payload_has_no_public_numbers(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["information_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.information_freshness_refresh_sla_readiness_report_payload(tampered)

    forbidden_value = dict(payload)
    forbidden_value["rows"] = [
        {
            **payload["rows"][0],
            "information_id": "wallet-auth-order",
        },
    ]
    with pytest.raises(ValueError, match="forbidden public value"):
        api.information_freshness_refresh_sla_readiness_report_payload(forbidden_value)


def test_mapping_payload_export_is_deeply_copied_from_caller_input() -> None:
    api = module()
    payload = api.information_freshness_refresh_sla_readiness_report_payload(
        build_report(item("mapping-copy")),
    )
    caller_input = json.loads(json.dumps(payload))

    exported = api.information_freshness_refresh_sla_readiness_report_payload(
        MappingProxyType(caller_input),
    )
    caller_input["readonly"] = False
    caller_input["rows"][0]["readonly"] = False
    caller_input["rows"].append(dict(caller_input["rows"][0]))

    assert exported["readonly"] is True
    assert exported["rows"][0]["readonly"] is True
    assert len(exported["rows"]) == 1
    _assert_json_payload_is_deeply_immutable(exported)


def test_rejects_rehashed_dict_payload_with_inconsistent_derived_fields() -> None:
    api = module()
    payload = api.information_freshness_refresh_sla_readiness_report_payload(
        build_report(item("rehashed-stale", age_seconds=d("121.000000"))),
    )
    tampered = dict(payload)
    tampered["rows"] = [
        {
            **payload["rows"][0],
            "readiness_status": "pass",
            "reason_codes": ["information_freshness_refresh_sla_ready"],
        },
    ]
    tampered.update(
        {
            "readiness_status": "pass",
            "recommendation_gate": "allow_report_only_information_freshness_readiness",
            "pass_count": "1.000000",
            "blocked_count": "0.000000",
            "blocking_required_information_count": "0.000000",
            "stale_information_count": "0.000000",
            "issue_ratio": "0.000000",
            "required_block_ratio": "0.000000",
            "reason_codes": ["information_freshness_refresh_sla_ready"],
        },
    )
    tampered["derived_validation_digest"] = recompute_payload_digest(tampered)

    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        api.information_freshness_refresh_sla_readiness_report_payload(tampered)


def test_standard_serializer_rejects_internally_tampered_report_object() -> None:
    api = module()
    report = build_report(item("object-stale", age_seconds=d("121.000000")))
    object.__setattr__(report.rows[0], "readiness_status", "pass")
    object.__setattr__(
        report.rows[0],
        "reason_codes",
        ("information_freshness_refresh_sla_ready",),
    )
    for field_name, value in (
        ("readiness_status", "pass"),
        ("recommendation_gate", "allow_report_only_information_freshness_readiness"),
        ("pass_count", d("1.000000")),
        ("blocked_count", d("0.000000")),
        ("blocking_required_information_count", d("0.000000")),
        ("stale_information_count", d("0.000000")),
        ("issue_ratio", d("0.000000")),
        ("required_block_ratio", d("0.000000")),
        ("reason_codes", ("information_freshness_refresh_sla_ready",)),
    ):
        object.__setattr__(report, field_name, value)
    object.__setattr__(
        report,
        "derived_validation_digest",
        api._report_derived_validation_digest(report),
    )

    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        api.information_freshness_refresh_sla_readiness_report_payload(report)


def test_object_serializer_rejects_list_backed_rows() -> None:
    api = module()
    report = build_report(item("list-backed-row"))
    object.__setattr__(report, "rows", list(report.rows))

    with pytest.raises(ValueError, match="rows.*tuple"):
        api.information_freshness_refresh_sla_readiness_report_payload(report)


def test_object_serializer_rejects_non_utc_materialized_datetime() -> None:
    api = module()
    report = build_report(item("non-utc-report"))
    offset = timezone(timedelta(hours=5, minutes=30))
    object.__setattr__(report, "generated_at", report.generated_at.astimezone(offset))

    with pytest.raises(ValueError, match="generated_at.*normalized to UTC"):
        api.information_freshness_refresh_sla_readiness_report_payload(report)


def test_object_serializer_rejects_rehashed_reversed_rows() -> None:
    api = module()
    report = build_report(item("a-pass"), item("b-pass"))
    object.__setattr__(report, "rows", tuple(reversed(report.rows)))
    object.__setattr__(
        report,
        "derived_validation_digest",
        api._report_derived_validation_digest(report),
    )

    with pytest.raises(ValueError, match="deterministic"):
        api.information_freshness_refresh_sla_readiness_report_payload(report)


def test_object_serializer_revalidates_decimal_shape_and_nested_flags() -> None:
    api = module()
    noncanonical_decimal = build_report(item("a-pass"), item("b-pass"))
    object.__setattr__(noncanonical_decimal, "information_count", d("2"))
    object.__setattr__(
        noncanonical_decimal,
        "derived_validation_digest",
        api._report_derived_validation_digest(noncanonical_decimal),
    )
    with pytest.raises(ValueError, match="information_count.*six decimal"):
        api.information_freshness_refresh_sla_readiness_report_payload(
            noncanonical_decimal,
        )

    nested_flag = build_report(item("nested-flag"))
    object.__setattr__(nested_flag.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="row readonly"):
        api.information_freshness_refresh_sla_readiness_report_payload(nested_flag)


def test_public_dataclasses_are_frozen_exact_decimal_only_and_hard_flags() -> None:
    api = module()
    report = build_report(item("frozen-pass"))

    assert tuple(api.__all__) == (
        "DEFAULT_INFORMATION_FRESHNESS_REFRESH_SLA_READINESS_CONFIG_VERSION",
        "InformationFreshnessRefreshSlaReadinessConfig",
        "InformationFreshnessRefreshSlaReadinessItem",
        "InformationFreshnessRefreshSlaReadinessReport",
        "InformationFreshnessRefreshSlaReadinessRow",
        "build_information_freshness_refresh_sla_readiness_report",
        "information_freshness_refresh_sla_readiness_report_payload",
    )
    for exported_name in api.__all__:
        value = getattr(api, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].readiness_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        item("flag-fail", paper_only=False)
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedConfig", (api.InformationFreshnessRefreshSlaReadinessConfig,), {})
    with pytest.raises(ValueError, match="market_data_stale_after_seconds"):
        config(market_data_stale_after_seconds=DecimalSubclass("120.000000"))
    with pytest.raises(ValueError, match="age_seconds"):
        item("age-float", age_seconds=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="latency_seconds"):
        item("latency-unquantized", latency_seconds=d("1.0000001"))

    for value in (
        config(),
        item("field-item"),
        *report.rows,
        report,
    ):
        for field in fields(value):
            if field.name.endswith(("_count", "_ratio", "_seconds")):
                assert type(getattr(value, field.name)) is Decimal


def test_rejects_bad_surfaces_duplicates_and_tampered_consistency() -> None:
    report = build_report(item("valid-pass"))

    with pytest.raises(ValueError, match="information_surface"):
        item("bad-surface", information_surface="team_memory")
    with pytest.raises(ValueError, match="information_id"):
        item(" bad-id ")
    with pytest.raises(ValueError, match="unique information_id"):
        build_report(item("dup"), item("dup"))
    with pytest.raises(ValueError, match="information_count"):
        replace(report, information_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=("market_data_stale",))
    with pytest.raises(ValueError, match="recommendation_gate"):
        replace(report, recommendation_gate="block_report_only_stale_information_recommendation")
    with pytest.raises(ValueError, match="deterministic"):
        replace(
            build_report(item("b-pass"), item("a-pass")),
            rows=tuple(reversed(build_report(item("b-pass"), item("a-pass")).rows)),
        )


def test_module_is_readonly_report_only_and_external_surface_free() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    assert set(_imported_modules(tree)) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
    }
    normalized_names = {
        _normalize_identifier(name)
        for name in _collected_names(tree)
        if _normalize_identifier(name) != "readonly"
    }
    for fragment in (
        "persist",
        "supabase",
        "teammemory",
        "cli",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "account",
        "broker",
        "submit",
        "cancel",
        "signing",
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
                "input",
                "open",
                "print",
                "read",
                "write",
            }


def _imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def _collected_names(tree: ast.Module) -> set[str]:
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


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _assert_json_payload_is_deeply_immutable(payload: object) -> None:
    assert isinstance(payload, dict)
    rows = payload["rows"]
    assert isinstance(rows, list)
    row = rows[0]
    assert isinstance(row, dict)

    object_mutators = (
        lambda value: value.__setitem__("readonly", False),
        lambda value: value.__delitem__("readonly"),
        lambda value: value.clear(),
        lambda value: value.pop("readonly"),
        lambda value: value.popitem(),
        lambda value: value.setdefault("extra", True),
        lambda value: value.update({"readonly": False}),
        lambda value: value.__ior__({"readonly": False}),
    )
    for value in (payload, row):
        for mutate in object_mutators:
            with pytest.raises(TypeError, match="payload is immutable"):
                mutate(value)

    array_mutators = (
        lambda value: value.__setitem__(0, value[0]),
        lambda value: value.__delitem__(0),
        lambda value: value.append(value[0]),
        lambda value: value.clear(),
        lambda value: value.extend((value[0],)),
        lambda value: value.insert(0, value[0]),
        lambda value: value.pop(),
        lambda value: value.remove(value[0]),
        lambda value: value.reverse(),
        lambda value: value.sort(),
        lambda value: value.__iadd__((value[0],)),
        lambda value: value.__imul__(2),
    )
    for value in (payload["reason_codes"], rows, row["reason_codes"]):
        assert isinstance(value, list)
        for mutate in array_mutators:
            with pytest.raises(TypeError, match="payload is immutable"):
                mutate(value)
