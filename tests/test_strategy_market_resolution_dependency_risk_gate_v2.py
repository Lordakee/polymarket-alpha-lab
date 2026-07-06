from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 6, 11, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")

UNSAFE_PUBLIC_TERMS = (
    "li" + "ve",
    "au" + "th",
    "wall" + "et",
    "ord" + "er",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "mut" + "ation",
    "b" + "uy",
    "s" + "ell",
    "tr" + "ade",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_resolution_dependency_risk_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_MARKET_RESOLUTION_DEPENDENCY_RISK_GATE_V2_CONFIG_VERSION
        ),
        "watch_dependency_risk_score": d("0.350000"),
        "blocked_dependency_risk_score": d("0.700000"),
        "high_settlement_delay_hours": d("72.000000"),
        "dependency_count_block_count": d("3"),
        "correlated_resolution_block_count": d("2"),
        "low_source_confidence_watch": d("0.750000"),
        "low_source_confidence_blocked": d("0.500000"),
    }
    values.update(overrides)
    return module.StrategyMarketResolutionDependencyRiskGateV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_slug": "alpha-market",
        "evaluated_at": EVALUATED_AT,
        "resolution_dependency_key": "event-alpha",
        "external_dependency_count": d("0"),
        "correlated_resolution_count": d("0"),
        "source_confidence_ratio": d("1.000000"),
        "settlement_delay_hours": d("0.000000"),
        "market_dependency_weight": d("0.000000"),
        "reason_codes": ("resolution_dependency_input",),
    }
    values.update(overrides)
    return module.StrategyMarketResolutionDependencyRiskGateV2Candidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_market_resolution_dependency_risk_gate_v2_report(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numbers(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def test_dependency_risk_scoring_watches_resolution_dependency_pressure() -> None:
    result = report(
        candidate(
            candidate_reference="score-alpha",
            market_slug="score-market",
            external_dependency_count=d("2"),
            source_confidence_ratio=d("0.700000"),
            settlement_delay_hours=d("24.000000"),
            market_dependency_weight=d("0.400000"),
        ),
    )

    assert is_dataclass(result)
    assert result.candidate_count == d("1")
    assert result.blocked_count == ZERO
    assert result.watch_count == d("1")
    assert result.paper_ok_count == ZERO
    assert result.status == "watch"
    assert result.reason_codes == ("resolution_dependency_risk_gate_watch",)

    row = result.rows[0]
    assert row.dependency_rank == d("1")
    assert row.dependency_count_penalty == d("0.666667")
    assert row.correlated_resolution_penalty == ZERO
    assert row.settlement_delay_penalty == d("0.333333")
    assert row.unresolved_source_risk == d("0.300000")
    assert row.total_dependency_risk_score == d("0.318333")
    assert row.dependency_risk_status == "watch"
    assert row.reason_codes == (
        "correlated_resolution_dependency_clear",
        "external_dependency_pressure_watch",
        "market_dependency_weight_watch",
        "resolution_dependency_input",
        "resolution_dependency_risk_gate_watch",
        "settlement_delay_penalty_clear",
        "source_confidence_gap_watch",
    )
    for value in (
        result.candidate_count,
        row.external_dependency_count,
        row.correlated_resolution_count,
        row.source_confidence_ratio,
        row.settlement_delay_hours,
        row.total_dependency_risk_score,
    ):
        assert type(value) is Decimal


def test_correlated_resolution_cluster_blocks_each_dependent_market() -> None:
    result = report(
        candidate(
            candidate_reference="cluster-alpha",
            market_slug="cluster-alpha",
            resolution_dependency_key="event-shared",
        ),
        candidate(
            candidate_reference="cluster-beta",
            market_slug="cluster-beta",
            resolution_dependency_key="event-shared",
        ),
    )

    assert result.status == "blocked"
    assert result.candidate_count == d("2")
    assert result.blocked_count == d("2")
    assert result.reason_codes == ("correlated_resolution_dependency_blocked",)
    assert tuple(row.market_slug for row in result.rows) == (
        "cluster-alpha",
        "cluster-beta",
    )
    for row in result.rows:
        assert row.correlated_resolution_count == d("2")
        assert row.correlated_resolution_penalty == d("1.000000")
        assert row.dependency_risk_status == "blocked"
        assert "correlated_resolution_dependency_blocked" in row.reason_codes


def test_settlement_delay_penalty_blocks_long_resolution_cash_wait() -> None:
    result = report(
        candidate(
            candidate_reference="delay-alpha",
            market_slug="delay-market",
            settlement_delay_hours=d("96.000000"),
        ),
    )
    row = result.rows[0]

    assert result.status == "blocked"
    assert row.settlement_delay_penalty == d("1.000000")
    assert row.total_dependency_risk_score == d("0.200000")
    assert row.dependency_risk_status == "blocked"
    assert "settlement_delay_penalty_blocked" in row.reason_codes


def test_public_payload_serializes_decimals_as_strings_and_rejects_unsafe_text() -> None:
    module = api()
    result = report(
        candidate(
            candidate_reference="payload-alpha",
            market_slug="payload-market",
            evaluated_at=datetime(2026, 7, 6, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
            external_dependency_count=d("2"),
            source_confidence_ratio=d("0.700000"),
            settlement_delay_hours=d("24.000000"),
            market_dependency_weight=d("0.400000"),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_market_resolution_dependency_risk_gate_v2_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_total_dependency_risk_score"] == "0.318333"
    assert payload["rows"][0]["evaluated_at"] == "2026-07-06T11:00:00+00:00"
    assert payload["rows"][0]["total_dependency_risk_score"] == "0.318333"
    assert payload["rows"][0]["settlement_delay_hours"] == "24.000000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert "payload-alpha" not in rendered
    assert_no_public_numbers(payload)

    for term in UNSAFE_PUBLIC_TERMS:
        with pytest.raises(ValueError, match="unsafe public"):
            module._payload_value({"safe_key": f"prefix-{term}-suffix"})
        with pytest.raises(ValueError, match="unsafe public"):
            module._payload_value({f"prefix_{term}_suffix": "safe"})


def test_frozen_dataclasses_hard_flags_and_digest_tampering_are_rejected() -> None:
    module = api()

    shifted = report(
        candidate(
            evaluated_at=datetime(2026, 7, 6, 6, 0, tzinfo=timezone(timedelta(hours=-5))),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.rows[0].evaluated_at == EVALUATED_AT

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="evaluated_at must be exactly datetime"):
        candidate(evaluated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="settlement_delay_hours must be exactly Decimal"):
        candidate(settlement_delay_hours=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="settlement_delay_hours must be exactly Decimal"):
        candidate(settlement_delay_hours=1)

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        candidate(report_only=False)

    row = report(candidate()).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.dependency_risk_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, total_dependency_risk_score=d("0.999999"))

    original = report(candidate())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(original, candidate_count=d("2"))

    with pytest.raises(ValueError, match="config must be exactly"):
        module.build_strategy_market_resolution_dependency_risk_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidate(), candidate())

    with pytest.raises(ValueError, match="unsafe public"):
        candidate(market_slug="prefix-" + UNSAFE_PUBLIC_TERMS[0])


def test_empty_report_is_zeroed_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == ZERO
    assert empty.blocked_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.paper_ok_count == ZERO
    assert empty.max_total_dependency_risk_score == ZERO
    assert empty.max_settlement_delay_hours == ZERO
    assert empty.max_correlated_resolution_count == ZERO
    assert empty.max_external_dependency_count == ZERO
    assert empty.status == "paper_ok"
    assert empty.reason_codes == ("resolution_dependency_risk_gate_v2_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidate())
    for value in (config(), empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_hours",
                    "_risk",
                    "_penalty",
                    "_score",
                    "_rank",
                    "_ratio",
                    "_weight",
                ),
            ):
                assert type(item_value) is Decimal


def test_source_scope_has_no_external_or_action_surfaces() -> None:
    module = api()
    source_paths = (
        Path(module.__file__),
        Path(__file__),
    )
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert not {
            "req" + "uests",
            "ht" + "tpx",
            "url" + "lib",
            "sql" + "ite3",
            "psy" + "copg",
            "supa" + "base",
            "we" + "b3",
        } & imports
        lower_text = text.lower()
        for term in UNSAFE_PUBLIC_TERMS:
            assert term not in lower_text

    assert module.__all__ == (
        "DEFAULT_STRATEGY_MARKET_RESOLUTION_DEPENDENCY_RISK_GATE_V2_CONFIG_VERSION",
        "StrategyMarketResolutionDependencyRiskGateV2Candidate",
        "StrategyMarketResolutionDependencyRiskGateV2Config",
        "StrategyMarketResolutionDependencyRiskGateV2Report",
        "StrategyMarketResolutionDependencyRiskGateV2Row",
        "build_strategy_market_resolution_dependency_risk_gate_v2_report",
        "strategy_market_resolution_dependency_risk_gate_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
