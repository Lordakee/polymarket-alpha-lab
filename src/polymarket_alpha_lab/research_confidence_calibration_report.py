"""Read-only research confidence calibration report for human review."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_CONFIDENCE_CALIBRATION_CONFIG_VERSION = (
    "research-confidence-calibration-report-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
STATUSES = ("pass", "watch", "block")
REPORT_REASON_CODES = {
    "pass": ("research_confidence_calibration_pass",),
    "watch": ("research_confidence_calibration_watch",),
    "block": ("research_confidence_calibration_block",),
}
PASS_REASON = "research_confidence_calibration_pass"
WATCH_REASON_CODES = frozenset(
    (
        "prediction_confidence_watch",
        "historical_calibration_watch",
        "recent_drift_watch",
        "domain_difficulty_watch",
    ),
)
BLOCK_REASON_CODES = frozenset(
    (
        "prediction_confidence_block",
        "historical_calibration_block",
        "recent_drift_block",
        "domain_difficulty_block",
    ),
)
REASON_CODE_PRIORITY = (
    "prediction_confidence_block",
    "historical_calibration_block",
    "recent_drift_block",
    "domain_difficulty_block",
    "prediction_confidence_watch",
    "historical_calibration_watch",
    "recent_drift_watch",
    "domain_difficulty_watch",
    PASS_REASON,
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
HARD_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "live",
        "network",
        "database",
        "persist",
        "mutation",
    ),
)

__all__ = (
    "ResearchConfidenceCalibrationConfig",
    "ResearchConfidenceCalibrationInput",
    "ResearchConfidenceCalibrationReport",
    "ResearchConfidenceCalibrationRow",
    "build_research_confidence_calibration_report",
    "research_confidence_calibration_report_payload",
)


@dataclass(frozen=True)
class ResearchConfidenceCalibrationConfig:
    config_version: str = DEFAULT_RESEARCH_CONFIDENCE_CALIBRATION_CONFIG_VERSION
    min_pass_prediction_confidence: Decimal = Decimal("0.600000")
    min_watch_prediction_confidence: Decimal = Decimal("0.400000")
    min_pass_historical_calibration: Decimal = Decimal("0.700000")
    min_watch_historical_calibration: Decimal = Decimal("0.500000")
    max_pass_recent_drift: Decimal = Decimal("0.150000")
    max_watch_recent_drift: Decimal = Decimal("0.300000")
    max_pass_domain_difficulty: Decimal = Decimal("0.500000")
    max_watch_domain_difficulty: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pass_prediction_confidence",
            "min_watch_prediction_confidence",
            "min_pass_historical_calibration",
            "min_watch_historical_calibration",
            "max_pass_recent_drift",
            "max_watch_recent_drift",
            "max_pass_domain_difficulty",
            "max_watch_domain_difficulty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.min_pass_prediction_confidence < self.min_watch_prediction_confidence:
            raise ValueError(
                "min_pass_prediction_confidence must be at least min_watch_prediction_confidence",
            )
        if self.min_pass_historical_calibration < self.min_watch_historical_calibration:
            raise ValueError(
                "min_pass_historical_calibration must be at least min_watch_historical_calibration",
            )
        if self.max_pass_recent_drift > self.max_watch_recent_drift:
            raise ValueError("max_pass_recent_drift must not exceed max_watch_recent_drift")
        if self.max_pass_domain_difficulty > self.max_watch_domain_difficulty:
            raise ValueError(
                "max_pass_domain_difficulty must not exceed max_watch_domain_difficulty",
            )
        _require_hard_flags("ResearchConfidenceCalibrationConfig", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchConfidenceCalibrationInput:
    prediction_key: str
    domain_key: str
    redacted_prediction_confidence: Decimal
    historical_calibration_score: Decimal
    recent_drift_score: Decimal
    domain_difficulty_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("prediction_key", self.prediction_key)
        _require_canonical_string("domain_key", self.domain_key)
        for field_name in (
            "redacted_prediction_confidence",
            "historical_calibration_score",
            "recent_drift_score",
            "domain_difficulty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("ResearchConfidenceCalibrationInput", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchConfidenceCalibrationRow:
    prediction_key: str
    domain_key: str
    redacted_prediction_confidence: Decimal
    historical_calibration_score: Decimal
    recent_drift_score: Decimal
    domain_difficulty_score: Decimal
    confidence_calibration_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("prediction_key", self.prediction_key)
        _require_canonical_string("domain_key", self.domain_key)
        for field_name in (
            "redacted_prediction_confidence",
            "historical_calibration_score",
            "recent_drift_score",
            "domain_difficulty_score",
            "confidence_calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("ResearchConfidenceCalibrationRow", self)
        _validate_row(self)
        _reject_unsafe_public_surface("row", self)
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _finalize_digest(self, self.derived_validation_digest),
        )


@dataclass(frozen=True)
class ResearchConfidenceCalibrationReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_calibration_score: Decimal | None
    max_recent_drift_score: Decimal | None
    max_domain_difficulty_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchConfidenceCalibrationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_calibration_score",
            "max_recent_drift_score",
            "max_domain_difficulty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("ResearchConfidenceCalibrationReport", self)
        _validate_report(self)
        _reject_unsafe_public_surface("report", self)
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _finalize_digest(self, self.derived_validation_digest),
        )


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


def build_research_confidence_calibration_report(
    inputs: Iterable[ResearchConfidenceCalibrationInput],
    *,
    config: ResearchConfidenceCalibrationConfig,
    generated_at: datetime,
) -> ResearchConfidenceCalibrationReport:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    if type(config) is not ResearchConfidenceCalibrationConfig:
        raise ValueError("config must be a ResearchConfidenceCalibrationConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("ResearchConfidenceCalibrationConfig", config)
    _reject_unsafe_public_surface("config", config)

    try:
        input_items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in input_items:
        if type(item) is not ResearchConfidenceCalibrationInput:
            raise ValueError(
                "inputs must contain ResearchConfidenceCalibrationInput values",
            )
        _require_hard_flags("ResearchConfidenceCalibrationInput", item)
        _reject_unsafe_public_surface("input", item)

    rows = tuple(
        _row_for_input(item, config=config)
        for item in sorted(input_items, key=lambda item: (item.prediction_key, item.domain_key))
    )
    return ResearchConfidenceCalibrationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(input_items)),
        pass_count=_count_decimal(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count_decimal(sum(1 for row in rows if row.status == "watch")),
        block_count=_count_decimal(sum(1 for row in rows if row.status == "block")),
        average_confidence_calibration_score=_average_score(rows),
        max_recent_drift_score=_max_metric(
            tuple(row.recent_drift_score for row in rows),
        ),
        max_domain_difficulty_score=_max_metric(
            tuple(row.domain_difficulty_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(_report_status(rows)),
        rows=rows,
    )


def research_confidence_calibration_report_payload(
    report: ResearchConfidenceCalibrationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchConfidenceCalibrationReport:
        _require_hard_flags("ResearchConfidenceCalibrationReport", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchConfidenceCalibrationReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_surface("payload", payload)
    _validate_payload_digests(payload)
    return payload


def _row_for_input(
    item: ResearchConfidenceCalibrationInput,
    *,
    config: ResearchConfidenceCalibrationConfig,
) -> ResearchConfidenceCalibrationRow:
    score = _confidence_calibration_score(item)
    status, reason_codes = _row_status(item, config=config)
    return ResearchConfidenceCalibrationRow(
        prediction_key=item.prediction_key,
        domain_key=item.domain_key,
        redacted_prediction_confidence=item.redacted_prediction_confidence,
        historical_calibration_score=item.historical_calibration_score,
        recent_drift_score=item.recent_drift_score,
        domain_difficulty_score=item.domain_difficulty_score,
        confidence_calibration_score=score,
        status=status,
        reason_codes=reason_codes,
    )


def _confidence_calibration_score(item: ResearchConfidenceCalibrationInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            (
                item.redacted_prediction_confidence
                + item.historical_calibration_score
                + (ONE - item.recent_drift_score)
                + (ONE - item.domain_difficulty_score)
            )
            / Decimal("4"),
        )


def _row_status(
    item: ResearchConfidenceCalibrationInput,
    *,
    config: ResearchConfidenceCalibrationConfig,
) -> tuple[str, tuple[str, ...]]:
    block_reasons: list[str] = []
    if item.redacted_prediction_confidence < config.min_watch_prediction_confidence:
        block_reasons.append("prediction_confidence_block")
    if item.historical_calibration_score < config.min_watch_historical_calibration:
        block_reasons.append("historical_calibration_block")
    if item.recent_drift_score > config.max_watch_recent_drift:
        block_reasons.append("recent_drift_block")
    if item.domain_difficulty_score > config.max_watch_domain_difficulty:
        block_reasons.append("domain_difficulty_block")
    if block_reasons:
        return "block", _prioritized_reason_codes(tuple(block_reasons))

    watch_reasons: list[str] = []
    if item.redacted_prediction_confidence < config.min_pass_prediction_confidence:
        watch_reasons.append("prediction_confidence_watch")
    if item.historical_calibration_score < config.min_pass_historical_calibration:
        watch_reasons.append("historical_calibration_watch")
    if item.recent_drift_score > config.max_pass_recent_drift:
        watch_reasons.append("recent_drift_watch")
    if item.domain_difficulty_score > config.max_pass_domain_difficulty:
        watch_reasons.append("domain_difficulty_watch")
    if watch_reasons:
        return "watch", _prioritized_reason_codes(tuple(watch_reasons))
    return "pass", (PASS_REASON,)


def _report_status(rows: tuple[ResearchConfidenceCalibrationRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(status: str) -> tuple[str, ...]:
    return REPORT_REASON_CODES[status]


def _average_score(rows: tuple[ResearchConfidenceCalibrationRow, ...]) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            sum((row.confidence_calibration_score for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _max_metric(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(max(values))


def _validate_row(row: ResearchConfidenceCalibrationRow) -> None:
    expected_score = _confidence_calibration_score(
        ResearchConfidenceCalibrationInput(
            prediction_key=row.prediction_key,
            domain_key=row.domain_key,
            redacted_prediction_confidence=row.redacted_prediction_confidence,
            historical_calibration_score=row.historical_calibration_score,
            recent_drift_score=row.recent_drift_score,
            domain_difficulty_score=row.domain_difficulty_score,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        ),
    )
    if row.confidence_calibration_score != expected_score:
        raise ValueError("confidence_calibration_score must match row inputs")
    if row.status == "pass":
        if row.reason_codes != (PASS_REASON,):
            raise ValueError("reason_codes must match pass status")
        return
    if row.status == "watch":
        if not row.reason_codes or any(
            reason_code not in WATCH_REASON_CODES for reason_code in row.reason_codes
        ):
            raise ValueError("watch rows require watch reason_codes")
        return
    if not row.reason_codes or any(
        reason_code not in BLOCK_REASON_CODES for reason_code in row.reason_codes
    ):
        raise ValueError("block rows require block reason_codes")


def _validate_report(report: ResearchConfidenceCalibrationReport) -> None:
    if report.input_count != _count_decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _count_decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("input_count must match status counts")
    if report.average_confidence_calibration_score != _average_score(report.rows):
        raise ValueError("average_confidence_calibration_score must match rows")
    if report.max_recent_drift_score != _max_metric(
        tuple(row.recent_drift_score for row in report.rows),
    ):
        raise ValueError("max_recent_drift_score must match rows")
    if report.max_domain_difficulty_score != _max_metric(
        tuple(row.domain_difficulty_score for row in report.rows),
    ):
        raise ValueError("max_domain_difficulty_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.status):
        raise ValueError("reason_codes must match status")


def _normalize_rows(value: object) -> tuple[ResearchConfidenceCalibrationRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchConfidenceCalibrationRow:
            raise ValueError("rows must contain ResearchConfidenceCalibrationRow values")
        _require_hard_flags("ResearchConfidenceCalibrationRow", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.prediction_key, row.domain_key)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by prediction_key and domain_key")
    row_keys = tuple((row.prediction_key, row.domain_key) for row in rows)
    if len(set(row_keys)) != len(row_keys):
        raise ValueError("rows must use unique prediction_key and domain_key values")
    return rows


def _prioritized_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason for reason in REASON_CODE_PRIORITY if reason in value)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not items:
        raise ValueError("reason_codes must contain canonical strings")
    for item in items:
        _require_canonical_string("reason_codes", item)
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must be unique")
    return items


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(value)


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return value.quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("ratio must be a Decimal")
    if not value.is_finite():
        raise ValueError("ratio must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public surface in {field_name}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _finalize_digest(value: object, supplied_digest: str) -> str:
    expected_digest = _derived_validation_digest(value)
    if supplied_digest == "":
        return expected_digest
    if type(supplied_digest) is not str or supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload")
    return supplied_digest


def _derived_validation_digest(value: object) -> str:
    ready = _json_ready(_digest_source(value))
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest_source(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_source(getattr(value, field.name))
            for field in fields(value)
            if field.name != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, dict):
        return {
            key: _digest_source(item)
            for key, item in value.items()
            if key != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, (list, tuple)):
        return [_digest_source(item) for item in value]
    return value


def _validate_payload_digests(value: object) -> None:
    if isinstance(value, dict):
        requires_digest = HARD_FLAG_FIELDS.issubset(value) and (
            "rows" in value or "prediction_key" in value
        )
        if requires_digest and DERIVED_VALIDATION_DIGEST_FIELD not in value:
            raise ValueError("derived_validation_digest is required")
        if DERIVED_VALIDATION_DIGEST_FIELD in value:
            supplied = value[DERIVED_VALIDATION_DIGEST_FIELD]
            expected = _derived_validation_digest(value)
            if type(supplied) is not str or supplied != expected:
                raise ValueError("derived_validation_digest must match payload")
        for item in value.values():
            _validate_payload_digests(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digests(item)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public surface in {path or label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public surface in {label}: {key}")
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_surface(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_surface(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
