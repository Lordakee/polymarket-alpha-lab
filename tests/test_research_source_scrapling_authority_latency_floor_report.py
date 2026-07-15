from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_scrapling_authority_latency_floor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    private_latency_ref: str = (
        "raw_candidate_id=secret-candidate|market_id=secret-market|"
        "market_slug=secret-slug|question=private question|"
        "source_url=https://example.invalid/path?token=secret&wallet=secret"
    ),
    observed_seconds_ago: int = 300,
    scrapling_latency_seconds: Decimal = d("300.000000"),
    authority_latency_seconds: Decimal = d("600.000000"),
    scrapling_freshness_score: Decimal = d("0.920000"),
    authority_freshness_score: Decimal = d("0.950000"),
    authority_recheck_confidence_score: Decimal = d("0.930000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraplingAuthorityLatencyFloorObservation(
        private_latency_ref=private_latency_ref,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        scrapling_latency_seconds=scrapling_latency_seconds,
        authority_latency_seconds=authority_latency_seconds,
        scrapling_freshness_score=scrapling_freshness_score,
        authority_freshness_score=authority_freshness_score,
        authority_recheck_confidence_score=authority_recheck_confidence_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_scrapling_authority_latency_floor_report(
        rows,
        config=cfg,
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def test_pass_report_redacts_private_inputs_and_exports_stable_digest_payload() -> None:
    module = api()
    report_a = build_report(
        observation(private_latency_ref="private-alpha"),
        observation(
            private_latency_ref=(
                "raw_candidate_id=secret-two|source_text=verbatim private text"
            ),
            observed_seconds_ago=600,
            scrapling_latency_seconds=d("600.000000"),
            authority_latency_seconds=d("900.000000"),
            scrapling_freshness_score=d("0.940000"),
            authority_freshness_score=d("0.960000"),
            authority_recheck_confidence_score=d("0.950000"),
        ),
    )
    report_b = build_report(
        observation(
            private_latency_ref="changed-private-two",
            observed_seconds_ago=600,
            scrapling_latency_seconds=d("600.000000"),
            authority_latency_seconds=d("900.000000"),
            scrapling_freshness_score=d("0.940000"),
            authority_freshness_score=d("0.960000"),
            authority_recheck_confidence_score=d("0.950000"),
        ),
        observation(private_latency_ref="changed-private-one"),
    )
    changed_report = build_report(
        observation(scrapling_latency_seconds=d("1800.000000")),
    )

    assert type(report_a) is module.ResearchSourceScraplingAuthorityLatencyFloorReport
    assert is_dataclass(report_a)
    assert report_a.__dataclass_params__.frozen
    assert report_a.status == "pass"
    assert report_a.observation_count == d("2.000000")
    assert report_a.pass_count == d("2.000000")
    assert report_a.watch_count == d("0.000000")
    assert report_a.block_count == d("0.000000")
    assert report_a.average_scrapling_latency_seconds == d("450.000000")
    assert report_a.average_authority_latency_seconds == d("750.000000")
    assert report_a.highest_latency_gap_seconds == d("300.000000")
    assert report_a.average_authority_latency_floor_score == d("0.943083")
    assert report_a.reason_codes == (
        "scrapling_authority_latency_floor_pass",
    )
    assert tuple(
        (item.reason_code, item.count) for item in report_a.reason_code_counts
    ) == (("scrapling_authority_latency_floor_pass", d("2.000000")),)
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.derived_validation_digest != changed_report.derived_validation_digest

    payload = report_a.payload
    assert payload == module.research_source_scrapling_authority_latency_floor_report_payload(
        report_a,
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == module.research_source_scrapling_authority_latency_floor_report_digest(
        report_a,
    )
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["row_index"] == "1.000000"
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    json.dumps(payload, sort_keys=True)
    assert module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        payload,
    )
    assert_no_decimal_or_float_values(payload)
    assert_payload_has_no_forbidden_values(payload)


def test_watch_and_block_statuses_use_only_pass_watch_block_reason_order() -> None:
    watch_report = build_report(
        observation(
            scrapling_latency_seconds=d("1500.000000"),
            authority_latency_seconds=d("2000.000000"),
            scrapling_freshness_score=d("0.700000"),
            authority_freshness_score=d("0.700000"),
            authority_recheck_confidence_score=d("0.700000"),
        ),
    )
    block_report = build_report(
        observation(
            scrapling_latency_seconds=d("4000.000000"),
            authority_latency_seconds=d("8000.000000"),
            scrapling_freshness_score=d("0.200000"),
            authority_freshness_score=d("0.200000"),
            authority_recheck_confidence_score=d("0.200000"),
        ),
    )

    assert module_statuses() == ("pass", "watch", "block")
    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "authority_latency_floor_score_below_pass_threshold",
        "scrapling_latency_above_pass_threshold",
        "authority_latency_above_pass_threshold",
    )
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].reason_codes == (
        "authority_latency_floor_score_below_watch_threshold",
        "scrapling_latency_above_watch_threshold",
        "authority_latency_above_watch_threshold",
        "latency_gap_above_watch_threshold",
    )
    assert {watch_report.status, block_report.status, "pass"} == {
        "pass",
        "watch",
        "block",
    }


