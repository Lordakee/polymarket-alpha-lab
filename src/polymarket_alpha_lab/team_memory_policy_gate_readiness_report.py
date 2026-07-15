"""Report-only team-memory policy gate for research context readiness.

This module models allow/throttle/block team-memory context policy as a
read-only research gate. It produces paper evidence for whether candidate
research context should proceed, slow down for manual review, or stop. It does
not score appeal, allocate capital, or permit execution.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "DEFAULT_TEAM_MEMORY_POLICY_GATE_READINESS_CONFIG_VERSION",
    "TeamMemoryPolicyGateCandidate",
    "TeamMemoryPolicyGateReadinessConfig",
    "TeamMemoryPolicyGateReadinessReasonCodeCount",
    "TeamMemoryPolicyGateReadinessReport",
    "TeamMemoryPolicyGateReadinessRow",
    "build_team_memory_policy_gate_readiness_report",
    "team_memory_policy_gate_readiness_report_payload",
)


DEFAULT_TEAM_MEMORY_POLICY_GATE_READINESS_CONFIG_VERSION = (
    "team-memory-policy-gate-readiness-v0"
)
POLICY_STATUSES = ("allow", "throttle", "block")
GATE_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_TERMS = (
    "dsn",
    "database_url",
    "postgres://",
    "postgresql://",
    "supabase.co",
    "raw_source",
    "raw-source",
    "raw source",
    "source_id",
    "source-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "market-",
    "token",
    "secret",
    "api_key",
    "bearer",
    "private" + "_key",
)


@dataclass(frozen=True)
class TeamMemoryPolicyGateReadinessConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_POLICY_GATE_READINESS_CONFIG_VERSION
    allow_context_floor: Decimal = Decimal("0.800000")
    throttle_context_floor: Decimal = Decimal("0.500000")
    manual_follow_up_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamMemoryPolicyGateReadinessConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_TEAM_MEMORY_POLICY_GATE_READINESS_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "allow_context_floor",
            "throttle_context_floor",
            "manual_follow_up_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.allow_context_floor <= self.throttle_context_floor:
            raise ValueError("allow_context_floor must exceed throttle_context_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class TeamMemoryPolicyGateCandidate:
    candidate_id: str
    memory_context_score: Decimal
    memory_gap_score: Decimal = ZERO
    redaction_confirmed: bool = True
    stale_memory_flag: bool = False
    conflicting_memory_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamMemoryPolicyGateCandidate, "candidate")
        _require_public_identifier("candidate_id", self.candidate_id)
        _reject_unsafe_public_text("candidate_id", self.candidate_id)
        for field_name in ("memory_context_score", "memory_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "redaction_confirmed",
            "stale_memory_flag",
            "conflicting_memory_flag",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class TeamMemoryPolicyGateReadinessRow:
    candidate_id: str
    memory_context_score: Decimal
    memory_gap_score: Decimal
    policy_status: str
    reason_codes: tuple[str, ...]
    manual_follow_up: bool
    gate_status: str
    redaction_confirmed: bool = True
    stale_memory_flag: bool = False
    conflicting_memory_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamMemoryPolicyGateReadinessRow, "row")
        _require_public_identifier("candidate_id", self.candidate_id)
        _reject_unsafe_public_text("candidate_id", self.candidate_id)
        for field_name in ("memory_context_score", "memory_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_enum("policy_status", self.policy_status, POLICY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in (
            "manual_follow_up",
            "redaction_confirmed",
            "stale_memory_flag",
            "conflicting_memory_flag",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_enum("gate_status", self.gate_status, GATE_STATUSES)
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class TeamMemoryPolicyGateReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamMemoryPolicyGateReadinessReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_whole_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class TeamMemoryPolicyGateReadinessReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    allow_count: Decimal
    throttle_count: Decimal
    block_count: Decimal
    manual_follow_up_count: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[TeamMemoryPolicyGateReadinessReasonCodeCount, ...]
    rows: tuple[TeamMemoryPolicyGateReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamMemoryPolicyGateReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "allow_count",
            "throttle_count",
            "block_count",
            "manual_follow_up_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_enum("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload(self)


def build_team_memory_policy_gate_readiness_report(
    candidates: Iterable[object],
    *,
    config: TeamMemoryPolicyGateReadinessConfig,
    generated_at: datetime,
) -> TeamMemoryPolicyGateReadinessReport:
    if type(config) is not TeamMemoryPolicyGateReadinessConfig:
        raise ValueError("config must be a TeamMemoryPolicyGateReadinessConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        _row_from_candidate(candidate, config=config)
        for candidate in sorted(normalized_candidates, key=lambda item: item.candidate_id)
    )
    report_reason_codes = _report_reason_codes(rows)

    return TeamMemoryPolicyGateReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_decimal_count(len(rows)),
        allow_count=_decimal_count(_policy_count(rows, "allow")),
        throttle_count=_decimal_count(_policy_count(rows, "throttle")),
        block_count=_decimal_count(_policy_count(rows, "block")),
        manual_follow_up_count=_decimal_count(
            sum(1 for row in rows if row.manual_follow_up),
        ),
        gate_status=_report_gate_status(rows),
        reason_codes=report_reason_codes,
        reason_code_counts=_reason_code_counts(rows, report_reason_codes),
        rows=rows,
    )


def team_memory_policy_gate_readiness_report_payload(
    report: TeamMemoryPolicyGateReadinessReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryPolicyGateReadinessReport:
        raise ValueError("report must be a TeamMemoryPolicyGateReadinessReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _row_from_candidate(
    candidate: TeamMemoryPolicyGateCandidate,
    *,
    config: TeamMemoryPolicyGateReadinessConfig,
) -> TeamMemoryPolicyGateReadinessRow:
    policy_status = _policy_status(candidate, config)
    reason_codes = _row_reason_codes(candidate, policy_status, config)
    manual_follow_up = _manual_follow_up(candidate, policy_status, config)
    return TeamMemoryPolicyGateReadinessRow(
        candidate_id=candidate.candidate_id,
        memory_context_score=candidate.memory_context_score,
        memory_gap_score=candidate.memory_gap_score,
        policy_status=policy_status,
        reason_codes=reason_codes,
        manual_follow_up=manual_follow_up,
        gate_status=_gate_status(policy_status),
        redaction_confirmed=candidate.redaction_confirmed,
        stale_memory_flag=candidate.stale_memory_flag,
        conflicting_memory_flag=candidate.conflicting_memory_flag,
    )


def _policy_status(
    candidate: TeamMemoryPolicyGateCandidate,
    config: TeamMemoryPolicyGateReadinessConfig,
) -> str:
    if not candidate.redaction_confirmed or candidate.conflicting_memory_flag:
        return "block"
    if candidate.memory_context_score >= config.allow_context_floor:
        return "allow"
    if candidate.memory_context_score >= config.throttle_context_floor:
        return "throttle"
    return "block"


def _row_reason_codes(
    candidate: TeamMemoryPolicyGateCandidate,
    policy_status: str,
    config: TeamMemoryPolicyGateReadinessConfig,
) -> tuple[str, ...]:
    reason_codes = list(candidate.reason_codes)
    if not candidate.redaction_confirmed:
        reason_codes.append("memory_context_redaction_not_confirmed")
    if candidate.memory_gap_score >= config.manual_follow_up_floor:
        reason_codes.append("memory_context_gap_follow_up")
    if candidate.stale_memory_flag:
        reason_codes.append("memory_policy_stale_context")
    if candidate.conflicting_memory_flag:
        reason_codes.append("memory_policy_conflicting_context")
    reason_codes.append(f"memory_policy_{policy_status}_context")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _manual_follow_up(
    candidate: TeamMemoryPolicyGateCandidate,
    policy_status: str,
    config: TeamMemoryPolicyGateReadinessConfig,
) -> bool:
    return (
        policy_status != "allow"
        or candidate.memory_gap_score >= config.manual_follow_up_floor
        or candidate.stale_memory_flag
        or candidate.conflicting_memory_flag
        or not candidate.redaction_confirmed
    )


def _gate_status(policy_status: str) -> str:
    if policy_status == "allow":
        return "pass"
    if policy_status == "throttle":
        return "watch"
    if policy_status == "block":
        return "block"
    raise ValueError("policy_status must be a known value")


def _report_gate_status(rows: tuple[TeamMemoryPolicyGateReadinessRow, ...]) -> str:
    if not rows or any(row.policy_status == "block" for row in rows):
        return "block"
    if any(row.policy_status == "throttle" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamMemoryPolicyGateReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_memory_policy_candidates",)
    return tuple(
        reason_code
        for reason_code in (
            "memory_policy_allow_context",
            "memory_policy_block_context",
            "memory_policy_throttle_context",
        )
        if any(reason_code in row.reason_codes for row in rows)
    )


def _reason_code_counts(
    rows: tuple[TeamMemoryPolicyGateReadinessRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[TeamMemoryPolicyGateReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            TeamMemoryPolicyGateReadinessReasonCodeCount(
                reason_code="no_memory_policy_candidates",
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        TeamMemoryPolicyGateReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in report_reason_codes
    )


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[TeamMemoryPolicyGateCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of candidate records")
    normalized: list[TeamMemoryPolicyGateCandidate] = []
    seen_candidate_ids: set[str] = set()
    for item in candidates:
        candidate = _coerce_candidate(item)
        if candidate.candidate_id in seen_candidate_ids:
            raise ValueError("candidate_id values must be unique")
        seen_candidate_ids.add(candidate.candidate_id)
        normalized.append(candidate)
    return tuple(normalized)


def _coerce_candidate(item: object) -> TeamMemoryPolicyGateCandidate:
    if type(item) is TeamMemoryPolicyGateCandidate:
        _require_hard_flags("candidate", item)
        _reject_unsafe_public_payload(item)
        return item
    required_fields = (
        "candidate_id",
        "memory_context_score",
        "memory_gap_score",
        "redaction_confirmed",
        "stale_memory_flag",
        "conflicting_memory_flag",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    if not all(hasattr(item, field_name) for field_name in required_fields):
        raise ValueError("candidate must expose the supported memory policy fields")
    return TeamMemoryPolicyGateCandidate(
        candidate_id=getattr(item, "candidate_id"),
        memory_context_score=getattr(item, "memory_context_score"),
        memory_gap_score=getattr(item, "memory_gap_score"),
        redaction_confirmed=getattr(item, "redaction_confirmed"),
        stale_memory_flag=getattr(item, "stale_memory_flag"),
        conflicting_memory_flag=getattr(item, "conflicting_memory_flag"),
        reason_codes=getattr(item, "reason_codes"),
        paper_only=getattr(item, "paper_only"),
        report_only=getattr(item, "report_only"),
        readonly=getattr(item, "readonly"),
    )


def _normalize_rows(
    rows: tuple[TeamMemoryPolicyGateReadinessRow, ...],
) -> tuple[TeamMemoryPolicyGateReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not TeamMemoryPolicyGateReadinessRow:
            raise ValueError("rows must contain TeamMemoryPolicyGateReadinessRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.candidate_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by candidate_id")
    if len({row.candidate_id for row in rows}) != len(rows):
        raise ValueError("rows must have unique candidate_id values")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[TeamMemoryPolicyGateReadinessReasonCodeCount, ...],
) -> tuple[TeamMemoryPolicyGateReadinessReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not TeamMemoryPolicyGateReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamMemoryPolicyGateReadinessReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: TeamMemoryPolicyGateReadinessRow) -> None:
    if row.gate_status != _gate_status(row.policy_status):
        raise ValueError("gate_status must match policy_status")
    if row.policy_status == "allow" and (
        "memory_policy_allow_context" not in row.reason_codes
        or "memory_policy_throttle_context" in row.reason_codes
        or "memory_policy_block_context" in row.reason_codes
    ):
        raise ValueError("policy_status must match reason_codes")
    if row.policy_status == "throttle" and (
        "memory_policy_throttle_context" not in row.reason_codes
        or "memory_policy_allow_context" in row.reason_codes
        or "memory_policy_block_context" in row.reason_codes
    ):
        raise ValueError("policy_status must match reason_codes")
    if row.policy_status == "block" and (
        "memory_policy_block_context" not in row.reason_codes
        or "memory_policy_allow_context" in row.reason_codes
        or "memory_policy_throttle_context" in row.reason_codes
    ):
        raise ValueError("policy_status must match reason_codes")


def _validate_report_consistency(report: TeamMemoryPolicyGateReadinessReport) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.allow_count != _decimal_count(_policy_count(report.rows, "allow")):
        raise ValueError("allow_count must match rows")
    if report.throttle_count != _decimal_count(_policy_count(report.rows, "throttle")):
        raise ValueError("throttle_count must match rows")
    if report.block_count != _decimal_count(_policy_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.manual_follow_up_count != _decimal_count(
        sum(1 for row in report.rows if row.manual_follow_up),
    ):
        raise ValueError("manual_follow_up_count must match rows")
    if report.gate_status != _report_gate_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _policy_count(rows: tuple[TeamMemoryPolicyGateReadinessRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.policy_status == status)


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value):
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value):
        _reject_unsafe_public_payload(asdict(value))
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text("payload", str(key))
            _reject_unsafe_public_payload(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_text("payload", value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public payload text")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name}.{flag} must be True")
    if is_dataclass(value):
        field_names = {field.name for field in fields(value)}
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in field_names:
                raise ValueError(f"{field_name}.{flag} must be a dataclass field")


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
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized.quantize(RATIO_QUANTUM)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if not all(character.isalnum() or character in "._-" for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    if not value.islower() or any(character == "-" for character in value):
        raise ValueError(f"{field_name} must be snake_case")
    _reject_unsafe_public_text(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    normalized = tuple(sorted(dict.fromkeys(reason_codes)))
    if len(normalized) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _format_decimal(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(value.quantize(Decimal("1")))
    return str(value.quantize(RATIO_QUANTUM))
