"""Read-only probability edge calibration digest for Phase 1 strategy outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


DEFAULT_STRATEGY_PROBABILITY_EDGE_CALIBRATION_DIGEST_CONFIG_VERSION = (
    "strategy-probability-edge-calibration-digest-v0"
)

INPUT_REASON_CODES = (
    "positive_edge_detected",
    "negative_edge_detected",
    "edge_within_threshold",
    "resolved_calibration_available",
    "calibration_error_detected",
    "calibration_error_within_threshold",
    "stale_edge",
    "edge_fresh",
)
REPORT_REASON_CODES = (
    "probability_edge_calibration_digest_clear",
    "material_probability_edge_detected",
    "resolved_calibration_available",
    "calibration_error_detected",
    "stale_probability_edge_detected",
)
STATUSES = ("pass", "watch")
WATCH_REASON_CODES = (
    "positive_edge_detected",
    "negative_edge_detected",
    "calibration_error_detected",
    "stale_edge",
)
SENSITIVE_TEXT_FRAGMENTS = ("secret", "private", "token")
REDACTED_CONDITION_ID_PREFIX = "condition_ref_"
REDACTED_DIGEST_LENGTH = 16

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCalibrationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_EDGE_CALIBRATION_DIGEST_CONFIG_VERSION
    )
    material_edge_threshold: Decimal = Decimal("0.050000")
    calibration_error_threshold: Decimal = Decimal("0.100000")
    stale_edge_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "material_edge_threshold",
            _normalize_nonnegative_ratio(
                "material_edge_threshold",
                self.material_edge_threshold,
            ),
        )
        object.__setattr__(
            self,
            "calibration_error_threshold",
            _normalize_nonnegative_ratio(
                "calibration_error_threshold",
                self.calibration_error_threshold,
            ),
        )
        object.__setattr__(
            self,
            "stale_edge_hours",
            _normalize_nonnegative_value("stale_edge_hours", self.stale_edge_hours),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCalibrationInput:
    strategy_id: str
    market_slug: str
    condition_id: str
    forecast_probability: Decimal
    market_probability: Decimal
    realized_probability: Decimal | None
    edge_probability: Decimal
    edge_age_hours: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("strategy_id", self.strategy_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "market_probability",
            _normalize_probability("market_probability", self.market_probability),
        )
        if self.realized_probability is not None:
            object.__setattr__(
                self,
                "realized_probability",
                _normalize_realized_probability(
                    "realized_probability",
                    self.realized_probability,
                ),
            )
        object.__setattr__(
            self,
            "edge_probability",
            _normalize_value("edge_probability", self.edge_probability),
        )
        object.__setattr__(
            self,
            "edge_age_hours",
            _normalize_nonnegative_value("edge_age_hours", self.edge_age_hours),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCalibrationRow:
    strategy_id: str
    market_slug: str
    redacted_condition_id: str
    forecast_probability: Decimal
    market_probability: Decimal
    realized_probability: Decimal | None
    edge_probability: Decimal
    calibration_error: Decimal
    edge_age_hours: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("strategy_id", self.strategy_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_redacted_condition_id(self.redacted_condition_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "market_probability",
            _normalize_probability("market_probability", self.market_probability),
        )
        if self.realized_probability is not None:
            object.__setattr__(
                self,
                "realized_probability",
                _normalize_realized_probability(
                    "realized_probability",
                    self.realized_probability,
                ),
            )
        object.__setattr__(
            self,
            "edge_probability",
            _normalize_value("edge_probability", self.edge_probability),
        )
        object.__setattr__(
            self,
            "calibration_error",
            _normalize_nonnegative_ratio("calibration_error", self.calibration_error),
        )
        object.__setattr__(
            self,
            "edge_age_hours",
            _normalize_nonnegative_value("edge_age_hours", self.edge_age_hours),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCalibrationDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    strategy_count: Decimal
    market_count: Decimal
    material_edge_count: Decimal
    resolved_calibration_count: Decimal
    calibration_error_count: Decimal
    stale_edge_count: Decimal
    mean_absolute_edge: Decimal
    mean_signed_edge: Decimal
    mean_calibration_error: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[StrategyProbabilityEdgeCalibrationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "strategy_count",
            "market_count",
            "material_edge_count",
            "resolved_calibration_count",
            "calibration_error_count",
            "stale_edge_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_absolute_edge",
            "mean_signed_edge",
            "mean_calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_strategy_probability_edge_calibration_digest(
    inputs: list[StrategyProbabilityEdgeCalibrationInput]
    | tuple[StrategyProbabilityEdgeCalibrationInput, ...],
    *,
    config: StrategyProbabilityEdgeCalibrationDigestConfig,
    generated_at: datetime,
) -> StrategyProbabilityEdgeCalibrationDigestReport:
    if type(config) is not StrategyProbabilityEdgeCalibrationDigestConfig:
        raise ValueError(
            "config must be a StrategyProbabilityEdgeCalibrationDigestConfig",
        )
    _require_hard_flags("config", config)
    source_rows = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(row, config) for row in source_rows),
            key=_row_sort_key,
        ),
    )
    return StrategyProbabilityEdgeCalibrationDigestReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        source_row_count=_count(len(source_rows)),
        strategy_count=_count(len({row.strategy_id for row in source_rows})),
        market_count=_count(len({row.market_slug for row in source_rows})),
        material_edge_count=_count(
            sum(
                1
                for row in rows
                if _abs_decimal(row.edge_probability) >= config.material_edge_threshold
            ),
        ),
        resolved_calibration_count=_count(
            sum(1 for row in rows if row.realized_probability is not None),
        ),
        calibration_error_count=_count(
            sum(
                1
                for row in rows
                if row.calibration_error >= config.calibration_error_threshold
            ),
        ),
        stale_edge_count=_count(
            sum(1 for row in rows if row.edge_age_hours >= config.stale_edge_hours),
        ),
        mean_absolute_edge=_mean(tuple(_abs_decimal(row.edge_probability) for row in rows)),
        mean_signed_edge=_mean(tuple(row.edge_probability for row in rows)),
        mean_calibration_error=_mean(
            tuple(
                row.calibration_error
                for row in rows
                if row.realized_probability is not None
            ),
        ),
        status=_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def strategy_probability_edge_calibration_digest_payload(
    report: StrategyProbabilityEdgeCalibrationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyProbabilityEdgeCalibrationDigestReport:
        _require_hard_flags("report", report)
        _reject_unsafe_payload_keys(
            "strategy probability edge calibration digest",
            report,
        )
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_payload_keys(
            "strategy probability edge calibration digest payload",
            report,
        )
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyProbabilityEdgeCalibrationDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_strings("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_inputs(
    inputs: list[StrategyProbabilityEdgeCalibrationInput]
    | tuple[StrategyProbabilityEdgeCalibrationInput, ...],
) -> tuple[StrategyProbabilityEdgeCalibrationInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyProbabilityEdgeCalibrationInput:
            raise ValueError(
                "inputs must contain StrategyProbabilityEdgeCalibrationInput values",
            )
        _require_hard_flags("input", row)
        key = (row.strategy_id, row.market_slug)
        if key in seen:
            raise ValueError("inputs must not contain duplicate strategy_id market_slug values")
        seen.add(key)
    return rows


def _row_from_input(
    row: StrategyProbabilityEdgeCalibrationInput,
    config: StrategyProbabilityEdgeCalibrationDigestConfig,
) -> StrategyProbabilityEdgeCalibrationRow:
    return StrategyProbabilityEdgeCalibrationRow(
        strategy_id=row.strategy_id,
        market_slug=row.market_slug,
        redacted_condition_id=_redact_sensitive_string(row.condition_id),
        forecast_probability=row.forecast_probability,
        market_probability=row.market_probability,
        realized_probability=row.realized_probability,
        edge_probability=row.edge_probability,
        calibration_error=_calibration_error(row),
        edge_age_hours=row.edge_age_hours,
        status=_row_status(row, config),
        reason_codes=_row_reason_codes(row, config),
    )


def _row_status(
    row: StrategyProbabilityEdgeCalibrationInput,
    config: StrategyProbabilityEdgeCalibrationDigestConfig,
) -> str:
    if _abs_decimal(row.edge_probability) >= config.material_edge_threshold:
        return "watch"
    if _calibration_error(row) >= config.calibration_error_threshold:
        return "watch"
    if row.edge_age_hours >= config.stale_edge_hours:
        return "watch"
    return "pass"


def _status(rows: tuple[StrategyProbabilityEdgeCalibrationRow, ...]) -> str:
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyProbabilityEdgeCalibrationRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("probability_edge_calibration_digest_clear",)
    codes: list[str] = []
    if any("positive_edge_detected" in row.reason_codes for row in rows) or any(
        "negative_edge_detected" in row.reason_codes for row in rows
    ):
        codes.append("material_probability_edge_detected")
    if any(row.realized_probability is not None for row in rows):
        codes.append("resolved_calibration_available")
    if any("calibration_error_detected" in row.reason_codes for row in rows):
        codes.append("calibration_error_detected")
    if any("stale_edge" in row.reason_codes for row in rows):
        codes.append("stale_probability_edge_detected")
    return tuple(codes)


def _row_reason_codes(
    row: StrategyProbabilityEdgeCalibrationInput,
    config: StrategyProbabilityEdgeCalibrationDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    edge = _edge_probability(row)
    if edge >= ZERO_RATIO:
        if edge >= config.material_edge_threshold:
            codes.append("positive_edge_detected")
        else:
            codes.append("edge_within_threshold")
    elif _abs_decimal(edge) >= config.material_edge_threshold:
        codes.append("negative_edge_detected")
    else:
        codes.append("edge_within_threshold")
    if row.realized_probability is not None:
        codes.append("resolved_calibration_available")
        if _calibration_error(row) >= config.calibration_error_threshold:
            codes.append("calibration_error_detected")
        else:
            codes.append("calibration_error_within_threshold")
    if row.edge_age_hours >= config.stale_edge_hours:
        codes.append("stale_edge")
    else:
        codes.append("edge_fresh")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[StrategyProbabilityEdgeCalibrationInput, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _row_sort_key(
    row: StrategyProbabilityEdgeCalibrationRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -_abs_decimal(row.edge_probability),
        -row.calibration_error,
        row.edge_age_hours,
        row.market_slug,
        row.strategy_id,
    )


def _validate_input(row: StrategyProbabilityEdgeCalibrationInput) -> None:
    if row.edge_probability != _edge_probability(row):
        raise ValueError("edge_probability must match forecast and market probability")
    if row.reason_codes != _input_reason_codes(row):
        raise ValueError("reason_codes must match input")


def _validate_row(row: StrategyProbabilityEdgeCalibrationRow) -> None:
    if row.edge_probability != _normalize_value(
        "edge_probability",
        row.forecast_probability - row.market_probability,
    ):
        raise ValueError("edge_probability must match forecast and market probability")
    if row.realized_probability is None and row.calibration_error != ZERO_RATIO:
        raise ValueError("calibration_error must be zero without resolved probability")
    if row.realized_probability is not None and row.calibration_error != _abs_decimal(
        row.realized_probability - row.forecast_probability,
    ):
        raise ValueError("calibration_error must match realized and forecast probability")
    if row.status == "pass" and (
        "positive_edge_detected" in row.reason_codes
        or "negative_edge_detected" in row.reason_codes
        or "calibration_error_detected" in row.reason_codes
        or "stale_edge" in row.reason_codes
    ):
        raise ValueError("pass rows must not contain watched signals")
    if row.status == "watch" and not any(
        reason_code in WATCH_REASON_CODES for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must contain watched signals")


def _validate_report(report: StrategyProbabilityEdgeCalibrationDigestReport) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.strategy_count > report.source_row_count:
        raise ValueError("strategy_count must not exceed source_row_count")
    if report.market_count > report.source_row_count:
        raise ValueError("market_count must not exceed source_row_count")
    if report.material_edge_count != _count(
        sum(
            1
            for row in report.rows
            if "positive_edge_detected" in row.reason_codes
            or "negative_edge_detected" in row.reason_codes
        ),
    ):
        raise ValueError("material_edge_count must match rows")
    if report.resolved_calibration_count != _count(
        sum(1 for row in report.rows if row.realized_probability is not None),
    ):
        raise ValueError("resolved_calibration_count must match rows")
    if report.calibration_error_count != _count(
        sum(1 for row in report.rows if "calibration_error_detected" in row.reason_codes),
    ):
        raise ValueError("calibration_error_count must match rows")
    if report.stale_edge_count != _count(
        sum(1 for row in report.rows if "stale_edge" in row.reason_codes),
    ):
        raise ValueError("stale_edge_count must match rows")
    if report.status != _status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    keys = tuple((row.strategy_id, row.market_slug) for row in report.rows)
    if len(set(keys)) != len(keys):
        raise ValueError("rows must contain unique strategy_id market_slug values")


def _reason_code_counts_from_rows(
    rows: tuple[StrategyProbabilityEdgeCalibrationRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _input_reason_codes(row: StrategyProbabilityEdgeCalibrationInput) -> tuple[str, ...]:
    codes: list[str] = []
    edge = _edge_probability(row)
    if edge >= ZERO_RATIO:
        if edge >= Decimal("0.050000"):
            codes.append("positive_edge_detected")
        else:
            codes.append("edge_within_threshold")
    else:
        if _abs_decimal(edge) >= Decimal("0.050000"):
            codes.append("negative_edge_detected")
        else:
            codes.append("edge_within_threshold")
    if row.realized_probability is not None:
        codes.append("resolved_calibration_available")
        if _calibration_error(row) >= Decimal("0.100000"):
            codes.append("calibration_error_detected")
        elif "calibration_error_within_threshold" in row.reason_codes:
            codes.append("calibration_error_within_threshold")
    if "stale_edge" in row.reason_codes:
        codes.append("stale_edge")
    elif "edge_fresh" in row.reason_codes:
        codes.append("edge_fresh")
    return tuple(codes)


def _edge_probability(row: StrategyProbabilityEdgeCalibrationInput) -> Decimal:
    return _normalize_value(
        "edge_probability",
        row.forecast_probability - row.market_probability,
    )


def _calibration_error(
    row: StrategyProbabilityEdgeCalibrationInput
    | StrategyProbabilityEdgeCalibrationRow,
) -> Decimal:
    if row.realized_probability is None:
        return ZERO_RATIO
    return _abs_decimal(row.realized_probability - row.forecast_probability)


def _redact_sensitive_string(value: str) -> str:
    _require_canonical_string("condition_id", value)
    digest = sha256(value.encode("utf-8")).hexdigest()[:REDACTED_DIGEST_LENGTH]
    return f"{REDACTED_CONDITION_ID_PREFIX}{digest}"


def _require_redacted_condition_id(value: str) -> None:
    _require_canonical_string("redacted_condition_id", value)
    if _contains_sensitive_text(value):
        raise ValueError("redacted_condition_id must be redacted")
    if not value.startswith(REDACTED_CONDITION_ID_PREFIX):
        raise ValueError("redacted_condition_id must be redacted")
    digest = value.removeprefix(REDACTED_CONDITION_ID_PREFIX)
    if len(digest) != REDACTED_DIGEST_LENGTH:
        raise ValueError("redacted_condition_id must be redacted")
    if any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("redacted_condition_id must be redacted")


def _normalize_rows(
    value: object,
) -> tuple[StrategyProbabilityEdgeCalibrationRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not StrategyProbabilityEdgeCalibrationRow:
            raise ValueError(
                "rows must contain StrategyProbabilityEdgeCalibrationRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    normalized = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason_code count tuples")
        reason_code, count = row
        if reason_code not in INPUT_REASON_CODES:
            raise ValueError("reason_code_counts reason_code is not supported")
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_strings(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe live surface value in {label}")
        if _contains_sensitive_text(value):
            raise ValueError(f"sensitive value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_strings(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_strings(label, item)
        return


def _reject_unsafe_payload_keys(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        if _has_unsafe_surface_fragment(key):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(
        part
        for part in "".join(char if char.isalnum() else "_" for char in lowered).split(
            "_",
        )
        if part
    )
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS:
        if "_" in fragment:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False


def _contains_sensitive_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in SENSITIVE_TEXT_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_realized_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_probability(field_name, value)
    if decimal_value not in (ZERO_RATIO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")
    return decimal_value


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_value(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize_ratio(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / Decimal(len(values)))


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(RATIO_QUANTUM)
