from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
import inspect
import json

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


class DecimalSubclass(Decimal):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.probability_event_correlation_cluster_exposure_report",
    )


def report(**overrides):
    module = api()
    values = {
        "cluster_id": "cluster_macro_rates",
        "open_candidate_count": d("3"),
        "same_outcome_family_count": d("1"),
        "aggregate_edge_probability": d("0.180000"),
        "correlation_risk_probability": d("0.040000"),
        "manual_exposure_limit_probability": d("0.250000"),
    }
    values.update(overrides)
    return module.build_probability_event_correlation_cluster_exposure_report(
        module.ProbabilityEventCorrelationClusterExposureInput(**values),
    )


def canonical_digest(payload: dict[str, object]) -> str:
    import hashlib

    body = {
        key: value
        for key, value in payload.items()
        if key not in {"payload_digest", "public_payload"}
    }
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def assert_decimal_only_dataclass(instance: object) -> None:
    assert is_dataclass(instance)
    assert instance.__dataclass_params__.frozen is True
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, Decimal):
            assert type(value) is Decimal


def test_correlation_cluster_exposure_report_blocks_limit_breach() -> None:
    result = report(
        cluster_id="cluster_macro_rates",
        open_candidate_count=d("4"),
        same_outcome_family_count=d("2"),
        aggregate_edge_probability=d("0.320000"),
        correlation_risk_probability=d("0.090000"),
        manual_exposure_limit_probability=d("0.250000"),
    )

    assert result.config_version == (
        "probability-event-correlation-cluster-exposure-report-v0"
    )
    assert result.cluster_id == "cluster_macro_rates"
    assert result.exposure_status == "block"
    assert result.adjusted_edge_probability == d("0.230000")
    assert result.reason_codes == (
        "correlation_cluster_same_outcome_family_watch",
        "correlation_cluster_risk_adjusted_edge_block",
    )
    assert result.manual_next_step == "manual_block_cluster_exposure_limit"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_decimal_only_dataclass(result)

    payload = result.public_payload
    assert payload == api().probability_event_correlation_cluster_exposure_report_payload(
        result,
    )
    assert payload["cluster_id"] == "cluster_macro_rates"
    assert payload["adjusted_edge_probability"] == "0.230000"
    assert payload["payload_digest"] == result.payload_digest
    assert payload["payload_digest"] == canonical_digest(payload)
    assert len(payload["payload_digest"]) == 64
    int(payload["payload_digest"], 16)
    api().validate_probability_event_correlation_cluster_exposure_public_payload(
        payload,
    )


def test_correlation_cluster_exposure_report_watches_correlated_open_candidates() -> None:
    result = report(
        cluster_id="cluster_elections",
        open_candidate_count=d("2"),
        same_outcome_family_count=d("0"),
        aggregate_edge_probability=d("0.210000"),
        correlation_risk_probability=d("0.050000"),
        manual_exposure_limit_probability=d("0.250000"),
    )

    assert result.exposure_status == "watch"
    assert result.adjusted_edge_probability == d("0.160000")
    assert result.reason_codes == ("correlation_cluster_open_candidate_watch",)
    assert result.manual_next_step == "manual_review_cluster_correlation"


def test_correlation_cluster_exposure_report_clears_single_uncorrelated_candidate() -> None:
    result = report(
        cluster_id="cluster_energy_inventory",
        open_candidate_count=d("1"),
        same_outcome_family_count=d("0"),
        aggregate_edge_probability=d("0.090000"),
        correlation_risk_probability=d("0.020000"),
        manual_exposure_limit_probability=d("0.250000"),
    )

    assert result.exposure_status == "clear"
    assert result.adjusted_edge_probability == d("0.070000")
    assert result.reason_codes == ("correlation_cluster_exposure_clear",)
    assert result.manual_next_step == "no_manual_action_required"


def test_correlation_cluster_exposure_report_clamps_negative_adjusted_edge() -> None:
    result = report(
        aggregate_edge_probability=d("0.030000"),
        correlation_risk_probability=d("0.080000"),
    )

    assert result.adjusted_edge_probability == d("0.000000")
    assert result.exposure_status == "watch"
    assert "correlation_cluster_open_candidate_watch" in result.reason_codes


