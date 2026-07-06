from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_probability_volatility_digest import (
    DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION,
    MarketProbabilityVolatilityDigestConfig,
    MarketProbabilityVolatilityDigestReport,
    MarketProbabilityVolatilityInput,
    MarketProbabilityVolatilityReasonCodeCount,
    MarketProbabilityVolatilityRow,
    build_market_probability_volatility_digest,
    market_probability_volatility_digest_json_payload,
    validate_market_probability_volatility_digest_public_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


def _config(**overrides: object) -> MarketProbabilityVolatilityDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION,
        "recent_probability_move_threshold": Decimal("0.050000"),
        "bid_ask_move_threshold": Decimal("0.080000"),
        "forecast_revision_threshold": Decimal("0.100000"),
        "confidence_move_threshold": Decimal("0.150000"),
        "stale_evidence_seconds_threshold": Decimal("3600.000000"),
    }
    values.update(overrides)
    return MarketProbabilityVolatilityDigestConfig(**values)


def _input(
    market_id: str,
    *,
    probability_before: Decimal = Decimal("0.420000"),
    probability_after: Decimal = Decimal("0.480000"),
    bid_before: Decimal | None = Decimal("0.400000"),
    bid_after: Decimal | None = Decimal("0.300000"),
    ask_before: Decimal | None = Decimal("0.440000"),
    ask_after: Decimal | None = Decimal("0.560000"),
    forecast_probability_before: Decimal | None = Decimal("0.410000"),
    forecast_probability_after: Decimal | None = Decimal("0.540000"),
    confidence_before: Decimal | None = Decimal("0.800000"),
    confidence_after: Decimal | None = Decimal("0.580000"),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    source_config_version: str = "market-probability-source-v0",
) -> MarketProbabilityVolatilityInput:
    return MarketProbabilityVolatilityInput(
        market_id=market_id,
        probability_before=probability_before,
        probability_after=probability_after,
        bid_before=bid_before,
        bid_after=bid_after,
        ask_before=ask_before,
        ask_after=ask_after,
        forecast_probability_before=forecast_probability_before,
        forecast_probability_after=forecast_probability_after,
        confidence_before=confidence_before,
        confidence_after=confidence_after,
        evidence_observed_at=evidence_observed_at,
        source_config_version=source_config_version,
    )


