from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from decimal import Decimal

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.portfolio_probability_event_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def test_public_dataclasses_cannot_be_subclassed() -> None:
    module = api()
    for base in (
        module.PortfolioProbabilityEventReadinessConfig,
        module.PortfolioProbabilityEventReadinessInput,
        module.PortfolioProbabilityEventReadinessRow,
        module.PortfolioProbabilityEventReadinessReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Unsafe{base.__name__}", (base,), {"__post_init__": lambda self: None})


def candidate(
    candidate_id: str,
    outcome_family: str,
    event_category: str,
    correlation_cluster: str,
    yes_exposure: str,
    no_exposure: str,
    capital_lockup_usdc: str,
    time_to_resolution_days: str,
    expected_edge: str,
    exit_liquidity_usdc: str,
):
    module = api()
    return module.PortfolioProbabilityEventReadinessInput(
        candidate_id=candidate_id,
        outcome_family=outcome_family,
        event_category=event_category,
        correlation_cluster=correlation_cluster,
        yes_probability_exposure=d(yes_exposure),
        no_probability_exposure=d(no_exposure),
        capital_lockup_usdc=d(capital_lockup_usdc),
        time_to_resolution_days=d(time_to_resolution_days),
        expected_edge=d(expected_edge),
        exit_liquidity_usdc=d(exit_liquidity_usdc),
    )


def report(*rows):
    module = api()
    return module.build_portfolio_probability_event_readiness_report(
        rows,
        config=module.PortfolioProbabilityEventReadinessConfig(),
    )


def independent_candidates():
    return tuple(
        candidate(
            f"candidate-{index}",
            f"outcome-{index}",
            f"category-{index}",
            f"cluster-{index}",
            "10.000000",
            "0.000000",
            "10.000000",
            "1.000000",
            "0.100000",
            "200.000000",
        )
        for index in range(3)
    )


def payload_digest(payload: dict[str, object]) -> str:
    digest_source = dict(payload)
    digest_source["payload_digest"] = ""
    return hashlib.sha256(
        json.dumps(
            digest_source,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
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
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_decimal_only_dataclass(item)


def test_portfolio_readiness_blocks_same_outcome_and_cluster_concentration() -> None:
    result = report(
        candidate(
            "alpha",
            "fed-july-cut",
            "macro",
            "fed-rates",
            "120.000000",
            "0.000000",
            "80.000000",
            "45.000000",
            "0.080000",
            "150.000000",
        ),
        candidate(
            "beta",
            "fed-july-cut",
            "macro",
            "fed-rates",
            "75.000000",
            "0.000000",
            "60.000000",
            "20.000000",
            "0.050000",
            "200.000000",
        ),
        candidate(
            "gamma",
            "btc-year-end",
            "crypto",
            "btc-spot",
            "0.000000",
            "40.000000",
            "25.000000",
            "7.000000",
            "0.070000",
            "75.000000",
        ),
    )

    assert result.config_version == "portfolio-probability-event-readiness-report-v0"
    assert result.candidate_count == d("3")
    assert result.total_probability_exposure == d("235.000000")
    assert result.total_capital_lockup_usdc == d("165.000000")
    assert result.max_outcome_family_concentration == d("0.829787")
    assert result.max_correlation_cluster_concentration == d("0.829787")
    assert result.max_event_category_concentration == d("0.829787")
    assert result.max_capital_lockup_concentration == d("0.848485")
    assert result.blocker_count == d("2")
    assert result.watch_count == d("1")
    assert result.pass_count == d("0")
    assert result.readiness_status == "blocked"
    assert result.reason_codes == (
        "same_outcome_dependency_block",
        "correlation_cluster_concentration_block",
        "event_category_concentration_block",
        "capital_lockup_concentration_block",
        "extended_lockup_block",
        "low_exit_liquidity_watch",
    )
    assert result.manual_next_step == "do_not_allocate_until_portfolio_blockers_clear"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_decimal_only_dataclass(result)

    alpha, beta, gamma = result.rows
    assert tuple(row.candidate_id for row in result.rows) == ("alpha", "beta", "gamma")
    assert alpha.readiness_status == "blocked"
    assert alpha.reason_codes == (
        "same_outcome_dependency_block",
        "correlation_cluster_concentration_block",
        "event_category_concentration_block",
        "capital_lockup_concentration_block",
        "extended_lockup_block",
    )
    assert alpha.outcome_family_concentration == d("0.829787")
    assert alpha.capital_lockup_concentration == d("0.848485")
    assert beta.readiness_status == "blocked"
    assert beta.reason_codes == (
        "same_outcome_dependency_block",
        "correlation_cluster_concentration_block",
        "event_category_concentration_block",
        "capital_lockup_concentration_block",
    )
    assert gamma.readiness_status == "watch"
    assert gamma.reason_codes == ("low_exit_liquidity_watch",)


def test_empty_portfolio_readiness_report_is_pass_and_readonly() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.total_probability_exposure == d("0.000000")
    assert result.total_capital_lockup_usdc == d("0.000000")
    assert result.max_outcome_family_concentration == d("0.000000")
    assert result.max_correlation_cluster_concentration == d("0.000000")
    assert result.max_event_category_concentration == d("0.000000")
    assert result.max_capital_lockup_concentration == d("0.000000")
    assert result.blocker_count == d("0")
    assert result.watch_count == d("0")
    assert result.pass_count == d("0")
    assert result.readiness_status == "pass"
    assert result.reason_codes == ("portfolio_probability_event_readiness_pass",)
    assert result.manual_next_step == "proceed_with_paper_portfolio_review"
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_decimal_only_dataclass(result)


@pytest.mark.parametrize(
    ("time_to_resolution_days", "expected_edge", "expected_reason"),
    (
        ("15.000000", "0.100000", "extended_lockup_watch"),
        ("1.000000", "-0.010000", "negative_edge_after_lockup_watch"),
    ),
)
def test_pure_watch_reasons_are_preserved_in_report_summary(
    time_to_resolution_days: str,
    expected_edge: str,
    expected_reason: str,
) -> None:
    result = report(
        *(
            candidate(
                f"candidate-{index}",
                f"outcome-{index}",
                f"category-{index}",
                f"cluster-{index}",
                "10.000000",
                "0.000000",
                "10.000000",
                time_to_resolution_days,
                expected_edge,
                "200.000000",
            )
            for index in range(3)
        ),
    )

    assert result.readiness_status == "watch"
    assert result.watch_count == d("3")
    assert result.reason_codes == (expected_reason,)
    assert all(row.reason_codes == (expected_reason,) for row in result.rows)


def test_direct_constructors_enforce_decimal_only_consistency_flags_and_freezing() -> None:
    module = api()
    result = report(
        candidate(
            "alpha",
            "fed-july-cut",
            "macro",
            "fed-rates",
            "25.000000",
            "0.000000",
            "10.000000",
            "7.000000",
            "0.100000",
            "100.000000",
        ),
    )

    rebuilt = module.PortfolioProbabilityEventReadinessReport(
        **{field.name: getattr(result, field.name) for field in fields(result)},
    )
    assert rebuilt == result

    with pytest.raises(FrozenInstanceError):
        result.readiness_status = "blocked"
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="yes_probability_exposure"):
        candidate(
            "bad",
            "fed-july-cut",
            "macro",
            "fed-rates",
            "1.000000",
            "0.000000",
            "1.000000",
            "1.000000",
            "0.100000",
            "100.000000",
        ).__class__(
            candidate_id="bad",
            outcome_family="fed-july-cut",
            event_category="macro",
            correlation_cluster="fed-rates",
            yes_probability_exposure=1,
            no_probability_exposure=d("0.000000"),
            capital_lockup_usdc=d("1.000000"),
            time_to_resolution_days=d("1.000000"),
            expected_edge=d("0.100000"),
            exit_liquidity_usdc=d("100.000000"),
        )
    with pytest.raises(ValueError, match="rows"):
        module.build_portfolio_probability_event_readiness_report(
            (object(),),
            config=module.PortfolioProbabilityEventReadinessConfig(),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_portfolio_probability_event_readiness_report((), config=object())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("portfolio_probability_event_readiness_pass", "low_exit_liquidity_watch"))


def test_portfolio_readiness_module_is_leaf_report_only_and_has_no_live_io_surface() -> None:
    import polymarket_alpha_lab.portfolio_probability_event_readiness_report as module

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
        "requests",
        "urllib",
        "http",
        "network",
        "auth",
        "wallet",
        "private_key",
        "database",
        "postgres",
        "supabase",
        "order",
        "trade",
        "execute",
        "live",
        "persist",
    ):
        assert forbidden not in lowered
    assert "float" not in lowered
    assert "paper_only: bool = true" in lowered
    assert "report_only: bool = true" in lowered
    assert "readonly: bool = true" in lowered


def test_direct_row_and_report_recompute_concentrations_reasons_status_and_step() -> None:
    module = api()
    result = report(*independent_candidates())
    row = result.rows[0]

    with pytest.raises(ValueError, match="outcome_family_concentration"):
        replace(row, outcome_family_concentration=d("1.000001"))
    with pytest.raises(ValueError, match="edge_after_lockup"):
        replace(row, edge_after_lockup=d("0.900000"))

    forged_concentration = replace(
        row,
        outcome_family_concentration=d("0.900000"),
    )
    forged_values = {field.name: getattr(result, field.name) for field in fields(result)}
    forged_values["rows"] = (forged_concentration,) + result.rows[1:]
    forged_values["max_outcome_family_concentration"] = d("0.900000")
    with pytest.raises(ValueError, match="outcome_family_concentration"):
        module.PortfolioProbabilityEventReadinessReport(**forged_values)

    blocked = report(
        candidate(
            "blocked",
            "same-outcome",
            "same-category",
            "same-cluster",
            "10.000000",
            "0.000000",
            "10.000000",
            "1.000000",
            "0.100000",
            "200.000000",
        ),
    )
    object.__setattr__(
        blocked.rows[0],
        "reason_codes",
        ("portfolio_probability_event_readiness_pass",),
    )
    object.__setattr__(blocked.rows[0], "readiness_status", "pass")
    forged_values = {field.name: getattr(blocked, field.name) for field in fields(blocked)}
    forged_values.update(
        blocker_count=d("0"),
        pass_count=d("1"),
        readiness_status="pass",
        reason_codes=("portfolio_probability_event_readiness_pass",),
        manual_next_step="proceed_with_paper_portfolio_review",
    )
    with pytest.raises(ValueError, match="reason_codes|readiness_status"):
        module.PortfolioProbabilityEventReadinessReport(**forged_values)


def test_builder_revalidates_mutated_config_and_input_exact_fields() -> None:
    module = api()
    config = module.PortfolioProbabilityEventReadinessConfig()
    object.__setattr__(config, "same_outcome_block_concentration", d("0.200000"))
    with pytest.raises(ValueError, match="same_outcome.*threshold"):
        module.build_portfolio_probability_event_readiness_report(
            independent_candidates(),
            config=config,
        )

    input_row = independent_candidates()[0]
    object.__setattr__(input_row, "yes_probability_exposure", d("10"))
    with pytest.raises(ValueError, match="yes_probability_exposure.*six decimal"):
        module.build_portfolio_probability_event_readiness_report(
            (input_row,),
            config=module.PortfolioProbabilityEventReadinessConfig(),
        )


def test_builder_rejects_duplicate_candidate_ids_before_portfolio_aggregation() -> None:
    module = api()
    first, second, _ = independent_candidates()
    duplicate = replace(second, candidate_id=first.candidate_id)

    with pytest.raises(ValueError, match="candidate_id.*unique"):
        module.build_portfolio_probability_event_readiness_report(
            (first, duplicate),
            config=module.PortfolioProbabilityEventReadinessConfig(),
        )


def test_direct_report_rejects_duplicate_candidate_ids_with_matching_digest() -> None:
    module = api()
    result = report(*independent_candidates())
    duplicate_row = replace(
        result.rows[1],
        candidate_id=result.rows[0].candidate_id,
    )
    forged_payload = json.loads(json.dumps(result.public_payload))
    forged_payload["rows"][1]["candidate_id"] = result.rows[0].candidate_id
    forged_payload["payload_digest"] = payload_digest(forged_payload)
    forged_values = {field.name: getattr(result, field.name) for field in fields(result)}
    forged_values["rows"] = (result.rows[0], duplicate_row, result.rows[2])
    forged_values["payload_digest"] = forged_payload["payload_digest"]

    with pytest.raises(ValueError, match="candidate_id.*unique"):
        module.PortfolioProbabilityEventReadinessReport(**forged_values)


def test_public_mapping_rejects_duplicate_candidate_ids_with_matching_digest() -> None:
    module = api()
    result = report(*independent_candidates())
    forged_payload = json.loads(json.dumps(result.public_payload))
    forged_payload["rows"][1]["candidate_id"] = result.rows[0].candidate_id
    forged_payload["payload_digest"] = payload_digest(forged_payload)

    with pytest.raises(ValueError, match="candidate_id.*unique"):
        module.portfolio_probability_event_readiness_report_payload(forged_payload)
    with pytest.raises(ValueError, match="candidate_id.*unique"):
        module.portfolio_probability_event_readiness_report_payload_digest(
            forged_payload,
        )


def test_signed_zero_is_canonicalized_on_input_and_rejected_in_stored_graphs() -> None:
    module = api()
    input_row = candidate(
        "zero",
        "zero-outcome",
        "zero-category",
        "zero-cluster",
        "-0.000000",
        "-0.000000",
        "-0.000000",
        "-0.000000",
        "-0.000000",
        "-0.000000",
    )
    for field_name in (
        "yes_probability_exposure",
        "no_probability_exposure",
        "capital_lockup_usdc",
        "time_to_resolution_days",
        "expected_edge",
        "exit_liquidity_usdc",
    ):
        assert getattr(input_row, field_name).as_tuple().sign == 0

    object.__setattr__(input_row, "expected_edge", d("-0.000000"))
    with pytest.raises(ValueError, match="expected_edge.*signed zero"):
        module.build_portfolio_probability_event_readiness_report(
            (input_row,),
            config=module.PortfolioProbabilityEventReadinessConfig(),
        )

    empty = report()
    with pytest.raises(ValueError, match="candidate_count.*signed zero"):
        replace(empty, candidate_count=d("-0"))


def test_effective_config_snapshot_and_direct_report_graph_are_independent_and_strict() -> None:
    module = api()
    config = module.PortfolioProbabilityEventReadinessConfig(
        same_outcome_watch_concentration=d("0.300000"),
        same_outcome_block_concentration=d("0.700000"),
    )
    result = module.build_portfolio_probability_event_readiness_report(
        independent_candidates(),
        config=config,
    )

    assert result.effective_config == config
    assert result.effective_config is not config
    object.__setattr__(config, "same_outcome_watch_concentration", d("0.900000"))
    assert result.effective_config.same_outcome_watch_concentration == d("0.300000")

    object.__setattr__(result.rows[0], "readonly", False)
    values = {field.name: getattr(result, field.name) for field in fields(result)}
    with pytest.raises(ValueError, match="row readonly"):
        module.PortfolioProbabilityEventReadinessReport(**values)

    object.__setattr__(result.rows[0], "readonly", True)
    object.__setattr__(result, "rows", tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="rows.*sorted"):
        module.portfolio_probability_event_readiness_report_payload(result)


def test_public_payload_digest_mapping_roundtrip_and_deep_readonly_contract() -> None:
    module = api()
    result = report(*independent_candidates())
    payload = module.portfolio_probability_event_readiness_report_payload(result)

    assert payload == result.public_payload
    assert payload["payload_digest"] == result.payload_digest
    assert payload["payload_digest"] == payload_digest(dict(payload))
    assert module.portfolio_probability_event_readiness_report_payload_digest(result) == (
        result.payload_digest
    )
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert "Decimal" not in rendered
    for field_name in (
        "candidate_count",
        "total_probability_exposure",
        "max_outcome_family_concentration",
    ):
        assert payload[field_name].count(".") == 1
        assert len(payload[field_name].split(".")[1]) == 6

    plain = json.loads(rendered)
    roundtrip = module.portfolio_probability_event_readiness_report_payload(plain)
    assert roundtrip == payload
    assert module.portfolio_probability_event_readiness_report_payload_digest(plain) == (
        result.payload_digest
    )

    with pytest.raises(TypeError, match="payload is immutable"):
        payload.__ior__({"extra": "value"})
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["effective_config"].__ior__({"extra": "value"})
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"][0].__ior__({"extra": "value"})
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})

    for field_name, forged_value, message in (
        ("readiness_status", "blocked", "readiness_status"),
        (
            "reason_codes",
            ["same_outcome_dependency_block"],
            "reason_codes",
        ),
        (
            "manual_next_step",
            "do_not_allocate_until_portfolio_blockers_clear",
            "manual_next_step",
        ),
    ):
        forged = json.loads(rendered)
        forged[field_name] = forged_value
        forged["payload_digest"] = payload_digest(forged)
        with pytest.raises(ValueError, match=message):
            module.portfolio_probability_event_readiness_report_payload(forged)

    forged = json.loads(rendered)
    forged["total_capital_lockup_usdc"] = "-0.000000"
    forged["payload_digest"] = payload_digest(forged)
    with pytest.raises(ValueError, match="signed zero"):
        module.portfolio_probability_event_readiness_report_payload(forged)

    object.__setattr__(result, "manual_next_step", "do_not_allocate_until_portfolio_blockers_clear")
    with pytest.raises(ValueError, match="manual_next_step|payload_digest"):
        module.portfolio_probability_event_readiness_report_payload(result)


def test_public_payload_is_the_validated_asdict_integration_boundary() -> None:
    module = api()
    result = report(*independent_candidates())
    raw = asdict(result)
    assert any(isinstance(value, Decimal) for value in raw.values())

    payload = module.portfolio_probability_event_readiness_report_payload(result)
    assert not any(isinstance(value, Decimal) for value in payload.values())
    assert payload["effective_config"]["config_version"] == result.config_version
