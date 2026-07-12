"""Pure paper-only probability event final review exception queue report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_AGE_24H = Decimal("24.000000")
_EXCEPTION_STATUSES = frozenset(("clear", "watch", "blocked"))
_EXCEPTION_TYPES = frozenset(
    (
        "source_gap",
        "unsafe_payload",
        "owner_missing",
        "conflicting_evidence",
        "liquidity_block",
    ),
)
_BLOCKING_STAGES = frozenset(
    (
        "final_review",
        "operator_safety",
        "evidence_review",
        "manual_assignment",
        "liquidity_review",
    ),
)
_BLOCKED_EXCEPTION_TYPES = frozenset(("unsafe_payload", "liquidity_block"))
_BLOCKED_STAGES = frozenset(("operator_safety", "liquidity_review"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "unsafe_payload_exception_present",
    "operator_safety_blocking_stage_present",
    "retry_not_allowed_present",
    "liquidity_block_exception_present",
    "liquidity_review_blocking_stage_present",
    "owner_missing_exception_present",
    "manual_assignment_blocking_stage_present",
    "manual_owner_missing",
    "age_over_24h",
    "source_gap_exception_present",
    "conflicting_evidence_exception_present",
    "evidence_review_blocking_stage_present",
)


@dataclass(frozen=True)
class FinalReviewExceptionQueueCandidate:
    candidate_id: str
    event_id: str
    exception_type: str
    blocking_stage: str
    age_hours: Decimal
    manual_owner: str | None
    retry_allowed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not FinalReviewExceptionQueueCandidate:
            raise ValueError("candidate must be exactly FinalReviewExceptionQueueCandidate")
        _require_public_string("candidate_id", self.candidate_id)
        _require_public_string("event_id", self.event_id)
        _require_exception_type("exception_type", self.exception_type)
        _require_blocking_stage("blocking_stage", self.blocking_stage)
        object.__setattr__(
            self,
            "age_hours",
            _require_nonnegative_decimal("age_hours", self.age_hours),
        )
        object.__setattr__(
            self,
            "manual_owner",
            _normalize_optional_public_string("manual_owner", self.manual_owner),
        )
        _require_bool("retry_allowed", self.retry_allowed)
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class FinalReviewExceptionQueueRow:
    candidate_id: str
    event_id: str
    exception_type: str
    blocking_stage: str
    age_hours: Decimal
    manual_owner: str | None
    retry_allowed: bool
    exception_status: str
    priority_rank: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not FinalReviewExceptionQueueRow:
            raise ValueError("row must be exactly FinalReviewExceptionQueueRow")
        _require_public_string("candidate_id", self.candidate_id)
        _require_public_string("event_id", self.event_id)
        _require_exception_type("exception_type", self.exception_type)
        _require_blocking_stage("blocking_stage", self.blocking_stage)
        object.__setattr__(
            self,
            "age_hours",
            _require_nonnegative_decimal("age_hours", self.age_hours),
        )
        object.__setattr__(
            self,
            "manual_owner",
            _normalize_optional_public_string("manual_owner", self.manual_owner),
        )
        _require_bool("retry_allowed", self.retry_allowed)
        _require_exception_status("exception_status", self.exception_status)
        object.__setattr__(
            self,
            "priority_rank",
            _require_count_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_string("manual_next_step", self.manual_next_step)
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ProbabilityEventFinalReviewExceptionQueueReport:
    exception_status: str
    total_exception_count: Decimal
    blocked_exception_count: Decimal
    watch_exception_count: Decimal
    manual_owner_missing_count: Decimal
    retry_allowed_count: Decimal
    oldest_age_hours: Decimal
    rows: tuple[FinalReviewExceptionQueueRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventFinalReviewExceptionQueueReport:
            raise ValueError("report must be exactly ProbabilityEventFinalReviewExceptionQueueReport")
        _require_exception_status("exception_status", self.exception_status)
        for field_name in (
            "total_exception_count",
            "blocked_exception_count",
            "watch_exception_count",
            "manual_owner_missing_count",
            "retry_allowed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_age_hours",
            _require_nonnegative_decimal("oldest_age_hours", self.oldest_age_hours),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _payload_without_digest(self)
        payload["digest"] = self.digest
        return payload

    @property
    def digest(self) -> str:
        canonical = json.dumps(
            _payload_without_digest(self),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_probability_event_final_review_exception_queue_report(
    candidates: Sequence[FinalReviewExceptionQueueCandidate],
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventFinalReviewExceptionQueueReport:
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)
    normalized_candidates = _normalize_candidates(candidates)
    rows = _rank_rows(tuple(_row_from_candidate(candidate) for candidate in normalized_candidates))

    return ProbabilityEventFinalReviewExceptionQueueReport(
        exception_status=_report_status(rows),
        total_exception_count=_decimal_count(len(rows)),
        blocked_exception_count=_status_count(rows, "blocked"),
        watch_exception_count=_status_count(rows, "watch"),
        manual_owner_missing_count=_decimal_count(
            _true_count(tuple(row.manual_owner is None for row in rows)),
        ),
        retry_allowed_count=_decimal_count(
            _true_count(tuple(row.retry_allowed for row in rows)),
        ),
        oldest_age_hours=_max_decimal(tuple(row.age_hours for row in rows)),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_final_review_exception_queue_report_payload(
    report: ProbabilityEventFinalReviewExceptionQueueReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventFinalReviewExceptionQueueReport:
        raise ValueError("report must be a ProbabilityEventFinalReviewExceptionQueueReport")
    return report.public_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _row_from_candidate(candidate: FinalReviewExceptionQueueCandidate) -> FinalReviewExceptionQueueRow:
    status = _row_status(candidate)
    return FinalReviewExceptionQueueRow(
        candidate_id=candidate.candidate_id,
        event_id=candidate.event_id,
        exception_type=candidate.exception_type,
        blocking_stage=candidate.blocking_stage,
        age_hours=candidate.age_hours,
        manual_owner=candidate.manual_owner,
        retry_allowed=candidate.retry_allowed,
        exception_status=status,
        priority_rank=Decimal("1.000000"),
        reason_codes=_row_reason_codes(candidate),
        manual_next_step=_manual_next_step(candidate),
        paper_only=candidate.paper_only,
        report_only=candidate.report_only,
        readonly=candidate.readonly,
    )


def _rank_rows(rows: tuple[FinalReviewExceptionQueueRow, ...]) -> tuple[FinalReviewExceptionQueueRow, ...]:
    ranked = sorted(
        rows,
        key=lambda row: (
            _status_priority(row.exception_status),
            _missing_owner_priority(row.manual_owner),
            _retry_priority(row.retry_allowed),
            -row.age_hours,
            row.candidate_id,
        ),
    )
    return tuple(
        FinalReviewExceptionQueueRow(
            candidate_id=row.candidate_id,
            event_id=row.event_id,
            exception_type=row.exception_type,
            blocking_stage=row.blocking_stage,
            age_hours=row.age_hours,
            manual_owner=row.manual_owner,
            retry_allowed=row.retry_allowed,
            exception_status=row.exception_status,
            priority_rank=_decimal_count(index),
            reason_codes=row.reason_codes,
            manual_next_step=row.manual_next_step,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        )
        for index, row in enumerate(ranked, start=1)
    )


def _row_status(candidate: FinalReviewExceptionQueueCandidate) -> str:
    if (
        candidate.exception_type in _BLOCKED_EXCEPTION_TYPES
        or candidate.blocking_stage in _BLOCKED_STAGES
        or not candidate.retry_allowed
    ):
        return "blocked"
    return "watch"


def _report_status(rows: tuple[FinalReviewExceptionQueueRow, ...]) -> str:
    if not rows:
        return "clear"
    if any(row.exception_status == "blocked" for row in rows):
        return "blocked"
    return "watch"


def _row_reason_codes(candidate: FinalReviewExceptionQueueCandidate) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.exception_type == "unsafe_payload":
        reason_codes.append("unsafe_payload_exception_present")
    if candidate.blocking_stage == "operator_safety":
        reason_codes.append("operator_safety_blocking_stage_present")
    if not candidate.retry_allowed:
        reason_codes.append("retry_not_allowed_present")
    if candidate.exception_type == "liquidity_block":
        reason_codes.append("liquidity_block_exception_present")
    if candidate.blocking_stage == "liquidity_review":
        reason_codes.append("liquidity_review_blocking_stage_present")
    if candidate.exception_type == "owner_missing":
        reason_codes.append("owner_missing_exception_present")
    if candidate.blocking_stage == "manual_assignment":
        reason_codes.append("manual_assignment_blocking_stage_present")
    if candidate.manual_owner is None:
        reason_codes.append("manual_owner_missing")
    if candidate.age_hours > _AGE_24H:
        reason_codes.append("age_over_24h")
    if candidate.exception_type == "source_gap":
        reason_codes.append("source_gap_exception_present")
    if candidate.exception_type == "conflicting_evidence":
        reason_codes.append("conflicting_evidence_exception_present")
    if candidate.blocking_stage == "evidence_review":
        reason_codes.append("evidence_review_blocking_stage_present")
    return _normalize_reason_codes(reason_codes)


def _report_reason_codes(rows: tuple[FinalReviewExceptionQueueRow, ...]) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _manual_next_step(candidate: FinalReviewExceptionQueueCandidate) -> str:
    if candidate.exception_type == "unsafe_payload" or candidate.blocking_stage == "operator_safety":
        if not candidate.retry_allowed:
            return "Escalate to safety owner; retry disabled."
        return "Escalate to safety owner before final review."
    if candidate.manual_owner is None or candidate.exception_type == "owner_missing":
        return "Assign a manual owner before retry."
    if candidate.exception_type == "liquidity_block" or candidate.blocking_stage == "liquidity_review":
        return "Route to liquidity reviewer before retry."
    if candidate.exception_type == "conflicting_evidence":
        return "Resolve conflicting evidence before retry."
    return "Refresh evidence and retry final review."


def _validate_row_consistency(row: FinalReviewExceptionQueueRow) -> None:
    candidate = FinalReviewExceptionQueueCandidate(
        candidate_id=row.candidate_id,
        event_id=row.event_id,
        exception_type=row.exception_type,
        blocking_stage=row.blocking_stage,
        age_hours=row.age_hours,
        manual_owner=row.manual_owner,
        retry_allowed=row.retry_allowed,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )
    if row.exception_status != _row_status(candidate):
        raise ValueError("exception_status must match row inputs")
    if row.reason_codes != _row_reason_codes(candidate):
        raise ValueError("reason_codes must match row inputs")
    if row.manual_next_step != _manual_next_step(candidate):
        raise ValueError("manual_next_step must match row inputs")


def _validate_report_consistency(report: ProbabilityEventFinalReviewExceptionQueueReport) -> None:
    rows = report.rows
    if report.exception_status != _report_status(rows):
        raise ValueError("exception_status must match report inputs")
    if report.total_exception_count != _decimal_count(len(rows)):
        raise ValueError("total_exception_count must match report inputs")
    if report.blocked_exception_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_exception_count must match report inputs")
    if report.watch_exception_count != _status_count(rows, "watch"):
        raise ValueError("watch_exception_count must match report inputs")
    if report.manual_owner_missing_count != _decimal_count(
        _true_count(tuple(row.manual_owner is None for row in rows)),
    ):
        raise ValueError("manual_owner_missing_count must match report inputs")
    if report.retry_allowed_count != _decimal_count(_true_count(tuple(row.retry_allowed for row in rows))):
        raise ValueError("retry_allowed_count must match report inputs")
    if report.oldest_age_hours != _max_decimal(tuple(row.age_hours for row in rows)):
        raise ValueError("oldest_age_hours must match report inputs")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match report inputs")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    actual_ranks = tuple(row.priority_rank for row in rows)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank must match report inputs")


def _status_priority(exception_status: str) -> int:
    if exception_status == "blocked":
        return 0
    if exception_status == "watch":
        return 1
    return 2


def _missing_owner_priority(manual_owner: str | None) -> int:
    if manual_owner is None:
        return 0
    return 1


def _retry_priority(retry_allowed: bool) -> int:
    if not retry_allowed:
        return 0
    return 1


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_string(field_name, value)


def _require_exception_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _EXCEPTION_TYPES:
        raise ValueError(f"{field_name} must be supported")


def _require_blocking_stage(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _BLOCKING_STAGES:
        raise ValueError(f"{field_name} must be supported")


def _require_exception_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _EXCEPTION_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _true_count(values: Sequence[bool]) -> int:
    return sum(1 for value in values if value is True)


def _status_count(rows: tuple[FinalReviewExceptionQueueRow, ...], status: str) -> Decimal:
    return _decimal_count(_true_count(tuple(row.exception_status == status for row in rows)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _normalize_candidates(
    candidates: Sequence[FinalReviewExceptionQueueCandidate],
) -> tuple[FinalReviewExceptionQueueCandidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        raise ValueError("candidates must be a sequence")
    normalized: list[FinalReviewExceptionQueueCandidate] = []
    seen_ids: set[str] = set()
    for candidate in candidates:
        if type(candidate) is not FinalReviewExceptionQueueCandidate:
            raise ValueError("candidates must contain FinalReviewExceptionQueueCandidate")
        if candidate.candidate_id in seen_ids:
            raise ValueError("candidate_id must be unique")
        seen_ids.add(candidate.candidate_id)
        _require_hard_flags("candidate", candidate)
        normalized.append(candidate)
    return tuple(normalized)


def _normalize_rows(rows: Sequence[FinalReviewExceptionQueueRow]) -> tuple[FinalReviewExceptionQueueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[FinalReviewExceptionQueueRow] = []
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not FinalReviewExceptionQueueRow:
            raise ValueError("rows must contain FinalReviewExceptionQueueRow")
        if row.candidate_id in seen_ids:
            raise ValueError("candidate_id must be unique")
        seen_ids.add(row.candidate_id)
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)


def _payload_without_digest(
    report: ProbabilityEventFinalReviewExceptionQueueReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
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


__all__ = (
    "FinalReviewExceptionQueueCandidate",
    "FinalReviewExceptionQueueRow",
    "ProbabilityEventFinalReviewExceptionQueueReport",
    "build_probability_event_final_review_exception_queue_report",
    "probability_event_final_review_exception_queue_report_payload",
)
