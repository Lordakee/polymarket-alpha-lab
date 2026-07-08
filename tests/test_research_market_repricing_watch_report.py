from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_repricing_watch_report"
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_MARKET_REPRICING_WATCH_CONFIG_VERSION,
        "watch_probability_move_age_seconds": d("900.000000"),
        "block_probability_move_age_seconds": d("3600.000000"),
        "watch_probability_move_ratio": d("0.050000"),
        "block_probability_move_ratio": d("0.150000"),
        "watch_spread_cost_pressure": d("0.300000"),
        "block_spread_cost_pressure": d("0.700000"),
        "watch_evidence_lag_seconds": d("1800.000000"),
        "block_evidence_lag_seconds": d("7200.000000"),
        "watch_manual_recheck_score": d("0.300000"),
        "block_manual_recheck_score": d("0.700000"),
        "watch_recheck_urgency_score": d("0.300000"),
        "block_recheck_urgency_score": d("0.700000"),
        "probability_move_weight": d("0.250000"),
        "probability_move_freshness_weight": d("0.250000"),
        "spread_cost_weight": d("0.200000"),
        "evidence_lag_weight": d("0.200000"),
        "manual_recheck_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchMarketRepricingWatchConfig(**values)


def observation(
    public_bucket: str = "public-repricing-bucket",
    *,
    observed_at: datetime | None = None,
    evidence_observed_at: datetime | None = None,
    sample_count: Decimal = d("5"),
    probability_move_ratio: Decimal = d("0.020000"),
    spread_cost_pressure_score: Decimal = d("0.100000"),
    manual_recheck_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketRepricingWatchObservation(
        public_bucket=public_bucket,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=5),
        evidence_observed_at=evidence_observed_at or GENERATED_AT - timedelta(minutes=10),
        sample_count=sample_count,
        probability_move_ratio=probability_move_ratio,
        spread_cost_pressure_score=spread_cost_pressure_score,
        manual_recheck_score=manual_recheck_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_repricing_watch_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_payload_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def test_repricing_watch_report_summarizes_freshness_cost_lag_and_recheck() -> None:
    module = api()
    built = report(
        observation("quiet-public-bucket"),
        observation(
            "watch-public-bucket",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=75),
            sample_count=d("3"),
            probability_move_ratio=d("0.080000"),
            spread_cost_pressure_score=d("0.400000"),
            manual_recheck_score=d("0.400000"),
            reason_codes=("public_evidence_check",),
        ),
        observation(
            "blocked-public-bucket",
            observed_at=GENERATED_AT - timedelta(hours=2),
            evidence_observed_at=GENERATED_AT - timedelta(hours=5),
            sample_count=d("7"),
            probability_move_ratio=d("0.170000"),
            spread_cost_pressure_score=d("0.800000"),
            manual_recheck_score=d("0.800000"),
        ),
    )

    assert type(built) is module.ResearchMarketRepricingWatchReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.status == "block"
    assert built.observation_count == d("3.000000")
    assert built.sample_count == d("15.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.probability_move_freshness_count == d("2.000000")
    assert built.spread_cost_pressure_count == d("2.000000")
    assert built.evidence_lag_count == d("2.000000")
    assert built.manual_recheck_count == d("2.000000")
    assert built.mean_probability_move_age_seconds == d("3100.000000")
    assert built.mean_evidence_lag_seconds == d("4600.000000")
    assert built.mean_recheck_urgency_score == d("0.422222")
    assert built.max_recheck_urgency_score == d("1.000000")
    assert built.manual_recheck_required is True

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_bucket == "blocked-public-bucket"
    assert blocked.probability_move_age_seconds == d("7200.000000")
    assert blocked.evidence_lag_seconds == d("10800.000000")
    assert blocked.recheck_urgency_score == d("1.000000")
    assert blocked.reason_codes == (
        "repricing_watch_probability_move_block",
        "repricing_watch_probability_move_freshness_block",
        "repricing_watch_spread_cost_pressure_block",
        "repricing_watch_evidence_lag_block",
        "repricing_watch_manual_recheck_block",
        "repricing_watch_recheck_urgency_block",
    )
    assert watched.public_bucket == "watch-public-bucket"
    assert watched.probability_move_pressure == d("0.300000")
    assert watched.probability_move_freshness_pressure == d("0.333333")
    assert watched.spread_cost_pressure == d("0.250000")
    assert watched.evidence_lag_pressure == d("0.166667")
    assert watched.manual_recheck_pressure == d("0.250000")
    assert watched.recheck_urgency_score == d("0.266667")
    assert watched.reason_codes == (
        "input_public_evidence_check",
        "repricing_watch_probability_move_watch",
        "repricing_watch_probability_move_freshness_watch",
        "repricing_watch_spread_cost_pressure_watch",
        "repricing_watch_evidence_lag_watch",
        "repricing_watch_manual_recheck_watch",
    )
    assert passed.reason_codes == ("repricing_watch_clear",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_recheck_urgency_block_can_trigger_from_aggregate_pressure() -> None:
    module = api()
    built = report(
        observation(
            "aggregate-block-public-bucket",
            observed_at=GENERATED_AT - timedelta(seconds=3240),
            evidence_observed_at=GENERATED_AT - timedelta(seconds=8940),
            probability_move_ratio=d("0.140000"),
            spread_cost_pressure_score=d("0.660000"),
            manual_recheck_score=d("0.660000"),
        ),
    )

    (row,) = built.rows
    assert row.status == "block"
    assert row.recheck_urgency_score == d("0.900000")
    assert config().block_recheck_urgency_score <= row.recheck_urgency_score < d("1.000000")
    assert "repricing_watch_recheck_urgency_block" in row.reason_codes
    assert "repricing_watch_probability_move_block" not in row.reason_codes
    payload = module.research_market_repricing_watch_report_payload(built)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))


