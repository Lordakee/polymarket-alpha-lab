"""Pure report-only risk report for event question ambiguity."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any


CONFIG_VERSION = "research_event_question_ambiguity_risk_report"
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

PASS = "pass"
WATCH = "watch"
BLOCK = "block"
PUBLIC_STATUSES = (PASS, WATCH, BLOCK)

CLAUSE_CLARITY_WEIGHT = Decimal("0.200000")
EDGE_CASE_COVERAGE_WEIGHT = Decimal("0.200000")
AUTHORITY_TRACEABILITY_WEIGHT = Decimal("0.150000")
DATE_BOUNDARY_PRECISION_WEIGHT = Decimal("0.250000")
CONTRADICTION_PRESSURE_WEIGHT = Decimal("0.200000")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "_id",
    "id",
    "id_",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "raw_question",
    "question_text",
    "source",
    "url",
    "source_text",
    "dsn",
    "table",
    "reco" + "mmend",
    "siz" + "ing",
    "alloc" + "ation",
    "pos" + "ition",
    "not" + "ional",
    "tok" + "en",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "liv" + "e",
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
    "http://",
    "https://",
    "www.",
    "url",
    "source text",
    "source_text",
    "dsn",
    "table",
    "reco" + "mmend",
    "siz" + "ing",
    "alloc" + "ation",
    "pos" + "ition",
    "not" + "ional",
    "tok" + "en",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "liv" + "e",
)
RAW_QUESTION_PREFIXES = (
    "will ",
    "does ",
    "did ",
    "can ",
    "is ",
    "are ",
)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityRiskConfig:
    config_version: str = CONFIG_VERSION
    clause_clarity_watch_floor: Decimal = Decimal("0.750000")
    clause_clarity_block_floor: Decimal = Decimal("0.500000")
    edge_case_coverage_watch_floor: Decimal = Decimal("0.750000")
    edge_case_coverage_block_floor: Decimal = Decimal("0.500000")
    authority_traceability_watch_floor: Decimal = Decimal("0.700000")
    authority_traceability_block_floor: Decimal = Decimal("0.500000")
    date_boundary_precision_watch_floor: Decimal = Decimal("0.750000")
    date_boundary_precision_block_floor: Decimal = Decimal("0.500000")
    contradiction_pressure_watch_ceiling: Decimal = Decimal("0.350000")
    contradiction_pressure_block_ceiling: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityRiskConfig:
            raise TypeError(
                "ResearchEventQuestionAmbiguityRiskConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityRiskConfig:
            raise ValueError("config must be exactly ResearchEventQuestionAmbiguityRiskConfig")
        _require_internal_string("config_version", self.config_version)
        for field_name in (
            "clause_clarity_watch_floor",
            "clause_clarity_block_floor",
            "edge_case_coverage_watch_floor",
            "edge_case_coverage_block_floor",
            "authority_traceability_watch_floor",
            "authority_traceability_block_floor",
            "date_boundary_precision_watch_floor",
            "date_boundary_precision_block_floor",
            "contradiction_pressure_watch_ceiling",
            "contradiction_pressure_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "clause_clarity",
            self.clause_clarity_block_floor,
            self.clause_clarity_watch_floor,
        )
        _require_floor_pair(
            "edge_case_coverage",
            self.edge_case_coverage_block_floor,
            self.edge_case_coverage_watch_floor,
        )
        _require_floor_pair(
            "authority_traceability",
            self.authority_traceability_block_floor,
            self.authority_traceability_watch_floor,
        )
        _require_floor_pair(
            "date_boundary_precision",
            self.date_boundary_precision_block_floor,
            self.date_boundary_precision_watch_floor,
        )
        if self.contradiction_pressure_block_ceiling < self.contradiction_pressure_watch_ceiling:
            raise ValueError(
                "contradiction_pressure_block_ceiling must be at least "
                "contradiction_pressure_watch_ceiling",
            )
        _require_hard_flags("ambiguity risk config", self)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityRiskSubject:
    public_event_bucket: str
    clause_clarity: Decimal
    edge_case_coverage: Decimal
    authority_traceability: Decimal
    date_boundary_precision: Decimal
    contradiction_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityRiskSubject:
            raise TypeError(
                "ResearchEventQuestionAmbiguityRiskSubject does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityRiskSubject:
            raise ValueError("subject must be exactly ResearchEventQuestionAmbiguityRiskSubject")
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "clause_clarity",
            "edge_case_coverage",
            "authority_traceability",
            "date_boundary_precision",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("ambiguity risk subject", self)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityRiskRow:
    public_event_bucket: str
    clause_clarity: Decimal
    edge_case_coverage: Decimal
    authority_traceability: Decimal
    date_boundary_precision: Decimal
    contradiction_pressure: Decimal
    ambiguity_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityRiskRow:
            raise TypeError(
                "ResearchEventQuestionAmbiguityRiskRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityRiskRow:
            raise ValueError("row must be exactly ResearchEventQuestionAmbiguityRiskRow")
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "clause_clarity",
            "edge_case_coverage",
            "authority_traceability",
            "date_boundary_precision",
            "contradiction_pressure",
            "ambiguity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_public_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=self.status == PASS),
        )
        _validate_row_consistency(self)
        _require_hard_flags("ambiguity risk row", self)


@dataclass(frozen=True)
class ResearchEventQuestionAmbiguityRiskReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    lowest_clause_clarity: Decimal
    lowest_edge_case_coverage: Decimal
    lowest_authority_traceability: Decimal
    lowest_date_boundary_precision: Decimal
    highest_contradiction_pressure: Decimal
    highest_ambiguity_risk_score: Decimal
    status: str
    rows: tuple[ResearchEventQuestionAmbiguityRiskRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventQuestionAmbiguityRiskReport:
            raise TypeError(
                "ResearchEventQuestionAmbiguityRiskReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventQuestionAmbiguityRiskReport:
            raise ValueError("report must be exactly ResearchEventQuestionAmbiguityRiskReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_internal_string("config_version", self.config_version)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_clause_clarity",
            "lowest_edge_case_coverage",
            "lowest_authority_traceability",
            "lowest_date_boundary_precision",
            "highest_contradiction_pressure",
            "highest_ambiguity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
        _require_hard_flags("ambiguity risk report", self)
        _require_report_payload_digest(self)
        _reject_unsafe_public_payload(_payload_value(asdict(self)))


def build_research_event_question_ambiguity_risk_report(
    subjects: tuple[ResearchEventQuestionAmbiguityRiskSubject, ...],
    *,
    generated_at: datetime,
    config: ResearchEventQuestionAmbiguityRiskConfig,
) -> ResearchEventQuestionAmbiguityRiskReport:
    if type(subjects) is not tuple:
        raise ValueError("subjects must be a tuple")
    if type(config) is not ResearchEventQuestionAmbiguityRiskConfig:
        raise ValueError("config must be a ResearchEventQuestionAmbiguityRiskConfig")
    rows = tuple(
        sorted(
            (_build_row(subject=subject, config=config) for subject in subjects),
            key=lambda row: row.public_event_bucket,
        ),
    )
    return ResearchEventQuestionAmbiguityRiskReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_count=_count_status(rows, PASS),
        watch_count=_count_status(rows, WATCH),
        block_count=_count_status(rows, BLOCK),
        lowest_clause_clarity=_minimum(row.clause_clarity for row in rows),
        lowest_edge_case_coverage=_minimum(row.edge_case_coverage for row in rows),
        lowest_authority_traceability=_minimum(row.authority_traceability for row in rows),
        lowest_date_boundary_precision=_minimum(row.date_boundary_precision for row in rows),
        highest_contradiction_pressure=_maximum(row.contradiction_pressure for row in rows),
        highest_ambiguity_risk_score=_maximum(row.ambiguity_risk_score for row in rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_question_ambiguity_risk_payload(
    report: ResearchEventQuestionAmbiguityRiskReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventQuestionAmbiguityRiskReport:
        _validate_report_consistency(report)
        _require_report_payload_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a ResearchEventQuestionAmbiguityRiskReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    *,
    subject: ResearchEventQuestionAmbiguityRiskSubject,
    config: ResearchEventQuestionAmbiguityRiskConfig,
) -> ResearchEventQuestionAmbiguityRiskRow:
    if type(subject) is not ResearchEventQuestionAmbiguityRiskSubject:
        raise ValueError(
            "subjects must contain ResearchEventQuestionAmbiguityRiskSubject values",
        )
    reason_codes = _row_reason_codes(subject=subject, config=config)
    return ResearchEventQuestionAmbiguityRiskRow(
        public_event_bucket=subject.public_event_bucket,
        clause_clarity=subject.clause_clarity,
        edge_case_coverage=subject.edge_case_coverage,
        authority_traceability=subject.authority_traceability,
        date_boundary_precision=subject.date_boundary_precision,
        contradiction_pressure=subject.contradiction_pressure,
        ambiguity_risk_score=_ambiguity_risk_score(subject),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    subject: ResearchEventQuestionAmbiguityRiskSubject,
    config: ResearchEventQuestionAmbiguityRiskConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_floor_reason(
        codes,
        metric_name="low_clause_clarity",
        value=subject.clause_clarity,
        watch_floor=config.clause_clarity_watch_floor,
        block_floor=config.clause_clarity_block_floor,
    )
    _append_floor_reason(
        codes,
        metric_name="thin_edge_case_coverage",
        value=subject.edge_case_coverage,
        watch_floor=config.edge_case_coverage_watch_floor,
        block_floor=config.edge_case_coverage_block_floor,
    )
    _append_floor_reason(
        codes,
        metric_name="weak_authority_traceability",
        value=subject.authority_traceability,
        watch_floor=config.authority_traceability_watch_floor,
        block_floor=config.authority_traceability_block_floor,
    )
    _append_floor_reason(
        codes,
        metric_name="imprecise_date_boundary",
        value=subject.date_boundary_precision,
        watch_floor=config.date_boundary_precision_watch_floor,
        block_floor=config.date_boundary_precision_block_floor,
    )
    if subject.contradiction_pressure >= config.contradiction_pressure_block_ceiling:
        codes.append("contradiction_pressure_block")
    elif subject.contradiction_pressure >= config.contradiction_pressure_watch_ceiling:
        codes.append("contradiction_pressure_watch")
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


def _ambiguity_risk_score(
    subject: ResearchEventQuestionAmbiguityRiskSubject | ResearchEventQuestionAmbiguityRiskRow,
) -> Decimal:
    return _quantize(
        ((ONE - subject.clause_clarity) * CLAUSE_CLARITY_WEIGHT)
        + ((ONE - subject.edge_case_coverage) * EDGE_CASE_COVERAGE_WEIGHT)
        + ((ONE - subject.authority_traceability) * AUTHORITY_TRACEABILITY_WEIGHT)
        + ((ONE - subject.date_boundary_precision) * DATE_BOUNDARY_PRECISION_WEIGHT)
        + (subject.contradiction_pressure * CONTRADICTION_PRESSURE_WEIGHT),
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return BLOCK
    if reason_codes:
        return WATCH
    return PASS


def _report_status(rows: tuple[ResearchEventQuestionAmbiguityRiskRow, ...]) -> str:
    if any(row.status == BLOCK for row in rows):
        return BLOCK
    if any(row.status == WATCH for row in rows):
        return WATCH
    return PASS


def _reason_code_counts(
    rows: tuple[ResearchEventQuestionAmbiguityRiskRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, _count(counter[code])) for code in sorted(counter))


def _count_status(
    rows: tuple[ResearchEventQuestionAmbiguityRiskRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


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
) -> tuple[ResearchEventQuestionAmbiguityRiskRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is ResearchEventQuestionAmbiguityRiskRow for row in rows):
        raise ValueError("rows must contain ResearchEventQuestionAmbiguityRiskRow values")
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


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _validate_row_consistency(row: ResearchEventQuestionAmbiguityRiskRow) -> None:
    if row.ambiguity_risk_score != _ambiguity_risk_score(row):
        raise ValueError("ambiguity_risk_score does not match row metrics")
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status does not match reason_codes")


def _validate_report_consistency(report: ResearchEventQuestionAmbiguityRiskReport) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count does not match rows")
    if report.pass_count != _count_status(rows, PASS):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _count_status(rows, WATCH):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _count_status(rows, BLOCK):
        raise ValueError("block_count does not match rows")
    if report.lowest_clause_clarity != _minimum(row.clause_clarity for row in rows):
        raise ValueError("lowest_clause_clarity does not match rows")
    if report.lowest_edge_case_coverage != _minimum(row.edge_case_coverage for row in rows):
        raise ValueError("lowest_edge_case_coverage does not match rows")
    if report.lowest_authority_traceability != _minimum(
        row.authority_traceability for row in rows
    ):
        raise ValueError("lowest_authority_traceability does not match rows")
    if report.lowest_date_boundary_precision != _minimum(
        row.date_boundary_precision for row in rows
    ):
        raise ValueError("lowest_date_boundary_precision does not match rows")
    if report.highest_contradiction_pressure != _maximum(
        row.contradiction_pressure for row in rows
    ):
        raise ValueError("highest_contradiction_pressure does not match rows")
    if report.highest_ambiguity_risk_score != _maximum(row.ambiguity_risk_score for row in rows):
        raise ValueError("highest_ambiguity_risk_score does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts does not match rows")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(payload)
    _reject_non_json_safe_numbers(payload)
    _require_payload_hard_flags(payload)
    _require_public_payload_semantics(payload)
    digest = payload.get("derived_payload_digest")
    _require_sha256_digest("derived_payload_digest", digest)
    expected_digest = _payload_digest_without_digest(payload)
    if digest != expected_digest:
        raise ValueError("derived_payload_digest does not match report payload")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_payload_semantics(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_public_status("status", item)
            elif key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _require_public_payload_semantics(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_semantics(item)


def _require_report_payload_digest(report: ResearchEventQuestionAmbiguityRiskReport) -> None:
    if report.derived_payload_digest != _report_payload_digest(report):
        raise ValueError("derived_payload_digest does not match report payload")


def _report_payload_digest(report: ResearchEventQuestionAmbiguityRiskReport) -> str:
    return _payload_digest_without_digest(_payload_value(asdict(report)))


def _payload_digest_without_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_payload_digest"
    }
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("payload numbers must be Decimal-derived strings")
    if type(value) in (str, bool):
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
    raise ValueError("value is not JSON serializable")


def _reject_non_json_safe_numbers(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_non_json_safe_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_non_json_safe_numbers(item)
        return
    if isinstance(value, float) or type(value) is int or isinstance(value, Decimal):
        raise ValueError("payload numbers must be Decimal-derived strings")


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            if _has_unsafe_fragment(key, UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_raw_question_text(value)
        _reject_unsafe_public_value(value)


def _reject_raw_question_text(value: str) -> None:
    normalized = value.strip().lower()
    if "?" in value or any(normalized.startswith(prefix) for prefix in RAW_QUESTION_PREFIXES):
        raise ValueError("raw question text must not be public")


def _reject_unsafe_public_value(value: str) -> None:
    if _has_unsafe_fragment(value, UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError("unsafe public payload value")


def _has_unsafe_fragment(value: str, fragments: tuple[str, ...]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


__all__ = (
    "ResearchEventQuestionAmbiguityRiskConfig",
    "ResearchEventQuestionAmbiguityRiskReport",
    "ResearchEventQuestionAmbiguityRiskRow",
    "ResearchEventQuestionAmbiguityRiskSubject",
    "build_research_event_question_ambiguity_risk_report",
    "research_event_question_ambiguity_risk_payload",
)
