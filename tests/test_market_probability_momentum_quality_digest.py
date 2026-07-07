from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_probability_momentum_quality_digest import (
    MarketProbabilityMomentumQualityConfig,
    MarketProbabilityMomentumQualityInput,
    MarketProbabilityMomentumQualityReport,
    build_market_probability_momentum_quality_digest,
    market_probability_momentum_quality_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def observation(
    market_id: str = "market-a",
    category: str = "politics",
    *,
    start_probability: Decimal = Decimal("0.42"),
    end_probability: Decimal = Decimal("0.47"),
    previous_probability: Decimal | None = Decimal("0.41"),
    source_confirmed: bool = True,
    forecast_probabilities: tuple[Decimal, ...] = (Decimal("0.46"), Decimal("0.48")),
    last_context_at: datetime | None = None,
    observed_at: datetime | None = None,
    reason_codes: tuple[str, ...] = ("source_confirmed_move",),
) -> MarketProbabilityMomentumQualityInput:
    if last_context_at is None:
        last_context_at = GENERATED_AT - timedelta(hours=2)
    if observed_at is None:
        observed_at = GENERATED_AT - timedelta(minutes=5)
    return MarketProbabilityMomentumQualityInput(
        market_id=market_id,
        category=category,
        observed_at=observed_at,
        start_probability=start_probability,
        end_probability=end_probability,
        previous_probability=previous_probability,
        source_confirmed=source_confirmed,
        forecast_probabilities=forecast_probabilities,
        last_context_at=last_context_at,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_empty_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )

    assert report == MarketProbabilityMomentumQualityReport(
        generated_at=GENERATED_AT,
        config_version="market_probability_momentum_quality_v1",
        row_count=Decimal("0"),
        market_count=Decimal("0"),
        category_count=Decimal("0"),
        high_reversal_risk_count=Decimal("0"),
        unconfirmed_move_count=Decimal("0"),
        high_dispersion_count=Decimal("0"),
        stale_context_count=Decimal("0"),
        rows=(),
        category_rollups=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_stable_confirmed_momentum_has_low_quality_pressure() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )

    row = report.rows[0]
    assert row.market_id == "market-a"
    assert row.category == "politics"
    assert row.momentum_size == Decimal("0.0500")
    assert row.reversal_size == Decimal("0.0000")
    assert row.reversal_risk_score == Decimal("0.0000")
    assert row.source_confirmed_move is True
    assert row.forecast_dispersion == Decimal("0.0200")
    assert row.stale_context_pressure == Decimal("0.0000")
    assert row.quality_status == "stable_confirmed"
    assert row.reason_codes == ("source_confirmed_move", "stable_confirmed")
    assert report.category_rollups[0].average_momentum_size == Decimal("0.0500")


def test_reversal_risk_flags_direction_flip_against_previous_move() -> None:
    report = build_market_probability_momentum_quality_digest(
        (
            observation(
                start_probability=Decimal("0.55"),
                end_probability=Decimal("0.45"),
                previous_probability=Decimal("0.40"),
                reason_codes=("manual_review",),
            ),
        ),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(reversal_risk_threshold=Decimal("0.25")),
    )

    row = report.rows[0]
    assert row.momentum_size == Decimal("-0.1000")
    assert row.reversal_size == Decimal("0.1000")
    assert row.reversal_risk_score == Decimal("0.6667")
    assert row.quality_status == "reversal_risk"
    assert "reversal_risk" in row.reason_codes
    assert report.high_reversal_risk_count == Decimal("1")


def test_unconfirmed_move_flags_large_move_without_source_confirmation() -> None:
    report = build_market_probability_momentum_quality_digest(
        (
            observation(
                start_probability=Decimal("0.30"),
                end_probability=Decimal("0.40"),
                previous_probability=Decimal("0.29"),
                source_confirmed=False,
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(unconfirmed_move_threshold=Decimal("0.05")),
    )

    row = report.rows[0]
    assert row.source_confirmed_move is False
    assert row.quality_status == "unconfirmed_move"
    assert row.reason_codes == ("unconfirmed_move",)
    assert report.unconfirmed_move_count == Decimal("1")


def test_high_dispersion_flags_forecast_disagreement() -> None:
    report = build_market_probability_momentum_quality_digest(
        (
            observation(
                forecast_probabilities=(Decimal("0.20"), Decimal("0.80"), Decimal("0.50")),
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(dispersion_threshold=Decimal("0.40")),
    )

    row = report.rows[0]
    assert row.forecast_count == Decimal("3")
    assert row.forecast_dispersion == Decimal("0.6000")
    assert row.quality_status == "high_dispersion"
    assert row.reason_codes == ("high_dispersion",)
    assert report.high_dispersion_count == Decimal("1")


def test_stale_context_pressure_uses_utc_normalized_datetimes() -> None:
    est = timezone(timedelta(hours=-5))
    stale_local_time = (GENERATED_AT - timedelta(hours=30)).astimezone(est)
    report = build_market_probability_momentum_quality_digest(
        (
            observation(
                observed_at := "market-a",
                last_context_at=stale_local_time,
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(
            stale_context_after_hours=Decimal("24"),
        ),
    )

    row = report.rows[0]
    assert row.market_id == observed_at
    assert report.generated_at == GENERATED_AT
    assert row.last_context_at == GENERATED_AT - timedelta(hours=30)
    assert row.context_age_hours == Decimal("30.0000")
    assert row.stale_context_pressure == Decimal("1.0000")
    assert row.quality_status == "stale_context"
    assert report.stale_context_count == Decimal("1")


def test_rejects_naive_none_offset_and_datetime_subclasses() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_probability_momentum_quality_digest(
            (),
            generated_at=datetime(2026, 7, 2, 12, 0),
            config=MarketProbabilityMomentumQualityConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        observation(observed_at=DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))


def test_rows_rollups_and_reason_codes_are_deterministically_sorted() -> None:
    report = build_market_probability_momentum_quality_digest(
        (
            observation(
                "z-market",
                "sports",
                start_probability=Decimal("0.50"),
                end_probability=Decimal("0.70"),
                source_confirmed=False,
                reason_codes=("zeta", "alpha"),
            ),
            observation(
                "a-market",
                "politics",
                start_probability=Decimal("0.70"),
                end_probability=Decimal("0.60"),
                previous_probability=Decimal("0.55"),
                source_confirmed=False,
                forecast_probabilities=(Decimal("0.10"), Decimal("0.90")),
                last_context_at=GENERATED_AT - timedelta(hours=40),
                reason_codes=("alpha",),
            ),
            observation(
                "m-market",
                "politics",
                start_probability=Decimal("0.40"),
                end_probability=Decimal("0.45"),
                previous_probability=Decimal("0.39"),
                reason_codes=("beta",),
            ),
        ),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(
            dispersion_threshold=Decimal("0.50"),
            stale_context_after_hours=Decimal("24"),
            unconfirmed_move_threshold=Decimal("0.05"),
        ),
    )

    assert [row.market_id for row in report.rows] == ["a-market", "m-market", "z-market"]
    assert [rollup.category for rollup in report.category_rollups] == ["politics", "sports"]
    assert report.reason_code_counts == (
        ("alpha", Decimal("2")),
        ("beta", Decimal("1")),
        ("high_dispersion", Decimal("1")),
        ("reversal_risk", Decimal("1")),
        ("source_confirmed_move", Decimal("1")),
        ("stable_confirmed", Decimal("1")),
        ("stale_context", Decimal("1")),
        ("unconfirmed_move", Decimal("2")),
        ("zeta", Decimal("1")),
    )


def test_payload_helper_uses_decimal_strings_and_no_float_values() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )

    payload = market_probability_momentum_quality_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["momentum_size"] == "0.0500"
    assert payload["row_count"] == "1.0000"
    assert payload["reason_code_counts"][0][1] == "1.0000"
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded


def test_payload_rejects_unsafe_public_surface_fields_and_values() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )

    payload = market_probability_momentum_quality_payload(report)
    unsafe_payloads = (
        {**payload, "live_mode": True},
        {**payload, "auth_ref": "redacted"},
        {**payload, "wallet_ref": "redacted"},
        {**payload, "order_ref": "redacted"},
        {**payload, "network_ref": "redacted"},
        {**payload, "database_ref": "redacted"},
        {**payload, "persist_ref": "redacted"},
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "quality_status": "connect_wallet",
                },
            ],
        },
    )

    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe public"):
            market_probability_momentum_quality_payload(unsafe_payload)


def test_payload_revalidates_tampered_report_and_public_payload_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_probability_momentum_quality_payload(tampered_payload)

    missing_flag_payload = dict(payload)
    missing_flag_payload.pop("readonly")
    with pytest.raises(ValueError, match="readonly"):
        market_probability_momentum_quality_payload(missing_flag_payload)

    object.__setattr__(report.rows[0], "momentum_size", Decimal("0.9900"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_probability_momentum_quality_payload(report)


def test_payload_rejects_missing_required_fields_even_with_recomputed_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)
    missing_rows_payload = dict(payload)
    missing_rows_payload.pop("rows")

    with pytest.raises(ValueError, match="rows"):
        market_probability_momentum_quality_payload(
            _with_recomputed_digest(missing_rows_payload),
        )


def test_payload_rejects_noncanonical_numeric_strings_even_with_recomputed_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)
    bad_count_payload = {
        **payload,
        "row_count": "1",
    }

    with pytest.raises(ValueError, match="row_count"):
        market_probability_momentum_quality_payload(
            _with_recomputed_digest(bad_count_payload),
        )


def test_payload_rejects_counts_that_do_not_match_rows_even_with_recomputed_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)
    bad_count_payload = {
        **payload,
        "row_count": "2.0000",
    }

    with pytest.raises(ValueError, match="row_count"):
        market_probability_momentum_quality_payload(
            _with_recomputed_digest(bad_count_payload),
        )


def test_payload_rejects_reason_counts_that_do_not_match_rows_even_with_recomputed_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)
    bad_reason_count_payload = {
        **payload,
        "reason_code_counts": [["stable_confirmed", "1.0000"]],
    }

    with pytest.raises(ValueError, match="reason_code_counts"):
        market_probability_momentum_quality_payload(
            _with_recomputed_digest(bad_reason_count_payload),
        )


