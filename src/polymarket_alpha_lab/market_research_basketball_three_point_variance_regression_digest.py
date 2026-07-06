"""Pure Phase 1 basketball three-point variance regression digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_BASKETBALL_THREE_POINT_VARIANCE_REGRESSION_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-three-point-variance-regression-digest-v0"
)

REGRESSION_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "basketball_three_point_variance_regression_attempt_rate_spike",
    "basketball_three_point_variance_regression_high_accuracy_delta",
    "basketball_three_point_variance_regression_inline",
    "basketball_three_point_variance_regression_small_sample",
    "basketball_three_point_variance_regression_watch_accuracy_delta",
)
REPORT_REASON_CODES = (
    "basketball_three_point_variance_regression_high_accuracy_delta_present",
    "basketball_three_point_variance_regression_attempt_rate_spike_present",
    "basketball_three_point_variance_regression_small_sample_present",
    "basketball_three_point_variance_regression_multi_team_signal_present",
    "basketball_three_point_variance_regression_digest_clear",
    "basketball_three_point_variance_regression_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
MULTI_TEAM_RISK_SCORE = Decimal("0.750000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_BASKETBALL_THREE_POINT_VARIANCE_REGRESSION_DIGEST_CONFIG_VERSION",
    "BasketballThreePointVarianceRegressionDigestConfig",
    "BasketballThreePointVarianceRegressionObservation",
    "BasketballThreePointVarianceRegressionDigestRow",
    "BasketballThreePointVarianceRegressionReasonCodeCount",
    "BasketballThreePointVarianceRegressionDigestReport",
    "build_market_research_basketball_three_point_variance_regression_digest",
    "market_research_basketball_three_point_variance_regression_digest_payload",
)


@dataclass(frozen=True)
class BasketballThreePointVarianceRegressionDigestConfig:
    config_version: str = (
        DEFAULT_BASKETBALL_THREE_POINT_VARIANCE_REGRESSION_DIGEST_CONFIG_VERSION
    )
    watch_accuracy_delta: Decimal = Decimal("0.050000")
    blocked_accuracy_delta: Decimal = Decimal("0.120000")
    attempt_rate_spike_delta: Decimal = Decimal("0.050000")
    small_sample_games: Decimal = Decimal("5.000000")
    multi_team_signal_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "BasketballThreePointVarianceRegressionDigestConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballThreePointVarianceRegressionDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASKETBALL_THREE_POINT_VARIANCE_REGRESSION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_accuracy_delta",
            "blocked_accuracy_delta",
            "attempt_rate_spike_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("small_sample_games", "multi_team_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_accuracy_delta > self.blocked_accuracy_delta:
            raise ValueError(
                "watch_accuracy_delta must not exceed blocked_accuracy_delta",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BasketballThreePointVarianceRegressionObservation:
    source_id: str
    team_id: str
    sample_id: str
    recent_three_point_attempt_rate: Decimal
    baseline_three_point_attempt_rate: Decimal
    recent_three_point_accuracy: Decimal
    baseline_three_point_accuracy: Decimal
    recent_game_count: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "BasketballThreePointVarianceRegressionObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballThreePointVarianceRegressionObservation,
            "observation",
        )
        for field_name in ("source_id", "team_id", "sample_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "recent_three_point_attempt_rate",
            "baseline_three_point_attempt_rate",
            "recent_three_point_accuracy",
            "baseline_three_point_accuracy",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_game_count",
            _require_positive_whole_decimal("recent_game_count", self.recent_game_count),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class BasketballThreePointVarianceRegressionDigestRow:
    source_id: str
    team_id: str
    sample_id: str
    recent_three_point_attempt_rate: Decimal
    baseline_three_point_attempt_rate: Decimal
    attempt_rate_delta: Decimal
    recent_three_point_accuracy: Decimal
    baseline_three_point_accuracy: Decimal
    accuracy_delta: Decimal
    recent_game_count: Decimal
    data_timestamp: datetime
    regression_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "BasketballThreePointVarianceRegressionDigestRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, BasketballThreePointVarianceRegressionDigestRow, "row")
        for field_name in ("source_id", "team_id", "sample_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "recent_three_point_attempt_rate",
            "baseline_three_point_attempt_rate",
            "recent_three_point_accuracy",
            "baseline_three_point_accuracy",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("attempt_rate_delta", "accuracy_delta"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_game_count",
            _require_positive_whole_decimal("recent_game_count", self.recent_game_count),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("regression_status", self.regression_status, REGRESSION_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class BasketballThreePointVarianceRegressionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "BasketballThreePointVarianceRegressionReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballThreePointVarianceRegressionReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class BasketballThreePointVarianceRegressionDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    elevated_accuracy_count: Decimal
    attempt_rate_spike_count: Decimal
    small_sample_count: Decimal
    max_accuracy_delta: Decimal
    average_accuracy_delta: Decimal
    regression_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...]
    reason_code_counts: tuple[
        BasketballThreePointVarianceRegressionReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "BasketballThreePointVarianceRegressionDigestReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, BasketballThreePointVarianceRegressionDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASKETBALL_THREE_POINT_VARIANCE_REGRESSION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "elevated_accuracy_count",
            "attempt_rate_spike_count",
            "small_sample_count",
            "max_accuracy_delta",
            "average_accuracy_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "elevated_accuracy_count",
            "attempt_rate_spike_count",
            "small_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "regression_risk_score",
            _require_ratio("regression_risk_score", self.regression_risk_score),
        )
        _require_member("digest_status", self.digest_status, REGRESSION_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_basketball_three_point_variance_regression_digest(
    observations: Iterable[BasketballThreePointVarianceRegressionObservation],
    *,
    config: BasketballThreePointVarianceRegressionDigestConfig,
    generated_at: datetime,
) -> BasketballThreePointVarianceRegressionDigestReport:
    if type(config) is not BasketballThreePointVarianceRegressionDigestConfig:
        raise ValueError(
            "config must be exactly BasketballThreePointVarianceRegressionDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows, config=config)
    digest_status = _digest_status(rows, config=config)

    return BasketballThreePointVarianceRegressionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        elevated_accuracy_count=_elevated_accuracy_count(rows),
        attempt_rate_spike_count=_reason_count(
            rows,
            "basketball_three_point_variance_regression_attempt_rate_spike",
        ),
        small_sample_count=_reason_count(
            rows,
            "basketball_three_point_variance_regression_small_sample",
        ),
        max_accuracy_delta=_max_positive_accuracy_delta(rows),
        average_accuracy_delta=_ratio(
            _sum_decimal(_positive_accuracy_delta(row) for row in rows),
            row_count,
        ),
        regression_risk_score=_regression_risk_score(rows, config=config),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_basketball_three_point_variance_regression_digest_payload(
    report: BasketballThreePointVarianceRegressionDigestReport,
) -> dict[str, Any]:
    if type(report) is not BasketballThreePointVarianceRegressionDigestReport:
        raise ValueError(
            "report must be exactly BasketballThreePointVarianceRegressionDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    observation: BasketballThreePointVarianceRegressionObservation,
    *,
    config: BasketballThreePointVarianceRegressionDigestConfig,
) -> BasketballThreePointVarianceRegressionDigestRow:
    attempt_rate_delta = _quantize_decimal(
        observation.recent_three_point_attempt_rate
        - observation.baseline_three_point_attempt_rate,
    )
    accuracy_delta = _quantize_decimal(
        observation.recent_three_point_accuracy
        - observation.baseline_three_point_accuracy,
    )
    regression_status = _regression_status(accuracy_delta, config=config)
    return BasketballThreePointVarianceRegressionDigestRow(
        source_id=observation.source_id,
        team_id=observation.team_id,
        sample_id=observation.sample_id,
        recent_three_point_attempt_rate=observation.recent_three_point_attempt_rate,
        baseline_three_point_attempt_rate=observation.baseline_three_point_attempt_rate,
        attempt_rate_delta=attempt_rate_delta,
        recent_three_point_accuracy=observation.recent_three_point_accuracy,
        baseline_three_point_accuracy=observation.baseline_three_point_accuracy,
        accuracy_delta=accuracy_delta,
        recent_game_count=observation.recent_game_count,
        data_timestamp=observation.data_timestamp,
        regression_status=regression_status,
        reason_codes=_row_reason_codes(
            observation,
            attempt_rate_delta=attempt_rate_delta,
            accuracy_delta=accuracy_delta,
            regression_status=regression_status,
            config=config,
        ),
    )


def _regression_status(
    accuracy_delta: Decimal,
    *,
    config: BasketballThreePointVarianceRegressionDigestConfig,
) -> str:
    if accuracy_delta >= config.blocked_accuracy_delta:
        return "blocked"
    if accuracy_delta >= config.watch_accuracy_delta:
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: BasketballThreePointVarianceRegressionObservation,
    *,
    attempt_rate_delta: Decimal,
    accuracy_delta: Decimal,
    regression_status: str,
    config: BasketballThreePointVarianceRegressionDigestConfig,
) -> tuple[str, ...]:
    if regression_status == "blocked":
        reason_codes = [
            "basketball_three_point_variance_regression_high_accuracy_delta",
        ]
    elif regression_status == "watch":
        reason_codes = [
            "basketball_three_point_variance_regression_watch_accuracy_delta",
        ]
    else:
        reason_codes = ["basketball_three_point_variance_regression_inline"]

    if (
        regression_status != "pass"
        and attempt_rate_delta >= config.attempt_rate_spike_delta
    ):
        reason_codes.append(
            "basketball_three_point_variance_regression_attempt_rate_spike",
        )
    if (
        regression_status != "pass"
        and observation.recent_game_count <= config.small_sample_games
    ):
        reason_codes.append("basketball_three_point_variance_regression_small_sample")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
    *,
    config: BasketballThreePointVarianceRegressionDigestConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("basketball_three_point_variance_regression_digest_empty",)
    reason_codes: list[str] = []
    if _reason_count(
        rows,
        "basketball_three_point_variance_regression_high_accuracy_delta",
    ) > ZERO:
        reason_codes.append(
            "basketball_three_point_variance_regression_high_accuracy_delta_present",
        )
    if _reason_count(
        rows,
        "basketball_three_point_variance_regression_attempt_rate_spike",
    ) > ZERO:
        reason_codes.append(
            "basketball_three_point_variance_regression_attempt_rate_spike_present",
        )
    if _reason_count(
        rows,
        "basketball_three_point_variance_regression_small_sample",
    ) > ZERO:
        reason_codes.append(
            "basketball_three_point_variance_regression_small_sample_present",
        )
    if _elevated_accuracy_count(rows) >= config.multi_team_signal_count:
        reason_codes.append(
            "basketball_three_point_variance_regression_multi_team_signal_present",
        )
    if not reason_codes:
        reason_codes.append("basketball_three_point_variance_regression_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
) -> tuple[BasketballThreePointVarianceRegressionReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("basketball_three_point_variance_regression_digest_empty",):
        return (
            BasketballThreePointVarianceRegressionReasonCodeCount(
                reason_code="basketball_three_point_variance_regression_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        BasketballThreePointVarianceRegressionReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
) -> Decimal:
    if reason_code == "basketball_three_point_variance_regression_digest_clear":
        return _reason_count(
            rows,
            "basketball_three_point_variance_regression_inline",
        )
    if reason_code == (
        "basketball_three_point_variance_regression_multi_team_signal_present"
    ):
        return _elevated_accuracy_count(rows)
    row_reason_code = {
        "basketball_three_point_variance_regression_high_accuracy_delta_present": (
            "basketball_three_point_variance_regression_high_accuracy_delta"
        ),
        "basketball_three_point_variance_regression_attempt_rate_spike_present": (
            "basketball_three_point_variance_regression_attempt_rate_spike"
        ),
        "basketball_three_point_variance_regression_small_sample_present": (
            "basketball_three_point_variance_regression_small_sample"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
    *,
    config: BasketballThreePointVarianceRegressionDigestConfig,
) -> str:
    if not rows:
        return "blocked"
    if any(row.regression_status == "blocked" for row in rows):
        return "blocked"
    if (
        _elevated_accuracy_count(rows) >= config.multi_team_signal_count
        and _reason_count(
            rows,
            "basketball_three_point_variance_regression_attempt_rate_spike",
        )
        > ZERO
    ):
        return "blocked"
    if any(row.regression_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_basketball_three_point_variance_regression_screening"
    if status == "watch":
        return "monitor_report_only_basketball_three_point_variance_regression_screening"
    return "block_report_only_basketball_three_point_variance_regression_screening"


def _regression_risk_score(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
    *,
    config: BasketballThreePointVarianceRegressionDigestConfig,
) -> Decimal:
    if not rows:
        return ZERO
    if _digest_status(rows, config=config) == "blocked":
        return ONE
    if _elevated_accuracy_count(rows) >= config.multi_team_signal_count:
        return MULTI_TEAM_RISK_SCORE
    if any(row.regression_status == "watch" for row in rows):
        return WATCH_RISK_SCORE
    return ZERO


def _validate_row(row: BasketballThreePointVarianceRegressionDigestRow) -> None:
    if row.attempt_rate_delta != _quantize_decimal(
        row.recent_three_point_attempt_rate - row.baseline_three_point_attempt_rate,
    ):
        raise ValueError("attempt_rate_delta must match attempt rates")
    if row.accuracy_delta != _quantize_decimal(
        row.recent_three_point_accuracy - row.baseline_three_point_accuracy,
    ):
        raise ValueError("accuracy_delta must match three-point accuracy rates")
    if row.regression_status == "pass":
        if row.reason_codes != ("basketball_three_point_variance_regression_inline",):
            raise ValueError("reason_codes must match regression_status")
        return
    if "basketball_three_point_variance_regression_inline" in row.reason_codes:
        raise ValueError("reason_codes must match regression_status")
    if row.regression_status == "watch":
        if (
            "basketball_three_point_variance_regression_watch_accuracy_delta"
            not in row.reason_codes
        ):
            raise ValueError("reason_codes must match regression_status")
        if (
            "basketball_three_point_variance_regression_high_accuracy_delta"
            in row.reason_codes
        ):
            raise ValueError("reason_codes must match regression_status")
    if row.regression_status == "blocked":
        if (
            "basketball_three_point_variance_regression_high_accuracy_delta"
            not in row.reason_codes
        ):
            raise ValueError("reason_codes must match regression_status")
        if (
            "basketball_three_point_variance_regression_watch_accuracy_delta"
            in row.reason_codes
        ):
            raise ValueError("reason_codes must match regression_status")


def _validate_report(report: BasketballThreePointVarianceRegressionDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.elevated_accuracy_count != _elevated_accuracy_count(report.rows):
        raise ValueError("elevated_accuracy_count must match rows")
    if report.attempt_rate_spike_count != _reason_count(
        report.rows,
        "basketball_three_point_variance_regression_attempt_rate_spike",
    ):
        raise ValueError("attempt_rate_spike_count must match rows")
    if report.small_sample_count != _reason_count(
        report.rows,
        "basketball_three_point_variance_regression_small_sample",
    ):
        raise ValueError("small_sample_count must match rows")
    if report.max_accuracy_delta != _max_positive_accuracy_delta(report.rows):
        raise ValueError("max_accuracy_delta must match rows")
    if report.average_accuracy_delta != _ratio(
        _sum_decimal(_positive_accuracy_delta(row) for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_accuracy_delta must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[BasketballThreePointVarianceRegressionObservation],
) -> tuple[BasketballThreePointVarianceRegressionObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain BasketballThreePointVarianceRegressionObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not BasketballThreePointVarianceRegressionObservation:
            raise ValueError(
                "observations must contain "
                "BasketballThreePointVarianceRegressionObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
) -> tuple[BasketballThreePointVarianceRegressionDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not BasketballThreePointVarianceRegressionDigestRow:
            raise ValueError(
                "rows must contain BasketballThreePointVarianceRegressionDigestRow",
            )
        _require_hard_flags("row", row)
        _validate_row(row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: tuple[BasketballThreePointVarianceRegressionReasonCodeCount, ...],
) -> tuple[BasketballThreePointVarianceRegressionReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not BasketballThreePointVarianceRegressionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "BasketballThreePointVarianceRegressionReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(values, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_member("reason_code", value, allowed)
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(values, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: BasketballThreePointVarianceRegressionDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.regression_status],
        -_positive_accuracy_delta(row),
        row.team_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.regression_status == status))


def _reason_count(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _elevated_accuracy_count(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.regression_status in ("blocked", "watch")),
    )


def _positive_accuracy_delta(
    row: BasketballThreePointVarianceRegressionDigestRow,
) -> Decimal:
    if row.accuracy_delta <= ZERO:
        return ZERO
    return row.accuracy_delta


def _max_positive_accuracy_delta(
    rows: tuple[BasketballThreePointVarianceRegressionDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(_positive_accuracy_delta(row) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _revalidate_public_dataclass(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
