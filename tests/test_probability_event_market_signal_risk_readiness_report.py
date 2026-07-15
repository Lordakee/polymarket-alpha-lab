from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab import probability_event_market_signal_risk_readiness_report as module
from polymarket_alpha_lab.probability_event_market_signal_risk_readiness_report import (
    ProbabilityEventMarketSignalRiskReadinessInput,
    ProbabilityEventMarketSignalRiskReadinessReport,
    build_probability_event_market_signal_risk_readiness_report,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_market_signal_risk_readiness_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def risk_input(**overrides: object) -> ProbabilityEventMarketSignalRiskReadinessInput:
    values = {
        "event_label": "fed-cut-july",
        "market_probability": d("0.510000"),
        "previous_probability": d("0.500000"),
        "probability_move_15m": d("0.010000"),
        "probability_move_1h": d("0.020000"),
        "top_depth_now": d("1000.000000"),
        "top_depth_baseline": d("1200.000000"),
        "spread_width": d("0.020000"),
        "public_signal_lag_minutes": d("5.000000"),
        "pre_news_volume_ratio": d("1.100000"),
        "maker_fill_imbalance": d("0.100000"),
        "maker_quote_retreat_ratio": d("0.100000"),
    }
    values.update(overrides)
    return ProbabilityEventMarketSignalRiskReadinessInput(**values)


def report(
    *rows: ProbabilityEventMarketSignalRiskReadinessInput,
) -> ProbabilityEventMarketSignalRiskReadinessReport:
    return build_probability_event_market_signal_risk_readiness_report(rows)


def resign_payload(payload: dict[str, object]) -> None:
    unsigned = deepcopy(payload)
    unsigned["payload_digest"] = ""
    payload["payload_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def test_readiness_detects_price_jump_depth_collapse_news_lead_and_maker_adverse_selection() -> None:
    readiness = report(
        risk_input(event_label="base-case"),
        risk_input(
            event_label="risk-stack",
            market_probability=d("0.760000"),
            previous_probability=d("0.420000"),
            probability_move_15m=d("0.180000"),
            probability_move_1h=d("0.240000"),
            top_depth_now=d("120.000000"),
            top_depth_baseline=d("1000.000000"),
            spread_width=d("0.160000"),
            public_signal_lag_minutes=d("45.000000"),
            pre_news_volume_ratio=d("4.500000"),
            maker_fill_imbalance=d("0.820000"),
            maker_quote_retreat_ratio=d("0.780000"),
        ),
    )

    assert type(readiness) is ProbabilityEventMarketSignalRiskReadinessReport
    assert readiness.status == "block"
    assert readiness.event_count == d("2")
    assert readiness.pass_count == d("1")
    assert readiness.watch_count == d("0")
    assert readiness.block_count == d("1")
    assert readiness.max_risk_score == d("1.000000")
    assert readiness.mean_risk_score == d("0.500000")
    assert readiness.reason_codes == (
        "market_signal_risk_readiness_block",
        "depth_collapse_block",
        "information_asymmetry_news_lead_block",
        "maker_adverse_selection_block",
        "price_jump_block",
        "spread_width_block",
    )
    assert readiness.manual_next_step == "pause_probability_event_until_manual_risk_review"
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    risk_row, clear_row = readiness.rows
    assert risk_row.event_label == "risk-stack"
    assert risk_row.status == "block"
    assert risk_row.probability_jump == d("0.340000")
    assert risk_row.depth_collapse_ratio == d("0.880000")
    assert risk_row.information_asymmetry_score == d("0.805556")
    assert risk_row.adverse_selection_score == d("0.800000")
    assert risk_row.risk_score == d("1.000000")
    assert risk_row.reason_codes == (
        "depth_collapse_block",
        "information_asymmetry_news_lead_block",
        "maker_adverse_selection_block",
        "price_jump_block",
        "spread_width_block",
    )

    assert clear_row.event_label == "base-case"
    assert clear_row.status == "pass"
    assert clear_row.reason_codes == ("market_signal_risk_clear",)


def test_watch_thresholds_capture_smaller_anomaly_and_asymmetry_readiness_signals() -> None:
    readiness = report(
        risk_input(
            event_label="watch-stack",
            probability_move_15m=d("0.080000"),
            probability_move_1h=d("0.090000"),
            top_depth_now=d("520.000000"),
            top_depth_baseline=d("1000.000000"),
            spread_width=d("0.090000"),
            public_signal_lag_minutes=d("18.000000"),
            pre_news_volume_ratio=d("2.500000"),
            maker_fill_imbalance=d("0.420000"),
            maker_quote_retreat_ratio=d("0.360000"),
        ),
    )

    assert readiness.status == "watch"
    assert readiness.watch_count == d("1")
    assert readiness.block_count == d("0")
    assert readiness.rows[0].reason_codes == (
        "depth_collapse_watch",
        "information_asymmetry_news_lead_watch",
        "maker_adverse_selection_watch",
        "price_jump_watch",
        "spread_width_watch",
    )
    assert readiness.manual_next_step == "refresh_public_sources_before_probability_review"


@pytest.mark.parametrize(
    ("pre_news_volume_ratio", "expected_score", "expected_status", "expected_reasons"),
    (
        (
            d("0.000000"),
            d("0.000000"),
            "pass",
            ("market_signal_risk_clear",),
        ),
        (
            d("0.000001"),
            d("0.000000"),
            "pass",
            ("market_signal_risk_clear",),
        ),
        (
            d("1.000000"),
            d("0.000000"),
            "pass",
            ("market_signal_risk_clear",),
        ),
        (
            d("5.000000"),
            d("0.400000"),
            "watch",
            ("information_asymmetry_news_lead_watch",),
        ),
    ),
)
def test_pre_news_volume_ratio_zero_and_positive_boundaries_are_continuous(
    pre_news_volume_ratio: Decimal,
    expected_score: Decimal,
    expected_status: str,
    expected_reasons: tuple[str, ...],
) -> None:
    readiness = report(
        risk_input(
            market_probability=d("0.500000"),
            previous_probability=d("0.500000"),
            probability_move_15m=d("0.000000"),
            probability_move_1h=d("0.000000"),
            top_depth_now=d("1000.000000"),
            top_depth_baseline=d("1000.000000"),
            spread_width=d("0.000000"),
            public_signal_lag_minutes=d("0.000000"),
            pre_news_volume_ratio=pre_news_volume_ratio,
            maker_fill_imbalance=d("0.000000"),
            maker_quote_retreat_ratio=d("0.000000"),
        ),
    )

    row = readiness.rows[0]
    assert row.information_asymmetry_score == expected_score
    assert row.status == expected_status
    assert row.reason_codes == expected_reasons


def test_payload_uses_decimal_strings_digest_and_no_action_or_private_surfaces() -> None:
    first = report(
        risk_input(event_label="zeta"),
        risk_input(
            event_label="alpha",
            probability_move_15m=d("0.180000"),
            top_depth_now=d("120.000000"),
            top_depth_baseline=d("1000.000000"),
            spread_width=d("0.160000"),
        ),
    )
    second = report(
        risk_input(
            event_label="alpha",
            probability_move_15m=d("0.180000"),
            top_depth_now=d("120.000000"),
            top_depth_baseline=d("1000.000000"),
            spread_width=d("0.160000"),
        ),
        risk_input(event_label="zeta"),
    )

    payload = module.probability_event_market_signal_risk_readiness_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert first.rows == second.rows
    assert first.payload_digest == second.payload_digest
    assert payload["payload_digest"] == first.payload_digest
    assert payload["rows"][0]["risk_score"] == "1.000000"
    assert payload["event_count"] == "2"
    assert module.probability_event_market_signal_risk_readiness_payload_digest(payload) == first.payload_digest
    assert_no_public_numeric_scalars(payload)

    for forbidden in (
        "wallet",
        "auth",
        "private_key",
        "secret",
        "token",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "advice",
    ):
        assert forbidden not in encoded.lower()

    tampered = dict(payload)
    tampered["event_count"] = "3"
    with pytest.raises(ValueError, match="payload_digest"):
        module.probability_event_market_signal_risk_readiness_payload_digest(tampered)


def test_payload_digest_accepts_reordered_json_mapping_keys() -> None:
    readiness = report(risk_input())
    payload = module.probability_event_market_signal_risk_readiness_payload(readiness)
    reordered = dict(reversed(tuple(payload.items())))

    assert (
        module.probability_event_market_signal_risk_readiness_payload_digest(reordered)
        == readiness.payload_digest
    )


@pytest.mark.parametrize("nested_collection", ("rows", "reason_code_counts"))
def test_payload_digest_rejects_rehashed_nested_hard_flag_tampering(
    nested_collection: str,
) -> None:
    payload = deepcopy(
        module.probability_event_market_signal_risk_readiness_payload(
            report(risk_input()),
        ),
    )
    nested_values = payload[nested_collection]
    assert isinstance(nested_values, list)
    nested_values[0]["readonly"] = False
    resign_payload(payload)

    with pytest.raises(ValueError, match="readonly"):
        module.probability_event_market_signal_risk_readiness_payload_digest(payload)


def test_payload_digest_rejects_rehashed_report_rollup_tampering() -> None:
    payload = deepcopy(
        module.probability_event_market_signal_risk_readiness_payload(
            report(risk_input()),
        ),
    )
    payload["event_count"] = "2"
    resign_payload(payload)

    with pytest.raises(ValueError, match="event_count must match rows"):
        module.probability_event_market_signal_risk_readiness_payload_digest(payload)


def test_payload_digest_rejects_rehashed_row_derivation_tampering() -> None:
    payload = deepcopy(
        module.probability_event_market_signal_risk_readiness_payload(
            report(risk_input()),
        ),
    )
    rows = payload["rows"]
    assert isinstance(rows, list)
    rows[0]["probability_jump"] = "0.900000"
    resign_payload(payload)

    with pytest.raises(ValueError, match="probability_jump must match row inputs"):
        module.probability_event_market_signal_risk_readiness_payload_digest(payload)


@pytest.mark.parametrize(
    "injected_digest",
    (
        pytest.param("", id="empty"),
        pytest.param("0" * 64, id="all-zero"),
        pytest.param("f" * 64, id="forged"),
    ),
)
def test_main_payload_serializer_rejects_an_injected_report_digest(
    injected_digest: str,
) -> None:
    readiness = report(risk_input())
    object.__setattr__(readiness, "payload_digest", injected_digest)

    with pytest.raises(ValueError, match="payload_digest"):
        module.probability_event_market_signal_risk_readiness_payload(readiness)


@pytest.mark.parametrize(
    "invalid_digest",
    (
        pytest.param("0" * 64, id="all-zero"),
        pytest.param("f" * 64, id="forged"),
    ),
)
def test_replace_rejects_an_invalid_report_digest(invalid_digest: str) -> None:
    readiness = report(risk_input())

    with pytest.raises(ValueError, match="payload_digest must match"):
        replace(readiness, payload_digest=invalid_digest)


def test_replace_recomputes_an_empty_digest_before_serialization() -> None:
    rebuilt = replace(report(risk_input()), payload_digest="")

    assert rebuilt.payload_digest
    assert module.probability_event_market_signal_risk_readiness_payload(rebuilt)[
        "payload_digest"
    ]


@pytest.mark.parametrize(
    "class_name",
    (
        "ProbabilityEventMarketSignalRiskReadinessInput",
        "ProbabilityEventMarketSignalRiskReadinessRow",
        "ProbabilityEventMarketSignalRiskReadinessReasonCodeCount",
        "ProbabilityEventMarketSignalRiskReadinessReport",
    ),
)
def test_public_dataclasses_reject_subclass_declarations(class_name: str) -> None:
    public_class = getattr(module, class_name)

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(f"{class_name}Subclass", (public_class,), {})


def test_frozen_decimal_only_validation_flags_and_exports() -> None:
    readiness_input = risk_input()
    readiness = report(readiness_input)

    assert module.__all__ == (
        "DEFAULT_PROBABILITY_EVENT_MARKET_SIGNAL_RISK_READINESS_VERSION",
        "ProbabilityEventMarketSignalRiskReadinessInput",
        "ProbabilityEventMarketSignalRiskReadinessReasonCodeCount",
        "ProbabilityEventMarketSignalRiskReadinessReport",
        "ProbabilityEventMarketSignalRiskReadinessRow",
        "build_probability_event_market_signal_risk_readiness_report",
        "probability_event_market_signal_risk_readiness_payload",
        "probability_event_market_signal_risk_readiness_payload_digest",
    )

    for value in (
        readiness_input,
        readiness.rows[0],
        readiness.reason_code_counts[0],
        readiness,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal, field.name
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="market_probability"):
        risk_input(market_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_move_15m"):
        risk_input(probability_move_15m=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="top_depth_baseline"):
        risk_input(top_depth_baseline=d("0.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        risk_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)


def test_module_has_no_io_persistence_scraping_cli_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        ".write(",
        "jsonl",
        "persist",
        "durable",
        "supabase",
        "scrap",
        "team_memory",
        "strategy_aggregator",
        "cli",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret",
        "signature",
        "signing",
        "execute",
        "execution",
        "place_",
        "submit_",
        "cancel_",
    ):
        assert forbidden not in source


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")
