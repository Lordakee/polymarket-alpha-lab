from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_source_trust_decay_gate_v2"
CONFIG_VERSION = "strategy-recommendation-source-trust-decay-gate-v2"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "source_age_watch_seconds": d("3600.000000"),
        "source_age_block_seconds": d("7200.000000"),
        "historical_reliability_watch_score": d("0.750000"),
        "historical_reliability_block_score": d("0.500000"),
        "contradiction_watch_score": d("0.250000"),
        "contradiction_block_score": d("0.500000"),
        "minimum_source_trust_score": d("0.700000"),
        "blocked_source_trust_score": d("0.450000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationSourceTrustDecayGateV2Config(**values)


def recommendation(
    recommendation_id: str = "rec-alpha",
    market_id: str = "market-alpha",
    **overrides: object,
) -> Any:
    module = api()
    values = {
        "recommendation_id": recommendation_id,
        "market_id": market_id,
        "recommendation_side": "yes",
        "base_confidence": d("0.850000"),
        "source_trust_score": d("0.900000"),
        "source_observed_at": GENERATED_AT - timedelta(minutes=30),
        "historical_reliability_score": d("0.900000"),
        "contradiction_score": d("0.050000"),
        "official_confirmation_observed_at": GENERATED_AT - timedelta(minutes=20),
        "observed_at": GENERATED_AT - timedelta(minutes=15),
        "reason_codes": ("source_inputs_available",),
    }
    values.update(overrides)
    return module.StrategyRecommendationSourceTrustDecayGateV2Input(**values)


def report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_recommendation_source_trust_decay_gate_v2_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool or item is None:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_gate_blocks_watch_pass_and_rolls_up_reasons_deterministically() -> None:
    result = report(
        recommendation(
            recommendation_id="rec-pass",
            market_id="market-pass",
            source_trust_score=d("0.900000"),
            source_observed_at=GENERATED_AT - timedelta(seconds=1800),
            historical_reliability_score=d("0.900000"),
            contradiction_score=d("0.050000"),
            official_confirmation_observed_at=GENERATED_AT - timedelta(seconds=1200),
        ),
        recommendation(
            recommendation_id="rec-watch",
            market_id="market-watch",
            source_trust_score=d("0.760000"),
            source_observed_at=GENERATED_AT - timedelta(seconds=4000),
            historical_reliability_score=d("0.650000"),
            contradiction_score=d("0.300000"),
            official_confirmation_observed_at=GENERATED_AT - timedelta(seconds=3000),
        ),
        recommendation(
            recommendation_id="rec-blocked",
            market_id="market-blocked",
            base_confidence=d("0.900000"),
            source_trust_score=d("0.400000"),
            source_observed_at=GENERATED_AT - timedelta(seconds=8000),
            historical_reliability_score=d("0.400000"),
            contradiction_score=d("0.700000"),
            official_confirmation_observed_at=None,
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.candidate_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "source_trust_decay_gate_blocked",
        "source_trust_decay_gate_watch",
        "source_trust_decay_gate_pass",
        "source_staleness_blocked",
        "historical_reliability_blocked",
        "source_contradiction_blocked",
        "official_confirmation_missing_blocked",
        "source_trust_score_blocked",
        "decayed_source_trust_blocked",
        "source_staleness_watch",
        "historical_reliability_watch",
        "source_contradiction_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.derived_validation_digest
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.recommendation_id for row in result.rows) == (
        "rec-blocked",
        "rec-watch",
        "rec-pass",
    )

    blocked, watched, passed = result.rows
    assert blocked.source_age_seconds == d("8000.000000")
    assert blocked.source_freshness_score == ZERO
    assert blocked.contradiction_resistance_score == d("0.300000")
    assert blocked.official_confirmation_score == ZERO
    assert blocked.source_trust_decay_score == d("0.220000")
    assert blocked.trust_adjusted_confidence == d("0.220000")
    assert blocked.gate_status == "blocked"
    assert blocked.reason_codes == (
        "source_trust_decay_gate_blocked",
        "source_staleness_blocked",
        "historical_reliability_blocked",
        "source_contradiction_blocked",
        "official_confirmation_missing_blocked",
        "source_trust_score_blocked",
        "decayed_source_trust_blocked",
        "source_inputs_available",
    )
    assert blocked.derived_validation_digest

    assert watched.source_age_seconds == d("4000.000000")
    assert watched.source_freshness_score == d("0.444444")
    assert watched.contradiction_resistance_score == d("0.700000")
    assert watched.official_confirmation_score == d("1.000000")
    assert watched.source_trust_decay_score == d("0.710889")
    assert watched.trust_adjusted_confidence == d("0.710889")
    assert watched.gate_status == "watch"
    assert watched.reason_codes == (
        "source_trust_decay_gate_watch",
        "source_staleness_watch",
        "historical_reliability_watch",
        "source_contradiction_watch",
        "source_inputs_available",
    )

    assert passed.source_age_seconds == d("1800.000000")
    assert passed.source_freshness_score == d("0.750000")
    assert passed.contradiction_resistance_score == d("0.950000")
    assert passed.official_confirmation_score == d("1.000000")
    assert passed.source_trust_decay_score == d("0.900000")
    assert passed.trust_adjusted_confidence == d("0.850000")
    assert passed.gate_status == "pass"
    assert passed.reason_codes == (
        "source_trust_decay_gate_pass",
        "source_inputs_available",
    )


def test_empty_report_is_blocked_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.candidate_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.blocked_count == ZERO
    assert result.status == "blocked"
    assert result.reason_codes == ("source_trust_decay_gate_v2_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_helper_is_json_ready_and_digest_validated() -> None:
    module = api()
    result = report(recommendation())

    payload = module.strategy_recommendation_source_trust_decay_gate_v2_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["source_trust_decay_score"] == "0.900000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert_no_float_values(payload)
    assert (
        module.strategy_recommendation_source_trust_decay_gate_v2_payload(payload)
        == payload
    )

    assert "0.900000" in encoded

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_source_trust_decay_gate_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_source_trust_decay_gate_v2_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="Decimal\\|string"):
        module.strategy_recommendation_source_trust_decay_gate_v2_payload(
            {**payload, "candidate_count": 1.0},
        )

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.strategy_recommendation_source_trust_decay_gate_v2_payload(
            {**payload, "candidate_count": "2.000000"},
        )


def test_inputs_config_and_datetimes_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_trust_score must be a Decimal"):
        recommendation(source_trust_score=1)
    with pytest.raises(ValueError, match="market_id must be a non-empty canonical string"):
        recommendation(market_id="market alpha")
    with pytest.raises(ValueError, match="reason_codes must not contain duplicate values"):
        recommendation(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="source_age_watch_seconds must be less than"):
        config(source_age_watch_seconds=d("9000.000000"))
    with pytest.raises(ValueError, match="historical_reliability_block_score must not exceed"):
        config(historical_reliability_block_score=d("0.800000"))
    with pytest.raises(ValueError, match="contradiction_watch_score must be less than"):
        config(contradiction_watch_score=d("0.600000"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_source_trust_decay_gate_v2_report(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_source_trust_decay_gate_v2_report(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="source_observed_at must not be after"):
        report(recommendation(source_observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="official_confirmation_observed_at must not be after"):
        report(
            recommendation(
                official_confirmation_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    with pytest.raises(ValueError, match="observed_at must not be after"):
        report(recommendation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="recommendations must not contain duplicate"):
        report(recommendation(), recommendation())

    result = report(recommendation())
    with pytest.raises(FrozenInstanceError):
        result.rows[0].gate_status = "blocked"


def test_tamper_evident_result_and_report_validation_recomputes_fields() -> None:
    result = report(recommendation())
    row = result.rows[0]

    with pytest.raises(ValueError, match="source_trust_decay_score must match"):
        replace(
            row,
            source_trust_decay_score=row.source_trust_decay_score + d("0.000001"),
        )

    with pytest.raises(ValueError, match="trust_adjusted_confidence must match"):
        replace(
            row,
            trust_adjusted_confidence=row.trust_adjusted_confidence + d("0.000001"),
        )

    with pytest.raises(ValueError, match="gate_status must match"):
        replace(row, gate_status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(row, derived_validation_digest="not-the-digest")

    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1.000000"))

    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            rows=(
                recommendation_result("zeta-pass", "market-zeta"),
                recommendation_result(
                    "alpha-blocked",
                    "market-alpha-blocked",
                    source_trust_score=d("0.300000"),
                    source_observed_at=GENERATED_AT - timedelta(seconds=9000),
                    historical_reliability_score=d("0.300000"),
                    contradiction_score=d("0.800000"),
                    official_confirmation_observed_at=None,
                ),
            ),
        )

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(result, derived_validation_digest="not-the-digest")


def recommendation_result(
    recommendation_id: str,
    market_id: str,
    **overrides: object,
) -> Any:
    return report(
        recommendation(
            recommendation_id=recommendation_id,
            market_id=market_id,
            **overrides,
        ),
    ).rows[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "strategy_recommendation_source_trust_decay_gate_v2.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = path.read_text(encoding="utf-8").lower()

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "submit",
        "post",
        "send",
        "login",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order placement",
        "database",
        "supabase",
        "private_key",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in source] == []
