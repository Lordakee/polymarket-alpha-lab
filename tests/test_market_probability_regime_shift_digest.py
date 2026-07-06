from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_probability_regime_shift_digest import (
    DEFAULT_MARKET_PROBABILITY_REGIME_SHIFT_DIGEST_CONFIG_VERSION,
    MarketProbabilityRegimeShiftCategoryRollup,
    MarketProbabilityRegimeShiftDigestConfig,
    MarketProbabilityRegimeShiftDigestReport,
    MarketProbabilityRegimeShiftInput,
    MarketProbabilityRegimeShiftReasonCodeCount,
    MarketProbabilityRegimeShiftRow,
    build_market_probability_regime_shift_digest,
    market_probability_regime_shift_digest_json_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


def _config(**overrides: object) -> MarketProbabilityRegimeShiftDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_PROBABILITY_REGIME_SHIFT_DIGEST_CONFIG_VERSION,
        "medium_move_threshold": Decimal("0.030000"),
        "high_move_threshold": Decimal("0.080000"),
        "extreme_move_threshold": Decimal("0.150000"),
        "liquidity_confirmation_threshold": Decimal("0.600000"),
        "stale_source_seconds_threshold": Decimal("3600.000000"),
    }
    values.update(overrides)
    return MarketProbabilityRegimeShiftDigestConfig(**values)