def test_digest_flags_probability_bid_ask_forecast_confidence_and_stale_evidence() -> None:
    report = build_market_probability_volatility_digest(
        (
            _input("market_alpha"),
            _input(
                "market_beta",
                probability_before=Decimal("0.300000"),
                probability_after=Decimal("0.320000"),
                bid_before=Decimal("0.290000"),
                bid_after=Decimal("0.300000"),
                ask_before=Decimal("0.330000"),
                ask_after=Decimal("0.340000"),
                forecast_probability_before=Decimal("0.310000"),
                forecast_probability_after=Decimal("0.330000"),
                confidence_before=Decimal("0.740000"),
                confidence_after=Decimal("0.720000"),
                evidence_observed_at=GENERATED_AT - timedelta(minutes=5),
                source_config_version="market-probability-source-v1",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketProbabilityVolatilityDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_probability_volatility_before_use"
    assert report.market_count == Decimal("2")
    assert report.volatile_market_count == Decimal("1")
    assert report.stale_evidence_market_count == Decimal("1")
    assert report.max_probability_change == Decimal("0.060000")
    assert report.max_bid_ask_move == Decimal("0.120000")
    assert report.max_forecast_revision == Decimal("0.130000")
    assert report.max_confidence_change == Decimal("0.220000")
    assert report.max_evidence_age_seconds == Decimal("7200.000000")
    assert report.source_config_versions == (
        ("market_alpha", "market-probability-source-v0"),
        ("market_beta", "market-probability-source-v1"),
    )
    assert report.reason_codes == (
        "probability_volatility_bid_ask_move_high",
        "probability_volatility_confidence_instability_high",
        "probability_volatility_forecast_revision_high",
        "probability_volatility_recent_probability_change_high",
        "probability_volatility_stale_evidence_present",
    )
    assert report.reason_code_counts == (
        MarketProbabilityVolatilityReasonCodeCount(
            reason_code="probability_volatility_bid_ask_move_high",
            market_count=Decimal("1"),
        ),
        MarketProbabilityVolatilityReasonCodeCount(
            reason_code="probability_volatility_confidence_instability_high",
            market_count=Decimal("1"),
        ),
        MarketProbabilityVolatilityReasonCodeCount(
            reason_code="probability_volatility_forecast_revision_high",
            market_count=Decimal("1"),
        ),
        MarketProbabilityVolatilityReasonCodeCount(
            reason_code="probability_volatility_recent_probability_change_high",
            market_count=Decimal("1"),
        ),
        MarketProbabilityVolatilityReasonCodeCount(
            reason_code="probability_volatility_stale_evidence_present",
            market_count=Decimal("1"),
        ),
    )
    assert report.rows == (
        MarketProbabilityVolatilityRow(
            market_id="market_alpha",
            probability_before=Decimal("0.420000"),
            probability_after=Decimal("0.480000"),
            probability_change=Decimal("0.060000"),
            bid_ask_move=Decimal("0.120000"),
            forecast_revision=Decimal("0.130000"),
            confidence_change=Decimal("0.220000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=2),
            evidence_age_seconds=Decimal("7200.000000"),
            source_config_version="market-probability-source-v0",
            volatility_status="watch",
            reason_codes=(
                "probability_volatility_bid_ask_move_high",
                "probability_volatility_confidence_instability_high",
                "probability_volatility_forecast_revision_high",
                "probability_volatility_recent_probability_change_high",
                "probability_volatility_stale_evidence_present",
            ),
        ),
        MarketProbabilityVolatilityRow(
            market_id="market_beta",
            probability_before=Decimal("0.300000"),
            probability_after=Decimal("0.320000"),
            probability_change=Decimal("0.020000"),
            bid_ask_move=Decimal("0.010000"),
            forecast_revision=Decimal("0.020000"),
            confidence_change=Decimal("0.020000"),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=5),
            evidence_age_seconds=Decimal("300.000000"),
            source_config_version="market-probability-source-v1",
            volatility_status="pass",
            reason_codes=("probability_volatility_market_stable",),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_digest_passes_for_empty_and_stable_inputs() -> None:
    empty_report = build_market_probability_volatility_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert empty_report.digest_status == "pass"
    assert empty_report.market_count == Decimal("0")
    assert empty_report.reason_codes == ("probability_volatility_digest_empty",)
    assert empty_report.max_probability_change is None
    assert empty_report.max_evidence_age_seconds is None

    stable_report = build_market_probability_volatility_digest(
        (
            _input(
                "market_alpha",
                probability_before=Decimal("0.400000"),
                probability_after=Decimal("0.410000"),
                bid_before=None,
                bid_after=None,
                ask_before=None,
                ask_after=None,
                forecast_probability_before=None,
                forecast_probability_after=None,
                confidence_before=None,
                confidence_after=None,
                evidence_observed_at=GENERATED_AT - timedelta(minutes=10),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.volatile_market_count == Decimal("0")
    assert stable_report.stale_evidence_market_count == Decimal("0")
    assert stable_report.reason_codes == ("probability_volatility_digest_passed",)
    assert stable_report.rows[0].reason_codes == ("probability_volatility_market_stable",)
    assert stable_report.rows[0].bid_ask_move is None
    assert stable_report.rows[0].forecast_revision is None
    assert stable_report.rows[0].confidence_change is None


def test_json_payload_helper_emits_decimal_strings_and_iso_datetimes() -> None:
    report = build_market_probability_volatility_digest(
        (_input("market_alpha"),),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = market_probability_volatility_digest_json_payload(report)
    json.dumps(payload, sort_keys=True)

    assert isinstance(payload["max_probability_change"], str)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["evidence_observed_at"] == "2026-07-02T10:00:00+00:00"
    assert payload["rows"][0]["probability_change"] == "0.060000"
    assert payload["rows"][0]["evidence_age_seconds"] == "7200.000000"
    assert payload["reason_code_counts"][0]["market_count"] == "1"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_digest_exposes_tamper_evident_derived_validation_digest() -> None:
    report = build_market_probability_volatility_digest(
        (_input("market_alpha"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert len(report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )

    payload = market_probability_volatility_digest_json_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert validate_market_probability_volatility_digest_public_payload(payload) is True

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["market_count"] = "999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_market_probability_volatility_digest_public_payload(tampered_payload)


def test_public_payload_uses_decimal_strings_and_rejects_unsafe_surfaces() -> None:
    payload = market_probability_volatility_digest_json_payload(
        build_market_probability_volatility_digest(
            (_input("market_alpha"),),
            config=_config(),
            generated_at=GENERATED_AT,
        ),
    )

    _assert_public_payload_has_no_numbers(payload)

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_market_probability_volatility_digest_public_payload(
            missing_digest_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["market_count"] = 1
    with pytest.raises(ValueError, match="Decimal string"):
        validate_market_probability_volatility_digest_public_payload(numeric_payload)

    for unsafe_token in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
    ):
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{unsafe_token}_surface"] = "blocked"
        with pytest.raises(ValueError, match="unsafe"):
            validate_market_probability_volatility_digest_public_payload(
                unsafe_key_payload,
            )

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["source_config_versions"] = [
            ["market_alpha", f"{unsafe_token}_source"]
        ]
        with pytest.raises(ValueError, match="unsafe"):
            validate_market_probability_volatility_digest_public_payload(
                unsafe_value_payload,
            )


def test_digest_normalizes_utc_and_rejects_invalid_sequences() -> None:
    report = build_market_probability_volatility_digest(
        (
            _input(
                "market_alpha",
                evidence_observed_at=datetime(
                    2026,
                    7,
                    2,
                    13,
                    30,
                    tzinfo=timezone(timedelta(hours=2)),
                ),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].evidence_observed_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert report.rows[0].evidence_age_seconds == Decimal("1800.000000")

    with pytest.raises(ValueError, match="generated_at"):
        build_market_probability_volatility_digest(
            (_input("market_alpha"),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_observed_at"):
        build_market_probability_volatility_digest(
            (
                _input(
                    "market_alpha",
                    evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_digest_validates_decimal_inputs_flags_uniqueness_and_reason_counts() -> None:
    with pytest.raises(ValueError, match="config_version"):
        MarketProbabilityVolatilityDigestConfig(
            config_version=_StringSubclass(
                DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="probability_before"):
        _input("market_alpha", probability_before=0.42)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_id"):
        _input("wallet_market")
    with pytest.raises(ValueError, match="source_config_version"):
        _input("market_alpha", source_config_version="auth-source-v0")
    for unsafe_token in ("live", "order", "network", "database", "persist"):
        with pytest.raises(ValueError, match="market_id"):
            _input(f"{unsafe_token}_market")
        with pytest.raises(ValueError, match="source_config_version"):
            _input("market_alpha", source_config_version=f"{unsafe_token}-source-v0")
    with pytest.raises(ValueError, match="unique"):
        build_market_probability_volatility_digest(
            (_input("market_alpha"), _input("market_alpha")),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(_input("market_alpha"), readonly=False)
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketProbabilityVolatilityDigestReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION,
            digest_status="pass",
            recommended_next_step="continue_probability_volatility_monitoring",
            market_count=Decimal("1"),
            volatile_market_count=Decimal("0"),
            stale_evidence_market_count=Decimal("0"),
            max_probability_change=Decimal("0.010000"),
            max_bid_ask_move=None,
            max_forecast_revision=None,
            max_confidence_change=None,
            max_evidence_age_seconds=Decimal("60.000000"),
            rows=(
                MarketProbabilityVolatilityRow(
                    market_id="market_alpha",
                    probability_before=Decimal("0.400000"),
                    probability_after=Decimal("0.410000"),
                    probability_change=Decimal("0.010000"),
                    bid_ask_move=None,
                    forecast_revision=None,
                    confidence_change=None,
                    evidence_observed_at=GENERATED_AT - timedelta(minutes=1),
                    evidence_age_seconds=Decimal("60.000000"),
                    source_config_version="market-probability-source-v0",
                    volatility_status="pass",
                    reason_codes=("probability_volatility_market_stable",),
                ),
            ),
            source_config_versions=(("market_alpha", "market-probability-source-v0"),),
            reason_code_counts=(),
            reason_codes=("probability_volatility_digest_passed",),
        )


def test_digest_rejects_status_string_subclasses() -> None:
    with pytest.raises(ValueError, match="volatility_status"):
        MarketProbabilityVolatilityRow(
            market_id="market_alpha",
            probability_before=Decimal("0.400000"),
            probability_after=Decimal("0.410000"),
            probability_change=Decimal("0.010000"),
            bid_ask_move=None,
            forecast_revision=None,
            confidence_change=None,
            evidence_observed_at=GENERATED_AT - timedelta(minutes=1),
            evidence_age_seconds=Decimal("60.000000"),
            source_config_version="market-probability-source-v0",
            volatility_status=_StringSubclass("pass"),
            reason_codes=("probability_volatility_market_stable",),
        )

    row = MarketProbabilityVolatilityRow(
        market_id="market_alpha",
        probability_before=Decimal("0.400000"),
        probability_after=Decimal("0.410000"),
        probability_change=Decimal("0.010000"),
        bid_ask_move=None,
        forecast_revision=None,
        confidence_change=None,
        evidence_observed_at=GENERATED_AT - timedelta(minutes=1),
        evidence_age_seconds=Decimal("60.000000"),
        source_config_version="market-probability-source-v0",
        volatility_status="pass",
        reason_codes=("probability_volatility_market_stable",),
    )
    with pytest.raises(ValueError, match="digest_status"):
        MarketProbabilityVolatilityDigestReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION,
            digest_status=_StringSubclass("pass"),
            recommended_next_step="continue_probability_volatility_monitoring",
            market_count=Decimal("1"),
            volatile_market_count=Decimal("0"),
            stale_evidence_market_count=Decimal("0"),
            max_probability_change=Decimal("0.010000"),
            max_bid_ask_move=None,
            max_forecast_revision=None,
            max_confidence_change=None,
            max_evidence_age_seconds=Decimal("60.000000"),
            rows=(row,),
            source_config_versions=(("market_alpha", "market-probability-source-v0"),),
            reason_code_counts=(
                MarketProbabilityVolatilityReasonCodeCount(
                    reason_code="probability_volatility_digest_passed",
                    market_count=Decimal("1"),
                ),
            ),
            reason_codes=("probability_volatility_digest_passed",),
        )


def test_digest_dataclasses_are_frozen() -> None:
    values = (
        _config(),
        _input("market_alpha"),
        MarketProbabilityVolatilityReasonCodeCount(
            reason_code="probability_volatility_digest_passed",
            market_count=Decimal("1"),
        ),
        build_market_probability_volatility_digest(
            (_input("market_alpha"),),
            config=_config(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.readonly = False


def test_digest_module_scope_excludes_sensitive_surfaces_and_io() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_probability_volatility_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_literals = (
        "live",
        "auth",
        "wallet",
        "broker",
        "order",
        "signing",
        "network",
        "db",
        "file",
        "advice",
        "investment",
        "trade",
        "buy",
        "sell",
        "position",
        "private_key",
        "secret",
    )
    lowered_source = source.lower()
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "pathlib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(
            child
            for item in value.values()
            for child in _walk_payload_values(item)
        )
    if isinstance(value, list):
        return tuple(child for item in value for child in _walk_payload_values(item))
    return (value,)


def _assert_public_payload_has_no_numbers(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_payload_has_no_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_payload_has_no_numbers(item)
        return
    assert not isinstance(value, (Decimal, float))
    assert type(value) is not int