def test_empty_report_blocks_with_decimal_zeroes_and_frozen_report_only_flags() -> None:
    module = api()
    report = build_report()

    assert module_statuses() == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.observation_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.average_scrapling_latency_seconds == d("0.000000")
    assert report.average_authority_latency_seconds == d("0.000000")
    assert report.average_authority_latency_floor_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "scrapling_authority_latency_floor_no_inputs",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.derived_validation_digest == module.research_source_scrapling_authority_latency_floor_report_digest(
        report,
    )
    assert_decimal_public_numbers(report)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceScraplingAuthorityLatencyFloorReport):
            pass


def test_validation_rejects_non_decimal_future_dates_flags_digest_and_unsafe_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        observation(scrapling_latency_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(authority_latency_seconds=_DecimalSubclass("600.000000"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(observation(observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_scrapling_authority_latency_floor_report(
            (),
            generated_at=datetime(2026, 7, 9, 15, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    broken_payload = dict(report.payload)
    broken_payload["average_authority_latency_floor_score"] = "0.100000"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        broken_payload,
    )
    unsafe_payload = dict(report.payload)
    unsafe_payload["source_url"] = "https://example.invalid/private"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        unsafe_payload,
    )


def test_validator_rejects_resigned_row_status_and_reason_forgery() -> None:
    module = api()
    forged = json.loads(json.dumps(build_report(observation()).payload))
    forged_reason = "authority_latency_floor_score_below_pass_threshold"
    forged["rows"][0]["status"] = "watch"
    forged["rows"][0]["reason_codes"] = [forged_reason]
    forged["status"] = "watch"
    forged["pass_count"] = "0.000000"
    forged["watch_count"] = "1.000000"
    forged["reason_codes"] = [forged_reason]
    forged["reason_code_counts"] = [
        {
            "reason_code": forged_reason,
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged),
    )


def test_validator_rejects_resigned_derived_count_and_score_forgeries() -> None:
    module = api()
    payload = build_report(observation()).payload

    forged_count = json.loads(json.dumps(payload))
    forged_count["pass_count"] = "2.000000"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged_count),
    )

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["count"] = "2.000000"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged_reason_count),
    )

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["authority_latency_floor_score"] = "0.100000"
    forged_score["average_authority_latency_floor_score"] = "0.100000"
    forged_score["rows"][0]["status"] = "block"
    forged_score["rows"][0]["reason_codes"] = [
        "authority_latency_floor_score_below_watch_threshold",
    ]
    forged_score["status"] = "block"
    forged_score["pass_count"] = "0.000000"
    forged_score["block_count"] = "1.000000"
    forged_score["reason_codes"] = [
        "authority_latency_floor_score_below_watch_threshold",
    ]
    forged_score["reason_code_counts"] = [
        {
            "reason_code": "authority_latency_floor_score_below_watch_threshold",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged_score),
    )


@pytest.mark.parametrize(
    "schema_change",
    (
        "extra_report_key",
        "missing_report_key",
        "extra_row_key",
        "missing_row_key",
        "extra_reason_count_key",
        "missing_reason_count_key",
    ),
)
def test_validator_rejects_resigned_payloads_without_exact_schemas(
    schema_change: str,
) -> None:
    module = api()
    forged = json.loads(json.dumps(build_report(observation()).payload))
    if schema_change == "extra_report_key":
        forged["unexpected"] = "safe"
    elif schema_change == "missing_report_key":
        forged.pop("row_count")
    elif schema_change == "extra_row_key":
        forged["rows"][0]["unexpected"] = "safe"
    elif schema_change == "missing_row_key":
        forged["rows"][0].pop("latency_gap_seconds")
    elif schema_change == "extra_reason_count_key":
        forged["reason_code_counts"][0]["unexpected"] = "safe"
    else:
        forged["reason_code_counts"][0].pop("count")

    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged),
    )


