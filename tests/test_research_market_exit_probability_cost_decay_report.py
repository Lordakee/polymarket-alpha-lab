from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from importlib import import_module
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 20, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 19, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "research_market_exit_probability_cost_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    internal_signal_ref: str = "exit-probability-cost-decay-pass",
    *,
    observed_at: datetime | None = None,
    reference_probability: Decimal = d("0.690000"),
    current_probability: Decimal = d("0.660000"),
    exit_fee_rate: Decimal = d("0.005000"),
    exit_spread_rate: Decimal = d("0.005000"),
    exit_slippage_rate: Decimal = d("0.005000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketExitProbabilityCostDecayObservation(
        internal_signal_ref=internal_signal_ref,
        observed_at=observed_at or OBSERVED_AT,
        reference_probability=reference_probability,
        current_probability=current_probability,
        exit_fee_rate=exit_fee_rate,
        exit_spread_rate=exit_spread_rate,
        exit_slippage_rate=exit_slippage_rate,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_EXIT_PROBABILITY_COST_DECAY_REPORT_CONFIG_VERSION
        ),
        "max_pass_exit_cost_rate": d("0.030000"),
        "max_watch_exit_cost_rate": d("0.070000"),
        "max_pass_probability_decay_rate": d("0.040000"),
        "max_watch_probability_decay_rate": d("0.120000"),
        "min_pass_net_probability_after_cost_decay_rate": d("0.050000"),
        "min_watch_net_probability_after_cost_decay_rate": d("0.000000"),
        "max_pass_cost_decay_to_probability_ratio": d("0.250000"),
        "max_watch_cost_decay_to_probability_ratio": d("0.600000"),
        "pass_exit_probability_cost_decay_score": d("0.750000"),
        "watch_exit_probability_cost_decay_score": d("0.450000"),
        "exit_cost_weight": d("0.350000"),
        "probability_decay_weight": d("0.300000"),
        "net_buffer_weight": d("0.200000"),
        "cost_decay_ratio_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchMarketExitProbabilityCostDecayConfig(**values)