def _input(
    condition_id: str,
    category: str,
    *,
    probability_before: Decimal = Decimal("0.420000"),
    probability_after: Decimal = Decimal("0.460000"),
    liquidity_confirmation_score: Decimal = Decimal("0.700000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=10),
    source_observed_at: datetime = GENERATED_AT - timedelta(minutes=10),
    source_config_version: str = "market-probability-source-v0",
    source_reference: str | None = "public-source-alpha",
) -> MarketProbabilityRegimeShiftInput:
    return MarketProbabilityRegimeShiftInput(
        condition_id=condition_id,
        category=category,
        probability_before=probability_before,
        probability_after=probability_after,
        liquidity_confirmation_score=liquidity_confirmation_score,
        observed_at=observed_at,
        source_observed_at=source_observed_at,
        source_config_version=source_config_version,
        source_reference=source_reference,
    )


def test_digest_summarizes_regime_shifts_by_condition_and_category() -> None:
    report = build_market_probability_regime_shift_digest(
        (
            _input(
                "condition_beta",
                "sports",
                probability_before=Decimal("0.300000"),
                probability_after=Decimal("0.460000"),
                liquidity_confirmation_score=Decimal("0.900000"),
                source_reference="wallet:0xabc123",
            ),
            _input(
                "condition_alpha",
                "crypto",
                probability_before=Decimal("0.400000"),
                probability_after=Decimal("0.490000"),
                liquidity_confirmation_score=Decimal("0.200000"),
                source_observed_at=GENERATED_AT - timedelta(hours=2),
                source_config_version="market-probability-source-v1",
            ),
            _input(
                "condition_gamma",
                "crypto",
                probability_before=Decimal("0.500000"),
                probability_after=Decimal("0.510000"),
                liquidity_confirmation_score=Decimal("0.750000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketProbabilityRegimeShiftDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_MARKET_PROBABILITY_REGIME_SHIFT_DIGEST_CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "review_probability_regime_shift_diagnostics"
    assert report.condition_count == Decimal("3")
    assert report.category_count == Decimal("2")
    assert report.shifted_condition_count == Decimal("2")
    assert report.liquidity_confirmed_shift_count == Decimal("1")
    assert report.unconfirmed_shift_count == Decimal("1")
    assert report.stale_source_condition_count == Decimal("1")
    assert report.max_recent_probability_move == Decimal("0.160000")
    assert report.max_source_age_seconds == Decimal("7200.000000")
    assert report.reason_codes == (
        "probability_regime_shift_extreme_move",
        "probability_regime_shift_high_move",
        "probability_regime_shift_liquidity_confirmed",
        "probability_regime_shift_source_stale",
        "probability_regime_shift_unconfirmed_liquidity",
    )
    assert report.reason_code_counts == (
        MarketProbabilityRegimeShiftReasonCodeCount(
            reason_code="probability_regime_shift_extreme_move",
            condition_count=Decimal("1"),
        ),
        MarketProbabilityRegimeShiftReasonCodeCount(
            reason_code="probability_regime_shift_high_move",
            condition_count=Decimal("1"),
        ),
        MarketProbabilityRegimeShiftReasonCodeCount(
            reason_code="probability_regime_shift_liquidity_confirmed",
            condition_count=Decimal("1"),
        ),
        MarketProbabilityRegimeShiftReasonCodeCount(
            reason_code="probability_regime_shift_source_stale",
            condition_count=Decimal("1"),
        ),
        MarketProbabilityRegimeShiftReasonCodeCount(
            reason_code="probability_regime_shift_unconfirmed_liquidity",
            condition_count=Decimal("1"),
        ),
    )
    assert report.category_rollups == (
        MarketProbabilityRegimeShiftCategoryRollup(
            category="crypto",
            condition_count=Decimal("2"),
            shifted_condition_count=Decimal("1"),
            liquidity_confirmed_shift_count=Decimal("0"),
            unconfirmed_shift_count=Decimal("1"),
            stale_source_condition_count=Decimal("1"),
            max_recent_probability_move=Decimal("0.090000"),
            category_status="watch",
            reason_codes=(
                "probability_regime_shift_high_move",
                "probability_regime_shift_source_stale",
                "probability_regime_shift_unconfirmed_liquidity",
            ),
        ),
        MarketProbabilityRegimeShiftCategoryRollup(
            category="sports",
            condition_count=Decimal("1"),
            shifted_condition_count=Decimal("1"),
            liquidity_confirmed_shift_count=Decimal("1"),
            unconfirmed_shift_count=Decimal("0"),
            stale_source_condition_count=Decimal("0"),
            max_recent_probability_move=Decimal("0.160000"),
            category_status="blocked",
            reason_codes=(
                "probability_regime_shift_extreme_move",
                "probability_regime_shift_liquidity_confirmed",
            ),
        ),
    )
    assert report.rows == (
        MarketProbabilityRegimeShiftRow(
            condition_id="condition_alpha",
            category="crypto",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            probability_before=Decimal("0.400000"),
            probability_after=Decimal("0.490000"),
            recent_probability_move=Decimal("0.090000"),
            volatility_bucket="high",
            liquidity_confirmation_score=Decimal("0.200000"),
            liquidity_confirmed=False,
            source_observed_at=GENERATED_AT - timedelta(hours=2),
            source_age_seconds=Decimal("7200.000000"),
            source_freshness_status="stale",
            source_config_version="market-probability-source-v1",
            redacted_source_reference="public-source-alpha",
            regime_shift_status="watch",
            reason_codes=(
                "probability_regime_shift_high_move",
                "probability_regime_shift_source_stale",
                "probability_regime_shift_unconfirmed_liquidity",
            ),
        ),
        MarketProbabilityRegimeShiftRow(
            condition_id="condition_gamma",
            category="crypto",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            probability_before=Decimal("0.500000"),
            probability_after=Decimal("0.510000"),
            recent_probability_move=Decimal("0.010000"),
            volatility_bucket="stable",
            liquidity_confirmation_score=Decimal("0.750000"),
            liquidity_confirmed=False,
            source_observed_at=GENERATED_AT - timedelta(minutes=10),
            source_age_seconds=Decimal("600.000000"),
            source_freshness_status="fresh",
            source_config_version="market-probability-source-v0",
            redacted_source_reference="public-source-alpha",
            regime_shift_status="pass",
            reason_codes=("probability_regime_shift_stable",),
        ),
        MarketProbabilityRegimeShiftRow(
            condition_id="condition_beta",
            category="sports",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            probability_before=Decimal("0.300000"),
            probability_after=Decimal("0.460000"),
            recent_probability_move=Decimal("0.160000"),
            volatility_bucket="extreme",
            liquidity_confirmation_score=Decimal("0.900000"),
            liquidity_confirmed=True,
            source_observed_at=GENERATED_AT - timedelta(minutes=10),
            source_age_seconds=Decimal("600.000000"),
            source_freshness_status="fresh",
            source_config_version="market-probability-source-v0",
            redacted_source_reference="[REDACTED]",
            regime_shift_status="blocked",
            reason_codes=(
                "probability_regime_shift_extreme_move",
                "probability_regime_shift_liquidity_confirmed",
            ),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_digest_passes_empty_and_stable_inputs() -> None:
    empty_report = build_market_probability_regime_shift_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert empty_report.digest_status == "pass"
    assert empty_report.condition_count == Decimal("0")
    assert empty_report.category_count == Decimal("0")
    assert empty_report.reason_codes == ("probability_regime_shift_digest_empty",)
    assert empty_report.max_recent_probability_move is None
    assert empty_report.max_source_age_seconds is None

    stable_report = build_market_probability_regime_shift_digest(
        (
            _input(
                "condition_alpha",
                "crypto",
                probability_before=Decimal("0.400000"),
                probability_after=Decimal("0.410000"),
                liquidity_confirmation_score=Decimal("0.900000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.shifted_condition_count == Decimal("0")
    assert stable_report.reason_codes == ("probability_regime_shift_digest_passed",)
    assert stable_report.rows[0].volatility_bucket == "stable"
    assert stable_report.rows[0].liquidity_confirmed is False
    assert stable_report.rows[0].reason_codes == ("probability_regime_shift_stable",)


def test_stable_probability_with_stale_source_is_watch_not_shifted() -> None:
    report = build_market_probability_regime_shift_digest(
        (
            _input(
                "condition_alpha",
                "crypto",
                probability_before=Decimal("0.400000"),
                probability_after=Decimal("0.410000"),
                liquidity_confirmation_score=Decimal("0.900000"),
                source_observed_at=GENERATED_AT - timedelta(hours=2),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "watch"
    assert report.shifted_condition_count == Decimal("0")
    assert report.liquidity_confirmed_shift_count == Decimal("0")
    assert report.unconfirmed_shift_count == Decimal("0")
    assert report.stale_source_condition_count == Decimal("1")
    assert report.reason_codes == ("probability_regime_shift_source_stale",)
    assert report.category_rollups[0].category_status == "watch"
    assert report.category_rollups[0].reason_codes == (
        "probability_regime_shift_source_stale",
    )
    assert report.rows[0].regime_shift_status == "watch"
    assert report.rows[0].volatility_bucket == "stable"
    assert report.rows[0].liquidity_confirmed is False
    assert report.rows[0].reason_codes == ("probability_regime_shift_source_stale",)


def test_json_payload_uses_decimal_strings_utc_datetimes_and_redaction() -> None:
    report = build_market_probability_regime_shift_digest(
        (
            _input(
                "condition_beta",
                "sports",
                probability_before=Decimal("0.300000"),
                probability_after=Decimal("0.460000"),
                liquidity_confirmation_score=Decimal("0.900000"),
                observed_at=datetime(2026, 7, 2, 10, 0, tzinfo=timezone(timedelta(hours=-2))),
                source_observed_at=datetime(
                    2026,
                    7,
                    2,
                    13,
                    30,
                    tzinfo=timezone(timedelta(hours=2)),
                ),
                source_reference="bearer token abc",
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = market_probability_regime_shift_digest_json_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["condition_count"] == "1"
    assert payload["max_recent_probability_move"] == "0.160000"
    assert payload["max_source_age_seconds"] == "1800.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["source_observed_at"] == "2026-07-02T11:30:00+00:00"
    assert payload["rows"][0]["recent_probability_move"] == "0.160000"
    assert payload["rows"][0]["liquidity_confirmation_score"] == "0.900000"
    assert payload["rows"][0]["redacted_source_reference"] == "[REDACTED]"
    assert payload["category_rollups"][0]["condition_count"] == "1"
    assert payload["reason_code_counts"][0]["condition_count"] == "1"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_payload_includes_matching_derived_validation_digest_and_rejects_tampering() -> None:
    report = build_market_probability_regime_shift_digest(
        (_input("condition_alpha", "crypto"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_probability_regime_shift_digest_json_payload(report)
    digest = payload["derived_validation_digest"]

    assert digest == report.derived_validation_digest
    assert isinstance(digest, str)
    assert len(digest) == 64
    int(digest, 16)

    tampered_payload = dict(payload)
    tampered_payload["condition_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_probability_regime_shift_digest_json_payload(tampered_payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_payload_rejects_unsafe_surfaces_flag_downgrades_and_non_decimal_counts() -> None:
    report = build_market_probability_regime_shift_digest(
        (_input("condition_alpha", "crypto"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    payload = market_probability_regime_shift_digest_json_payload(report)

    downgraded_payload = dict(payload)
    downgraded_payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        market_probability_regime_shift_digest_json_payload(downgraded_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["live_order_url"] = "https://example.invalid"
    with pytest.raises(ValueError, match="unsafe"):
        market_probability_regime_shift_digest_json_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_rows = [dict(row) for row in payload["rows"]]
    unsafe_rows[0]["redacted_source_reference"] = "network database persist wallet"
    unsafe_value_payload["rows"] = unsafe_rows
    with pytest.raises(ValueError, match="unsafe"):
        market_probability_regime_shift_digest_json_payload(unsafe_value_payload)

    non_decimal_payload = dict(payload)
    non_decimal_payload["condition_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived string"):
        market_probability_regime_shift_digest_json_payload(non_decimal_payload)


def test_validation_rejects_floats_nonfinite_dates_duplicates_and_false_flags() -> None:
    with pytest.raises(ValueError, match="probability_before"):
        _input(
            "condition_alpha",
            "crypto",
            probability_before=0.4,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="finite"):
        _input(
            "condition_alpha",
            "crypto",
            probability_after=Decimal("NaN"),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        _input(
            "condition_alpha",
            "crypto",
            observed_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="datetime"):
        build_market_probability_regime_shift_digest(
            (),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="unique condition_id"):
        build_market_probability_regime_shift_digest(
            (
                _input("condition_alpha", "crypto"),
                _input("condition_alpha", "sports"),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only"):
        MarketProbabilityRegimeShiftInput(
            condition_id="condition_alpha",
            category="crypto",
            probability_before=Decimal("0.400000"),
            probability_after=Decimal("0.450000"),
            liquidity_confirmation_score=Decimal("0.900000"),
            observed_at=GENERATED_AT,
            source_observed_at=GENERATED_AT,
            source_config_version="market-probability-source-v0",
            paper_only=False,
        )


def test_public_dataclasses_are_frozen_and_reject_inconsistent_reports() -> None:
    row = MarketProbabilityRegimeShiftRow(
        condition_id="condition_alpha",
        category="crypto",
        observed_at=GENERATED_AT,
        probability_before=Decimal("0.400000"),
        probability_after=Decimal("0.490000"),
        recent_probability_move=Decimal("0.090000"),
        volatility_bucket="high",
        liquidity_confirmation_score=Decimal("0.900000"),
        liquidity_confirmed=True,
        source_observed_at=GENERATED_AT,
        source_age_seconds=Decimal("0"),
        source_freshness_status="fresh",
        source_config_version="market-probability-source-v0",
        redacted_source_reference=None,
        regime_shift_status="watch",
        reason_codes=(
            "probability_regime_shift_high_move",
            "probability_regime_shift_liquidity_confirmed",
        ),
    )

    with pytest.raises(FrozenInstanceError):
        row.category = "sports"  # type: ignore[misc]

    with pytest.raises(ValueError, match="recent_probability_move"):
        replace(row, recent_probability_move=Decimal("0.080000"))

    report = build_market_probability_regime_shift_digest(
        (_input("condition_alpha", "crypto"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="condition_count"):
        replace(report, condition_count=Decimal("9"))


def test_module_has_no_live_trading_network_db_or_file_io_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_probability_regime_shift_digest",
    )
    source = getattr(module, "__loader__").get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    forbidden_imports = {
        "builtins.open",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_name_fragments = (
        "account",
        "advice",
        "auth",
        "cancel",
        "order",
        "private_key",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_imports
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "open"


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(_walk_payload_values(item))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_walk_payload_values(item))
        return tuple(items)
    return (value,)
