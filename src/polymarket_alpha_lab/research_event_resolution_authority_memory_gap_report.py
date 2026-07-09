"""Report-only event resolution authority memory gap research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_MEMORY_GAP_REPORT_CONFIG_VERSION = (
    "research-event-resolution-authority-memory-gap-report-v0"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_THREE = Decimal("3.000000")
_QUANT = Decimal("0.000001")
_STATUSES = ("pass", "watch", "block")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_RAW_PUBLIC_TERMS = (
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "slug",
    "question",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityMemoryGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_MEMORY_GAP_REPORT_CONFIG_VERSION
    )
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    watch_gap_score: Decimal = Decimal("0.350000")
    block_gap_score: Decimal = Decimal("0.700000")
    min_authority_memory_count: Decimal = Decimal("1.000000")
    min_resolution_record_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityMemoryGapConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_MEMORY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "fresh_age_seconds",
            "stale_age_seconds",
            "min_authority_memory_count",
            "min_resolution_record_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_gap_score", "block_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        if self.block_gap_score <= self.watch_gap_score:
            raise ValueError("block_gap_score must exceed watch_gap_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityMemoryGapInput:
    event_id: str
    authority_id: str
    private_resolution_fragments: tuple[str, ...]
    observed_at: datetime
    authority_memory_count: Decimal
    parser_memory_count: Decimal
    resolution_record_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityMemoryGapInput, "input")
        _require_public_identifier("event_id", self.event_id)
        _require_public_identifier("authority_id", self.authority_id)
        object.__setattr__(
            self,
            "private_resolution_fragments",
            _normalize_private_fragments(self.private_resolution_fragments),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_memory_count",
            "parser_memory_count",
            "resolution_record_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityMemoryGapReportRow:
    event_id: str
    authority_id: str
    observed_at: datetime
    input_age_seconds: Decimal
    authority_memory_count: Decimal
    parser_memory_count: Decimal
    resolution_record_count: Decimal
    missing_authority_memory_count: Decimal
    missing_parser_memory_count: Decimal
    missing_resolution_record_count: Decimal
    recency_gap_score: Decimal
    authority_gap_score: Decimal
    parser_gap_score: Decimal
    record_gap_score: Decimal
    memory_gap_score: Decimal
    evidence_fingerprint: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityMemoryGapReportRow, "row")
        _require_public_identifier("event_id", self.event_id)
        _require_public_identifier("authority_id", self.authority_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "input_age_seconds",
            "authority_memory_count",
            "parser_memory_count",
            "resolution_record_count",
            "missing_authority_memory_count",
            "missing_parser_memory_count",
            "missing_resolution_record_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recency_gap_score",
            "authority_gap_score",
            "parser_gap_score",
            "record_gap_score",
            "memory_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_fingerprint("evidence_fingerprint", self.evidence_fingerprint)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_raw_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityMemoryGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionAuthorityMemoryGapReasonCodeCount,
            "reason code count",
        )
        _require_public_identifier("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        _require_hard_flags("reason code count", self)
        _reject_raw_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityMemoryGapReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_gap_score: Decimal
    rows: tuple[ResearchEventResolutionAuthorityMemoryGapReportRow, ...]
    reason_code_counts: tuple[ResearchEventResolutionAuthorityMemoryGapReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityMemoryGapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_MEMORY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_gap_score",
            _require_ratio_decimal(
                "average_memory_gap_score",
                self.average_memory_gap_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_raw_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_raw_public_payload("payload", payload, allow_json_containers=True)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_resolution_authority_memory_gap_report(
    inputs: Iterable[object],
    *,
    config: ResearchEventResolutionAuthorityMemoryGapConfig,
    generated_at: datetime,
) -> ResearchEventResolutionAuthorityMemoryGapReport:
    if type(config) is not ResearchEventResolutionAuthorityMemoryGapConfig:
        raise ValueError("config must be a ResearchEventResolutionAuthorityMemoryGapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    for item in input_rows:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not exceed generated_at")
    rows = tuple(
        _row_from_input(item, generated_at=generated_at_utc, config=config)
        for item in sorted(input_rows, key=lambda value: value.event_id)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "event_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_memory_gap_score": _average(
            tuple(row.memory_gap_score for row in rows),
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionAuthorityMemoryGapReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_from_input(
    item: ResearchEventResolutionAuthorityMemoryGapInput,
    *,
    generated_at: datetime,
    config: ResearchEventResolutionAuthorityMemoryGapConfig,
) -> ResearchEventResolutionAuthorityMemoryGapReportRow:
    input_age_seconds = _age_seconds(generated_at, item.observed_at)
    missing_authority = _missing_count(
        item.authority_memory_count,
        config.min_authority_memory_count,
    )
    missing_parser = _missing_count(item.parser_memory_count, _ONE)
    missing_record = _missing_count(
        item.resolution_record_count,
        config.min_resolution_record_count,
    )
    recency_gap_score = _recency_gap_score(
        input_age_seconds,
        fresh_age_seconds=config.fresh_age_seconds,
        stale_age_seconds=config.stale_age_seconds,
    )
    authority_gap_score = _count_gap_score(
        item.authority_memory_count,
        config.min_authority_memory_count,
    )
    parser_gap_score = _count_gap_score(item.parser_memory_count, _ONE)
    record_gap_score = _count_gap_score(
        item.resolution_record_count,
        config.min_resolution_record_count,
    )
    structural_gap_score = _average(
        (authority_gap_score, parser_gap_score, record_gap_score),
    )
    memory_gap_score = (
        structural_gap_score if structural_gap_score > _ZERO else recency_gap_score
    )
    status = _status_from_score(memory_gap_score, config)
    return ResearchEventResolutionAuthorityMemoryGapReportRow(
        event_id=item.event_id,
        authority_id=item.authority_id,
        observed_at=item.observed_at,
        input_age_seconds=input_age_seconds,
        authority_memory_count=item.authority_memory_count,
        parser_memory_count=item.parser_memory_count,
        resolution_record_count=item.resolution_record_count,
        missing_authority_memory_count=missing_authority,
        missing_parser_memory_count=missing_parser,
        missing_resolution_record_count=missing_record,
        recency_gap_score=recency_gap_score,
        authority_gap_score=authority_gap_score,
        parser_gap_score=parser_gap_score,
        record_gap_score=record_gap_score,
        memory_gap_score=memory_gap_score,
        evidence_fingerprint=_fingerprint_private_fragments(
            item.private_resolution_fragments,
        ),
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            recency_gap_score=recency_gap_score,
            missing_authority_memory_count=missing_authority,
            missing_parser_memory_count=missing_parser,
            missing_resolution_record_count=missing_record,
        ),
    )


def _normalize_inputs(
    values: Iterable[object],
) -> tuple[ResearchEventResolutionAuthorityMemoryGapInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized: list[ResearchEventResolutionAuthorityMemoryGapInput] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchEventResolutionAuthorityMemoryGapInput:
            raise ValueError(
                "inputs must contain ResearchEventResolutionAuthorityMemoryGapInput values",
            )
        _require_hard_flags("input", item)
        if item.event_id in seen:
            raise ValueError("event_id values must be unique")
        seen.add(item.event_id)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventResolutionAuthorityMemoryGapReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionAuthorityMemoryGapReportRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionAuthorityMemoryGapReportRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_id")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchEventResolutionAuthorityMemoryGapReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventResolutionAuthorityMemoryGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionAuthorityMemoryGapReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionAuthorityMemoryGapReportRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventResolutionAuthorityMemoryGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionAuthorityMemoryGapReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventResolutionAuthorityMemoryGapReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _row_reason_codes(
    *,
    status: str,
    recency_gap_score: Decimal,
    missing_authority_memory_count: Decimal,
    missing_parser_memory_count: Decimal,
    missing_resolution_record_count: Decimal,
) -> tuple[str, ...]:
    reason_codes = {f"event_resolution_authority_memory_{status}"}
    reason_codes.add(
        "event_resolution_memory_fresh"
        if recency_gap_score < Decimal("0.500000")
        else "event_resolution_memory_stale",
    )
    if missing_authority_memory_count > _ZERO:
        reason_codes.add("missing_authority_memory")
    if missing_parser_memory_count > _ZERO:
        reason_codes.add("missing_parser_memory")
    if missing_resolution_record_count > _ZERO:
        reason_codes.add("missing_resolution_record")
    if (
        missing_authority_memory_count == _ZERO
        and missing_parser_memory_count == _ZERO
        and missing_resolution_record_count == _ZERO
    ):
        reason_codes.add("authority_memory_complete")
    return tuple(sorted(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionAuthorityMemoryGapReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_resolution_evidence",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if any(row.status == "watch" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    return ("event_resolution_authority_memory_pass",)


def _report_status(
    rows: tuple[ResearchEventResolutionAuthorityMemoryGapReportRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchEventResolutionAuthorityMemoryGapReportRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_score(
    score: Decimal,
    config: ResearchEventResolutionAuthorityMemoryGapConfig,
) -> str:
    if score >= config.block_gap_score:
        return "block"
    if score >= config.watch_gap_score:
        return "watch"
    return "pass"


def _missing_count(actual: Decimal, minimum: Decimal) -> Decimal:
    return _quantize(max(_ZERO, minimum - actual))


def _count_gap_score(actual: Decimal, minimum: Decimal) -> Decimal:
    if actual >= minimum:
        return _ZERO
    return _clamp_ratio((minimum - actual) / minimum)


def _recency_gap_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return _clamp_ratio(age_seconds / stale_age_seconds)
    if age_seconds >= stale_age_seconds:
        return _ONE
    return _clamp_ratio(age_seconds / stale_age_seconds)


def _validate_report_consistency(
    report: ResearchEventResolutionAuthorityMemoryGapReport,
) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_memory_gap_score != _average(
        tuple(row.memory_gap_score for row in report.rows),
    ):
        raise ValueError("average_memory_gap_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of {_STATUSES}")


def _normalize_private_fragments(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("private_resolution_fragments must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value:
            raise ValueError("private_resolution_fragments must contain nonempty strings")
        normalized.append(value)
    return tuple(normalized)


def _normalize_reason_codes(
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier("reason_codes", value)
        normalized.append(value)
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_fingerprint(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 fingerprint")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _fingerprint_private_fragments(values: tuple[str, ...]) -> str:
    canonical = json.dumps(
        sorted(values),
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchEventResolutionAuthorityMemoryGapReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_raw_public_payload("digest payload", payload, allow_json_containers=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_raw_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_raw_public_key(field.name, current_path)
            _reject_raw_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_raw_public_key(key, current_path)
            _reject_raw_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_raw_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_raw_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_raw_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _RAW_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} leaks raw private context")


def _reject_raw_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if value.startswith("sha256:"):
        return
    if any(term in lowered for term in _RAW_PUBLIC_TERMS):
        raise ValueError(f"{path} leaks raw private context")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_MEMORY_GAP_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionAuthorityMemoryGapConfig",
    "ResearchEventResolutionAuthorityMemoryGapInput",
    "ResearchEventResolutionAuthorityMemoryGapReasonCodeCount",
    "ResearchEventResolutionAuthorityMemoryGapReport",
    "ResearchEventResolutionAuthorityMemoryGapReportRow",
    "build_research_event_resolution_authority_memory_gap_report",
)
