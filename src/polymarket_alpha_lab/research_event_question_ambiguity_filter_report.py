"""Pure report-only ambiguity filter for event question research."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any


CONFIG_VERSION = "research_event_question_ambiguity_filter_report"
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

PASS = "pass"
WATCH = "watch"
BLOCK = "block"
PUBLIC_STATUSES = (PASS, WATCH, BLOCK)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "_id",
    "id_",
    "slug",
    "raw_question",
    "question_text",
    "question",
    "source_ref",
    "source_reference",
    "storage",
    "auth",
    "trad" + "ing",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "_id",
    "id_",
    "-id",
    " id",
    "candidate",
    "market_id",
    "market-id",
    "market id",
    "market_slug",
    "market-slug",
    "market slug",
    "slug",
    "source_ref",
    "source-reference",
    "source reference",
    "source_reference",
    "storage",
    "auth",
    "trad" + "ing",
)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityFilterConfig:
    config_version: str = CONFIG_VERSION
    rule_clarity_watch_floor: Decimal = Decimal("0.750000")
    rule_clarity_block_floor: Decimal = Decimal("0.500000")
    condition_specificity_watch_floor: Decimal = Decimal("0.750000")
    condition_specificity_block_floor: Decimal = Decimal("0.500000")
    edge_case_watch_count: Decimal = Decimal("2")
    edge_case_block_count: Decimal = Decimal("5")
    resolution_source_consistency_watch_floor: Decimal = Decimal("0.700000")
    resolution_source_consistency_block_floor: Decimal = Decimal("0.500000")
    deadline_clarity_watch_floor: Decimal = Decimal("0.750000")
    deadline_clarity_block_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityFilterConfig:
            raise TypeError(
                "ResearchEventQuestionAmbiguityFilterConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityFilterConfig:
            raise ValueError(
                "config must be exactly ResearchEventQuestionAmbiguityFilterConfig",
            )
        _require_internal_string("config_version", self.config_version)
        for field_name in (
            "rule_clarity_watch_floor",
            "rule_clarity_block_floor",
            "condition_specificity_watch_floor",
            "condition_specificity_block_floor",
            "resolution_source_consistency_watch_floor",
            "resolution_source_consistency_block_floor",
            "deadline_clarity_watch_floor",
            "deadline_clarity_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("edge_case_watch_count", "edge_case_block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "rule_clarity",
            self.rule_clarity_block_floor,
            self.rule_clarity_watch_floor,
        )
        _require_floor_pair(
            "condition_specificity",
            self.condition_specificity_block_floor,
            self.condition_specificity_watch_floor,
        )
        _require_floor_pair(
            "resolution_source_consistency",
            self.resolution_source_consistency_block_floor,
            self.resolution_source_consistency_watch_floor,
        )
        _require_floor_pair(
            "deadline_clarity",
            self.deadline_clarity_block_floor,
            self.deadline_clarity_watch_floor,
        )
        if self.edge_case_watch_count <= ZERO:
            raise ValueError("edge_case_watch_count must be positive")
        if self.edge_case_block_count < self.edge_case_watch_count:
            raise ValueError("edge_case_block_count must be at least edge_case_watch_count")
        _require_hard_flags("ambiguity filter config", self)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityFilterSubject:
    public_event_bucket: str
    aggregate_rule_clarity: Decimal
    condition_specificity: Decimal
    edge_case_count: Decimal
    resolution_source_consistency: Decimal
    deadline_clarity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityFilterSubject:
            raise TypeError(
                "ResearchEventQuestionAmbiguityFilterSubject does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityFilterSubject:
            raise ValueError(
                "subject must be exactly ResearchEventQuestionAmbiguityFilterSubject",
            )
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "aggregate_rule_clarity",
            "condition_specificity",
            "resolution_source_consistency",
            "deadline_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_case_count",
            _normalize_count_decimal("edge_case_count", self.edge_case_count),
        )
        _require_hard_flags("ambiguity filter subject", self)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityFilterRow:
    public_event_bucket: str
    aggregate_rule_clarity: Decimal
    condition_specificity: Decimal
    edge_case_count: Decimal
    resolution_source_consistency: Decimal
    deadline_clarity: Decimal
    ambiguity_score: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityFilterRow:
            raise TypeError(
                "ResearchEventQuestionAmbiguityFilterRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityFilterRow:
            raise ValueError("row must be exactly ResearchEventQuestionAmbiguityFilterRow")
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "aggregate_rule_clarity",
            "condition_specificity",
            "resolution_source_consistency",
            "deadline_clarity",
            "ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_case_count",
            _normalize_count_decimal("edge_case_count", self.edge_case_count),
        )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=self.public_status == PASS),
        )
        _validate_row_consistency(self)
        _require_hard_flags("ambiguity filter row", self)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityFilterReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    lowest_rule_clarity: Decimal
    lowest_condition_specificity: Decimal
    highest_edge_case_count: Decimal
    lowest_resolution_source_consistency: Decimal
    lowest_deadline_clarity: Decimal
    highest_ambiguity_score: Decimal
    status: str
    rows: tuple[ResearchEventQuestionAmbiguityFilterRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityFilterReport:
            raise TypeError(
                "ResearchEventQuestionAmbiguityFilterReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityFilterReport:
            raise ValueError(
                "report must be exactly ResearchEventQuestionAmbiguityFilterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_internal_string("config_version", self.config_version)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_rule_clarity",
            "lowest_condition_specificity",
            "highest_edge_case_count",
            "lowest_resolution_source_consistency",
            "lowest_deadline_clarity",
            "highest_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_payload_digest == "":
            object.__setattr__(self, "derived_payload_digest", _report_payload_digest(self))
        _require_sha256_digest("derived_payload_digest", self.derived_payload_digest)
        _validate_report_consistency(self)
        _require_hard_flags("ambiguity filter report", self)
        _require_report_payload_digest(self)
        _reject_unsafe_public_payload(_payload_value(asdict(self)))


def build_research_event_question_ambiguity_filter_report(
    subjects: tuple[ResearchEventQuestionAmbiguityFilterSubject, ...],
    *,
    generated_at: datetime,
    config: ResearchEventQuestionAmbiguityFilterConfig,
) -> ResearchEventQuestionAmbiguityFilterReport:
    if type(subjects) is not tuple:
        raise ValueError("subjects must be a tuple")
    if type(config) is not ResearchEventQuestionAmbiguityFilterConfig:
        raise ValueError("config must be a ResearchEventQuestionAmbiguityFilterConfig")
    rows = tuple(
        sorted(
            (_build_row(subject=subject, config=config) for subject in subjects),
            key=lambda row: row.public_event_bucket,
        ),
    )
    return ResearchEventQuestionAmbiguityFilterReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_count=_count_status(rows, PASS),
        watch_count=_count_status(rows, WATCH),
        block_count=_count_status(rows, BLOCK),
        lowest_rule_clarity=_minimum(row.aggregate_rule_clarity for row in rows),
        lowest_condition_specificity=_minimum(row.condition_specificity for row in rows),
        highest_edge_case_count=_maximum(row.edge_case_count for row in rows),
        lowest_resolution_source_consistency=_minimum(
            row.resolution_source_consistency for row in rows
        ),
        lowest_deadline_clarity=_minimum(row.deadline_clarity for row in rows),
        highest_ambiguity_score=_maximum(row.ambiguity_score for row in rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_question_ambiguity_filter_payload(
    report: ResearchEventQuestionAmbiguityFilterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventQuestionAmbiguityFilterReport:
        _validate_report_consistency(report)
        _require_report_payload_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a ResearchEventQuestionAmbiguityFilterReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    *,
    subject: ResearchEventQuestionAmbiguityFilterSubject,
    config: ResearchEventQuestionAmbiguityFilterConfig,
) -> ResearchEventQuestionAmbiguityFilterRow:
    if type(subject) is not ResearchEventQuestionAmbiguityFilterSubject:
        raise ValueError(
            "subjects must contain ResearchEventQuestionAmbiguityFilterSubject values",
        )
    reason_codes = _row_reason_codes(subject=subject, config=config)
    return ResearchEventQuestionAmbiguityFilterRow(
        public_event_bucket=subject.public_event_bucket,
        aggregate_rule_clarity=subject.aggregate_rule_clarity,
        condition_specificity=subject.condition_specificity,
        edge_case_count=subject.edge_case_count,
        resolution_source_consistency=subject.resolution_source_consistency,
        deadline_clarity=subject.deadline_clarity,
        ambiguity_score=_ambiguity_score(subject, config),
        public_status=_public_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    subject: ResearchEventQuestionAmbiguityFilterSubject,
    config: ResearchEventQuestionAmbiguityFilterConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_floor_reason(
        codes,
        metric_name="low_rule_clarity",
        value=subject.aggregate_rule_clarity,
        watch_floor=config.rule_clarity_watch_floor,
        block_floor=config.rule_clarity_block_floor,
    )
    _append_floor_reason(
        codes,
        metric_name="low_condition_specificity",
        value=subject.condition_specificity,
        watch_floor=config.condition_specificity_watch_floor,
        block_floor=config.condition_specificity_block_floor,
    )
    if subject.edge_case_count >= config.edge_case_block_count:
        codes.append("edge_case_count_block")
    elif subject.edge_case_count >= config.edge_case_watch_count:
        codes.append("edge_case_count_watch")
    _append_floor_reason(
        codes,
        metric_name="inconsistent_resolution_source",
        value=subject.resolution_source_consistency,
        watch_floor=config.resolution_source_consistency_watch_floor,
        block_floor=config.resolution_source_consistency_block_floor,
    )
    _append_floor_reason(
        codes,
        metric_name="unclear_deadline",
        value=subject.deadline_clarity,
        watch_floor=config.deadline_clarity_watch_floor,
        block_floor=config.deadline_clarity_block_floor,
    )
    return _normalize_reason_codes(tuple(codes), allow_empty=True)


def _append_floor_reason(
    codes: list[str],
    *,
    metric_name: str,
    value: Decimal,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if value <= block_floor:
        codes.append(f"{metric_name}_block")
    elif value <= watch_floor:
        codes.append(f"{metric_name}_watch")


def _ambiguity_score(
    subject: ResearchEventQuestionAmbiguityFilterSubject,
    config: ResearchEventQuestionAmbiguityFilterConfig,
) -> Decimal:
    edge_pressure = min(ONE, subject.edge_case_count / config.edge_case_block_count)
    return _quantize(
        (
            (ONE - subject.aggregate_rule_clarity)
            + (ONE - subject.condition_specificity)
            + edge_pressure
            + (ONE - subject.resolution_source_consistency)
            + (ONE - subject.deadline_clarity)
        )
        / Decimal("5"),
    )


def _public_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return BLOCK
    if reason_codes:
        return WATCH
    return PASS


def _report_status(rows: tuple[ResearchEventQuestionAmbiguityFilterRow, ...]) -> str:
    if any(row.public_status == BLOCK for row in rows):
        return BLOCK
    if any(row.public_status == WATCH for row in rows):
        return WATCH
    return PASS


def _reason_code_counts(
    rows: tuple[ResearchEventQuestionAmbiguityFilterRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, _count(counter[code])) for code in sorted(counter))


def _count_status(
    rows: tuple[ResearchEventQuestionAmbiguityFilterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.public_status == status))


def _minimum(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(min(items))


def _maximum(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(max(items))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return _quantize(Decimal(value))


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventQuestionAmbiguityFilterRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is ResearchEventQuestionAmbiguityFilterRow for row in rows):
        raise ValueError("rows must contain ResearchEventQuestionAmbiguityFilterRow values")
    if rows != tuple(sorted(rows, key=lambda row: row.public_event_bucket)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts values must be pairs")
        code, count = item
        _require_public_string("reason_code_counts", code)
        if previous is not None and previous > code:
            raise ValueError("reason_code_counts must be sorted")
        normalized.append((code, _normalize_count_decimal("reason_code_counts", count)))
        previous = code
    return tuple(normalized)


def _normalize_reason_codes(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError("reason_codes is required")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_public_string("reason_codes", code)
    return tuple(sorted(codes))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_floor_pair(name: str, block_floor: Decimal, watch_floor: Decimal) -> None:
    if block_floor > watch_floor:
        raise ValueError(f"{name} block floor must be at most watch floor")


def _require_internal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be one line")


def _require_public_string(field_name: str, value: object) -> None:
    _require_internal_string(field_name, value)
    _reject_raw_question_text(value)
    _reject_unsafe_public_value(value)


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_row_consistency(row: ResearchEventQuestionAmbiguityFilterRow) -> None:
    if row.public_status != _public_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")


def _validate_report_consistency(report: ResearchEventQuestionAmbiguityFilterReport) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _count_status(rows, PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(rows, WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(rows, BLOCK):
        raise ValueError("block_count must match rows")
    if report.lowest_rule_clarity != _minimum(row.aggregate_rule_clarity for row in rows):
        raise ValueError("lowest_rule_clarity must match rows")
    if report.lowest_condition_specificity != _minimum(
        row.condition_specificity for row in rows
    ):
        raise ValueError("lowest_condition_specificity must match rows")
    if report.highest_edge_case_count != _maximum(row.edge_case_count for row in rows):
        raise ValueError("highest_edge_case_count must match rows")
    if report.lowest_resolution_source_consistency != _minimum(
        row.resolution_source_consistency for row in rows
    ):
        raise ValueError("lowest_resolution_source_consistency must match rows")
    if report.lowest_deadline_clarity != _minimum(row.deadline_clarity for row in rows):
        raise ValueError("lowest_deadline_clarity must match rows")
    if report.highest_ambiguity_score != _maximum(row.ambiguity_score for row in rows):
        raise ValueError("highest_ambiguity_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_report_payload_digest(report: ResearchEventQuestionAmbiguityFilterReport) -> None:
    if report.derived_payload_digest != _report_payload_digest(report):
        raise ValueError("derived_payload_digest does not match report payload")


def _report_payload_digest(report: ResearchEventQuestionAmbiguityFilterReport) -> str:
    payload = _payload_value(asdict(report))
    payload["derived_payload_digest"] = ""
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload["derived_payload_digest"] = ""
    encoded = json.dumps(digest_payload, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("payload values must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(payload)
    _reject_payload_values(payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    digest = payload.get("derived_payload_digest")
    _require_sha256_digest("derived_payload_digest", digest)
    if digest != _payload_digest(payload):
        raise ValueError("derived_payload_digest does not match payload")


def _reject_payload_values(value: object) -> None:
    if type(value) is int:
        raise ValueError("payload values must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_payload_values(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            _reject_unsafe_public_key(key)
            if key != "config_version" and type(item) is str:
                _reject_raw_question_text(item)
                _reject_unsafe_public_value(item)
            else:
                _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)


def _reject_raw_question_text(value: str) -> None:
    lowered = value.lower()
    if "?" in value or lowered.startswith(("will ", "when ", "what ", "which ", "who ")):
        raise ValueError("raw question text is not public-safe")


def _reject_unsafe_public_key(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError("unsafe public payload field")


def _reject_unsafe_public_value(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError("unsafe public value")


@dataclass(frozen=True)
class _PayloadFlags:
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


__all__ = (
    "ResearchEventQuestionAmbiguityFilterConfig",
    "ResearchEventQuestionAmbiguityFilterReport",
    "ResearchEventQuestionAmbiguityFilterRow",
    "ResearchEventQuestionAmbiguityFilterSubject",
    "build_research_event_question_ambiguity_filter_report",
    "research_event_question_ambiguity_filter_payload",
)
