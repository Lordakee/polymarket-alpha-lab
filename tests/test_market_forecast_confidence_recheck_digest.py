from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 15, 0, tzinfo=UTC)
FORECAST_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_forecast_confidence_recheck_digest.py",
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_forecast_confidence_recheck_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "market-forecast-confidence-recheck-digest-v0",
        "watch_confidence_threshold": d("0.650000"),
        "blocked_confidence_threshold": d("0.400000"),
        "watch_probability_delta": d("0.080000"),
        "blocked_probability_delta": d("0.200000"),
        "stale_forecast_age_hours": d("24.000000"),
        "expired_forecast_age_hours": d("72.000000"),
        "minimum_evidence_count": d("2"),
    }
    values.update(overrides)
    return module.MarketForecastConfidenceRecheckDigestConfig(**values)


def forecast(**overrides: object):
    module = api()
    values = {
        "market_slug": "market-alpha",
        "forecast_id": "forecast-a",
        "forecasted_at": FORECAST_AT,
        "forecast_probability": d("0.540000"),
        "current_probability": d("0.570000"),
        "confidence_score": d("0.820000"),
        "evidence_count": d("3"),
        "reference": "https://research.example/market-alpha?token=SECRET#private_key",
        "reason_codes": ("initial_forecast",),
    }
    values.update(overrides)
    return module.MarketForecastConfidenceRecheckInput(**values)