def build_report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_exit_probability_cost_decay_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def payload_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_input_blocks_exit_probability_cost_decay_review() -> None:
    module = api()
    report = build_report()

    assert module.MARKET_EXIT_PROBABILITY_COST_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "MARKET_EXIT_PROBABILITY_COST_DECAY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_EXIT_PROBABILITY_COST_DECAY_REPORT_CONFIG_VERSION",
        "ResearchMarketExitProbabilityCostDecayConfig",
        "ResearchMarketExitProbabilityCostDecayObservation",
        "ResearchMarketExitProbabilityCostDecayReasonCodeCount",
        "ResearchMarketExitProbabilityCostDecayReport",
        "ResearchMarketExitProbabilityCostDecayRow",
        "build_research_market_exit_probability_cost_decay_report",
        "research_market_exit_probability_cost_decay_report_digest",
        "research_market_exit_probability_cost_decay_report_payload",
    )
    assert type(report) is module.ResearchMarketExitProbabilityCostDecayReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-market-exit-probability-cost-decay-report-v0"
    assert report.observation_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_total_exit_cost_rate is None
    assert report.average_probability_decay_rate is None
    assert report.average_net_probability_after_cost_decay_rate is None
    assert report.average_exit_probability_cost_decay_score is None
    assert report.max_total_exit_cost_rate == ZERO
    assert report.max_probability_decay_rate == ZERO
    assert report.min_net_probability_after_cost_decay_rate == ZERO
    assert report.max_cost_decay_to_probability_ratio == ZERO
    assert report.status == "block"
    assert report.reason_codes == ("no_exit_probability_cost_decay_observations",)
    assert report.reason_code_counts == (
        module.ResearchMarketExitProbabilityCostDecayReasonCodeCount(
            reason_code="no_exit_probability_cost_decay_observations",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_scores_sorts_and_summarizes_pass_watch_block_rows() -> None:
    report = build_report(
        observation(
            "watch-ref",
            reference_probability=d("0.650000"),
            current_probability=d("0.590000"),
            exit_fee_rate=d("0.010000"),
            exit_spread_rate=d("0.015000"),
            exit_slippage_rate=d("0.010000"),
        ),
        observation(
            "block-ref",
            reference_probability=d("0.480000"),
            current_probability=d("0.300000"),
            exit_fee_rate=d("0.030000"),
            exit_spread_rate=d("0.030000"),
            exit_slippage_rate=d("0.030000"),
            reason_codes=("manual_probability_review",),
        ),
        observation("pass-ref"),
    )

    assert report.observation_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_total_exit_cost_rate == d("0.046667")
    assert report.average_probability_decay_rate == d("0.090000")
    assert report.average_net_probability_after_cost_decay_rate == d("0.380000")
    assert report.average_exit_probability_cost_decay_score == d("0.529233")
    assert report.max_total_exit_cost_rate == d("0.090000")
    assert report.max_probability_decay_rate == d("0.180000")
    assert report.min_net_probability_after_cost_decay_rate == d("0.030000")
    assert report.max_cost_decay_to_probability_ratio == d("0.900000")
    assert report.status == "block"

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.public_row_ref for row in report.rows) == (
        "exit_probability_cost_decay_row_001",
        "exit_probability_cost_decay_row_002",
        "exit_probability_cost_decay_row_003",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    assert block_row.probability_decay_rate == d("0.180000")
    assert block_row.total_exit_cost_rate == d("0.090000")
    assert block_row.net_probability_after_cost_decay_rate == d("0.030000")
    assert block_row.cost_decay_to_probability_ratio == d("0.900000")
    assert block_row.exit_cost_score == ZERO
    assert block_row.probability_decay_score == ZERO
    assert block_row.net_buffer_score == d("0.600000")
    assert block_row.cost_decay_ratio_score == ZERO
    assert block_row.exit_probability_cost_decay_score == d("0.120000")
    assert block_row.reason_codes == (
        "cost_decay_ratio_block",
        "exit_cost_pressure_block",
        "exit_probability_cost_decay_block",
        "input_manual_probability_review",
        "net_probability_buffer_watch",
        "probability_decay_block",
    )

    assert watch_row.probability_decay_rate == d("0.060000")
    assert watch_row.total_exit_cost_rate == d("0.035000")
    assert watch_row.net_probability_after_cost_decay_rate == d("0.495000")
    assert watch_row.cost_decay_to_probability_ratio == d("0.161017")
    assert watch_row.exit_cost_score == d("0.500000")
    assert watch_row.probability_decay_score == d("0.500000")
    assert watch_row.net_buffer_score == d("1.000000")
    assert watch_row.cost_decay_ratio_score == d("0.731638")
    assert watch_row.exit_probability_cost_decay_score == d("0.634746")
    assert watch_row.reason_codes == (
        "cost_decay_ratio_pass",
        "exit_cost_pressure_watch",
        "exit_probability_cost_decay_watch",
        "net_probability_buffer_pass",
        "probability_decay_watch",
    )

    assert pass_row.probability_decay_rate == d("0.030000")
    assert pass_row.total_exit_cost_rate == d("0.015000")
    assert pass_row.net_probability_after_cost_decay_rate == d("0.615000")
    assert pass_row.cost_decay_to_probability_ratio == d("0.068182")
    assert pass_row.exit_cost_score == d("0.785714")
    assert pass_row.probability_decay_score == d("0.750000")
    assert pass_row.net_buffer_score == d("1.000000")
    assert pass_row.cost_decay_ratio_score == d("0.886363")
    assert pass_row.exit_probability_cost_decay_score == d("0.832954")
    assert pass_row.reason_codes == (
        "cost_decay_ratio_pass",
        "exit_cost_pressure_pass",
        "exit_probability_cost_decay_pass",
        "net_probability_buffer_pass",
        "probability_decay_pass",
    )


def test_payload_digest_is_deterministic_immutable_decimal_strings_and_public_safe() -> None:
    module = api()
    sensitive_ref = (
        "raw_candidate=alpha candidate_id=cid market_id=mid market_slug=slug "
        "question text source_url=https://example.invalid/a source_text dsn=postgres "
        "table_name=markets token=secret wallet order trade"
    )
    first = build_report(
        observation(sensitive_ref, reason_codes=("zeta", "alpha")),
        observation("stable-public-sort-a"),
    )
    second = build_report(
        observation("stable-public-sort-a"),
        observation(sensitive_ref, reason_codes=("alpha", "zeta")),
    )

    payload = module.research_market_exit_probability_cost_decay_report_payload(first)
    repeated_payload = module.research_market_exit_probability_cost_decay_report_payload(second)
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == repeated_payload
    assert module.research_market_exit_probability_cost_decay_report_digest(first) == (
        module.research_market_exit_probability_cost_decay_report_digest(second)
    )
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert set(first.derived_validation_digest) <= set("0123456789abcdef")
    assert not any(type(value) in (int, float, Decimal) for value in walk_json(payload))
    assert payload["rows"][0]["total_exit_cost_rate"] == "0.015000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    for forbidden in (
        sensitive_ref,
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question text",
        "source_url",
        "source_text",
        "https://example.invalid/a",
        "dsn=postgres",
        "table_name",
        "token=secret",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden.lower() not in rendered_payload.lower()

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_exit_probability_cost_decay_report_payload(tampered)

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="payload"):
        module.research_market_exit_probability_cost_decay_report_payload(unsafe_payload)

    for digest_field in ("signal_ref_digest", "row_validation_digest"):
        digest_tampered_payload = json.loads(json.dumps(payload, sort_keys=True))
        digest_tampered_payload["rows"][0][digest_field] = "abc123"
        digest_tampered_payload["derived_validation_digest"] = payload_digest(
            digest_tampered_payload,
        )
        with pytest.raises(ValueError, match=digest_field):
            module.research_market_exit_probability_cost_decay_report_payload(
                digest_tampered_payload,
            )

    stale_row_digest_payload = json.loads(json.dumps(payload, sort_keys=True))
    stale_row_digest_payload["rows"][0]["total_exit_cost_rate"] = "0.016000"
    stale_row_digest_payload["derived_validation_digest"] = payload_digest(
        stale_row_digest_payload,
    )
    with pytest.raises(ValueError, match="row_validation_digest"):
        module.research_market_exit_probability_cost_decay_report_payload(
            stale_row_digest_payload,
        )


def test_contracts_are_frozen_decimal_only_strict_and_flag_locked() -> None:
    module = api()
    report = build_report(observation("strict-contracts"))

    for contract in (
        module.ResearchMarketExitProbabilityCostDecayConfig,
        module.ResearchMarketExitProbabilityCostDecayObservation,
        module.ResearchMarketExitProbabilityCostDecayRow,
        module.ResearchMarketExitProbabilityCostDecayReasonCodeCount,
        module.ResearchMarketExitProbabilityCostDecayReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{contract.__name__}Child", (contract,), {})

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        observation("decimal-subclass", exit_fee_rate=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="datetime"):
        observation("datetime-subclass", observed_at=_DateTimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="exceed pass threshold"):
        config(
            max_pass_cost_decay_to_probability_ratio=d("0.600000"),
            max_watch_cost_decay_to_probability_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="current_probability"):
        observation(
            "probability-increase",
            reference_probability=d("0.500000"),
            current_probability=d("0.510000"),
        )


def test_source_excludes_network_database_wallet_action_and_advice_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__).lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for banned in (
        "api_key",
        "private_key",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "open(",
        ".read(",
        ".write(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
        "recommendation",
        "position_size",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "table_name",
    ):
        assert banned not in source