def test_payload_rejects_rollups_that_do_not_match_rows_even_with_recomputed_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)
    bad_rollup = dict(payload["category_rollups"][0])
    bad_rollup["average_momentum_size"] = "0.9900"
    bad_rollup_payload = {
        **payload,
        "category_rollups": [bad_rollup],
    }

    with pytest.raises(ValueError, match="category_rollups"):
        market_probability_momentum_quality_payload(
            _with_recomputed_digest(bad_rollup_payload),
        )


def test_payload_rejects_unknown_row_status_even_with_recomputed_digest() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)
    bad_row = dict(payload["rows"][0])
    bad_row["quality_status"] = "manual_review"
    bad_status_payload = {
        **payload,
        "rows": [bad_row],
    }

    with pytest.raises(ValueError, match="quality_status"):
        market_probability_momentum_quality_payload(
            _with_recomputed_digest(bad_status_payload),
        )


def test_payload_rejects_probability_strings_outside_unit_interval() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )
    payload = market_probability_momentum_quality_payload(report)
    bad_row = dict(payload["rows"][0])
    bad_row["end_probability"] = "1.2000"
    bad_probability_payload = {
        **payload,
        "rows": [bad_row],
    }

    with pytest.raises(ValueError, match="end_probability"):
        market_probability_momentum_quality_payload(
            _with_recomputed_digest(bad_probability_payload),
        )


