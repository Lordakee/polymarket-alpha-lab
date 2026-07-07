"""Pure readonly research evidence collection gap planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Mapping


DEFAULT_RESEARCH_EVIDENCE_COLLECTION_GAP_PLAN_CONFIG_VERSION = (
    "research-evidence-collection-gap-plan-v0"
)

SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUSES = ("pass", "watch", "block")
GAP_REASON_CODES = (
    "coverage_below_floor",
    "evidence_age_above_floor",
    "conflict_pressure_present",
    "traceability_below_floor",
)

COVERAGE_WEIGHT = Decimal("0.500000")
FRESHNESS_WEIGHT = Decimal("0.100000")
CONFLICT_WEIGHT = Decimal("0.300000")
TRACEABILITY_WEIGHT = Decimal("0.100000")

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _j(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _j("can", "did", "ate"),
    _j("mar", "ket"),
    _j("ques", "tion"),
    _j("sou", "rce"),
    _j("d", "s", "n"),
    _j("tab", "le"),
    _j("to", "ken"),
    _j("wal", "let"),
    _j("au", "th"),
    _j("or", "der"),
    _j("tra", "de"),
    _j("pos", "ition"),
    _j("b", "u", "y"),
    _j("s", "e", "l", "l"),
    _j("rec", "ommen", "dation"),
)


@dataclass(frozen=True)
class ResearchEvidenceCollectionGapPlanConfig:
    config_version: str = DEFAULT_RESEARCH_EVIDENCE_COLLECTION_GAP_PLAN_CONFIG_VERSION
    min_coverage_ratio: Decimal = Decimal("1.000000")
    max_freshest_evidence_age_hours: Decimal = Decimal("24.000000")
    freshness_gap_span_hours: Decimal = Decimal("60.000000")
    max_conflict_score: Decimal = Decimal("0.000000")
    min_traceability_ratio: Decimal = Decimal("1.000000")
    watch_priority_score: Decimal = Decimal("0.050000")
    block_priority_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceCollectionGapPlanConfig:
            raise TypeError(
                "ResearchEvidenceCollectionGapPlanConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceCollectionGapPlanConfig:
            raise ValueError(
                "config must be exactly ResearchEvidenceCollectionGapPlanConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_COLLECTION_GAP_PLAN_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_coverage_ratio",
            "max_conflict_score",
            "min_traceability_ratio",
            "watch_priority_score",
            "block_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_freshest_evidence_age_hours",
            "freshness_gap_span_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_priority_score >= self.block_priority_score:
            raise ValueError("watch_priority_score must be below block_priority_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEvidenceCollectionGapSubject:
    case_ref: str
    domain_ref: str
    coverage_ratio: Decimal
    freshest_evidence_age_hours: Decimal
    conflict_score: Decimal
    traceability_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceCollectionGapSubject:
            raise TypeError(
                "ResearchEvidenceCollectionGapSubject does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceCollectionGapSubject:
            raise ValueError(
                "subject must be exactly ResearchEvidenceCollectionGapSubject",
            )
        for field_name in ("case_ref", "domain_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in ("coverage_ratio", "conflict_score", "traceability_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_evidence_age_hours",
            _require_nonnegative_decimal(
                "freshest_evidence_age_hours",
                self.freshest_evidence_age_hours,
            ),
        )
        _require_hard_flags("subject", self)
        _reject_unsafe_public_payload("subject", self)


@dataclass(frozen=True)
class ResearchEvidenceCollectionGapRow:
    case_ref: str
    domain_ref: str
    priority_rank: Decimal
    status: str
    priority_score: Decimal
    coverage_gap_score: Decimal
    freshness_gap_score: Decimal
    conflict_gap_score: Decimal
    traceability_gap_score: Decimal
    coverage_ratio: Decimal
    freshest_evidence_age_hours: Decimal
    conflict_score: Decimal
    traceability_ratio: Decimal
    gap_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceCollectionGapRow:
            raise TypeError(
                "ResearchEvidenceCollectionGapRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceCollectionGapRow:
            raise ValueError("row must be exactly ResearchEvidenceCollectionGapRow")
        for field_name in ("case_ref", "domain_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_decimal("priority_rank", self.priority_rank),
        )
        _require_status("status", self.status)
        for field_name in (
            "priority_score",
            "coverage_gap_score",
            "freshness_gap_score",
            "conflict_gap_score",
            "traceability_gap_score",
            "coverage_ratio",
            "conflict_score",
            "traceability_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_evidence_age_hours",
            _require_nonnegative_decimal(
                "freshest_evidence_age_hours",
                self.freshest_evidence_age_hours,
            ),
        )
        object.__setattr__(self, "gap_codes", _normalize_gap_codes(self.gap_codes))
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEvidenceCollectionGapReport:
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchEvidenceCollectionGapRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceCollectionGapReport:
            raise TypeError(
                "ResearchEvidenceCollectionGapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceCollectionGapReport:
            raise ValueError("report must be exactly ResearchEvidenceCollectionGapReport")
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _require_probability_decimal(
                "highest_priority_score",
                self.highest_priority_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_gap_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_payload(_payload_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            normalized_digest = _require_public_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            object.__setattr__(self, "derived_validation_digest", normalized_digest)
            if normalized_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload(
            "ResearchEvidenceCollectionGapReport.payload",
            payload,
            allow_json_containers=True,
        )
        return payload


def build_research_evidence_collection_gap_plan(
    subjects: object,
    *,
    config: ResearchEvidenceCollectionGapPlanConfig | None = None,
) -> ResearchEvidenceCollectionGapReport:
    normalized_config = config or ResearchEvidenceCollectionGapPlanConfig()
    if type(normalized_config) is not ResearchEvidenceCollectionGapPlanConfig:
        raise ValueError("config must be exactly ResearchEvidenceCollectionGapPlanConfig")
    _require_hard_flags("config", normalized_config)
    input_subjects = _normalize_subjects(subjects)
    unranked_rows = tuple(
        _row_for_subject(subject, config=normalized_config)
        for subject in input_subjects
    )
    rows = tuple(
        _rank_row(row, rank=index + 1)
        for index, row in enumerate(sorted(unranked_rows, key=_row_sort_key))
    )
    status = _report_status(rows)
    return ResearchEvidenceCollectionGapReport(
        config_version=normalized_config.config_version,
        status=status,
        input_count=_count(len(input_subjects)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        highest_priority_score=_max_priority_score(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_evidence_collection_gap_plan_payload(
    report: ResearchEvidenceCollectionGapReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchEvidenceCollectionGapReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload(
            "ResearchEvidenceCollectionGapReport.payload",
            report,
            allow_json_containers=True,
        )
        _require_public_payload_fields(report)
        rebuilt = _report_from_payload(report)
        _validate_report(rebuilt)
        return dict(report)
    raise ValueError("report must be a ResearchEvidenceCollectionGapReport")


def _row_for_subject(
    subject: ResearchEvidenceCollectionGapSubject,
    *,
    config: ResearchEvidenceCollectionGapPlanConfig,
) -> ResearchEvidenceCollectionGapRow:
    coverage_gap_score = _coverage_gap_score(subject.coverage_ratio, config)
    freshness_gap_score = _freshness_gap_score(
        subject.freshest_evidence_age_hours,
        config,
    )
    conflict_gap_score = _conflict_gap_score(subject.conflict_score, config)
    traceability_gap_score = _traceability_gap_score(subject.traceability_ratio, config)
    priority_score = _priority_score(
        coverage_gap_score=coverage_gap_score,
        freshness_gap_score=freshness_gap_score,
        conflict_gap_score=conflict_gap_score,
        traceability_gap_score=traceability_gap_score,
    )
    status = _row_status(priority_score, config)
    return ResearchEvidenceCollectionGapRow(
        case_ref=subject.case_ref,
        domain_ref=subject.domain_ref,
        priority_rank=ONE,
        status=status,
        priority_score=priority_score,
        coverage_gap_score=coverage_gap_score,
        freshness_gap_score=freshness_gap_score,
        conflict_gap_score=conflict_gap_score,
        traceability_gap_score=traceability_gap_score,
        coverage_ratio=subject.coverage_ratio,
        freshest_evidence_age_hours=subject.freshest_evidence_age_hours,
        conflict_score=subject.conflict_score,
        traceability_ratio=subject.traceability_ratio,
        gap_codes=_row_gap_codes(
            status=status,
            coverage_gap_score=coverage_gap_score,
            freshness_gap_score=freshness_gap_score,
            conflict_gap_score=conflict_gap_score,
            traceability_gap_score=traceability_gap_score,
        ),
    )


def _rank_row(
    row: ResearchEvidenceCollectionGapRow,
    *,
    rank: int,
) -> ResearchEvidenceCollectionGapRow:
    return ResearchEvidenceCollectionGapRow(
        case_ref=row.case_ref,
        domain_ref=row.domain_ref,
        priority_rank=_count(rank),
        status=row.status,
        priority_score=row.priority_score,
        coverage_gap_score=row.coverage_gap_score,
        freshness_gap_score=row.freshness_gap_score,
        conflict_gap_score=row.conflict_gap_score,
        traceability_gap_score=row.traceability_gap_score,
        coverage_ratio=row.coverage_ratio,
        freshest_evidence_age_hours=row.freshest_evidence_age_hours,
        conflict_score=row.conflict_score,
        traceability_ratio=row.traceability_ratio,
        gap_codes=row.gap_codes,
    )


def _coverage_gap_score(
    coverage_ratio: Decimal,
    config: ResearchEvidenceCollectionGapPlanConfig,
) -> Decimal:
    if coverage_ratio >= config.min_coverage_ratio:
        return ZERO
    return _clamp_probability(
        (config.min_coverage_ratio - coverage_ratio) / config.min_coverage_ratio,
    )


def _freshness_gap_score(
    freshest_evidence_age_hours: Decimal,
    config: ResearchEvidenceCollectionGapPlanConfig,
) -> Decimal:
    if freshest_evidence_age_hours <= config.max_freshest_evidence_age_hours:
        return ZERO
    excess_age = freshest_evidence_age_hours - config.max_freshest_evidence_age_hours
    return _clamp_probability(excess_age / config.freshness_gap_span_hours)


def _conflict_gap_score(
    conflict_score: Decimal,
    config: ResearchEvidenceCollectionGapPlanConfig,
) -> Decimal:
    if conflict_score <= config.max_conflict_score:
        return ZERO
    return _clamp_probability(conflict_score - config.max_conflict_score)


def _traceability_gap_score(
    traceability_ratio: Decimal,
    config: ResearchEvidenceCollectionGapPlanConfig,
) -> Decimal:
    if traceability_ratio >= config.min_traceability_ratio:
        return ZERO
    return _clamp_probability(
        (config.min_traceability_ratio - traceability_ratio)
        / config.min_traceability_ratio,
    )


def _priority_score(
    *,
    coverage_gap_score: Decimal,
    freshness_gap_score: Decimal,
    conflict_gap_score: Decimal,
    traceability_gap_score: Decimal,
) -> Decimal:
    return _clamp_probability(
        (coverage_gap_score * COVERAGE_WEIGHT)
        + (freshness_gap_score * FRESHNESS_WEIGHT)
        + (conflict_gap_score * CONFLICT_WEIGHT)
        + (traceability_gap_score * TRACEABILITY_WEIGHT),
    )


def _row_status(
    priority_score: Decimal,
    config: ResearchEvidenceCollectionGapPlanConfig,
) -> str:
    if priority_score >= config.block_priority_score:
        return "block"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_gap_codes(
    *,
    status: str,
    coverage_gap_score: Decimal,
    freshness_gap_score: Decimal,
    conflict_gap_score: Decimal,
    traceability_gap_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"collection_gap_status_{status}"]
    if coverage_gap_score > ZERO:
        codes.append("coverage_below_floor")
    if freshness_gap_score > ZERO:
        codes.append("evidence_age_above_floor")
    if conflict_gap_score > ZERO:
        codes.append("conflict_pressure_present")
    if traceability_gap_score > ZERO:
        codes.append("traceability_below_floor")
    return tuple(codes)


def _row_sort_key(row: ResearchEvidenceCollectionGapRow) -> tuple[Decimal, str, str]:
    return (-row.priority_score, row.case_ref, row.domain_ref)


def _report_status(rows: tuple[ResearchEvidenceCollectionGapRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEvidenceCollectionGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("collection_gap_no_inputs",)
    status = _report_status(rows)
    row_codes = {code for row in rows for code in row.gap_codes}
    codes = [f"collection_gap_status_{status}"]
    for code in GAP_REASON_CODES:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _status_count(rows: tuple[ResearchEvidenceCollectionGapRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _max_priority_score(rows: tuple[ResearchEvidenceCollectionGapRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _validate_report(report: ResearchEvidenceCollectionGapReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.highest_priority_score != _max_priority_score(report.rows):
        raise ValueError("highest_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _digest_payload(_payload_without_digest(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_subjects(
    value: object,
) -> tuple[ResearchEvidenceCollectionGapSubject, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("subjects must be ResearchEvidenceCollectionGapSubject values")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not ResearchEvidenceCollectionGapSubject:
            raise ValueError("subjects must be ResearchEvidenceCollectionGapSubject values")
        _require_hard_flags("subject", item)
    return normalized


def _normalize_rows(value: object) -> tuple[ResearchEvidenceCollectionGapRow, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("rows must be ResearchEvidenceCollectionGapRow values")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEvidenceCollectionGapRow:
            raise ValueError("rows must be ResearchEvidenceCollectionGapRow values")
        _require_hard_flags("row", row)
    expected_ranks = tuple(_count(index + 1) for index in range(len(rows)))
    actual_ranks = tuple(row.priority_rank for row in rows)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank must match row sequence")
    return rows


def _normalize_gap_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("gap_codes must be a non-empty tuple")
    for value in values:
        _require_public_identifier("gap_codes", value)
    return values


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label}.{field_name} must be present")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


REPORT_PAYLOAD_FIELDS = (
    "config_version",
    "status",
    "input_count",
    "pass_count",
    "watch_count",
    "block_count",
    "highest_priority_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _require_public_payload_fields(payload: Mapping[str, object]) -> None:
    for field_name in REPORT_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(REPORT_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _report_from_payload(payload: Mapping[str, object]) -> ResearchEvidenceCollectionGapReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    return ResearchEvidenceCollectionGapReport(
        config_version=_payload_string("config_version", payload["config_version"]),
        status=_payload_string("status", payload["status"]),
        input_count=_decimal_from_payload("input_count", payload["input_count"]),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        highest_priority_score=_decimal_from_payload(
            "highest_priority_score",
            payload["highest_priority_score"],
        ),
        rows=tuple(_row_from_payload(item) for item in rows_value),
        reason_codes=_tuple_from_payload("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_payload(value: object) -> ResearchEvidenceCollectionGapRow:
    if type(value) is not dict:
        raise ValueError("row must be a dict")
    return ResearchEvidenceCollectionGapRow(
        case_ref=_payload_string("case_ref", value.get("case_ref")),
        domain_ref=_payload_string("domain_ref", value.get("domain_ref")),
        priority_rank=_decimal_from_payload("priority_rank", value.get("priority_rank")),
        status=_payload_string("status", value.get("status")),
        priority_score=_decimal_from_payload("priority_score", value.get("priority_score")),
        coverage_gap_score=_decimal_from_payload(
            "coverage_gap_score",
            value.get("coverage_gap_score"),
        ),
        freshness_gap_score=_decimal_from_payload(
            "freshness_gap_score",
            value.get("freshness_gap_score"),
        ),
        conflict_gap_score=_decimal_from_payload(
            "conflict_gap_score",
            value.get("conflict_gap_score"),
        ),
        traceability_gap_score=_decimal_from_payload(
            "traceability_gap_score",
            value.get("traceability_gap_score"),
        ),
        coverage_ratio=_decimal_from_payload("coverage_ratio", value.get("coverage_ratio")),
        freshest_evidence_age_hours=_decimal_from_payload(
            "freshest_evidence_age_hours",
            value.get("freshest_evidence_age_hours"),
        ),
        conflict_score=_decimal_from_payload("conflict_score", value.get("conflict_score")),
        traceability_ratio=_decimal_from_payload(
            "traceability_ratio",
            value.get("traceability_ratio"),
        ),
        gap_codes=_tuple_from_payload("gap_codes", value.get("gap_codes")),
        paper_only=_payload_bool("paper_only", value.get("paper_only")),
        report_only=_payload_bool("report_only", value.get("report_only")),
        readonly=_payload_bool("readonly", value.get("readonly")),
    )


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    return _require_decimal(field_name, Decimal(value))


def _tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_without_digest(report: ResearchEvidenceCollectionGapReport) -> dict[str, object]:
    payload = asdict(report)
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(
        ("research_evidence_collection_gap_plan|" + encoded.decode("utf-8")).encode(
            "utf-8",
        ),
    ).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_string("field", field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string("field", key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if value is None or type(value) in (bool, Decimal):
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


__all__ = (
    "DEFAULT_RESEARCH_EVIDENCE_COLLECTION_GAP_PLAN_CONFIG_VERSION",
    "ResearchEvidenceCollectionGapPlanConfig",
    "ResearchEvidenceCollectionGapReport",
    "ResearchEvidenceCollectionGapRow",
    "ResearchEvidenceCollectionGapSubject",
    "build_research_evidence_collection_gap_plan",
    "research_evidence_collection_gap_plan_payload",
)
