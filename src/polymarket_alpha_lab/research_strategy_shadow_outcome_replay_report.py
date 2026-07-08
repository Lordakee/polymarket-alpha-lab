from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from typing import Any, Iterable

DEFAULT_RESEARCH_STRATEGY_SHADOW_OUTCOME_REPLAY_REPORT_VERSION = (
    "research_strategy_shadow_outcome_replay_report_v1"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_UP)
STATUSES = ("pass", "watch", "block")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "research_strategy_shadow_outcome_replay_no_inputs"


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
class ResearchStrategyShadowOutcomeReplayConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_STRATEGY_SHADOW_OUTCOME_REPLAY_REPORT_VERSION
    probability_gap_watch: Decimal = Decimal("0.150000")
    probability_gap_block: Decimal = Decimal("0.300000")
    low_confidence_floor: Decimal = Decimal("0.550000")
    review_age_seconds_watch: Decimal = Decimal("2592000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyShadowOutcomeReplayConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "probability_gap_watch",
            "probability_gap_block",
            "low_confidence_floor",
            "review_age_seconds_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_probability("probability_gap_watch", self.probability_gap_watch)
        _require_probability("probability_gap_block", self.probability_gap_block)
        _require_probability("low_confidence_floor", self.low_confidence_floor)
        _require_at_most(
            "probability_gap_watch",
            self.probability_gap_watch,
            self.probability_gap_block,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyShadowOutcomeReplayInput(_FinalPublicDataclass):
    public_label: str
    submitted_probability: Decimal
    outcome_probability: Decimal
    calibration_weight: Decimal
    observed_at: datetime
    hypothetical: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyShadowOutcomeReplayInput, "input")
        _require_canonical_string("public_label", self.public_label)
        for field_name in ("submitted_probability", "outcome_probability"):
            value = _normalize_decimal(field_name, getattr(self, field_name))
            _require_probability(field_name, value)
            object.__setattr__(self, field_name, value)
        object.__setattr__(
            self,
            "calibration_weight",
            _normalize_positive_decimal("calibration_weight", self.calibration_weight),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.hypothetical) is not bool:
            raise ValueError("hypothetical must be a bool")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyShadowOutcomeReplayRow(_FinalPublicDataclass):
    public_label: str
    status: str
    submitted_probability: Decimal
    outcome_probability: Decimal
    absolute_probability_error: Decimal
    weighted_probability_error: Decimal
    calibration_weight: Decimal
    observed_at: datetime
    age_seconds: Decimal
    hypothetical: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyShadowOutcomeReplayRow, "row")
        _require_canonical_string("public_label", self.public_label)
        _require_status("status", self.status)
        for field_name in ("submitted_probability", "outcome_probability"):
            value = _normalize_decimal(field_name, getattr(self, field_name))
            _require_probability(field_name, value)
            object.__setattr__(self, field_name, value)
        for field_name in (
            "absolute_probability_error",
            "weighted_probability_error",
            "calibration_weight",
            "age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.calibration_weight <= ZERO:
            raise ValueError("calibration_weight must be positive")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.hypothetical) is not bool:
            raise ValueError("hypothetical must be a bool")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyShadowOutcomeReplayReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyShadowOutcomeReplayReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyShadowOutcomeReplayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hypothetical_count: Decimal
    mean_absolute_probability_error: Decimal
    max_absolute_probability_error: Decimal
    weighted_probability_error_total: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyShadowOutcomeReplayReasonCodeCount, ...]
    replay_rows: tuple[ResearchStrategyShadowOutcomeReplayRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyShadowOutcomeReplayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hypothetical_count",
            "mean_absolute_probability_error",
            "max_absolute_probability_error",
            "weighted_probability_error_total",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "replay_rows", _normalize_rows(self.replay_rows))
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchStrategyShadowOutcomeReplayConfig,
    ResearchStrategyShadowOutcomeReplayInput,
    ResearchStrategyShadowOutcomeReplayReasonCodeCount,
    ResearchStrategyShadowOutcomeReplayReport,
    ResearchStrategyShadowOutcomeReplayRow,
)


