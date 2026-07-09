"""Pure report-only event resolution clause ambiguity matrix report."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_CONFIG_VERSION = (
    "research-event-resolution-clause-ambiguity-matrix-report-v0"
)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BOUNDARY_CONDITION_COUNT_SCORE_CAP = Decimal("8.000000")

PASS = "pass"
WATCH = "watch"
BLOCK = "block"
RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_STATUSES = (PASS, WATCH, BLOCK)
RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_DIMENSIONS = (
    "authority_clarity",
    "boundary_condition_count",
    "conflicting_interpretation_pressure",
    "deadline_proximity",
)

AUTHORITY_CLARITY_WEIGHT = Decimal("0.350000")
BOUNDARY_CONDITION_COUNT_WEIGHT = Decimal("0.250000")
CONFLICTING_INTERPRETATION_PRESSURE_WEIGHT = Decimal("0.250000")
DEADLINE_PROXIMITY_WEIGHT = Decimal("0.150000")

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
    "http://",
    "https://",
    "www.",
    "url",
    "dsn",
    "database",
    "table",
    "token",
    "secret",
    "credential",
    "wallet",
    "order",
    "trade",
    "live",
    "recommendation",
    "sizing",
    "buy",
    "sell",
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
    "clause_ambiguity_matrix_report_empty",
    "clause_evidence_missing",
    "clause_ambiguity_matrix_report_block_rows",
    "clause_ambiguity_matrix_report_watch_rows",
    "clause_ambiguity_matrix_report_clear",
    "authority_clarity_block",
    "boundary_condition_count_block",
    "conflicting_interpretation_pressure_block",
    "deadline_proximity_block",
    "clause_ambiguity_score_block",
    "authority_clarity_watch",
    "boundary_condition_count_watch",
    "conflicting_interpretation_pressure_watch",
    "deadline_proximity_watch",
    "clause_ambiguity_score_watch",
    "clause_ambiguity_clear",
)


@dataclass(frozen=True)
class ResearchEventResolutionClauseAmbiguityMatrixConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_CONFIG_VERSION
    )
    authority_clarity_watch_floor: Decimal = Decimal("0.800000")
    authority_clarity_block_floor: Decimal = Decimal("0.550000")
    boundary_condition_watch_count: Decimal = Decimal("2.000000")
    boundary_condition_block_count: Decimal = Decimal("5.000000")
    conflicting_interpretation_watch_ceiling: Decimal = Decimal("0.300000")
    conflicting_interpretation_block_ceiling: Decimal = Decimal("0.700000")
    deadline_proximity_watch_ceiling: Decimal = Decimal("0.500000")
    deadline_proximity_block_ceiling: Decimal = Decimal("0.850000")
    watch_ambiguity_score_threshold: Decimal = Decimal("0.250000")
    block_ambiguity_score_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClauseAmbiguityMatrixConfig:
            raise TypeError(
                "ResearchEventResolutionClauseAmbiguityMatrixConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClauseAmbiguityMatrixConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventResolutionClauseAmbiguityMatrixConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_clarity_watch_floor",
            "authority_clarity_block_floor",
            "conflicting_interpretation_watch_ceiling",
            "conflicting_interpretation_block_ceiling",
            "deadline_proximity_watch_ceiling",
            "deadline_proximity_block_ceiling",
            "watch_ambiguity_score_threshold",
            "block_ambiguity_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "boundary_condition_watch_count",
            "boundary_condition_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "authority_clarity",
            self.authority_clarity_block_floor,
            self.authority_clarity_watch_floor,
        )
        _require_count_pair(
            "boundary_condition_count",
            self.boundary_condition_watch_count,
            self.boundary_condition_block_count,
        )
        _require_ceiling_pair(
            "conflicting_interpretation_pressure",
            self.conflicting_interpretation_watch_ceiling,
            self.conflicting_interpretation_block_ceiling,
        )
        _require_ceiling_pair(
            "deadline_proximity",
            self.deadline_proximity_watch_ceiling,
            self.deadline_proximity_block_ceiling,
        )
        if self.block_ambiguity_score_threshold <= self.watch_ambiguity_score_threshold:
            raise ValueError(
                "block_ambiguity_score_threshold must exceed "
                "watch_ambiguity_score_threshold",
            )
        _require_hard_flags("clause ambiguity matrix config", self)


@dataclass(frozen=True)
class ResearchEventResolutionClauseAmbiguityMatrixSubject:
    public_event_bucket: str
    authority_clarity: Decimal
    boundary_condition_count: Decimal
    conflicting_interpretation_pressure: Decimal
    deadline_proximity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClauseAmbiguityMatrixSubject:
            raise TypeError(
                "ResearchEventResolutionClauseAmbiguityMatrixSubject does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClauseAmbiguityMatrixSubject:
            raise ValueError(
                "subject must be exactly "
                "ResearchEventResolutionClauseAmbiguityMatrixSubject",
            )
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "authority_clarity",
            "conflicting_interpretation_pressure",
            "deadline_proximity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "boundary_condition_count",
            _normalize_nonnegative_decimal(
                "boundary_condition_count",
                self.boundary_condition_count,
            ),
        )
        _require_hard_flags("clause ambiguity matrix subject", self)


@dataclass(frozen=True)
class ResearchEventResolutionClauseAmbiguityMatrixRow:
    public_event_bucket: str
    authority_clarity: Decimal
    boundary_condition_count: Decimal
    conflicting_interpretation_pressure: Decimal
    deadline_proximity: Decimal
    clause_ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClauseAmbiguityMatrixRow:
            raise TypeError(
                "ResearchEventResolutionClauseAmbiguityMatrixRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClauseAmbiguityMatrixRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionClauseAmbiguityMatrixRow",
            )
        _require_public_string("public_event_bucket", self.public_event_bucket)
        for field_name in (
            "authority_clarity",
            "conflicting_interpretation_pressure",
            "deadline_proximity",
            "clause_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "boundary_condition_count",
            _normalize_nonnegative_decimal(
                "boundary_condition_count",
                self.boundary_condition_count,
            ),
        )
        _require_public_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_status_consistency(self)
        _require_hard_flags("clause ambiguity matrix row", self)


@dataclass(frozen=True)
class ResearchEventResolutionClauseAmbiguityMatrixReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    lowest_authority_clarity: Decimal
    highest_boundary_condition_count: Decimal
    highest_conflicting_interpretation_pressure: Decimal
    highest_deadline_proximity: Decimal
    highest_clause_ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchEventResolutionClauseAmbiguityMatrixRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClauseAmbiguityMatrixReport:
            raise TypeError(
                "ResearchEventResolutionClauseAmbiguityMatrixReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClauseAmbiguityMatrixReport:
            raise ValueError(
                "report must be exactly "
                "ResearchEventResolutionClauseAmbiguityMatrixReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "highest_boundary_condition_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_authority_clarity",
            "highest_conflicting_interpretation_pressure",
            "highest_deadline_proximity",
            "highest_clause_ambiguity_score",
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
        _require_hard_flags("clause ambiguity matrix report", self)
        expected_digest = _digest_payload(_unsigned_report_payload(self))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_event_resolution_clause_ambiguity_matrix_report(
    subjects: tuple[ResearchEventResolutionClauseAmbiguityMatrixSubject, ...]
    | list[ResearchEventResolutionClauseAmbiguityMatrixSubject],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionClauseAmbiguityMatrixConfig | None = None,
) -> ResearchEventResolutionClauseAmbiguityMatrixReport:
    if config is None:
        config = ResearchEventResolutionClauseAmbiguityMatrixConfig()
    if type(config) is not ResearchEventResolutionClauseAmbiguityMatrixConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionClauseAmbiguityMatrixConfig",
        )
    normalized_subjects = _normalize_subjects(subjects)
    rows = tuple(_row_from_subject(subject, config) for subject in normalized_subjects)
    rows = tuple(sorted(rows, key=_row_sort_key))
    event_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == PASS))
    watch_count = _count(sum(1 for row in rows if row.status == WATCH))
    block_count = _count(sum(1 for row in rows if row.status == BLOCK))

    if rows:
        lowest_authority_clarity = min(row.authority_clarity for row in rows)
        highest_boundary_condition_count = max(
            row.boundary_condition_count for row in rows
        )
        highest_conflicting_interpretation_pressure = max(
            row.conflicting_interpretation_pressure for row in rows
        )
        highest_deadline_proximity = max(row.deadline_proximity for row in rows)
        highest_clause_ambiguity_score = max(
            row.clause_ambiguity_score for row in rows
        )
    else:
        lowest_authority_clarity = ZERO
        highest_boundary_condition_count = ZERO
        highest_conflicting_interpretation_pressure = ZERO
        highest_deadline_proximity = ZERO
        highest_clause_ambiguity_score = ZERO

    status = _report_status(rows)
    reason_codes = _report_reason_codes(status, rows)

    return ResearchEventResolutionClauseAmbiguityMatrixReport(
        generated_at=generated_at,
        config_version=config.config_version,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        lowest_authority_clarity=lowest_authority_clarity,
        highest_boundary_condition_count=highest_boundary_condition_count,
        highest_conflicting_interpretation_pressure=(
            highest_conflicting_interpretation_pressure
        ),
        highest_deadline_proximity=highest_deadline_proximity,
        highest_clause_ambiguity_score=highest_clause_ambiguity_score,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_event_resolution_clause_ambiguity_matrix_report_payload(
    report: ResearchEventResolutionClauseAmbiguityMatrixReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionClauseAmbiguityMatrixReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionClauseAmbiguityMatrixReport",
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
    subject: ResearchEventResolutionClauseAmbiguityMatrixSubject,
    config: ResearchEventResolutionClauseAmbiguityMatrixConfig,
) -> ResearchEventResolutionClauseAmbiguityMatrixRow:
    ambiguity_score = _clause_ambiguity_score(subject)
    reason_codes = _row_reason_codes(subject, ambiguity_score, config)
    status = _status_from_reason_codes(reason_codes)
    if status == PASS:
        reason_codes = ("clause_ambiguity_clear",)
    return ResearchEventResolutionClauseAmbiguityMatrixRow(
        public_event_bucket=subject.public_event_bucket,
        authority_clarity=subject.authority_clarity,
        boundary_condition_count=subject.boundary_condition_count,
        conflicting_interpretation_pressure=subject.conflicting_interpretation_pressure,
        deadline_proximity=subject.deadline_proximity,
        clause_ambiguity_score=ambiguity_score,
        status=status,
        reason_codes=reason_codes,
    )


def _clause_ambiguity_score(
    subject: ResearchEventResolutionClauseAmbiguityMatrixSubject,
) -> Decimal:
    boundary_condition_pressure = min(
        subject.boundary_condition_count / BOUNDARY_CONDITION_COUNT_SCORE_CAP,
        ONE,
    )
    score = (
        (ONE - subject.authority_clarity) * AUTHORITY_CLARITY_WEIGHT
        + boundary_condition_pressure * BOUNDARY_CONDITION_COUNT_WEIGHT
        + subject.conflicting_interpretation_pressure
        * CONFLICTING_INTERPRETATION_PRESSURE_WEIGHT
        + subject.deadline_proximity * DEADLINE_PROXIMITY_WEIGHT
    )
    return _quantize_decimal(score)


def _row_reason_codes(
    subject: ResearchEventResolutionClauseAmbiguityMatrixSubject,
    ambiguity_score: Decimal,
    config: ResearchEventResolutionClauseAmbiguityMatrixConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_floor_reason(
        codes,
        "authority_clarity",
        subject.authority_clarity,
        config.authority_clarity_block_floor,
        config.authority_clarity_watch_floor,
    )
    _append_count_reason(
        codes,
        "boundary_condition_count",
        subject.boundary_condition_count,
        config.boundary_condition_block_count,
        config.boundary_condition_watch_count,
    )
    _append_ceiling_reason(
        codes,
        "conflicting_interpretation_pressure",
        subject.conflicting_interpretation_pressure,
        config.conflicting_interpretation_block_ceiling,
        config.conflicting_interpretation_watch_ceiling,
    )
    _append_ceiling_reason(
        codes,
        "deadline_proximity",
        subject.deadline_proximity,
        config.deadline_proximity_block_ceiling,
        config.deadline_proximity_watch_ceiling,
    )
    _append_ceiling_reason(
        codes,
        "clause_ambiguity_score",
        ambiguity_score,
        config.block_ambiguity_score_threshold,
        config.watch_ambiguity_score_threshold,
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


def _append_count_reason(
    codes: list[str],
    prefix: str,
    value: Decimal,
    block_count: Decimal,
    watch_count: Decimal,
) -> None:
    if value >= block_count:
        codes.append(f"{prefix}_block")
    elif value >= watch_count:
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


def _report_status(
    rows: tuple[ResearchEventResolutionClauseAmbiguityMatrixRow, ...],
) -> str:
    if not rows:
        return BLOCK
    if any(row.status == BLOCK for row in rows):
        return BLOCK
    if any(row.status == WATCH for row in rows):
        return WATCH
    return PASS


def _report_reason_codes(
    status: str,
    rows: tuple[ResearchEventResolutionClauseAmbiguityMatrixRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            "clause_ambiguity_matrix_report_empty",
            "clause_evidence_missing",
        )
    codes: list[str] = []
    if status == BLOCK:
        codes.append("clause_ambiguity_matrix_report_block_rows")
    if any(row.status == WATCH for row in rows):
        codes.append("clause_ambiguity_matrix_report_watch_rows")
    if status == PASS:
        codes.append("clause_ambiguity_matrix_report_clear")
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in codes and reason_code != "clause_ambiguity_clear":
                codes.append(reason_code)
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionClauseAmbiguityMatrixRow, ...],
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
    subjects: tuple[ResearchEventResolutionClauseAmbiguityMatrixSubject, ...]
    | list[ResearchEventResolutionClauseAmbiguityMatrixSubject],
) -> tuple[ResearchEventResolutionClauseAmbiguityMatrixSubject, ...]:
    if not isinstance(subjects, (list, tuple)):
        raise ValueError("subjects must be a list or tuple")
    normalized: list[ResearchEventResolutionClauseAmbiguityMatrixSubject] = []
    for subject in subjects:
        if type(subject) is not ResearchEventResolutionClauseAmbiguityMatrixSubject:
            raise ValueError(
                "subjects must contain "
                "ResearchEventResolutionClauseAmbiguityMatrixSubject",
            )
        normalized.append(subject)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchEventResolutionClauseAmbiguityMatrixRow, ...],
) -> tuple[ResearchEventResolutionClauseAmbiguityMatrixRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionClauseAmbiguityMatrixRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionClauseAmbiguityMatrixRow",
            )
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


def _row_sort_key(
    row: ResearchEventResolutionClauseAmbiguityMatrixRow,
) -> tuple[int, Decimal, str]:
    return (
        {BLOCK: 0, WATCH: 1, PASS: 2}[row.status],
        -row.clause_ambiguity_score,
        row.public_event_bucket,
    )


def _validate_row_status_consistency(
    row: ResearchEventResolutionClauseAmbiguityMatrixRow,
) -> None:
    if row.status == PASS:
        if row.reason_codes != ("clause_ambiguity_clear",):
            raise ValueError("pass row reason_codes must be clause_ambiguity_clear")
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
    report: ResearchEventResolutionClauseAmbiguityMatrixReport,
) -> None:
    if report.event_count != _count(len(report.rows)):
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
    report: ResearchEventResolutionClauseAmbiguityMatrixReport,
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


def _require_count_pair(
    field_name: str,
    watch_count: Decimal,
    block_count: Decimal,
) -> None:
    if block_count < watch_count:
        raise ValueError(f"{field_name} block count must be at least watch count")


def _require_ceiling_pair(
    field_name: str,
    watch_ceiling: Decimal,
    block_ceiling: Decimal,
) -> None:
    if block_ceiling < watch_ceiling:
        raise ValueError(f"{field_name} block ceiling must be at least watch ceiling")


def _require_public_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_STATUSES:
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
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_CONFIG_VERSION",
    "RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_DIMENSIONS",
    "RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_STATUSES",
    "ResearchEventResolutionClauseAmbiguityMatrixConfig",
    "ResearchEventResolutionClauseAmbiguityMatrixReport",
    "ResearchEventResolutionClauseAmbiguityMatrixRow",
    "ResearchEventResolutionClauseAmbiguityMatrixSubject",
    "build_research_event_resolution_clause_ambiguity_matrix_report",
    "research_event_resolution_clause_ambiguity_matrix_report_payload",
)