def test_payload_and_digest_are_deterministic_decimal_strings_and_report_only() -> None:
    module = api()
    first = report(
        observation("beta-public-bucket", probability_move_ratio=d("0.080000")),
        observation("alpha-public-bucket"),
    )
    second = report(
        observation("alpha-public-bucket"),
        observation("beta-public-bucket", probability_move_ratio=d("0.080000")),
    )
    first_payload = module.research_market_repricing_watch_report_payload(first)
    second_payload = module.research_market_repricing_watch_report_payload(second)
    digest = module.research_market_repricing_watch_report_digest(first)

    assert first == second
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True)
    assert digest == hashlib.sha256(
        json.dumps(first_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert digest == module.research_market_repricing_watch_report_digest(second)
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["public_bucket"] == "beta-public-bucket"
    assert first_payload["rows"][0]["probability_move_ratio"] == "0.080000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    assert "order" not in payload_text
    assert "trade" not in payload_text
    assert "sizing" not in payload_text
    assert "recommend" not in payload_text
    assert "buy" not in payload_text
    assert "sell" not in payload_text


def test_empty_report_blocks_for_manual_recheck_with_public_reason() -> None:
    module = api()
    empty = report()

    assert empty.status == "block"
    assert empty.observation_count == ZERO
    assert empty.row_count == ZERO
    assert empty.rows == ()
    assert empty.manual_recheck_required is True
    assert empty.reason_codes == ("repricing_watch_no_observations",)
    assert empty.reason_code_counts == (
        module.ResearchMarketRepricingWatchReasonCodeCount(
            reason_code="repricing_watch_no_observations",
            count=d("1.000000"),
            sample_ratio=ZERO,
        ),
    )


def test_validation_rejects_bad_numeric_types_flags_times_and_tampering() -> None:
    module = api()
    good = report(observation())

    with pytest.raises(FrozenInstanceError):
        good.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        good.rows[0].recheck_urgency_score = d("0.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="probability_move_ratio"):
        observation(probability_move_ratio=0.006)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_cost_pressure_score"):
        observation(spread_cost_pressure_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        replace(observation(), observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        observation(evidence_observed_at=GENERATED_AT)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="public_bucket"):
        observation("market_id:raw-source-id")

    tampered = replace(good)
    object.__setattr__(tampered, "observation_count", d("2.000000"))
    with pytest.raises(ValueError, match="observation_count"):
        module.research_market_repricing_watch_report_payload(tampered)

    bad_flag_row = replace(good.rows[0])
    object.__setattr__(bad_flag_row, "report_only", False)
    bad_nested = replace(good)
    object.__setattr__(bad_nested, "rows", (bad_flag_row,))
    with pytest.raises(ValueError, match="report_only"):
        module.research_market_repricing_watch_report_payload(bad_nested)


def test_module_is_pure_report_only_without_live_surfaces() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    forbidden_fragments = (
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "web3",
        "clob",
        "place_order",
        "submit_order",
        "wallet",
        "private_key",
        "execute_trade",
        "trade_recommendation",
        "position_size",
        "recommend",
        "sizing",
        "buy",
        "sell",
        "order",
    )

    for fragment in forbidden_fragments:
        assert fragment not in source

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type) and is_dataclass(exported):
            names = {field.name for field in fields(exported)}
            if {"paper_only", "report_only", "readonly"} <= names:
                instance = (
                    config()
                    if exported_name.endswith("Config")
                    else observation()
                    if exported_name.endswith("Observation")
                    else report()
                    if exported_name.endswith("Report")
                    else None
                )
                if instance is not None:
                    assert instance.paper_only is True
                    assert instance.report_only is True
                    assert instance.readonly is True
