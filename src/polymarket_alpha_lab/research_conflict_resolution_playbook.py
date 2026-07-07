"""Pure report builder for caller-supplied research conflict cases."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_CONFLICT_RESOLUTION_CONFIG_VERSION = (
    "research-conflict-resolution-playbook-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "blocked"))
_CONFLICT_TYPES = frozenset(
    (
        "factual_mismatch",
        "timing_mismatch",
        "source_methodology_mismatch",
        "source_identity_mismatch",
        "outcome_definition_mismatch",
    ),
)
_REVIEW_STATUSES = frozenset(("resolved", "in_review", "unreviewed", "escalated"))
_ESCALATION_PATHS = frozenset(
    (
        "none_required",
        "source_owner_review",
        "senior_research_review",
    ),
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "b" + "uy",
    "s" + "ell",
    "pos" + "ition",
    "li" + "ve",
    "tr" + "ading",
    "aut" + "h",
    "wall" + "et",
    "ord" + "er",
    "mut" + "ation",
    "net" + "work",
    "data" + "base",
    "persist",
)
_REASON_CODE_SEQUENCE = (
    "empty_conflict_resolution_queue",
    "conflict_resolution_pass",
    "resolved_review_status",
    "in_review_review_status",
    "unreviewed_review_status",
    "escalated_review_status",
    "supplemental_information_needed",
    "factual_mismatch_conflict",
    "timing_mismatch_conflict",
    "source_methodology_mismatch_conflict",
    "source_identity_mismatch_conflict",
    "outcome_definition_mismatch_conflict",
    "unscored_conflict",
    "watch_conflict_score",
    "block_conflict_score",
)


@dataclass(frozen=True)
class ResearchConflictResolutionConfig:
    config_version: str = DEFAULT_RESEARCH_CONFLICT_RESOLUTION_CONFIG_VERSION
    pass_max_conflict_score: Decimal = Decimal("0.200000")
    block_min_conflict_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchConflictResolutionConfig:
            raise TypeError("ResearchConflictResolutionConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchConflictResolutionConfig:
            raise ValueError("config must be exactly ResearchConflictResolutionConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CONFLICT_RESOLUTION_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "pass_max_conflict_score",
            _require_ratio_decimal("pass_max_conflict_score", self.pass_max_conflict_score),
        )
        object.__setattr__(
            self,
            "block_min_conflict_score",
            _require_ratio_decimal("block_min_conflict_score", self.block_min_conflict_score),
        )
        if self.pass_max_conflict_score >= self.block_min_conflict_score:
            raise ValueError("pass_max_conflict_score must be less than block_min_conflict_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchConflictResolutionCase:
    case_id: str
    claim_id: str
    conflict_type: str
    evidence_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    public_summary: str
    observed_at: datetime
    severity_score: Decimal | None = None
    review_status: str = "unreviewed"
    supplemental_information_needed: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchConflictResolutionCase:
            raise TypeError("ResearchConflictResolutionCase does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchConflictResolutionCase:
            raise ValueError("case must be exactly ResearchConflictResolutionCase")
        _require_public_identifier("case_id", self.case_id)
        _require_public_identifier("claim_id", self.claim_id)
        _require_conflict_type("conflict_type", self.conflict_type)
        object.__setattr__(
            self,
            "evidence_ids",
            _normalize_public_identifier_tuple(
                "evidence_ids",
                self.evidence_ids,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_public_identifier_tuple(
                "source_families",
                self.source_families,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "public_summary",
            _require_public_text("public_summary", self.public_summary),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "severity_score",
            _require_optional_ratio_decimal("severity_score", self.severity_score),
        )
        _require_review_status("review_status", self.review_status)
        object.__setattr__(
            self,
            "supplemental_information_needed",
            _normalize_public_identifier_tuple(
                "supplemental_information_needed",
                self.supplemental_information_needed,
                allow_empty=True,
            ),
        )
        _require_hard_flags("case", self)
        _reject_unsafe_public_payload("case", self)


@dataclass(frozen=True)
class ResearchConflictResolutionPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchConflictResolutionPublicPayloadItem:
            raise TypeError(
                "ResearchConflictResolutionPublicPayloadItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchConflictResolutionPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchConflictResolutionPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchConflictResolutionRow:
    case_id: str
    claim_id: str
    conflict_type: str
    evidence_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    public_summary: str
    observed_at: datetime
    severity_score: Decimal | None
    review_status: str
    supplemental_information_needed: tuple[str, ...]
    escalation_path: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchConflictResolutionRow:
            raise TypeError("ResearchConflictResolutionRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchConflictResolutionRow:
            raise ValueError("row must be exactly ResearchConflictResolutionRow")
        _require_public_identifier("case_id", self.case_id)
        _require_public_identifier("claim_id", self.claim_id)
        _require_conflict_type("conflict_type", self.conflict_type)
        object.__setattr__(
            self,
            "evidence_ids",
            _normalize_public_identifier_tuple(
                "evidence_ids",
                self.evidence_ids,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_public_identifier_tuple(
                "source_families",
                self.source_families,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "public_summary",
            _require_public_text("public_summary", self.public_summary),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "severity_score",
            _require_optional_ratio_decimal("severity_score", self.severity_score),
        )
        _require_review_status("review_status", self.review_status)
        object.__setattr__(
            self,
            "supplemental_information_needed",
            _normalize_public_identifier_tuple(
                "supplemental_information_needed",
                self.supplemental_information_needed,
                allow_empty=True,
            ),
        )
        _require_escalation_path("escalation_path", self.escalation_path)
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchConflictResolutionReport:
    generated_at: datetime
    config_version: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_severity_score: Decimal | None
    status: str
    rows: tuple[ResearchConflictResolutionRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchConflictResolutionPublicPayloadItem, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchConflictResolutionReport:
            raise TypeError("ResearchConflictResolutionReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchConflictResolutionReport:
            raise ValueError("report must be exactly ResearchConflictResolutionReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CONFLICT_RESOLUTION_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("case_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_severity_score",
            _require_optional_ratio_decimal(
                "average_severity_score",
                self.average_severity_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchConflictResolutionReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_conflict_resolution_playbook(
    cases: Sequence[ResearchConflictResolutionCase],
    *,
    generated_at: datetime,
    config: ResearchConflictResolutionConfig | None = None,
    public_payload: Sequence[ResearchConflictResolutionPublicPayloadItem] = (),
) -> ResearchConflictResolutionReport:
    if config is None:
        config = ResearchConflictResolutionConfig()
    if type(config) is not ResearchConflictResolutionConfig:
        raise ValueError("config must be a ResearchConflictResolutionConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_cases = _normalize_cases(cases)
    for item in normalized_cases:
        if item.observed_at > generated_at:
            raise ValueError("case observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = tuple(_row_from_case(item, config) for item in normalized_cases)
    reason_codes = _report_reason_codes(rows)
    return ResearchConflictResolutionReport(
        generated_at=generated_at,
        config_version=config.config_version,
        case_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_severity_score=_average_optional(
            tuple(row.severity_score for row in rows if row.severity_score is not None),
        ),
        status=_report_status(rows),
        rows=rows,
        reason_codes=reason_codes,
        public_payload=payload_items,
    )


def research_conflict_resolution_playbook_payload(
    report: ResearchConflictResolutionReport,
) -> dict[str, object]:
    if type(report) is not ResearchConflictResolutionReport:
        raise ValueError("report must be a ResearchConflictResolutionReport")
    _require_hard_flags("report", report)
    return report.payload


def _row_from_case(
    item: ResearchConflictResolutionCase,
    config: ResearchConflictResolutionConfig,
) -> ResearchConflictResolutionRow:
    status = _row_status(item, config)
    return ResearchConflictResolutionRow(
        case_id=item.case_id,
        claim_id=item.claim_id,
        conflict_type=item.conflict_type,
        evidence_ids=item.evidence_ids,
        source_families=item.source_families,
        public_summary=item.public_summary,
        observed_at=item.observed_at,
        severity_score=item.severity_score,
        review_status=item.review_status,
        supplemental_information_needed=item.supplemental_information_needed,
        escalation_path=_escalation_path_for_status(status),
        status=status,
        reason_codes=_row_reason_codes(item, status, config),
    )


def _row_status(
    item: ResearchConflictResolutionCase,
    config: ResearchConflictResolutionConfig,
) -> str:
    if item.review_status == "resolved" and not item.supplemental_information_needed:
        if item.severity_score is None or item.severity_score <= config.pass_max_conflict_score:
            return "pass"
    if item.review_status in ("unreviewed", "escalated"):
        return "blocked"
    if item.severity_score is not None and item.severity_score >= config.block_min_conflict_score:
        return "blocked"
    return "watch"


def _escalation_path_for_status(status: str) -> str:
    if status == "pass":
        return "none_required"
    if status == "watch":
        return "source_owner_review"
    if status == "blocked":
        return "senior_research_review"
    raise ValueError("status must be known")


def _row_reason_codes(
    item: ResearchConflictResolutionCase,
    status: str,
    config: ResearchConflictResolutionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == "pass":
        reason_codes.append("conflict_resolution_pass")
    reason_codes.append(f"{item.review_status}_review_status")
    if item.supplemental_information_needed:
        reason_codes.append("supplemental_information_needed")
    if status != "pass":
        reason_codes.append(f"{item.conflict_type}_conflict")
    if item.severity_score is None:
        reason_codes.append("unscored_conflict")
    elif item.severity_score >= config.block_min_conflict_score:
        reason_codes.append("block_conflict_score")
    elif item.severity_score > config.pass_max_conflict_score:
        reason_codes.append("watch_conflict_score")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchConflictResolutionRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchConflictResolutionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_conflict_resolution_queue",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[ResearchConflictResolutionRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_cases(
    cases: Sequence[ResearchConflictResolutionCase],
) -> tuple[ResearchConflictResolutionCase, ...]:
    if isinstance(cases, (str, bytes)) or not isinstance(cases, Sequence):
        raise ValueError("cases must be a sequence")
    normalized: list[ResearchConflictResolutionCase] = []
    for item in cases:
        if type(item) is not ResearchConflictResolutionCase:
            raise ValueError("cases must contain ResearchConflictResolutionCase")
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.claim_id, item.case_id)))


def _normalize_rows(
    rows: Sequence[ResearchConflictResolutionRow],
) -> tuple[ResearchConflictResolutionRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchConflictResolutionRow] = []
    for row in rows:
        if type(row) is not ResearchConflictResolutionRow:
            raise ValueError("rows must contain ResearchConflictResolutionRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.claim_id, row.case_id)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchConflictResolutionPublicPayloadItem],
) -> tuple[ResearchConflictResolutionPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchConflictResolutionPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchConflictResolutionPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchConflictResolutionPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_public_identifier_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_public_identifier(field_name, value))
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(dict.fromkeys(normalized)))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _validate_row_consistency(row: ResearchConflictResolutionRow) -> None:
    expected_status = _status_from_row_values(row)
    if row.status != expected_status:
        raise ValueError("status must match conflict score and review status")
    if row.escalation_path != _escalation_path_for_status(row.status):
        raise ValueError("escalation_path must match status")
    if row.reason_codes != _reason_codes_from_row_values(row):
        raise ValueError("reason_codes must match row values")


def _status_from_row_values(row: ResearchConflictResolutionRow) -> str:
    if row.review_status == "resolved" and not row.supplemental_information_needed:
        if row.severity_score is None or row.severity_score <= Decimal("0.200000"):
            return "pass"
    if row.review_status in ("unreviewed", "escalated"):
        return "blocked"
    if row.severity_score is not None and row.severity_score >= Decimal("0.700000"):
        return "blocked"
    return "watch"


def _reason_codes_from_row_values(
    row: ResearchConflictResolutionRow,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.status == "pass":
        reason_codes.append("conflict_resolution_pass")
    reason_codes.append(f"{row.review_status}_review_status")
    if row.supplemental_information_needed:
        reason_codes.append("supplemental_information_needed")
    if row.status != "pass":
        reason_codes.append(f"{row.conflict_type}_conflict")
    if row.severity_score is None:
        reason_codes.append("unscored_conflict")
    elif row.severity_score >= Decimal("0.700000"):
        reason_codes.append("block_conflict_score")
    elif row.severity_score > Decimal("0.200000"):
        reason_codes.append("watch_conflict_score")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_report_consistency(report: ResearchConflictResolutionReport) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    expected_average = _average_optional(
        tuple(row.severity_score for row in report.rows if row.severity_score is not None),
    )
    if report.average_severity_score != expected_average:
        raise ValueError("average_severity_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_conflict_type(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _CONFLICT_TYPES:
        raise ValueError(f"{field_name} must be a supported conflict type")
    return value


def _require_review_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REVIEW_STATUSES:
        raise ValueError(f"{field_name} must be a supported review status")
    return value


def _require_escalation_path(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ESCALATION_PATHS:
        raise ValueError(f"{field_name} must be a supported escalation path")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a known status")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
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
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
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
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_CONFLICT_RESOLUTION_CONFIG_VERSION",
    "ResearchConflictResolutionCase",
    "ResearchConflictResolutionConfig",
    "ResearchConflictResolutionPublicPayloadItem",
    "ResearchConflictResolutionReport",
    "ResearchConflictResolutionRow",
    "build_research_conflict_resolution_playbook",
    "research_conflict_resolution_playbook_payload",
)