def test_decimal_bounds_are_checked_before_quantization() -> None:
    module = api()

    with pytest.raises(ValueError, match="between 0 and 1"):
        observation(scrapling_freshness_score=d("1.0000004"))
    with pytest.raises(ValueError, match="nonnegative"):
        observation(authority_latency_seconds=d("-0.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        module.ResearchSourceScraplingAuthorityLatencyFloorConfig(
            authority_latency_floor_pass_score=d("1.0000004"),
        )

    report = build_report(observation())
    with pytest.raises(ValueError, match="whole"):
        replace(
            report,
            row_count=d("0.9999996"),
            derived_validation_digest="",
        )


def test_signed_zero_is_rejected_in_models_and_resigned_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="signed zero"):
        observation(scrapling_freshness_score=d("-0"))
    with pytest.raises(ValueError, match="signed zero"):
        observation(scrapling_latency_seconds=d("-0.000000"))

    empty_report = build_report()
    with pytest.raises(ValueError, match="signed zero"):
        replace(
            empty_report,
            pass_count=d("-0.000000"),
            derived_validation_digest="",
        )

    forged = json.loads(json.dumps(build_report(observation()).payload))
    forged["rows"][0]["latency_gap_seconds"] = "-0.000000"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged),
    )


def test_all_public_dataclasses_are_frozen_phase_one_surfaces() -> None:
    module = api()
    report = build_report(observation())
    values = (
        module.ResearchSourceScraplingAuthorityLatencyFloorConfig(),
        observation(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False


def test_boundary_revalidates_object_setattr_bypasses() -> None:
    module = api()

    cfg = module.ResearchSourceScraplingAuthorityLatencyFloorConfig()
    object.__setattr__(cfg, "scrapling_latency_pass_threshold_seconds", "1200")
    with pytest.raises(ValueError, match="exactly Decimal"):
        build_report(observation(), cfg=cfg)

    supplied = observation()
    object.__setattr__(supplied, "authority_latency_seconds", "600")
    with pytest.raises(ValueError, match="exactly Decimal"):
        build_report(supplied)

    row = build_report(observation()).rows[0]
    object.__setattr__(row, "authority_latency_floor_score", "0.943083")
    with pytest.raises(ValueError, match="exactly Decimal"):
        module.ResearchSourceScraplingAuthorityLatencyFloorReport(
            generated_at=GENERATED_AT,
            config_version=(
                module.DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
            ),
            observation_count=d("1.000000"),
            row_count=d("1.000000"),
            pass_count=d("1.000000"),
            watch_count=d("0.000000"),
            block_count=d("0.000000"),
            average_scrapling_latency_seconds=d("300.000000"),
            average_authority_latency_seconds=d("600.000000"),
            highest_latency_gap_seconds=d("300.000000"),
            average_authority_latency_floor_score=d("0.943083"),
            status="pass",
            reason_codes=("scrapling_authority_latency_floor_pass",),
            reason_code_counts=(
                module.ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount(
                    reason_code="scrapling_authority_latency_floor_pass",
                    count=d("1.000000"),
                ),
            ),
            rows=(row,),
        )

    count = build_report(observation()).reason_code_counts[0]
    object.__setattr__(count, "count", "1")
    with pytest.raises(ValueError, match="exactly Decimal"):
        module.ResearchSourceScraplingAuthorityLatencyFloorReport(
            generated_at=GENERATED_AT,
            config_version=(
                module.DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
            ),
            observation_count=d("1.000000"),
            row_count=d("1.000000"),
            pass_count=d("1.000000"),
            watch_count=d("0.000000"),
            block_count=d("0.000000"),
            average_scrapling_latency_seconds=d("300.000000"),
            average_authority_latency_seconds=d("600.000000"),
            highest_latency_gap_seconds=d("300.000000"),
            average_authority_latency_floor_score=d("0.943083"),
            status="pass",
            reason_codes=("scrapling_authority_latency_floor_pass",),
            reason_code_counts=(count,),
            rows=(build_report(observation()).rows[0],),
        )


def test_validator_rejects_resigned_noncanonical_mapping_order_and_row_indices() -> None:
    module = api()
    payload = build_report(
        observation(),
        observation(
            observed_seconds_ago=600,
            scrapling_latency_seconds=d("1500.000000"),
        ),
    ).payload

    reordered = {
        key: value
        for key, value in reversed(tuple(payload.items()))
    }
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(reordered),
    )

    forged_indices = json.loads(json.dumps(payload))
    forged_indices["rows"][0]["row_index"] = "7.000000"
    forged_indices["rows"][1]["row_index"] = "8.000000"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged_indices),
    )


def test_validator_rederives_row_age_and_observation_order_from_public_rows() -> None:
    module = api()
    payload = build_report(
        observation(observed_seconds_ago=300),
        observation(
            observed_seconds_ago=600,
            scrapling_latency_seconds=d("300.000000"),
            authority_latency_seconds=d("900.000000"),
        ),
    ).payload

    assert payload["rows"][0]["observed_at"] == "2026-07-09T14:50:00+00:00"

    forged_age = json.loads(json.dumps(payload))
    forged_age["rows"][0]["observed_age_seconds"] = "0.000000"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged_age),
    )

    forged_order = json.loads(json.dumps(payload))
    forged_order["rows"].reverse()
    forged_order["rows"][0]["row_index"] = "1.000000"
    forged_order["rows"][1]["row_index"] = "2.000000"
    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged_order),
    )


