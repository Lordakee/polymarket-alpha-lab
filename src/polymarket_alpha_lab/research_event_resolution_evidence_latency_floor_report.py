"""In-memory report-only event-resolution evidence latency floor report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


CONFIG_VERSION = "research_event_resolution_evidence_latency_floor_report_v1"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)


@dataclass(frozen=True)
class EventResolutionEvidenceLatencyFloorConfig:
    config_version: str = CONFIG_VERSION
    minimum_latency_floor_seconds: Decimal = Decimal("1200")
    minimum_independent_source_count: Decimal = Decimal("3")
    minimum_official_source_count: Decimal = Decimal("2")
    conflict_penalty_full_count: Decimal = Decimal("6")
    pass_evidence_score_threshold: Decimal = Decimal("0.8500")
    block_evidence_score_threshold: Decimal = Decimal("0.5000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionEvidenceLatencyFloorConfig:
            raise TypeError(
                "EventResolutionEvidenceLatencyFloorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EventResolutionEvidenceLatencyFloorConfig:
            raise ValueError("config must be exactly EventResolutionEvidenceLatencyFloorConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_latency_floor_seconds",
            "minimum_independent_source_count",
            "minimum_official_source_count",
            "conflict_penalty_full_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_evidence_score_threshold",
            "block_evidence_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_evidence_score_threshold <= self.block_evidence_score_threshold:
            raise ValueError(
                "pass_evidence_score_threshold must exceed block_evidence_score_threshold",
            )
        require_paper_only_flags("event resolution evidence latency floor config", self)


@dataclass(frozen=True)
class EventResolutionEvidenceLatencyFloorInput:
    private_candidate_ref: str
    resolved_at: datetime
    first_evidence_at: datetime
    independent_source_count: Decimal
    official_source_count: Decimal
    corroborating_source_count: Decimal
    conflicting_source_count: Decimal
    evidence_confidence: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionEvidenceLatencyFloorInput:
            raise TypeError(
                "EventResolutionEvidenceLatencyFloorInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EventResolutionEvidenceLatencyFloorInput:
            raise ValueError("input must be exactly EventResolutionEvidenceLatencyFloorInput")
        _require_canonical_string("private_candidate_ref", self.private_candidate_ref)
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        object.__setattr__(
            self,
            "first_evidence_at",
            _as_utc("first_evidence_at", self.first_evidence_at),
        )
        for field_name in (
            "independent_source_count",
            "official_source_count",
            "corroborating_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.official_source_count > self.independent_source_count:
            raise ValueError("official_source_count must not exceed independent_source_count")
        if self.corroborating_source_count > self.independent_source_count:
            raise ValueError(
                "corroborating_source_count must not exceed independent_source_count",
            )
        object.__setattr__(
            self,
            "evidence_confidence",
            _normalize_probability("evidence_confidence", self.evidence_confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("event resolution evidence latency floor input", self)


@dataclass(frozen=True)
class EventResolutionEvidenceLatencyFloorRow:
    public_row_id: str
    resolved_at: datetime
    first_evidence_at: datetime
    latency_seconds: Decimal
    latency_floor_score: Decimal
    independent_source_count: Decimal
    official_source_count: Decimal
    corroborating_source_count: Decimal
    conflicting_source_count: Decimal
    evidence_confidence: Decimal
    evidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionEvidenceLatencyFloorRow:
            raise TypeError(
                "EventResolutionEvidenceLatencyFloorRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EventResolutionEvidenceLatencyFloorRow:
            raise ValueError("row must be exactly EventResolutionEvidenceLatencyFloorRow")
        _require_public_row_id(self.public_row_id)
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        object.__setattr__(
            self,
            "first_evidence_at",
            _as_utc("first_evidence_at", self.first_evidence_at),
        )
        object.__setattr__(
            self,
            "latency_seconds",
            _normalize_finite_decimal("latency_seconds", self.latency_seconds),
        )
        for field_name in (
            "latency_floor_score",
            "evidence_confidence",
            "evidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_source_count",
            "official_source_count",
            "corroborating_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status not in self.reason_codes:
            raise ValueError("reason_codes must include status")
        require_paper_only_flags("event resolution evidence latency floor row", self)


@dataclass(frozen=True)
class EventResolutionEvidenceLatencyFloorReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    median_latency_seconds: Decimal | None
    floor_latency_seconds: Decimal | None
    strongest_evidence_score: Decimal
    weakest_evidence_score: Decimal
    rows: tuple[EventResolutionEvidenceLatencyFloorRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionEvidenceLatencyFloorReport:
            raise TypeError(
                "EventResolutionEvidenceLatencyFloorReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EventResolutionEvidenceLatencyFloorReport:
            raise ValueError("report must be exactly EventResolutionEvidenceLatencyFloorReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("median_latency_seconds", "floor_latency_seconds"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_finite_decimal(field_name, value),
                )
        for field_name in ("strongest_evidence_score", "weakest_evidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _report_digest(self))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        require_paper_only_flags("event resolution evidence latency floor report", self)
        _require_report_digest(self)
        _reject_unsafe_public_payload(_report_payload_without_digest(self))


def build_research_event_resolution_evidence_latency_floor_report(
    inputs: tuple[EventResolutionEvidenceLatencyFloorInput, ...],
    *,
    generated_at: datetime,
    config: EventResolutionEvidenceLatencyFloorConfig,
) -> EventResolutionEvidenceLatencyFloorReport:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    if type(config) is not EventResolutionEvidenceLatencyFloorConfig:
        raise ValueError("config must be an EventResolutionEvidenceLatencyFloorConfig")
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(sorted((_row_from_input(item, config) for item in inputs), key=_row_sort_key))
    return EventResolutionEvidenceLatencyFloorReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        median_latency_seconds=_median(row.latency_seconds for row in rows),
        floor_latency_seconds=_minimum(row.latency_seconds for row in rows),
        strongest_evidence_score=_maximum(row.evidence_score for row in rows),
        weakest_evidence_score=_minimum(row.evidence_score for row in rows) or ZERO,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_resolution_evidence_latency_floor_payload(
    report: EventResolutionEvidenceLatencyFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is EventResolutionEvidenceLatencyFloorReport:
        require_paper_only_flags("event resolution evidence latency floor report", report)
        _validate_report_consistency(report)
        _require_report_digest(report)
        payload = _report_payload(report)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be an EventResolutionEvidenceLatencyFloorReport or object")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _row_from_input(
    item: EventResolutionEvidenceLatencyFloorInput,
    config: EventResolutionEvidenceLatencyFloorConfig,
) -> EventResolutionEvidenceLatencyFloorRow:
    if type(item) is not EventResolutionEvidenceLatencyFloorInput:
        raise ValueError("inputs must contain EventResolutionEvidenceLatencyFloorInput values")
    latency_seconds = _duration_seconds(item.resolved_at, item.first_evidence_at)
    latency_floor_score = _latency_floor_score(latency_seconds, config)
    independent_score = _capped_ratio(
        item.independent_source_count,
        config.minimum_independent_source_count,
    )
    official_score = _capped_ratio(
        item.official_source_count,
        config.minimum_official_source_count,
    )
    conflict_score = _capped_ratio(
        item.conflicting_source_count,
        config.conflict_penalty_full_count,
    )
    evidence_score = _evidence_score(
        latency_floor_score=latency_floor_score,
        independent_score=independent_score,
        official_score=official_score,
        conflict_score=conflict_score,
        confidence_score=item.evidence_confidence,
    )
    status = _status(
        latency_seconds=latency_seconds,
        latency_floor_score=latency_floor_score,
        evidence_score=evidence_score,
        config=config,
    )
    return EventResolutionEvidenceLatencyFloorRow(
        public_row_id=_public_row_id(item.private_candidate_ref),
        resolved_at=item.resolved_at,
        first_evidence_at=item.first_evidence_at,
        latency_seconds=latency_seconds,
        latency_floor_score=latency_floor_score,
        independent_source_count=item.independent_source_count,
        official_source_count=item.official_source_count,
        corroborating_source_count=item.corroborating_source_count,
        conflicting_source_count=item.conflicting_source_count,
        evidence_confidence=item.evidence_confidence,
        evidence_score=evidence_score,
        status=status,
        reason_codes=_row_reason_codes(item.reason_codes, latency_seconds=latency_seconds, status=status),
    )


def _public_row_id(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"candidate:{digest[:12]}"


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _quantize(seconds)


def _latency_floor_score(
    latency_seconds: Decimal,
    config: EventResolutionEvidenceLatencyFloorConfig,
) -> Decimal:
    if latency_seconds <= ZERO:
        return ZERO
    return _capped_ratio(latency_seconds, config.minimum_latency_floor_seconds)


def _evidence_score(
    *,
    latency_floor_score: Decimal,
    independent_score: Decimal,
    official_score: Decimal,
    conflict_score: Decimal,
    confidence_score: Decimal,
) -> Decimal:
    base_score = (
        latency_floor_score
        + independent_score
        + official_score
        + confidence_score
    ) / Decimal("4")
    penalty = conflict_score / Decimal("4")
    return _clamp_probability(base_score - penalty)


def _status(
    *,
    latency_seconds: Decimal,
    latency_floor_score: Decimal,
    evidence_score: Decimal,
    config: EventResolutionEvidenceLatencyFloorConfig,
) -> str:
    if latency_seconds < ZERO or evidence_score < config.block_evidence_score_threshold:
        return STATUS_BLOCK
    if (
        latency_floor_score == ONE
        and evidence_score >= config.pass_evidence_score_threshold
    ):
        return STATUS_PASS
    return STATUS_WATCH


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    latency_seconds: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes = set(existing_reason_codes)
    reason_codes.add(status)
    if latency_seconds < ZERO:
        reason_codes.add("pre_resolution_evidence")
    return tuple(sorted(reason_codes))


def _row_sort_key(row: EventResolutionEvidenceLatencyFloorRow) -> tuple[str, datetime, datetime]:
    return (row.public_row_id, row.resolved_at, row.first_evidence_at)


def _reason_code_counts(
    rows: tuple[EventResolutionEvidenceLatencyFloorRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, _quantize(Decimal(counter[code]))) for code in sorted(counter))


def _count_status(rows: tuple[EventResolutionEvidenceLatencyFloorRow, ...], status: str) -> Decimal:
    return _quantize(Decimal(sum(1 for row in rows if row.status == status)))


def _median(values: Any) -> Decimal | None:
    items = tuple(sorted(values))
    if not items:
        return None
    middle = len(items) // 2
    if len(items) % 2:
        return _quantize(items[middle])
    return _quantize((items[middle - 1] + items[middle]) / Decimal("2"))


def _minimum(values: Any) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(min(items))


def _maximum(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(max(items))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    if numerator >= denominator:
        return ONE
    return _quantize(numerator / denominator)


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _quantize(value)


def _normalize_rows(
    value: object,
) -> tuple[EventResolutionEvidenceLatencyFloorRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is EventResolutionEvidenceLatencyFloorRow for row in rows):
        raise ValueError("rows must contain EventResolutionEvidenceLatencyFloorRow values")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
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
        _require_canonical_string("reason_code_counts", code)
        if previous is not None and previous > code:
            raise ValueError("reason_code_counts must be sorted")
        normalized.append((code, _normalize_count_decimal("reason_code_counts", count)))
        previous = code
    return tuple(normalized)


def _normalize_reason_codes(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes is required")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(reason_codes))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _require_public_row_id(value: object) -> None:
    _require_canonical_string("public_row_id", value)
    if not isinstance(value, str):
        raise ValueError("public_row_id must be a string")
    prefix = "candidate:"
    suffix = value.removeprefix(prefix)
    if len(suffix) != 12 or suffix == value:
        raise ValueError("public_row_id must use a redacted candidate digest")
    if any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError("public_row_id must use a hex digest")


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_report_consistency(report: EventResolutionEvidenceLatencyFloorReport) -> None:
    rows = report.rows
    if report.row_count != _quantize(Decimal(len(rows))):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count_status(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.median_latency_seconds != _median(row.latency_seconds for row in rows):
        raise ValueError("median_latency_seconds must match rows")
    if report.floor_latency_seconds != _minimum(row.latency_seconds for row in rows):
        raise ValueError("floor_latency_seconds must match rows")
    if report.strongest_evidence_score != _maximum(row.evidence_score for row in rows):
        raise ValueError("strongest_evidence_score must match rows")
    weakest = _minimum(row.evidence_score for row in rows) or ZERO
    if report.weakest_evidence_score != weakest:
        raise ValueError("weakest_evidence_score must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _report_payload(report: EventResolutionEvidenceLatencyFloorReport) -> dict[str, Any]:
    payload = _report_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    payload["paper_only"] = report.paper_only
    payload["report_only"] = report.report_only
    payload["readonly"] = report.readonly
    return payload


def _report_payload_without_digest(
    report: EventResolutionEvidenceLatencyFloorReport,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(report):
        if field.name in {
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        payload[field.name] = _payload_value(getattr(report, field.name))
    payload["paper_only"] = report.paper_only
    payload["report_only"] = report.report_only
    payload["readonly"] = report.readonly
    return payload


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        for field in fields(value):
            payload[field.name] = _payload_value(getattr(value, field.name))
        return payload
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _report_digest(report: EventResolutionEvidenceLatencyFloorReport) -> str:
    return _payload_digest(_report_payload_without_digest(report))


def _require_report_digest(report: EventResolutionEvidenceLatencyFloorReport) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(payload)
    _require_exact_keys("payload", payload, _PUBLIC_PAYLOAD_KEYS)
    require_paper_only_flags("event resolution evidence latency floor payload", _PayloadFlags(payload))
    _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    for key, value in payload.items():
        _validate_payload_json_value(key, value)
    for field_name in (
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "strongest_evidence_score",
        "weakest_evidence_score",
    ):
        _decimal_from_payload(field_name, payload[field_name])
    for field_name in ("median_latency_seconds", "floor_latency_seconds"):
        value = payload[field_name]
        if value is not None:
            _decimal_from_payload(field_name, value)
    rows_payload = payload["rows"]
    if type(rows_payload) is not list:
        raise ValueError("rows must be a JSON list")
    for row_payload in rows_payload:
        _validate_public_row_payload(row_payload)
    reason_count_payload = payload["reason_code_counts"]
    if type(reason_count_payload) is not list:
        raise ValueError("reason_code_counts must be a JSON list")
    for item in reason_count_payload:
        _validate_public_reason_count_payload(item)
    payload_without_digest = {
        key: payload[key]
        for key in _PUBLIC_PAYLOAD_KEYS
        if key != "derived_validation_digest"
    }
    expected_digest = _payload_digest(payload_without_digest)
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_exact_keys("row", value, _PUBLIC_ROW_KEYS)
    _require_public_row_id(value["public_row_id"])
    _as_utc("resolved_at", _datetime_from_payload("resolved_at", value["resolved_at"]))
    _as_utc(
        "first_evidence_at",
        _datetime_from_payload("first_evidence_at", value["first_evidence_at"]),
    )
    for field_name in (
        "latency_seconds",
        "latency_floor_score",
        "independent_source_count",
        "official_source_count",
        "corroborating_source_count",
        "conflicting_source_count",
        "evidence_confidence",
        "evidence_score",
    ):
        _decimal_from_payload(field_name, value[field_name])
    _require_status("status", value["status"])
    reason_codes = value["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a JSON list")
    normalized_reason_codes = _normalize_reason_codes(tuple(reason_codes))
    if tuple(reason_codes) != normalized_reason_codes:
        raise ValueError("reason_codes must be sorted")
    if value["status"] not in normalized_reason_codes:
        raise ValueError("reason_codes must include status")


def _validate_public_reason_count_payload(value: object) -> None:
    if type(value) is not list or len(value) != 2:
        raise ValueError("reason_code_counts values must be pairs")
    code, count = value
    _require_canonical_string("reason_code_counts", code)
    _decimal_from_payload("reason_code_counts", count)


def _validate_payload_json_value(field_name: str, value: object) -> None:
    if type(value) in (str, bool) or value is None:
        return
    if type(value) is list:
        for item in value:
            _validate_payload_json_value(field_name, item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _validate_payload_json_value(key, item)
        return
    raise ValueError(f"{field_name} must be a public JSON value")


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(parsed)


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_exact_keys(label: str, value: dict[str, Any], expected_keys: tuple[str, ...]) -> None:
    actual = tuple(value.keys())
    if actual != expected_keys:
        raise ValueError(f"{label} keys must match public schema")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _reject_unsafe_public_payload(payload: object) -> None:
    reject_unsafe_surface_fields("event resolution evidence latency floor payload", payload)
    for key in _iter_payload_keys(payload):
        normalized = key.lower()
        if any(fragment in normalized for fragment in _EXTRA_FORBIDDEN_PUBLIC_KEY_FRAGMENTS):
            raise ValueError(f"unsafe public payload field: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


class _PayloadFlags:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


_PUBLIC_ROW_KEYS = (
    "public_row_id",
    "resolved_at",
    "first_evidence_at",
    "latency_seconds",
    "latency_floor_score",
    "independent_source_count",
    "official_source_count",
    "corroborating_source_count",
    "conflicting_source_count",
    "evidence_confidence",
    "evidence_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

_PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "median_latency_seconds",
    "floor_latency_seconds",
    "strongest_evidence_score",
    "weakest_evidence_score",
    "rows",
    "reason_code_counts",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)

_EXTRA_FORBIDDEN_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "".join(("candidate", "_id")),
        "".join(("market", "_id")),
        "".join(("market", "_slug")),
        "".join(("ques", "tion")),
        "".join(("source", "_url")),
        "".join(("source", "_text")),
        "".join(("d", "sn")),
        "".join(("tab", "le")),
        "".join(("tok", "en")),
        "".join(("wal", "let")),
        "".join(("or", "der")),
        "".join(("tr", "ade")),
        "".join(("siz", "ing")),
        "".join(("recomm", "endation")),
    ),
)

__all__ = (
    "EventResolutionEvidenceLatencyFloorConfig",
    "EventResolutionEvidenceLatencyFloorInput",
    "EventResolutionEvidenceLatencyFloorReport",
    "EventResolutionEvidenceLatencyFloorRow",
    "build_research_event_resolution_evidence_latency_floor_report",
    "research_event_resolution_evidence_latency_floor_payload",
)
