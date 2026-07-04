from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import get_args, get_origin, get_type_hints

import pytest

from polymarket_alpha_lab.strategy_team_forecast_calibration_memory_digest import (
    DEFAULT_STRATEGY_TEAM_FORECAST_CALIBRATION_MEMORY_DIGEST_CONFIG_VERSION,
    StrategyTeamForecastCalibrationMemoryDigestConfig,
    StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount,
    StrategyTeamForecastCalibrationMemoryDigestReport,
    StrategyTeamForecastCalibrationMemoryDigestRollup,
    StrategyTeamForecastCalibrationMemoryDigestRow,
    StrategyTeamForecastCalibrationMemoryDigestSource,
    build_strategy_team_forecast_calibration_memory_digest,
    strategy_team_forecast_calibration_memory_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_forecast_calibration_memory_digest.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _source(
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    forecast_id: str = "forecast-btc-july-4",
    forecast_probability: Decimal = d("0.700000"),
    observed_at: datetime = GENERATED_AT - timedelta(days=2),
    resolved_at: datetime | None = GENERATED_AT - timedelta(hours=2),
    resolved_outcome: Decimal | None = d("1.000000"),
    forecast_reference: str = "memory://team/btc?token=paper-secret",
    reason_codes: tuple[str, ...] = ("source_forecast_calibration_observed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyTeamForecastCalibrationMemoryDigestSource:
    return StrategyTeamForecastCalibrationMemoryDigestSource(
        team_id=team_id,
        category_id=category_id,
        forecast_id=forecast_id,
        forecast_probability=forecast_probability,
        observed_at=observed_at,
        resolved_at=resolved_at,
        resolved_outcome=resolved_outcome,
        forecast_reference=forecast_reference,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _pending_source(
    *,
    forecast_id: str,
    observed_at: datetime = GENERATED_AT - timedelta(hours=3),
    **kwargs: object,
) -> StrategyTeamForecastCalibrationMemoryDigestSource:
    return _source(
        forecast_id=forecast_id,
        observed_at=observed_at,
        resolved_at=None,
        resolved_outcome=None,
        **kwargs,
    )


def _build_report(
    *sources: StrategyTeamForecastCalibrationMemoryDigestSource,
    config: StrategyTeamForecastCalibrationMemoryDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyTeamForecastCalibrationMemoryDigestReport:
    return build_strategy_team_forecast_calibration_memory_digest(
        sources,
        config=config or StrategyTeamForecastCalibrationMemoryDigestConfig(),
        generated_at=generated_at,
    )


def test_empty_input_builds_blocked_paper_only_digest() -> None:
    report = _build_report()

    assert report.config_version == (
        DEFAULT_STRATEGY_TEAM_FORECAST_CALIBRATION_MEMORY_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.next_review_step == "pause_forecast_calibration_memory_use"
    assert report.source_count == d("0")
    assert report.row_count == d("0")
    assert report.resolved_count == d("0")
    assert report.pending_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.high_brier_count == d("0")
    assert report.stale_pending_count == d("0")
    assert report.insufficient_resolved_count == d("0")
    assert report.mean_brier_score is None
    assert report.mean_signed_error is None
    assert report.rows == ()
    assert report.rollups == ()
    assert report.reason_codes == (
        "strategy_team_forecast_calibration_memory_digest_empty_sources",
    )
    assert report.reason_code_counts == (
        StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount(
            reason_code=(
                "strategy_team_forecast_calibration_memory_digest_empty_sources"
            ),
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_resolved_and_pending_observations_build_team_category_readiness() -> None:
    report = _build_report(
        _source(
            forecast_id="forecast-crypto-win",
            forecast_probability=d("0.700000"),
            resolved_outcome=d("1.000000"),
            forecast_reference="memory://team/btc/win?token=paper-secret",
        ),
        _source(
            forecast_id="forecast-crypto-loss",
            forecast_probability=d("0.200000"),
            resolved_outcome=d("0.000000"),
            forecast_reference="paper://btc/loss#public-note",
        ),
        _pending_source(
            forecast_id="forecast-crypto-pending",
            forecast_probability=d("0.550000"),
            forecast_reference="https://example.invalid/btc-pending",
        ),
        _source(
            team_id="politics",
            category_id="politics",
            forecast_id="forecast-politics-high-error",
            forecast_probability=d("0.950000"),
            resolved_outcome=d("0.000000"),
            forecast_reference="paper://politics/high-error?token=paper-secret",
        ),
        _pending_source(
            team_id="politics",
            category_id="politics",
            forecast_id="forecast-politics-stale",
            forecast_probability=d("0.500000"),
            observed_at=GENERATED_AT - timedelta(days=10),
            forecast_reference="paper://politics/stale#public-note",
        ),
    )

    assert report.digest_status == "blocked"
    assert report.next_review_step == "pause_forecast_calibration_memory_use"
    assert report.source_count == d("5")
    assert report.row_count == d("2")
    assert report.resolved_count == d("3")
    assert report.pending_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("1")
    assert report.high_brier_count == d("1")
    assert report.stale_pending_count == d("1")
    assert report.insufficient_resolved_count == d("1")
    assert report.mean_brier_score == d("0.344167")
    assert report.mean_signed_error == d("0.283333")
    assert report.reason_codes == (
        "strategy_team_forecast_calibration_memory_digest_insufficient_resolved_observations",
        "strategy_team_forecast_calibration_memory_digest_high_brier_score",
        "strategy_team_forecast_calibration_memory_digest_directional_bias",
        "strategy_team_forecast_calibration_memory_digest_stale_pending_observations",
    )

    assert tuple((row.team_id, row.category_id) for row in report.rows) == (
        ("crypto_btc", "finance.crypto.btc"),
        ("politics", "politics"),
    )

    crypto, politics = report.rows
    assert crypto.readiness_status == "pass"
    assert crypto.observation_count == d("3")
    assert crypto.resolved_count == d("2")
    assert crypto.pending_count == d("1")
    assert crypto.pending_ratio == d("0.333333")
    assert crypto.high_brier_count == d("0")
    assert crypto.stale_pending_count == d("0")
    assert crypto.insufficient_resolved_count == d("0")
    assert crypto.mean_brier_score == d("0.065000")
    assert crypto.mean_signed_error == d("-0.050000")
    assert crypto.redacted_forecast_references == ("[REDACTED_REFERENCE]",)
    assert crypto.reason_codes == (
        "strategy_team_forecast_calibration_memory_digest_passed",
    )

    assert politics.readiness_status == "blocked"
    assert politics.observation_count == d("2")
    assert politics.resolved_count == d("1")
    assert politics.pending_count == d("1")
    assert politics.pending_ratio == d("0.500000")
    assert politics.high_brier_count == d("1")
    assert politics.stale_pending_count == d("1")
    assert politics.insufficient_resolved_count == d("1")
    assert politics.mean_brier_score == d("0.902500")
    assert politics.mean_signed_error == d("0.950000")
    assert politics.reason_codes == report.reason_codes

    assert tuple((rollup.rollup_kind, rollup.rollup_key) for rollup in report.rollups) == (
        ("category", "finance.crypto.btc"),
        ("category", "politics"),
        ("team", "crypto_btc"),
        ("team", "politics"),
    )
    assert tuple(rollup.readiness_status for rollup in report.rollups) == (
        "pass",
        "blocked",
        "pass",
        "blocked",
    )


def test_reason_counts_and_rows_are_deterministically_sorted() -> None:
    report = _build_report(
        _source(
            team_id="politics",
            category_id="politics",
            forecast_id="forecast-politics-high-error",
            forecast_probability=d("0.950000"),
            resolved_outcome=d("0.000000"),
        ),
        _pending_source(
            team_id="crypto_eth",
            category_id="finance.crypto.eth",
            forecast_id="forecast-eth-pending",
            observed_at=GENERATED_AT - timedelta(days=9),
        ),
        _source(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            forecast_id="forecast-btc-win",
            forecast_probability=d("0.600000"),
            resolved_outcome=d("1.000000"),
        ),
        _source(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            forecast_id="forecast-btc-loss",
            forecast_probability=d("0.300000"),
            resolved_outcome=d("0.000000"),
        ),
    )

    assert tuple((row.team_id, row.category_id) for row in report.rows) == (
        ("crypto_btc", "finance.crypto.btc"),
        ("crypto_eth", "finance.crypto.eth"),
        ("politics", "politics"),
    )
    assert tuple(count.reason_code for count in report.reason_code_counts) == (
        "strategy_team_forecast_calibration_memory_digest_insufficient_resolved_observations",
        "strategy_team_forecast_calibration_memory_digest_high_brier_score",
        "strategy_team_forecast_calibration_memory_digest_directional_bias",
        "strategy_team_forecast_calibration_memory_digest_stale_pending_observations",
    )
    assert tuple(count.count for count in report.reason_code_counts) == (
        d("2"),
        d("1"),
        d("1"),
        d("1"),
    )


def test_payload_uses_decimal_strings_rejects_ints_and_redacts_references() -> None:
    source = _source(forecast_reference="paper://btc?token=paper-secret")
    report = _build_report(
        source,
        _source(
            forecast_id="forecast-btc-loss",
            forecast_probability=d("0.000000"),
            resolved_outcome=d("0"),
        ),
    )
    payload = strategy_team_forecast_calibration_memory_digest_payload(report)
    source_payload = strategy_team_forecast_calibration_memory_digest_payload(source)

    assert "paper-secret" not in repr(source)
    assert "paper-secret" not in repr(report)
    assert "paper-secret" not in repr(payload)
    assert "forecast_reference" not in source_payload
    assert source_payload["redacted_forecast_reference"] == "[REDACTED_REFERENCE]"
    assert payload["source_count"] == "2"
    assert payload["resolved_count"] == "2"
    assert payload["mean_brier_score"] == "0.045000"
    assert payload["rows"][0]["observation_count"] == "2"
    assert payload["rows"][0]["redacted_forecast_references"] == [
        "[REDACTED_REFERENCE]",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_int(payload)

    with pytest.raises(ValueError, match="float"):
        _source(forecast_probability=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="integer"):
        strategy_team_forecast_calibration_memory_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "source_count": 1,
            }
        )
    with pytest.raises(ValueError, match="paper_only"):
        strategy_team_forecast_calibration_memory_digest_payload(
            {
                "paper_only": False,
                "report_only": True,
                "readonly": True,
            }
        )


def test_validation_requires_flags_utc_and_exact_datetime_type() -> None:
    normalized = _source(
        observed_at=datetime(2026, 7, 4, 7, 0, tzinfo=EASTERN),
        resolved_at=datetime(2026, 7, 4, 7, 30, tzinfo=EASTERN),
    )

    assert normalized.observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert normalized.resolved_at == datetime(2026, 7, 4, 11, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _source(observed_at=datetime(2026, 7, 4, 11, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _source(observed_at=datetime(2026, 7, 4, 11, 0, tzinfo=NoOffsetTZ()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        _source(observed_at=DateTimeSubclass(2026, 7, 4, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="resolved_at and resolved_outcome"):
        _source(resolved_at=None, resolved_outcome=d("1.000000"))
    with pytest.raises(ValueError, match="resolved_at must not be before observed_at"):
        _source(resolved_at=GENERATED_AT - timedelta(days=3))
    with pytest.raises(ValueError, match="generated_at"):
        _build_report(_source(), generated_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="config"):
        build_strategy_team_forecast_calibration_memory_digest(
            (_source(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source"):
        build_strategy_team_forecast_calibration_memory_digest(
            (object(),),
            config=StrategyTeamForecastCalibrationMemoryDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="readonly"):
        _source(readonly=False)
    with pytest.raises(ValueError, match="forecast_id"):
        _source(forecast_id="duplicate")
        build_strategy_team_forecast_calibration_memory_digest(
            (_source(forecast_id="duplicate"), _source(forecast_id="duplicate")),
            config=StrategyTeamForecastCalibrationMemoryDigestConfig(),
            generated_at=GENERATED_AT,
        )


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    source = _source()
    report = _build_report(source, _source(forecast_id="forecast-btc-loss", resolved_outcome=d("0")))

    module_types = (
        StrategyTeamForecastCalibrationMemoryDigestConfig,
        StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount,
        StrategyTeamForecastCalibrationMemoryDigestReport,
        StrategyTeamForecastCalibrationMemoryDigestRollup,
        StrategyTeamForecastCalibrationMemoryDigestRow,
        StrategyTeamForecastCalibrationMemoryDigestSource,
    )
    for dataclass_type in module_types:
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if _is_numeric_public_field(field.name):
                assert _annotation_allows_decimal_only(hints[field.name]), (
                    dataclass_type.__name__,
                    field.name,
                    hints[field.name],
                )

    for instance in (
        StrategyTeamForecastCalibrationMemoryDigestConfig(),
        source,
        report.rows[0],
        report.rollups[0],
        report.reason_code_counts[0],
        report,
    ):
        for field in fields(instance):
            if _is_numeric_public_field(field.name):
                value = getattr(instance, field.name)
                if value is not None:
                    assert type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        source.team_id = "politics"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"  # type: ignore[misc]


def test_manual_report_validation_rejects_inconsistent_rows_and_counts() -> None:
    valid = _build_report(
        _source(),
        _source(forecast_id="forecast-btc-loss", resolved_outcome=d("0.000000")),
    )

    with pytest.raises(ValueError, match="row_count"):
        StrategyTeamForecastCalibrationMemoryDigestReport(
            generated_at=valid.generated_at,
            config_version=valid.config_version,
            digest_status=valid.digest_status,
            next_review_step=valid.next_review_step,
            source_count=valid.source_count,
            row_count=d("2"),
            resolved_count=valid.resolved_count,
            pending_count=valid.pending_count,
            pass_count=valid.pass_count,
            watch_count=valid.watch_count,
            blocked_count=valid.blocked_count,
            high_brier_count=valid.high_brier_count,
            stale_pending_count=valid.stale_pending_count,
            insufficient_resolved_count=valid.insufficient_resolved_count,
            mean_brier_score=valid.mean_brier_score,
            mean_signed_error=valid.mean_signed_error,
            rows=valid.rows,
            rollups=valid.rollups,
            reason_code_counts=valid.reason_code_counts,
            reason_codes=valid.reason_codes,
        )
    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        StrategyTeamForecastCalibrationMemoryDigestReport(
            generated_at=valid.generated_at,
            config_version=valid.config_version,
            digest_status="blocked",
            next_review_step="pause_forecast_calibration_memory_use",
            source_count=valid.source_count + d("1"),
            row_count=d("2"),
            resolved_count=valid.resolved_count + d("1"),
            pending_count=valid.pending_count,
            pass_count=valid.pass_count,
            watch_count=valid.watch_count,
            blocked_count=valid.blocked_count + d("1"),
            high_brier_count=valid.high_brier_count,
            stale_pending_count=valid.stale_pending_count,
            insufficient_resolved_count=valid.insufficient_resolved_count + d("1"),
            mean_brier_score=valid.mean_brier_score,
            mean_signed_error=valid.mean_signed_error,
            rows=(
                StrategyTeamForecastCalibrationMemoryDigestRow(
                    team_id="politics",
                    category_id="politics",
                    readiness_status="blocked",
                    observation_count=d("1"),
                    resolved_count=d("0"),
                    pending_count=d("1"),
                    pending_ratio=d("1.000000"),
                    high_brier_count=d("0"),
                    stale_pending_count=d("1"),
                    insufficient_resolved_count=d("1"),
                    mean_brier_score=None,
                    mean_signed_error=None,
                    latest_observed_at=GENERATED_AT,
                    latest_resolved_at=None,
                    redacted_forecast_references=("[REDACTED_REFERENCE]",),
                    reason_codes=(
                        "strategy_team_forecast_calibration_memory_digest_insufficient_resolved_observations",
                        "strategy_team_forecast_calibration_memory_digest_stale_pending_observations",
                    ),
                ),
                valid.rows[0],
            ),
            rollups=valid.rollups,
            reason_code_counts=valid.reason_code_counts,
            reason_codes=valid.reason_codes,
        )


def test_static_module_source_stays_pure_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "psycopg",
        "sqlite",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "account",
        "signing",
        "cancel",
        "replace",
        "trade_execution",
        "persist",
        "db",
    )
    for term in forbidden_terms:
        assert term not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
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


class NoOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class DateTimeSubclass(datetime):
    pass


def _assert_no_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload contains public numeric {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_float_or_int(item)


def _is_numeric_public_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_score")
        or field_name.endswith("_error")
        or field_name.endswith("_probability")
        or field_name.endswith("_outcome")
        or field_name.endswith("_seconds")
    )


def _annotation_allows_decimal_only(annotation: object) -> bool:
    if annotation is Decimal:
        return True
    origin = get_origin(annotation)
    if origin is None:
        return False
    return set(get_args(annotation)) <= {Decimal, type(None)}
