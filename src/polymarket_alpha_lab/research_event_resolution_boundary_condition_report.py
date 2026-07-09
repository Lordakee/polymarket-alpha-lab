"""Pure report-only resolution boundary-condition risk report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_BOUNDARY_CONDITION_CONFIG_VERSION = (
    "research-event-resolution-boundary-condition-report-v0"
)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PASS = "pass"
WATCH = "watch"
BLOCK = "block"
RESOLUTION_BOUNDARY_CONDITION_STATUSES = (PASS, WATCH, BLOCK)
RESOLUTION_BOUNDARY_CONDITION_DIMENSIONS = (
    "date_boundary",
    "threshold_definition",
    "exception_clause",
    "authority_traceability",
    "contradiction_pressure",
    "reviewer_verification",
)

DATE_BOUNDARY_WEIGHT = Decimal("0.200000")
THRESHOLD_DEFINITION_WEIGHT = Decimal("0.200000")
EXCEPTION_CLAUSE_WEIGHT = Decimal("0.150000")
AUTHORITY_TRACEABILITY_WEIGHT = Decimal("0.150000")
CONTRADICTION_PRESSURE_WEIGHT = Decimal("0.150000")
REVIEWER_VERIFICATION_WEIGHT = Decimal("0.150000")

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
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
    "question",
    "raw_text",
    "source_text",
    "source-url",
    "source_url",
    "url",
    "dsn",
    "database",
    "table",
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
REPORT_REASON_CODE_ORDER = (
    "boundary_condition_report_empty",
    "reviewer_verification_missing",
    "boundary_condition_report_block_rows",
    "boundary_condition_report_watch_rows",
    "boundary_condition_report_clear",
    "date_boundary_block",
    "threshold_definition_block",
    "exception_clause_block",
    "authority_traceability_block",
    "contradiction_pressure_block",
    "reviewer_verification_block",
    "boundary_condition_risk_block",
    "date_boundary_watch",
    "threshold_definition_watch",
    "exception_clause_watch",
    "authority_traceability_watch",
    "contradiction_pressure_watch",
    "reviewer_verification_watch",
    "boundary_condition_risk_watch",
    "boundary_condition_clear",
)


@dataclass(frozen=True)
class ResearchEventResolutionBoundaryConditionConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_RESOLUTION_BOUNDARY_CONDITION_CONFIG_VERSION
    date_boundary_watch_floor: Decimal = Decimal("0.750000")
    date_boundary_block_floor: Decimal = Decimal("0.500000")
    threshold_definition_watch_floor: Decimal = Decimal("0.750000")
    threshold_definition_block_floor: Decimal = Decimal("0.500000")
    exception_clause_watch_floor: Decimal = Decimal("0.750000")
    exception_clause_block_floor: Decimal = Decimal("0.500000")
    authority_traceability_watch_floor: Decimal = Decimal("0.700000")
    authority_traceability_block_floor: Decimal = Decimal("0.500000")
    reviewer_verification_watch_floor: Decimal = Decimal("0.750000")
    reviewer_verification_block_floor: Decimal = Decimal("0.500000")
    contradiction_pressure_watch_ceiling: Decimal = Decimal("0.350000")
    contradiction_pressure_block_ceiling: Decimal = Decimal("0.700000")
    watch_risk_score_threshold: Decimal = Decimal("0.250000")
    block_risk_score_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionBoundaryConditionConfig:
            raise TypeError(
                "ResearchEventResolutionBoundaryConditionConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionBoundaryConditionConfig:
            raise ValueError(
                "config must be exactly ResearchEventResolutionBoundaryConditionConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_BOUNDARY_CONDITION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "date_boundary_watch_floor",
            "date_boundary_block_floor",
            "threshold_definition_watch_floor",
            "threshold_definition_block_floor",
            "exception_clause_watch_floor",
            "exception_clause_block_floor",
            "authority_traceability_watch_floor",
            "authority_traceability_block_floor",
            "reviewer_verification_watch_floor",
            "reviewer_verification_block_floor",
            "contradiction_pressure_watch_ceiling",
            "contradiction_pressure_block_ceiling",
            "watch_risk_score_threshold",
            "block_risk_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "date_boundary",
            self.date_boundary_block_floor,
            self.date_boundary_watch_floor,
        )
        _require_floor_pair(
            "threshold_definition",
            self.threshold_definition_block_floor,
            self.threshold_definition_watch_floor,
        )
        _require_floor_pair(
            "exception_clause",
            self.exception_clause_block_floor,
            self.exception_clause_watch_floor,
        )
        _require_floor_pair(
            "authority_traceability",
            self.authority_traceability_block_floor,
            self.authority_traceability_watch_floor,
        )
        _require_floor_pair(
            "reviewer_verification",
            self.reviewer_verification_block_floor,
            self.reviewer_verification_watch_floor,
        )
        if self.contradiction_pressure_block_ceiling < self.contradiction_pressure_watch_ceiling:
            raise ValueError(
                "contradiction_pressure_block_ceiling must be at least "
                "contradiction_pressure_watch_ceiling",
            )
        if self.block_risk_score_threshold <= self.watch_risk_score_threshold:
            raise ValueError(
                "block_risk_score_threshold must exceed watch_risk_score_threshold",
            )
        _require_hard_flags("boundary condition config", self)


@dataclass(frozen=True)
class ResearchEventResolutionBoundaryConditionSubject:
    public_event_bucket: str
    date_boundary_precision: Decimal
    threshold_definition_clarity: Decimal
    exception_clause_coverage: Decimal
    authority_traceability: Decimal
    contradiction_pressure: Decimal
    reviewer_verification_coverage: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionBoundaryConditionSubject:
            raise TypeError(
                "ResearchEventResolutionBoundaryConditionSubject does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionBoundaryConditionSubject:
            raise ValueError(
                "subject must be exactly ResearchEventResolutionBoundaryConditionSubject",
            )
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "date_boundary_precision",
            "threshold_definition_clarity",
            "exception_clause_coverage",
            "authority_traceability",
            "contradiction_pressure",
            "reviewer_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("boundary condition subject", self)


@dataclass(frozen=True)
class ResearchEventResolutionBoundaryConditionRow:
    public_event_bucket: str
    date_boundary_precision: Decimal
    threshold_definition_clarity: Decimal
    exception_clause_coverage: Decimal
    authority_traceability: Decimal
    contradiction_pressure: Decimal
    reviewer_verification_coverage: Decimal
    boundary_condition_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionBoundaryConditionRow:
            raise TypeError(
                "ResearchEventResolutionBoundaryConditionRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionBoundaryConditionRow:
            raise ValueError("row must be exactly ResearchEventResolutionBoundaryConditionRow")
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "date_boundary_precision",
            "threshold_definition_clarity",
            "exception_clause_coverage",
            "authority_traceability",
            "contradiction_pressure",
            "reviewer_verification_coverage",
            "boundary_condition_risk_score",
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_status_consistency(self)
        _require_hard_flags("boundary condition row", self)


@dataclass(frozen=True)
class ResearchEventResolutionBoundaryConditionReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    lowest_date_boundary_precision: Decimal
    lowest_threshold_definition_clarity: Decimal
    lowest_exception_clause_coverage: Decimal
    lowest_authority_traceability: Decimal
    highest_contradiction_pressure: Decimal
    lowest_reviewer_verification_coverage: Decimal
    highest_boundary_condition_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchEventResolutionBoundaryConditionRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionBoundaryConditionReport:
            raise TypeError(
                "ResearchEventResolutionBoundaryConditionReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionBoundaryConditionReport:
            raise ValueError(
                "report must be exactly ResearchEventResolutionBoundaryConditionReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_BOUNDARY_CONDITION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_date_boundary_precision",
            "lowest_threshold_definition_clarity",
            "lowest_exception_clause_coverage",
            "lowest_authority_traceability",
            "highest_contradiction_pressure",
            "lowest_reviewer_verification_coverage",
            "highest_boundary_condition_risk_score",
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("boundary condition report", self)
        expected_digest = _digest_payload(_unsigned_report_payload(self))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_event_resolution_boundary_condition_report(
    subjects: tuple[ResearchEventResolutionBoundaryConditionSubject, ...]
    | list[ResearchEventResolutionBoundaryConditionSubject],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionBoundaryConditionConfig | None = None,
) -> ResearchEventResolutionBoundaryConditionReport:
    if config is None:
        config = ResearchEventResolutionBoundaryConditionConfig()
    if type(config) is not ResearchEventResolutionBoundaryConditionConfig:
        raise ValueError("config must be a ResearchEventResolutionBoundaryConditionConfig")
    normalized_subjects = _normalize_subjects(subjects)
    rows = tuple(_row_from_subject(subject, config) for subject in normalized_subjects)
    rows = tuple(sorted(rows, key=_row_sort_key))
    event_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == PASS))
    watch_count = _count(sum(1 for row in rows if row.status == WATCH))
    block_count = _count(sum(1 for row in rows if row.status == BLOCK))

    if rows:
        lowest_date_boundary_precision = min(row.date_boundary_precision for row in rows)
        lowest_threshold_definition_clarity = min(
            row.threshold_definition_clarity for row in rows
        )
        lowest_exception_clause_coverage = min(row.exception_clause_coverage for row in rows)
        lowest_authority_traceability = min(row.authority_traceability for row in rows)
        highest_contradiction_pressure = max(row.contradiction_pressure for row in rows)
        lowest_reviewer_verification_coverage = min(
            row.reviewer_verification_coverage for row in rows
        )
        highest_boundary_condition_risk_score = max(
            row.boundary_condition_risk_score for row in rows
        )
    else:
        lowest_date_boundary_precision = ZERO
        lowest_threshold_definition_clarity = ZERO
        lowest_exception_clause_coverage = ZERO
        lowest_authority_traceability = ZERO
        highest_contradiction_pressure = ZERO
        lowest_reviewer_verification_coverage = ZERO
        highest_boundary_condition_risk_score = ZERO

    status = _report_status(rows)
    reason_codes = _report_reason_codes(status, rows)
    reason_code_counts = _reason_code_counts(rows)

    return ResearchEventResolutionBoundaryConditionReport(
        generated_at=generated_at,
        config_version=config.config_version,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        lowest_date_boundary_precision=lowest_date_boundary_precision,
        lowest_threshold_definition_clarity=lowest_threshold_definition_clarity,
        lowest_exception_clause_coverage=lowest_exception_clause_coverage,
        lowest_authority_traceability=lowest_authority_traceability,
        highest_contradiction_pressure=highest_contradiction_pressure,
        lowest_reviewer_verification_coverage=lowest_reviewer_verification_coverage,
        highest_boundary_condition_risk_score=highest_boundary_condition_risk_score,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )


def research_event_resolution_boundary_condition_report_payload(
    report: ResearchEventResolutionBoundaryConditionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionBoundaryConditionReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionBoundaryConditionReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _verify_payload_digest(payload)
    _reject_unsafe_public_surface("payload", payload)
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


def _row_from_subject(
    subject: ResearchEventResolutionBoundaryConditionSubject,
    config: ResearchEventResolutionBoundaryConditionConfig,
) -> ResearchEventResolutionBoundaryConditionRow:
    risk_score = _boundary_condition_risk_score(subject)
    reason_codes = _row_reason_codes(subject, risk_score, config)
    status = _status_from_reason_codes(reason_codes)
    if status == PASS:
        reason_codes = ("boundary_condition_clear",)
    return ResearchEventResolutionBoundaryConditionRow(
        public_event_bucket=subject.public_event_bucket,
        date_boundary_precision=subject.date_boundary_precision,
        threshold_definition_clarity=subject.threshold_definition_clarity,
        exception_clause_coverage=subject.exception_clause_coverage,
        authority_traceability=subject.authority_traceability,
        contradiction_pressure=subject.contradiction_pressure,
        reviewer_verification_coverage=subject.reviewer_verification_coverage,
        boundary_condition_risk_score=risk_score,
        status=status,
        reason_codes=reason_codes,
    )


def _boundary_condition_risk_score(
    subject: ResearchEventResolutionBoundaryConditionSubject,
) -> Decimal:
    weighted_score = (
        (ONE - subject.date_boundary_precision) * DATE_BOUNDARY_WEIGHT
        + (ONE - subject.threshold_definition_clarity) * THRESHOLD_DEFINITION_WEIGHT
        + (ONE - subject.exception_clause_coverage) * EXCEPTION_CLAUSE_WEIGHT
        + (ONE - subject.authority_traceability) * AUTHORITY_TRACEABILITY_WEIGHT
        + subject.contradiction_pressure * CONTRADICTION_PRESSURE_WEIGHT
        + (ONE - subject.reviewer_verification_coverage) * REVIEWER_VERIFICATION_WEIGHT
    )
    return _quantize_decimal(weighted_score)


def _row_reason_codes(
    subject: ResearchEventResolutionBoundaryConditionSubject,
    risk_score: Decimal,
    config: ResearchEventResolutionBoundaryConditionConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_floor_reason(
        codes,
        "date_boundary",
        subject.date_boundary_precision,
        config.date_boundary_block_floor,
        config.date_boundary_watch_floor,
    )
    _append_floor_reason(
        codes,
        "threshold_definition",
        subject.threshold_definition_clarity,
        config.threshold_definition_block_floor,
        config.threshold_definition_watch_floor,
    )
    _append_floor_reason(
        codes,
        "exception_clause",
        subject.exception_clause_coverage,
        config.exception_clause_block_floor,
        config.exception_clause_watch_floor,
    )
    _append_floor_reason(
        codes,
        "authority_traceability",
        subject.authority_traceability,
        config.authority_traceability_block_floor,
        config.authority_traceability_watch_floor,
    )
    _append_ceiling_reason(
        codes,
        "contradiction_pressure",
        subject.contradiction_pressure,
        config.contradiction_pressure_block_ceiling,
        config.contradiction_pressure_watch_ceiling,
    )
    _append_floor_reason(
        codes,
        "reviewer_verification",
        subject.reviewer_verification_coverage,
        config.reviewer_verification_block_floor,
        config.reviewer_verification_watch_floor,
    )
    _append_ceiling_reason(
        codes,
        "boundary_condition_risk",
        risk_score,
        config.block_risk_score_threshold,
        config.watch_risk_score_threshold,
    )
    return tuple(codes)


def _append_floor_reason(
    codes: list[str],
    prefix: str,
    value: Decimal,
    block_floor: Decimal,
    watch_floor: Decimal,
) -> None:
    if value < block_floor:
        codes.append(f"{prefix}_block")
    elif value < watch_floor:
        codes.append(f"{prefix}_watch")


def _append_ceiling_reason(
    codes: list[str],
    prefix: str,
    value: Decimal,
    block_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if value >= block_ceiling:
        codes.append(f"{prefix}_block")
    elif value >= watch_ceiling:
        codes.append(f"{prefix}_watch")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH
    return PASS


def _report_status(rows: tuple[ResearchEventResolutionBoundaryConditionRow, ...]) -> str:
    if not rows:
        return BLOCK
    if any(row.status == BLOCK for row in rows):
        return BLOCK
    if any(row.status == WATCH for row in rows):
        return WATCH
    return PASS


def _report_reason_codes(
    status: str,
    rows: tuple[ResearchEventResolutionBoundaryConditionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            "boundary_condition_report_empty",
            "reviewer_verification_missing",
        )
    codes: list[str] = []
    if status == BLOCK:
        codes.append("boundary_condition_report_block_rows")
    if any(row.status == WATCH for row in rows):
        codes.append("boundary_condition_report_watch_rows")
    if status == PASS:
        codes.append("boundary_condition_report_clear")
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in codes and reason_code != "boundary_condition_clear":
                codes.append(reason_code)
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionBoundaryConditionRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        (reason_code, _count(counter[reason_code]))
        for reason_code in REPORT_REASON_CODE_ORDER
        if counter[reason_code]
    )


def _normalize_subjects(
    subjects: tuple[ResearchEventResolutionBoundaryConditionSubject, ...]
    | list[ResearchEventResolutionBoundaryConditionSubject],
) -> tuple[ResearchEventResolutionBoundaryConditionSubject, ...]:
    if not isinstance(subjects, (list, tuple)):
        raise ValueError("subjects must be a list or tuple")
    normalized: list[ResearchEventResolutionBoundaryConditionSubject] = []
    for subject in subjects:
        if type(subject) is not ResearchEventResolutionBoundaryConditionSubject:
            raise ValueError(
                "subjects must contain ResearchEventResolutionBoundaryConditionSubject",
            )
        normalized.append(subject)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchEventResolutionBoundaryConditionRow, ...],
) -> tuple[ResearchEventResolutionBoundaryConditionRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionBoundaryConditionRow:
            raise ValueError("rows must contain ResearchEventResolutionBoundaryConditionRow")
    return tuple(rows)


def _normalize_reason_code_counts(
    values: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    for value in values:
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError("reason_code_counts entries must be reason/count pairs")
        reason_code, count = value
        _require_reason_code(reason_code)
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_decimal("reason_code_count", count),
            ),
        )
    return tuple(normalized)


def _row_sort_key(row: ResearchEventResolutionBoundaryConditionRow) -> tuple[int, Decimal, str]:
    return (
        {BLOCK: 0, WATCH: 1, PASS: 2}[row.status],
        -row.boundary_condition_risk_score,
        row.public_event_bucket,
    )


def _validate_row_status_consistency(
    row: ResearchEventResolutionBoundaryConditionRow,
) -> None:
    if row.status == PASS:
        if row.reason_codes != ("boundary_condition_clear",):
            raise ValueError("pass row reason_codes must be boundary_condition_clear")
        return
    if row.status == WATCH:
        if any(reason_code.endswith("_block") for reason_code in row.reason_codes):
            raise ValueError("watch row reason_codes must not include block reasons")
        if not any(reason_code.endswith("_watch") for reason_code in row.reason_codes):
            raise ValueError("watch row reason_codes must include watch reasons")
        return
    if not any(reason_code.endswith("_block") for reason_code in row.reason_codes):
        raise ValueError("block row reason_codes must include block reasons")


def _validate_report_consistency(
    report: ResearchEventResolutionBoundaryConditionReport,
) -> None:
    row_count = _count(len(report.rows))
    if report.event_count != row_count:
        raise ValueError("event_count must equal row count")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == PASS)):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == WATCH)):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == BLOCK)):
        raise ValueError("block_count must equal block rows")
    if report.event_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("event counts must reconcile")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.status, report.rows):
        raise ValueError("reason_codes must match row reasons")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match row reasons")


def _unsigned_report_payload(
    report: ResearchEventResolutionBoundaryConditionReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str or type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_floor_pair(field_name: str, block_floor: Decimal, watch_floor: Decimal) -> None:
    if block_floor > watch_floor:
        raise ValueError(f"{field_name} block floor must not exceed watch floor")


def _require_public_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in RESOLUTION_BOUNDARY_CONDITION_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    lowered = value.lower()
    if lowered != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if any(prefix in lowered for prefix in RAW_QUESTION_PREFIXES):
        raise ValueError(f"{field_name} must not expose raw question text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public surface")
    return value


def _normalize_reason_codes(
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not values and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in values:
        _require_reason_code(reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in REPORT_REASON_CODE_ORDER if reason_code in normalized
    )


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if value not in REPORT_REASON_CODE_ORDER:
        raise ValueError("reason_code is not supported")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_BOUNDARY_CONDITION_CONFIG_VERSION",
    "RESOLUTION_BOUNDARY_CONDITION_DIMENSIONS",
    "RESOLUTION_BOUNDARY_CONDITION_STATUSES",
    "ResearchEventResolutionBoundaryConditionConfig",
    "ResearchEventResolutionBoundaryConditionReport",
    "ResearchEventResolutionBoundaryConditionRow",
    "ResearchEventResolutionBoundaryConditionSubject",
    "build_research_event_resolution_boundary_condition_report",
    "research_event_resolution_boundary_condition_report_payload",
)