def test_direct_constructors_revalidate_decimal_consistency_flags_and_digest() -> None:
    module = api()
    result = report()

    assert module.__all__ == (
        "DEFAULT_CONFIG_VERSION",
        "EXPOSURE_STATUSES",
        "ProbabilityEventCorrelationClusterExposureInput",
        "ProbabilityEventCorrelationClusterExposureReport",
        "build_probability_event_correlation_cluster_exposure_report",
        "probability_event_correlation_cluster_exposure_report_digest",
        "probability_event_correlation_cluster_exposure_report_payload",
        "validate_probability_event_correlation_cluster_exposure_public_payload",
    )

    rebuilt = module.ProbabilityEventCorrelationClusterExposureReport(
        **{field.name: getattr(result, field.name) for field in fields(result)},
    )
    assert rebuilt == result

    with pytest.raises(FrozenInstanceError):
        result.exposure_status = "block"
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="payload_digest"):
        replace(result, payload_digest="0" * 64)
    with pytest.raises(ValueError, match="open_candidate_count"):
        report(open_candidate_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="same_outcome_family_count"):
        report(same_outcome_family_count=d("1.5"))
    with pytest.raises(ValueError, match="aggregate_edge_probability"):
        report(aggregate_edge_probability=d("1.000001"))
    with pytest.raises(ValueError, match="correlation_risk_probability"):
        report(correlation_risk_probability=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="cluster_id"):
        report(cluster_id=" cluster_macro_rates")
    with pytest.raises(ValueError, match="unsafe public payload value"):
        report(cluster_id="live_cluster")
    with pytest.raises(ValueError, match="manual_exposure_limit_probability"):
        report(
            aggregate_edge_probability=d("0.500000"),
            correlation_risk_probability=d("0.200000"),
            manual_exposure_limit_probability=d("0.000000"),
        )


def test_public_payload_validator_rejects_execution_and_numeric_leaks() -> None:
    module = api()
    payload = report().public_payload

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.probability_event_correlation_cluster_exposure_report_digest(
        payload,
    ) == payload["payload_digest"]
    module.validate_probability_event_correlation_cluster_exposure_public_payload(
        payload,
    )

    for unsafe_key in (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "private_key",
        "signature",
        "execute_path",
        "market_id",
        "candidate_id",
        "persist_jsonl",
    ):
        forged_payload = dict(payload)
        forged_payload[unsafe_key] = "public_aggregate"
        forged_payload["payload_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.validate_probability_event_correlation_cluster_exposure_public_payload(
                forged_payload,
            )

    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_probability_event_correlation_cluster_exposure_public_payload(
            {**payload, "open_candidate_count": 3},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_probability_event_correlation_cluster_exposure_public_payload(
            {**payload, "readonly": False},
        )
    forged_status = {**payload, "exposure_status": "hold"}
    forged_status["payload_digest"] = canonical_digest(forged_status)
    with pytest.raises(ValueError, match="exposure_status"):
        module.validate_probability_event_correlation_cluster_exposure_public_payload(
            forged_status,
        )
    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_probability_event_correlation_cluster_exposure_public_payload(
            {**payload, "adjusted_edge_probability": "0.999999"},
        )


def test_module_scope_is_pure_in_memory_readonly_report_only() -> None:
    import polymarket_alpha_lab.probability_event_correlation_cluster_exposure_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)
    project_imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported = node.module or ""
            if imported.startswith("polymarket_alpha_lab."):
                project_imports.add(imported)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("polymarket_alpha_lab."):
                    project_imports.add(alias.name)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    assert project_imports == set()
    lowered = source.lower()
    for forbidden in (
        ".read(",
        ".write(",
        "open(",
        "path",
        "logging",
        "logger",
        "client",
        "request",
        "response",
        "socket",
        "supabase",
        "database",
        "db",
        "persist",
        "jsonl",
        "live",
        "auth",
        "wallet",
        "order",
        "key",
        "signature",
        "execute",
        "trade",
    ):
        assert forbidden not in lowered
    assert "float" not in lowered
    assert "paper_only: bool = true" in lowered
    assert "report_only: bool = true" in lowered
    assert "readonly: bool = true" in lowered