def build_research_strategy_shadow_outcome_replay_report(
    observations: Iterable[ResearchStrategyShadowOutcomeReplayInput],
    *,
    config: ResearchStrategyShadowOutcomeReplayConfig,
    generated_at: datetime,
) -> ResearchStrategyShadowOutcomeReplayReport:
    if type(config) is not ResearchStrategyShadowOutcomeReplayConfig:
        raise ValueError("config must be a ResearchStrategyShadowOutcomeReplayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations)
    rows = tuple(
        sorted(
            (
                _replay_row(row, config=config, generated_at=generated_at_utc)
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyShadowOutcomeReplayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        hypothetical_count=_count(sum(1 for row in rows if row.hypothetical)),
        mean_absolute_probability_error=_mean(
            tuple(row.absolute_probability_error for row in rows),
        ),
        max_absolute_probability_error=_max_decimal(
            tuple(row.absolute_probability_error for row in rows),
        ),
        weighted_probability_error_total=_sum_decimal(
            tuple(row.weighted_probability_error for row in rows),
        ),
        status=_rollup_status(tuple(row.status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        replay_rows=rows,
    )


def research_strategy_shadow_outcome_replay_report_payload(
    report: ResearchStrategyShadowOutcomeReplayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyShadowOutcomeReplayReport:
        raise ValueError("report must be a ResearchStrategyShadowOutcomeReplayReport")
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_shadow_outcome_replay_report_digest(
    report: ResearchStrategyShadowOutcomeReplayReport,
) -> str:
    payload = research_strategy_shadow_outcome_replay_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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


def _replay_row(
    row: ResearchStrategyShadowOutcomeReplayInput,
    *,
    config: ResearchStrategyShadowOutcomeReplayConfig,
    generated_at: datetime,
) -> ResearchStrategyShadowOutcomeReplayRow:
    age_seconds = _age_seconds(row.observed_at, generated_at)
    absolute_probability_error = _absolute_probability_error(row)
    reason_codes = _row_reason_codes(
        row,
        absolute_probability_error=absolute_probability_error,
        age_seconds=age_seconds,
        config=config,
    )
    return ResearchStrategyShadowOutcomeReplayRow(
        public_label=row.public_label,
        status=_row_status(reason_codes),
        submitted_probability=row.submitted_probability,
        outcome_probability=row.outcome_probability,
        absolute_probability_error=absolute_probability_error,
        weighted_probability_error=_quantize(
            absolute_probability_error * row.calibration_weight,
        ),
        calibration_weight=row.calibration_weight,
        observed_at=row.observed_at,
        age_seconds=age_seconds,
        hypothetical=row.hypothetical,
        reason_codes=reason_codes,
    )


def _absolute_probability_error(row: ResearchStrategyShadowOutcomeReplayInput) -> Decimal:
    difference = _quantize(row.submitted_probability - row.outcome_probability)
    if difference < ZERO:
        return _quantize(-difference)
    return difference


def _row_reason_codes(
    row: ResearchStrategyShadowOutcomeReplayInput,
    *,
    absolute_probability_error: Decimal,
    age_seconds: Decimal,
    config: ResearchStrategyShadowOutcomeReplayConfig,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    if absolute_probability_error >= config.probability_gap_block:
        reason_codes.append("probability_gap_block")
    elif absolute_probability_error >= config.probability_gap_watch:
        reason_codes.append("probability_gap_watch")
    if _conviction(row.submitted_probability) < config.low_confidence_floor:
        reason_codes.append("low_confidence_watch")
    if row.hypothetical:
        reason_codes.append("hypothetical_settlement_watch")
    if age_seconds > config.review_age_seconds_watch:
        reason_codes.append("replay_age_watch")
    if not _has_shadow_reason(reason_codes):
        reason_codes.append("shadow_replay_calibrated")
    return tuple(sorted(reason_codes))


def _conviction(probability: Decimal) -> Decimal:
    inverse = _quantize(ONE - probability)
    if probability >= inverse:
        return probability
    return inverse


def _has_shadow_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code.endswith("_watch") or reason_code.endswith("_block")
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ResearchStrategyShadowOutcomeReplayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"shadow_outcome_replay_{status}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "hypothetical_settlement_watch",
        "low_confidence_watch",
        "probability_gap_block",
        "probability_gap_watch",
        "replay_age_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyShadowOutcomeReplayRow, ...],
) -> tuple[ResearchStrategyShadowOutcomeReplayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyShadowOutcomeReplayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyShadowOutcomeReplayReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must be at or before generated_at")
    return _quantize(Decimal(str((generated_at - observed_at).total_seconds())))


def _normalize_inputs(
    observations: Iterable[ResearchStrategyShadowOutcomeReplayInput],
) -> tuple[ResearchStrategyShadowOutcomeReplayInput, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyShadowOutcomeReplayInput:
            raise ValueError(
                "observations must contain ResearchStrategyShadowOutcomeReplayInput values",
            )
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyShadowOutcomeReplayRow],
) -> tuple[ResearchStrategyShadowOutcomeReplayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("replay_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("replay_rows must be an iterable") from exc
    for row in values:
        if type(row) is not ResearchStrategyShadowOutcomeReplayRow:
            raise ValueError("replay_rows must contain ResearchStrategyShadowOutcomeReplayRow values")
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("replay_rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategyShadowOutcomeReplayReasonCodeCount],
) -> tuple[ResearchStrategyShadowOutcomeReplayReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchStrategyShadowOutcomeReplayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyShadowOutcomeReplayReasonCodeCount values",
            )
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _validate_report(report: ResearchStrategyShadowOutcomeReplayReport) -> None:
    rows = report.replay_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count does not match replay_rows")
    for status in STATUSES:
        field_name = f"{status}_count"
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} does not match replay_rows")
    if report.hypothetical_count != _count(sum(1 for row in rows if row.hypothetical)):
        raise ValueError("hypothetical_count does not match replay_rows")
    if report.mean_absolute_probability_error != _mean(
        tuple(row.absolute_probability_error for row in rows),
    ):
        raise ValueError("mean_absolute_probability_error does not match replay_rows")
    if report.max_absolute_probability_error != _max_decimal(
        tuple(row.absolute_probability_error for row in rows),
    ):
        raise ValueError("max_absolute_probability_error does not match replay_rows")
    if report.weighted_probability_error_total != _sum_decimal(
        tuple(row.weighted_probability_error for row in rows),
    ):
        raise ValueError("weighted_probability_error_total does not match replay_rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status does not match replay_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes do not match replay_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts do not match replay_rows")


def _status_count(
    rows: tuple[ResearchStrategyShadowOutcomeReplayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchStrategyShadowOutcomeReplayRow) -> tuple[Decimal, Decimal, str]:
    return (_status_rank(row.status), -row.absolute_probability_error, row.public_label)


def _status_rank(status: str) -> Decimal:
    if status == "block":
        return ZERO
    if status == "watch":
        return ONE
    return Decimal("2.000000")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        _require_six_decimal_decimal(path or label, value)
        return
    if isinstance(value, datetime):
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw" + "_" + "candidate",
    "candidate" + "_" + "id",
    "market" + "_" + "id",
    "market" + "_" + "slug",
    "market" + "_" + "question",
    "slug",
    "question",
    "sou" + "rce",
    "sou" + "rce" + "_" + "te" + "xt",
    "ref",
    "u" + "rl",
    "://",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wa" + "llet",
    "au" + "th",
    "or" + "der",
    "pos" + "ition",
    "tr" + "ade",
    "tra" + "ding",
    "li" + "ve",
    "bu" + "y",
    "se" + "ll",
    "re" + "commend",
    "be" + "t",
    "sta" + "ke",
)


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


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_reason_codes_tuple(reason_codes: object) -> None:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SHADOW_OUTCOME_REPLAY_REPORT_VERSION",
    "ResearchStrategyShadowOutcomeReplayConfig",
    "ResearchStrategyShadowOutcomeReplayInput",
    "ResearchStrategyShadowOutcomeReplayReasonCodeCount",
    "ResearchStrategyShadowOutcomeReplayReport",
    "ResearchStrategyShadowOutcomeReplayRow",
    "build_research_strategy_shadow_outcome_replay_report",
    "research_strategy_shadow_outcome_replay_report_digest",
    "research_strategy_shadow_outcome_replay_report_payload",
)
