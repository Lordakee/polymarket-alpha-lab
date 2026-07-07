"""Pure report reducer for comparing caller-supplied forecast signals."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchForecastModelComparisonConfig",
    "ResearchForecastModelComparisonInputRow",
    "ResearchForecastModelComparisonReasonCodeCount",
    "ResearchForecastModelComparisonReport",
    "ResearchForecastModelComparisonSignalRow",
    "build_research_forecast_model_comparison_report",
    "research_forecast_model_comparison_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-forecast-model-comparison-report-v0"
STATUSES = ("pass", "watch", "blocked")
MODEL_NAMES = ("naive", "book_imbalance", "llm", "manual_research")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")

NO_INPUTS_REASON = "forecast_model_comparison_no_inputs"
REPORT_REASON_PREFIX = "research_forecast_model_comparison_"
ROW_REASON_PREFIX = "forecast_model_comparison_"

NEXT_STEPS = {
    "pass": "use_report_only_forecast_model_comparison",
    "watch": "watch_report_only_forecast_model_comparison",
    "blocked": "block_report_only_forecast_model_comparison",
}

UNSAFE_PUBLIC_TEXT = ("secret", "private", "credential", "token")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchForecastModelComparisonConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    min_coverage_ratio: Decimal = Decimal("0.750000")
    watch_disagreement_threshold: Decimal = Decimal("0.150000")
    block_disagreement_threshold: Decimal = Decimal("0.300000")
    min_calibration_observation_count: Decimal = Decimal("30")
    max_expected_calibration_error: Decimal = Decimal("0.100000")
    stale_signal_age_seconds: Decimal = Decimal("86400.000000")
    risk_watch_threshold: Decimal = Decimal("0.300000")
    risk_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchForecastModelComparisonConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_coverage_ratio",
            "watch_disagreement_threshold",
            "block_disagreement_threshold",
            "max_expected_calibration_error",
            "risk_watch_threshold",
            "risk_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_calibration_observation_count",
            _normalize_positive_whole_decimal(
                "min_calibration_observation_count",
                self.min_calibration_observation_count,
            ),
        )
        object.__setattr__(
            self,
            "stale_signal_age_seconds",
            _normalize_positive_decimal(
                "stale_signal_age_seconds",
                self.stale_signal_age_seconds,
            ),
        )
        _require_at_most(
            "watch_disagreement_threshold",
            self.watch_disagreement_threshold,
            self.block_disagreement_threshold,
        )
        _require_at_most(
            "risk_watch_threshold",
            self.risk_watch_threshold,
            self.risk_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchForecastModelComparisonInputRow(_FinalPublicDataclass):
    market_id: str
    model_name: str
    probability: Decimal
    observed_at: datetime
    calibration_observation_count: Decimal | None = None
    calibration_error: Decimal | None = None
    risk_score: Decimal = Decimal("0.000000")
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchForecastModelComparisonInputRow, "input")
        _require_canonical_string("market_id", self.market_id)
        _require_model_name("model_name", self.model_name)
        object.__setattr__(
            self,
            "probability",
            _normalize_probability_decimal("probability", self.probability),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "calibration_observation_count",
            _normalize_optional_nonnegative_whole_decimal(
                "calibration_observation_count",
                self.calibration_observation_count,
            ),
        )
        object.__setattr__(
            self,
            "calibration_error",
            _normalize_optional_probability_decimal(
                "calibration_error",
                self.calibration_error,
            ),
        )
        if self.calibration_error is not None and self.calibration_observation_count is None:
            raise ValueError("calibration_error requires calibration_observation_count")
        object.__setattr__(
            self,
            "risk_score",
            _normalize_probability_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchForecastModelComparisonSignalRow(_FinalPublicDataclass):
    market_id: str
    signal_count: Decimal
    coverage_ratio: Decimal
    model_names: tuple[str, ...]
    min_probability: Decimal
    max_probability: Decimal
    disagreement_score: Decimal
    calibrated_signal_count: Decimal
    calibration_available_ratio: Decimal
    average_calibration_error: Decimal | None
    max_risk_score: Decimal
    latest_observed_at: datetime
    max_signal_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchForecastModelComparisonConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchForecastModelComparisonConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchForecastModelComparisonSignalRow, "row")
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_whole_decimal("signal_count", self.signal_count),
        )
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_probability_decimal("coverage_ratio", self.coverage_ratio),
        )
        object.__setattr__(
            self,
            "model_names",
            _normalize_model_names(self.model_names),
        )
        for field_name in (
            "min_probability",
            "max_probability",
            "disagreement_score",
            "calibration_available_ratio",
            "max_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibrated_signal_count",
            _normalize_nonnegative_whole_decimal(
                "calibrated_signal_count",
                self.calibrated_signal_count,
            ),
        )
        object.__setattr__(
            self,
            "average_calibration_error",
            _normalize_optional_probability_decimal(
                "average_calibration_error",
                self.average_calibration_error,
            ),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _normalize_nonnegative_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_signal_row(
            self,
            config=validation_config or ResearchForecastModelComparisonConfig(),
        )


@dataclass(frozen=True)
class ResearchForecastModelComparisonReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchForecastModelComparisonReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "market_ratio",
            _normalize_probability_decimal("market_ratio", self.market_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchForecastModelComparisonReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    market_count: Decimal
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    thin_coverage_count: Decimal
    high_disagreement_count: Decimal
    uncalibrated_count: Decimal
    high_risk_count: Decimal
    average_coverage_ratio: Decimal
    max_disagreement_score: Decimal
    average_calibration_available_ratio: Decimal
    status: str
    next_step: str
    rows: tuple[ResearchForecastModelComparisonSignalRow, ...]
    reason_code_counts: tuple[ResearchForecastModelComparisonReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchForecastModelComparisonReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "signal_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "thin_coverage_count",
            "high_disagreement_count",
            "uncalibrated_count",
            "high_risk_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_coverage_ratio",
            "max_disagreement_score",
            "average_calibration_available_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        if self.next_step != NEXT_STEPS[self.status]:
            raise ValueError("next_step must match status")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchForecastModelComparisonConfig,
    ResearchForecastModelComparisonInputRow,
    ResearchForecastModelComparisonSignalRow,
    ResearchForecastModelComparisonReasonCodeCount,
    ResearchForecastModelComparisonReport,
)


def build_research_forecast_model_comparison_report(
    signals: Iterable[ResearchForecastModelComparisonInputRow],
    *,
    config: ResearchForecastModelComparisonConfig,
    generated_at: datetime,
) -> ResearchForecastModelComparisonReport:
    if type(config) is not ResearchForecastModelComparisonConfig:
        raise ValueError("config must be a ResearchForecastModelComparisonConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(signals, generated_at_utc)
    grouped: dict[str, list[ResearchForecastModelComparisonInputRow]] = {}
    for row in input_rows:
        grouped.setdefault(row.market_id, []).append(row)
    rows = tuple(
        _build_signal_row(
            market_id=market_id,
            signals=tuple(grouped[market_id]),
            config=config,
            generated_at=generated_at_utc,
        )
        for market_id in sorted(grouped)
    )
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = _report_reason_codes(rows, status)
    return ResearchForecastModelComparisonReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        signal_count=sum((row.signal_count for row in rows), ZERO),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        thin_coverage_count=_count(
            sum(1 for row in rows if _has_missing_model_reason(row.reason_codes)),
        ),
        high_disagreement_count=_count(
            sum(1 for row in rows if _has_disagreement_reason(row.reason_codes)),
        ),
        uncalibrated_count=_count(
            sum(1 for row in rows if _has_calibration_gap_reason(row.reason_codes)),
        ),
        high_risk_count=_count(
            sum(1 for row in rows if _has_risk_reason(row.reason_codes)),
        ),
        average_coverage_ratio=_mean(tuple(row.coverage_ratio for row in rows)),
        max_disagreement_score=_max_decimal(
            tuple(row.disagreement_score for row in rows),
        ),
        average_calibration_available_ratio=_mean(
            tuple(row.calibration_available_ratio for row in rows),
        ),
        status=status,
        next_step=NEXT_STEPS[status],
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_forecast_model_comparison_report_payload(
    report: ResearchForecastModelComparisonReport,
) -> dict[str, Any]:
    if type(report) is not ResearchForecastModelComparisonReport:
        raise ValueError("report must be a ResearchForecastModelComparisonReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    _reject_unsafe_public_payload("payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_signal_row(
    *,
    market_id: str,
    signals: tuple[ResearchForecastModelComparisonInputRow, ...],
    config: ResearchForecastModelComparisonConfig,
    generated_at: datetime,
) -> ResearchForecastModelComparisonSignalRow:
    sorted_signals = tuple(sorted(signals, key=lambda row: row.model_name))
    probabilities = tuple(row.probability for row in sorted_signals)
    model_names = tuple(row.model_name for row in sorted_signals)
    signal_count = _count(len(sorted_signals))
    coverage_ratio = _ratio(signal_count, _count(len(MODEL_NAMES)))
    min_probability = min(probabilities)
    max_probability = max(probabilities)
    disagreement_score = _quantize(max_probability - min_probability)
    calibrated_errors = tuple(
        row.calibration_error
        for row in sorted_signals
        if _is_calibrated(row, config) and row.calibration_error is not None
    )
    calibrated_count = _count(len(calibrated_errors))
    average_calibration_error = (
        _mean(calibrated_errors) if calibrated_errors else None
    )
    max_risk_score = max((row.risk_score for row in sorted_signals), default=ZERO)
    latest_observed_at = max(row.observed_at for row in sorted_signals)
    max_signal_age_seconds = max(
        _age_seconds(generated_at, row.observed_at) for row in sorted_signals
    )
    reason_codes = _row_reason_codes(
        sorted_signals,
        coverage_ratio=coverage_ratio,
        disagreement_score=disagreement_score,
        calibrated_count=calibrated_count,
        average_calibration_error=average_calibration_error,
        max_risk_score=max_risk_score,
        max_signal_age_seconds=max_signal_age_seconds,
        config=config,
    )
    return ResearchForecastModelComparisonSignalRow(
        market_id=market_id,
        signal_count=signal_count,
        coverage_ratio=coverage_ratio,
        model_names=model_names,
        min_probability=min_probability,
        max_probability=max_probability,
        disagreement_score=disagreement_score,
        calibrated_signal_count=calibrated_count,
        calibration_available_ratio=_ratio(calibrated_count, signal_count),
        average_calibration_error=average_calibration_error,
        max_risk_score=max_risk_score,
        latest_observed_at=latest_observed_at,
        max_signal_age_seconds=max_signal_age_seconds,
        status=_row_status(
            reason_codes,
            coverage_ratio=coverage_ratio,
            config=config,
        ),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    signals: tuple[ResearchForecastModelComparisonInputRow, ...],
    *,
    coverage_ratio: Decimal,
    disagreement_score: Decimal,
    calibrated_count: Decimal,
    average_calibration_error: Decimal | None,
    max_risk_score: Decimal,
    max_signal_age_seconds: Decimal,
    config: ResearchForecastModelComparisonConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    model_names = frozenset(row.model_name for row in signals)
    for model_name in MODEL_NAMES:
        if model_name not in model_names:
            reason_codes.append(f"missing_model_{model_name}")
    if disagreement_score >= config.block_disagreement_threshold:
        reason_codes.append("high_disagreement_block")
    elif disagreement_score >= config.watch_disagreement_threshold:
        reason_codes.append("disagreement_watch")
    if calibrated_count == ZERO:
        reason_codes.append("uncalibrated_block")
    elif calibrated_count < _count(len(signals)):
        reason_codes.append("calibration_partial_watch")
    if (
        average_calibration_error is not None
        and average_calibration_error > config.max_expected_calibration_error
    ):
        reason_codes.append("calibration_error_watch")
    if max_risk_score >= config.risk_block_threshold:
        reason_codes.append("risk_block")
    elif max_risk_score >= config.risk_watch_threshold:
        reason_codes.append("risk_watch")
    if max_signal_age_seconds > config.stale_signal_age_seconds:
        reason_codes.append("signal_stale_watch")
    for row in signals:
        reason_codes.extend(f"input_{reason_code}" for reason_code in row.reason_codes)
    status = _row_status(
        tuple(reason_codes),
        coverage_ratio=coverage_ratio,
        config=config,
    )
    reason_codes.append(f"{ROW_REASON_PREFIX}{status}")
    return tuple(sorted(set(reason_codes)))


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    coverage_ratio: Decimal,
    config: ResearchForecastModelComparisonConfig,
) -> str:
    if coverage_ratio < config.min_coverage_ratio:
        return "blocked"
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchForecastModelComparisonSignalRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons = [f"{REPORT_REASON_PREFIX}{status}"]
    for reason_code in sorted(
        {
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if not reason_code.startswith(ROW_REASON_PREFIX)
        },
    ):
        reasons.append(reason_code)
    return tuple(sorted(set(reasons)))


def _reason_code_counts(
    rows: tuple[ResearchForecastModelComparisonSignalRow, ...],
) -> tuple[ResearchForecastModelComparisonReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchForecastModelComparisonReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                market_ratio=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    market_count = _count(len(rows))
    return tuple(
        ResearchForecastModelComparisonReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            market_ratio=_ratio(_count(count), market_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    signals: Iterable[ResearchForecastModelComparisonInputRow],
    generated_at: datetime,
) -> tuple[ResearchForecastModelComparisonInputRow, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchForecastModelComparisonInputRow:
            raise ValueError(
                "signals must contain ResearchForecastModelComparisonInputRow values",
            )
        _require_hard_flags("input", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.market_id, row.model_name)
        if key in seen:
            raise ValueError("signals must not contain duplicate market_id and model_name")
        seen.add(key)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchForecastModelComparisonSignalRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchForecastModelComparisonSignalRow:
            raise ValueError(
                "rows must contain ResearchForecastModelComparisonSignalRow values",
            )
        _require_hard_flags("row", row)
        if row.market_id in seen:
            raise ValueError("rows must not contain duplicate market_id values")
        seen.add(row.market_id)
    expected = tuple(sorted(rows, key=lambda row: row.market_id))
    if rows != expected:
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchForecastModelComparisonReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchForecastModelComparisonReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchForecastModelComparisonReasonCodeCount values",
            )
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    expected = tuple(sorted(rows, key=lambda row: (-row.count, row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return rows


def _normalize_model_names(model_names: object) -> tuple[str, ...]:
    if type(model_names) is not tuple:
        raise ValueError("model_names must be a tuple")
    seen: set[str] = set()
    for model_name in model_names:
        _require_model_name("model_names", model_name)
        if model_name in seen:
            raise ValueError("model_names must not contain duplicates")
        seen.add(model_name)
    expected = tuple(sorted(model_names))
    if model_names != expected:
        raise ValueError("model_names must use canonical sequence")
    return model_names


def _validate_signal_row(
    row: ResearchForecastModelComparisonSignalRow,
    *,
    config: ResearchForecastModelComparisonConfig,
) -> None:
    if row.signal_count != _count(len(row.model_names)):
        raise ValueError("signal_count must match model_names")
    if row.coverage_ratio != _ratio(row.signal_count, _count(len(MODEL_NAMES))):
        raise ValueError("coverage_ratio must match signal_count")
    if row.min_probability > row.max_probability:
        raise ValueError("min_probability must be less than or equal to max_probability")
    if row.disagreement_score != _quantize(row.max_probability - row.min_probability):
        raise ValueError("disagreement_score must match probability range")
    if row.calibrated_signal_count > row.signal_count:
        raise ValueError("calibrated_signal_count must not exceed signal_count")
    if row.calibration_available_ratio != _ratio(
        row.calibrated_signal_count,
        row.signal_count,
    ):
        raise ValueError("calibration_available_ratio must match counts")
    if row.calibrated_signal_count == ZERO and row.average_calibration_error is not None:
        raise ValueError("average_calibration_error requires calibrated signals")
    if row.calibrated_signal_count > ZERO and row.average_calibration_error is None:
        raise ValueError("average_calibration_error must be present")
    expected_status = _row_status(
        row.reason_codes,
        coverage_ratio=row.coverage_ratio,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.disagreement_score >= config.watch_disagreement_threshold:
        raise ValueError("disagreement_score must support pass status")


def _validate_report(report: ResearchForecastModelComparisonReport) -> None:
    rows = report.rows
    if report.market_count != _count(len(rows)):
        raise ValueError("market_count must match rows")
    if report.signal_count != sum((row.signal_count for row in rows), ZERO):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.thin_coverage_count != _count(
        sum(1 for row in rows if _has_missing_model_reason(row.reason_codes)),
    ):
        raise ValueError("thin_coverage_count must match rows")
    if report.high_disagreement_count != _count(
        sum(1 for row in rows if _has_disagreement_reason(row.reason_codes)),
    ):
        raise ValueError("high_disagreement_count must match rows")
    if report.uncalibrated_count != _count(
        sum(1 for row in rows if _has_calibration_gap_reason(row.reason_codes)),
    ):
        raise ValueError("uncalibrated_count must match rows")
    if report.high_risk_count != _count(
        sum(1 for row in rows if _has_risk_reason(row.reason_codes)),
    ):
        raise ValueError("high_risk_count must match rows")
    if report.average_coverage_ratio != _mean(tuple(row.coverage_ratio for row in rows)):
        raise ValueError("average_coverage_ratio must match rows")
    if report.max_disagreement_score != _max_decimal(
        tuple(row.disagreement_score for row in rows),
    ):
        raise ValueError("max_disagreement_score must match rows")
    if report.average_calibration_available_ratio != _mean(
        tuple(row.calibration_available_ratio for row in rows),
    ):
        raise ValueError("average_calibration_available_ratio must match rows")
    expected_status = _rollup_status(tuple(row.status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _has_missing_model_reason(reason_codes: tuple[str, ...]) -> bool:
    return any(reason_code.startswith("missing_model_") for reason_code in reason_codes)


def _has_disagreement_reason(reason_codes: tuple[str, ...]) -> bool:
    return "disagreement_watch" in reason_codes or "high_disagreement_block" in reason_codes


def _has_calibration_gap_reason(reason_codes: tuple[str, ...]) -> bool:
    return (
        "calibration_partial_watch" in reason_codes
        or "uncalibrated_block" in reason_codes
        or "calibration_error_watch" in reason_codes
    )


def _has_risk_reason(reason_codes: tuple[str, ...]) -> bool:
    return "risk_watch" in reason_codes or "risk_block" in reason_codes


def _status_count(
    rows: tuple[ResearchForecastModelComparisonSignalRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "blocked"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _is_calibrated(
    row: ResearchForecastModelComparisonInputRow,
    config: ResearchForecastModelComparisonConfig,
) -> bool:
    return (
        row.calibration_observation_count is not None
        and row.calibration_error is not None
        and row.calibration_observation_count >= config.min_calibration_observation_count
    )


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    normalized = _quantize(seconds)
    if normalized < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return normalized


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload contains unsupported dataclass")
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "validation_config"
        }
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            if field.name == "validation_config":
                continue
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        _require_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_text(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list or type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(+value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_optional_nonnegative_whole_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_whole_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_model_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MODEL_NAMES:
        raise ValueError(f"{field_name} must be a known model")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