def test_report_rejects_rollups_that_do_not_match_rows() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )

    with pytest.raises(ValueError, match="category_rollups"):
        dataclasses.replace(
            report,
            category_rollups=(),
            derived_validation_digest="",
        )


def test_report_rejects_reason_code_counts_that_do_not_match_rows() -> None:
    report = build_market_probability_momentum_quality_digest(
        (observation(),),
        generated_at=GENERATED_AT,
        config=MarketProbabilityMomentumQualityConfig(),
    )

    with pytest.raises(ValueError, match="reason_code_counts"):
        dataclasses.replace(
            report,
            reason_code_counts=(),
            derived_validation_digest="",
        )


def test_validation_rejects_invalid_decimals_datetimes_counts_and_flags() -> None:
    with pytest.raises(ValueError, match="start_probability"):
        observation(start_probability=Decimal("1.1"))
    with pytest.raises(ValueError, match="stale_context_after_hours"):
        MarketProbabilityMomentumQualityConfig(stale_context_after_hours=24)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_count"):
        dataclasses.replace(
            build_market_probability_momentum_quality_digest(
                (observation(),),
                generated_at=GENERATED_AT,
                config=MarketProbabilityMomentumQualityConfig(),
            ).rows[0],
            forecast_count=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="forecast_probabilities"):
        observation(forecast_probabilities=(Decimal("0.20"), Decimal("NaN")))
    with pytest.raises(ValueError, match="observed_at"):
        dataclasses.replace(observation(), observed_at="2026-07-02")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_context_after_hours"):
        MarketProbabilityMomentumQualityConfig(stale_context_after_hours=Decimal("0"))
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(MarketProbabilityMomentumQualityConfig(), paper_only=False)


def test_public_dataclasses_are_frozen() -> None:
    config = MarketProbabilityMomentumQualityConfig()
    row = observation()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.market_id = "changed"  # type: ignore[misc]


def test_public_dataclasses_reject_subclasses_and_build_inputs_are_exact_type() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(MarketProbabilityMomentumQualityConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(MarketProbabilityMomentumQualityInput):
            pass


def test_static_module_has_no_forbidden_live_surface_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_probability_momentum_quality_digest.py",
    ).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "wallet",
        "broker",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "auth",
        "private_key",
        "advice",
    )

    assert not [term for term in forbidden_terms if term in source.lower()]

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)


def _with_recomputed_digest(payload: dict[str, object]) -> dict[str, object]:
    redigested = dict(payload)
    digest_payload = {
        key: value
        for key, value in redigested.items()
        if key != "derived_validation_digest"
    }
    redigested["derived_validation_digest"] = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8",
        ),
    ).hexdigest()
    return redigested