def test_decimal_arithmetic_uses_fixed_local_context() -> None:
    baseline = build_report(observation()).payload

    with localcontext() as context:
        context.prec = 1
        constrained = build_report(observation()).payload

    assert constrained == baseline


def test_finite_unquantizable_decimals_use_the_validation_error_contract() -> None:
    with pytest.raises(ValueError, match="quantizable"):
        observation(scrapling_latency_seconds=d("1E+100"))


def test_custom_config_is_signed_and_reconstructed_for_status_rederivation() -> None:
    module = api()
    cfg = module.ResearchSourceScraplingAuthorityLatencyFloorConfig(
        scrapling_latency_pass_threshold_seconds=d("200.000000"),
    )
    report = build_report(observation(), cfg=cfg)

    assert report.rows[0].status == "watch"
    assert report.payload["config"]["scrapling_latency_pass_threshold_seconds"] == (
        "200.000000"
    )
    assert module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        report.payload,
    )


@pytest.mark.parametrize("target", ("config", "row", "reason_code_count"))
def test_validator_rejects_resigned_nested_noncanonical_mapping_order(
    target: str,
) -> None:
    module = api()
    forged = json.loads(json.dumps(build_report(observation()).payload))
    if target == "config":
        forged["config"] = {
            key: value for key, value in reversed(tuple(forged["config"].items()))
        }
    elif target == "row":
        forged["rows"][0] = {
            key: value for key, value in reversed(tuple(forged["rows"][0].items()))
        }
    else:
        forged["reason_code_counts"][0] = {
            key: value
            for key, value in reversed(
                tuple(forged["reason_code_counts"][0].items()),
            )
        }

    assert not module.validate_research_source_scrapling_authority_latency_floor_report_payload(
        resign_payload(forged),
    )


def test_observation_sort_tie_breaks_are_complete_and_deterministic() -> None:
    observations = (
        observation(
            observed_seconds_ago=300,
            scrapling_latency_seconds=d("1500.000000"),
            authority_latency_seconds=d("600.000000"),
        ),
        observation(
            observed_seconds_ago=300,
            scrapling_latency_seconds=d("1500.000000"),
            authority_latency_seconds=d("900.000000"),
        ),
        observation(
            observed_seconds_ago=600,
            scrapling_latency_seconds=d("300.000000"),
            authority_latency_seconds=d("600.000000"),
        ),
    )

    assert build_report(*observations).payload == build_report(*reversed(observations)).payload


def test_public_dataclasses_are_explicitly_final() -> None:
    module = api()

    for cls in (
        module.ResearchSourceScraplingAuthorityLatencyFloorConfig,
        module.ResearchSourceScraplingAuthorityLatencyFloorObservation,
        module.ResearchSourceScraplingAuthorityLatencyFloorRow,
        module.ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount,
        module.ResearchSourceScraplingAuthorityLatencyFloorReport,
    ):
        assert getattr(cls, "__final__", False) is True


def test_module_scope_has_no_network_database_wallet_order_or_trade_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_calls = {
        "agent_reach",
        "authenticate",
        "authorize",
        "commit",
        "connect",
        "execute",
        "executemany",
        "fetch",
        "login",
        "mkdir",
        "open",
        "persist",
        "read_bytes",
        "read_text",
        "request",
        "post",
        "put",
        "patch",
        "save",
        "scrape",
        "scrapling",
        "send",
        "trade",
        "order",
        "recommend",
        "size",
        "unlink",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    forbidden_import_fragments = (
        "db",
        "agent_reach",
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "scrapling",
        "socket",
        "sql",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    forbidden_public_names = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_trade",
        "position_sizing",
        "recommendation",
    }
    public_field_names = {
        field.name
        for cls in (
            module.ResearchSourceScraplingAuthorityLatencyFloorConfig,
            module.ResearchSourceScraplingAuthorityLatencyFloorRow,
            module.ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount,
            module.ResearchSourceScraplingAuthorityLatencyFloorReport,
        )
        for field in fields(cls)
    }
    assert forbidden_public_names.isdisjoint(public_field_names)


def module_statuses() -> tuple[str, str, str]:
    module = api()
    return module.RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_STATUSES


def assert_no_decimal_or_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_or_float_values(item)
    else:
        assert type(value) is not Decimal
        assert type(value) is not float


def assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if type(value) is tuple:
        for item in value:
            assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_decimal_public_numbers(getattr(value, field.name))


def assert_payload_has_no_forbidden_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "verbatim private",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "private-alpha",
        "changed-private",
        "secret",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_forbidden_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_forbidden_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