def report(*rows: object, cfg: object | None = None):
    module = api()
    return module.build_market_forecast_confidence_recheck_digest(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_digest_summarizes_confidence_recheck_with_deterministic_rows() -> None:
    result = report(
        forecast(
            market_slug="market-pass",
            forecast_id="forecast-pass",
            forecast_probability=d("0.510000"),
            current_probability=d("0.550000"),
            confidence_score=d("0.900000"),
            evidence_count=d("4"),
        ),
        forecast(
            market_slug="market-watch",
            forecast_id="forecast-watch",
            forecasted_at=GENERATED_AT - timedelta(hours=30),
            forecast_probability=d("0.500000"),
            current_probability=d("0.620000"),
            confidence_score=d("0.600000"),
            evidence_count=d("2"),
        ),
        forecast(
            market_slug="market-blocked",
            forecast_id="forecast-blocked",
            forecasted_at=GENERATED_AT - timedelta(hours=90),
            forecast_probability=d("0.200000"),
            current_probability=d("0.500000"),
            confidence_score=d("0.350000"),
            evidence_count=d("1"),
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "market-forecast-confidence-recheck-digest-v0"
    assert result.forecast_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.average_confidence_score == d("0.616667")
    assert result.max_probability_delta == d("0.300000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "market_forecast_confidence_recheck_blocked",
        "confidence_recheck_passed",
        "low_confidence_watch",
        "low_confidence_blocked",
        "probability_delta_watch",
        "probability_delta_blocked",
        "forecast_stale",
        "forecast_expired",
        "evidence_count_below_minimum",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.forecast_id for row in result.rows) == (
        "forecast-blocked",
        "forecast-watch",
        "forecast-pass",
    )
    blocked, watched, passed = result.rows
    assert blocked.recheck_status == "blocked"
    assert blocked.forecast_age_hours == d("90.000000")
    assert blocked.probability_delta == d("0.300000")
    assert blocked.reason_codes == (
        "low_confidence_blocked",
        "probability_delta_blocked",
        "forecast_expired",
        "evidence_count_below_minimum",
    )
    assert watched.recheck_status == "watch"
    assert watched.reason_codes == (
        "low_confidence_watch",
        "probability_delta_watch",
        "forecast_stale",
    )
    assert passed.recheck_status == "pass"
    assert passed.reason_codes == ("confidence_recheck_passed",)


def test_empty_digest_is_report_only_readonly_and_decimal_zeroes() -> None:
    result = report()

    assert result.forecast_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.average_confidence_score == d("0.000000")
    assert result.max_probability_delta == d("0.000000")
    assert result.status == "watch"
    assert result.reason_codes == ("market_forecast_confidence_recheck_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_validation_rejects_floats_nonfinite_datetimes_and_false_flags() -> None:
    module = api()
    result = report(forecast())

    with pytest.raises(FrozenInstanceError):
        result.rows[0].confidence_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        forecast(forecast_probability=0.5)
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        forecast(forecast_probability=1)
    with pytest.raises(ValueError, match="evidence_count must be a Decimal"):
        forecast(evidence_count=True)
    with pytest.raises(ValueError, match="confidence_score must be finite"):
        forecast(confidence_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="evidence_count must be an integer Decimal"):
        forecast(evidence_count=d("1.100000"))
    with pytest.raises(ValueError, match="forecasted_at must be timezone-aware"):
        forecast(forecasted_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="forecasted_at must be timezone-aware"):
        forecast(forecasted_at=datetime(2026, 7, 2, 12, 0, tzinfo=NoneOffsetTz()))
    with pytest.raises(ValueError, match="forecasted_at must be a datetime"):
        forecast(forecasted_at=DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="config must be"):
        module.build_market_forecast_confidence_recheck_digest(
            (forecast(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(forecast(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_utc_normalization_sensitive_reference_redaction_and_no_float_payload() -> None:
    module = api()
    raw = forecast(
        forecasted_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
        reference="https://research.example/path?password=SECRET&ok=1#credential",
    )
    result = module.build_market_forecast_confidence_recheck_digest(
        (raw,),
        config=config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    row = result.rows[0]
    assert result.generated_at == GENERATED_AT
    assert row.forecasted_at == FORECAST_AT
    assert raw.reference == "https://research.example/path"
    assert row.redacted_reference == "https://research.example/path"
    payload = module.market_forecast_confidence_recheck_digest_payload(result)
    payload_text = repr(payload)
    assert "SECRET" not in payload_text
    assert "password" not in payload_text.lower()
    assert "credential" not in payload_text.lower()
    assert payload["generated_at"] == "2026-07-02T15:00:00Z"
    assert payload["rows"][0]["redacted_reference"] == "https://research.example/path"
    assert not any(type(value) is float for value in _walk_payload(payload))
    assert not any(type(value) is int for value in _walk_payload(payload))
    assert isinstance(payload["forecast_count"], str)
    assert isinstance(payload["rows"][0]["evidence_count"], str)
    assert isinstance(payload["rows"][0]["forecast_age_hours"], str)


def test_duplicate_future_and_inconsistent_reports_are_rejected() -> None:
    module = api()
    valid = report(forecast(forecast_id="forecast-a"), forecast(forecast_id="forecast-b"))

    with pytest.raises(ValueError, match="forecasts must be unique"):
        report(forecast(forecast_id="forecast-a"), forecast(forecast_id="forecast-a"))
    with pytest.raises(ValueError, match="forecasted_at must not be after generated_at"):
        report(forecast(forecasted_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="forecast_count must match rows"):
        module.MarketForecastConfidenceRecheckDigestReport(
            generated_at=valid.generated_at,
            config_version=valid.config_version,
            forecast_count=d("9"),
            pass_count=valid.pass_count,
            watch_count=valid.watch_count,
            blocked_count=valid.blocked_count,
            average_confidence_score=valid.average_confidence_score,
            max_probability_delta=valid.max_probability_delta,
            status=valid.status,
            reason_codes=valid.reason_codes,
            rows=valid.rows,
        )


def test_derived_validation_digest_revalidates_rows_report_and_payload() -> None:
    module = api()
    result = report(
        forecast(
            market_slug="market-digest",
            forecast_id="forecast-digest",
            current_probability=d("0.690000"),
            confidence_score=d("0.610000"),
        ),
    )

    assert len(result.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in result.derived_validation_digest)
    payload = module.market_forecast_confidence_recheck_digest_payload(result)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert isinstance(payload["forecast_count"], str)
    assert isinstance(payload["rows"][0]["probability_delta"], str)

    payload_copy = dict(payload)
    assert module.market_forecast_confidence_recheck_digest_payload(payload_copy) == payload_copy

    tampered_report = report(forecast(forecast_id="forecast-count-tamper"))
    object.__setattr__(tampered_report, "forecast_count", d("2"))
    with pytest.raises(ValueError, match="derived_validation_digest|forecast_count"):
        module.market_forecast_confidence_recheck_digest_payload(tampered_report)

    tampered_row_report = report(forecast(forecast_id="forecast-row-tamper"))
    object.__setattr__(tampered_row_report.rows[0], "confidence_score", d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest|average_confidence_score"):
        module.market_forecast_confidence_recheck_digest_payload(tampered_row_report)

    tampered_payload = dict(payload)
    tampered_payload["forecast_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest|forecast_count"):
        module.market_forecast_confidence_recheck_digest_payload(tampered_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.market_forecast_confidence_recheck_digest_payload(missing_digest)


def test_unsafe_public_surface_terms_are_rejected() -> None:
    module = api()
    unsafe_terms = (
        "li" + "ve-market",
        "a" + "uth-check",
        "wal" + "let-signal",
        "place-" + "or" + "der",
        "net" + "work-probe",
        "data" + "base-sink",
        "per" + "sist-cache",
    )

    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            forecast(market_slug=unsafe_term)
        with pytest.raises(ValueError, match="unsafe"):
            forecast(reason_codes=(unsafe_term,))

    payload = module.market_forecast_confidence_recheck_digest_payload(report(forecast()))
    unsafe_payload = dict(payload)
    unsafe_payload["rows"] = (
        {
            **unsafe_payload["rows"][0],
            "market_slug": "li" + "ve-market",
        },
    )
    with pytest.raises(ValueError, match="unsafe|derived_validation_digest"):
        module.market_forecast_confidence_recheck_digest_payload(unsafe_payload)


def test_public_numeric_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "MarketForecastConfidenceRecheckDigestConfig": {
            "watch_confidence_threshold",
            "blocked_confidence_threshold",
            "watch_probability_delta",
            "blocked_probability_delta",
            "stale_forecast_age_hours",
            "expired_forecast_age_hours",
            "minimum_evidence_count",
        },
        "MarketForecastConfidenceRecheckInput": {
            "forecast_probability",
            "current_probability",
            "confidence_score",
            "evidence_count",
        },
        "MarketForecastConfidenceRecheckRow": {
            "forecast_probability",
            "current_probability",
            "confidence_score",
            "evidence_count",
            "probability_delta",
            "forecast_age_hours",
        },
        "MarketForecastConfidenceRecheckDigestReport": {
            "forecast_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "average_confidence_score",
            "max_probability_delta",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


class NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


class DatetimeSubclass(datetime):
    pass


def test_module_scope_has_no_live_io_or_sensitive_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "account",
        "order",
        "submit",
        "cancel",
        "recommend",
        "advice",
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "open(",
        ".read(",
        ".write(",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk_payload(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_payload(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_payload(item)
    else:
        yield value
