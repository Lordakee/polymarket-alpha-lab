from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_resolution_source_risk_premium_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-pass",
        "market_id": "market-alpha",
        "event_slug": "fed-july-cut",
        "category": "macro",
        "base_edge": d("0.080000"),
        "polymarket_rule_source_count": d("2"),
        "official_source_count": d("2"),
        "proxy_source_count": d("0"),
        "ambiguity_score": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyMarketResolutionSourceRiskPremiumV2Candidate(**values)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-market-resolution-source-risk-premium-v2",
        "official_source_gap_weight": d("0.020000"),
        "proxy_source_weight": d("0.010000"),
        "ambiguity_weight": d("0.030000"),
        "missing_rule_source_weight": d("0.015000"),
        "watch_risk_premium": d("0.020000"),
        "block_risk_premium": d("0.050000"),
        "high_risk_premium_threshold": d("0.040000"),
    }
    values.update(overrides)
    return module.StrategyMarketResolutionSourceRiskPremiumV2Config(**values)


def report(*, candidates=(), cfg=None):
    module = api()
    return module.build_strategy_market_resolution_source_risk_premium_v2_report(
        candidates,
        config=cfg if cfg is not None else config(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_report_computes_risk_premium_statuses_rollups_and_sorting() -> None:
    result = report(
        candidates=(
            candidate(candidate_id="candidate-pass", market_id="market-2"),
            candidate(
                candidate_id="candidate-watch",
                market_id="market-1",
                base_edge=d("0.090000"),
                official_source_count=d("1"),
                proxy_source_count=d("1"),
                ambiguity_score=d("0.500000"),
            ),
            candidate(
                candidate_id="candidate-block",
                market_id="market-3",
                base_edge=d("0.060000"),
                polymarket_rule_source_count=d("0"),
                official_source_count=d("0"),
                proxy_source_count=d("2"),
                ambiguity_score=d("1.000000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.config_version == "strategy-market-resolution-source-risk-premium-v2"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.high_risk_premium_count == d("2")
    assert result.proxy_source_count == d("2")
    assert result.missing_official_source_count == d("1")
    assert result.max_risk_premium == d("0.085000")
    assert result.report_status == "block"
    assert result.validation_digest
    assert result.reason_code_counts == (
        ("ambiguous_resolution_criteria", d("2")),
        ("missing_official_resolution_source", d("1")),
        ("missing_polymarket_rule_source", d("1")),
        ("official_resolution_source_gap", d("1")),
        ("resolution_source_risk_block", d("1")),
        ("resolution_source_risk_pass", d("1")),
        ("resolution_source_risk_watch", d("1")),
        ("uses_proxy_resolution_source", d("2")),
    )
    assert result.reason_codes == (
        "ambiguous_resolution_criteria",
        "missing_official_resolution_source",
        "missing_polymarket_rule_source",
        "official_resolution_source_gap",
        "resolution_source_risk_block",
        "resolution_source_risk_pass",
        "resolution_source_risk_watch",
        "uses_proxy_resolution_source",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.candidate_id for row in result.rows) == (
        "candidate-block",
        "candidate-watch",
        "candidate-pass",
    )
    blocked, watched, passed = result.rows

    assert blocked.resolution_source_risk_premium == d("0.085000")
    assert blocked.risk_adjusted_edge == d("-0.025000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "missing_polymarket_rule_source",
        "missing_official_resolution_source",
        "uses_proxy_resolution_source",
        "ambiguous_resolution_criteria",
        "resolution_source_risk_block",
    )

    assert watched.resolution_source_risk_premium == d("0.045000")
    assert watched.risk_adjusted_edge == d("0.045000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "official_resolution_source_gap",
        "uses_proxy_resolution_source",
        "ambiguous_resolution_criteria",
        "resolution_source_risk_watch",
    )

    assert passed.resolution_source_risk_premium == d("0.003000")
    assert passed.risk_adjusted_edge == d("0.077000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("resolution_source_risk_pass",)


def test_empty_report_is_empty_status_and_zero_decimals() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.high_risk_premium_count == d("0")
    assert empty.proxy_source_count == d("0")
    assert empty.missing_official_source_count == d("0")
    assert empty.max_risk_premium == ZERO
    assert empty.report_status == "empty"
    assert empty.reason_code_counts == ()
    assert empty.reason_codes == ()
    assert empty.rows == ()
    assert empty.validation_digest
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidates=(candidate(),))
    for value in (empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_edge",
                    "_premium",
                    "_score",
                    "_source_count",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_is_json_safe_decimal_stringed_and_has_validation_digest() -> None:
    module = api()
    result = report(
        candidates=(
            candidate(
                candidate_id="candidate-block",
                market_id="market-3",
                base_edge=d("0.060000"),
                polymarket_rule_source_count=d("0"),
                official_source_count=d("0"),
                proxy_source_count=d("2"),
                ambiguity_score=d("1.000000"),
            ),
        ),
    )

    payload = module.strategy_market_resolution_source_risk_premium_v2_payload(result)

    assert payload["candidate_count"] == "1"
    assert payload["block_count"] == "1"
    assert payload["max_risk_premium"] == "0.085000"
    assert payload["report_status"] == "block"
    assert payload["validation_digest"] == result.validation_digest
    assert payload["reason_code_counts"] == [
        ["ambiguous_resolution_criteria", "1"],
        ["missing_official_resolution_source", "1"],
        ["missing_polymarket_rule_source", "1"],
        ["resolution_source_risk_block", "1"],
        ["uses_proxy_resolution_source", "1"],
    ]
    assert payload["rows"][0]["resolution_source_risk_premium"] == "0.085000"
    assert payload["rows"][0]["risk_adjusted_edge"] == "-0.025000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_duplicates_flags_and_unsorted_rows() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_market_resolution_source_risk_premium_v2_report(
            (),
            config=object(),
        )
    with pytest.raises(ValueError, match="base_edge"):
        candidate(base_edge=0.08)
    with pytest.raises(ValueError, match="ambiguity_score"):
        candidate(ambiguity_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="official_source_count"):
        candidate(official_source_count=d("-1"))
    with pytest.raises(ValueError, match="ambiguity_score"):
        candidate(ambiguity_score=d("1.000001"))
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id="candidate bad")
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        report(candidates=(candidate(), candidate()))
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)

    row = report(candidates=(candidate(),)).rows[0]
    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        module.StrategyMarketResolutionSourceRiskPremiumV2Report(
            config_version="strategy-market-resolution-source-risk-premium-v2",
            candidate_count=d("2"),
            pass_count=d("2"),
            watch_count=d("0"),
            block_count=d("0"),
            high_risk_premium_count=d("0"),
            proxy_source_count=d("0"),
            missing_official_source_count=d("0"),
            max_risk_premium=d("0.003000"),
            report_status="pass",
            reason_codes=("resolution_source_risk_pass",),
            reason_code_counts=(("resolution_source_risk_pass", d("2")),),
            validation_digest="a" * 64,
            rows=(replace(row, candidate_id="candidate-z"), row),
        )

    frozen = candidate()
    with pytest.raises(FrozenInstanceError):
        frozen.category = "sports"  # type: ignore[misc]


def test_validation_digest_is_derived_and_rejects_manual_mismatch() -> None:
    module = api()
    result = report(candidates=(candidate(),))

    assert len(result.validation_digest) == 64
    assert result.validation_digest == report(candidates=(candidate(),)).validation_digest

    with pytest.raises(ValueError, match="validation_digest"):
        module.StrategyMarketResolutionSourceRiskPremiumV2Report(
            config_version=result.config_version,
            candidate_count=result.candidate_count,
            pass_count=result.pass_count,
            watch_count=result.watch_count,
            block_count=result.block_count,
            high_risk_premium_count=result.high_risk_premium_count,
            proxy_source_count=result.proxy_source_count,
            missing_official_source_count=result.missing_official_source_count,
            max_risk_premium=result.max_risk_premium,
            report_status=result.report_status,
            reason_codes=result.reason_codes,
            reason_code_counts=result.reason_code_counts,
            validation_digest="0" * 64,
            rows=result.rows,
        )


def test_module_has_no_external_io_or_live_surface_terms() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/strategy_market_resolution_source_risk_premium_v2.py",
    )
    source = source_path.read_text()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "pathlib",
    }
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imports.isdisjoint(forbidden_import_roots)

    forbidden_calls = {"open", "connect", "execute", "urlopen"}
    call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert call_names.isdisjoint(forbidden_calls)

    lowered_source = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "signing",
        "order submit",
        "order cancel",
        "account",
        "advice",
    ):
        assert forbidden not in lowered_source
