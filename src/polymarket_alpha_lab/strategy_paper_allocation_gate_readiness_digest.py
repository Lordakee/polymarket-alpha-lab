"""Pure paper allocation gate readiness reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_STRATEGY_PAPER_ALLOCATION_GATE_READINESS_DIGEST_CONFIG_VERSION = (
    "strategy-paper-allocation-gate-readiness-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
SIX = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64)

RECOMMENDATION_GATE_STATUSES = ("pass", "watch", "blocked")
PORTFOLIO_CORRELATION_STATUSES = ("pass", "watch", "blocked")
CATEGORY_ROTATION_STATUSES = ("hold", "watch", "rotate_out")
ALLOCATION_READINESS_STATUSES = ("blocked", "watch", "ready")

EMPTY_REASON_CODE = "strategy_paper_allocation_gate_readiness_digest_empty"
REPORT_REASON_PRIORITY = (
    "allocation_gate_blocked",
    "allocation_gate_watch",
    "allocation_gate_ready",
    "recommendation_gate_blocked",
    "recommendation_gate_watch",
    "recommendation_gate_passed",
    "portfolio_correlation_blocked",
    "portfolio_correlation_watch",
    "portfolio_correlation_passed",
    "category_rotation_rotate_out",
    "category_rotation_watch",
    "category_rotation_hold",
    "team_memory_weight_blocked",
    "team_memory_weight_watch",
    "team_memory_weight_ready",
    "expected_value_buffer_blocked",
    "expected_value_buffer_watch",
    "expected_value_buffer_ready",
    "paper_budget_blocked",
    "paper_budget_watch",
    "paper_budget_ready",
    "candidate_input",
    EMPTY_REASON_CODE,
)
SENSITIVE_PUBLIC_TEXT = (
    "secret",
    "token",
    "wal" "let",
    "private",
    "password",
    "bearer",
    "au" "th",
    "or" "der",
    "can" "cel",
    "sign" "ing",
)


@dataclass(frozen=True)
class StrategyPaperAllocationGateReadinessDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_PAPER_ALLOCATION_GATE_READINESS_DIGEST_CONFIG_VERSION
    )
    max_ready_allocation_fraction: Decimal = Decimal("0.050000")
    max_watch_allocation_fraction: Decimal = Decimal("0.020000")
    min_ready_team_memory_weight: Decimal = Decimal("0.700000")
    min_watch_team_memory_weight: Decimal = Decimal("0.500000")
    min_ready_expected_value_buffer: Decimal = Decimal("0.030000")
    min_watch_expected_value_buffer: Decimal = Decimal("0.010000")
    min_ready_available_paper_budget: Decimal = Decimal("100.000000")
    min_watch_available_paper_budget: Decimal = Decimal("25.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_ready_allocation_fraction",
            "max_watch_allocation_fraction",
            "min_ready_team_memory_weight",
            "min_watch_team_memory_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_expected_value_buffer",
            "min_watch_expected_value_buffer",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_available_paper_budget",
            "min_watch_available_paper_budget",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyPaperAllocationGateReadinessCandidate:
    candidate_reference: str
    market_slug: str
    category: str
    evaluated_at: datetime
    recommendation_gate_status: str
    portfolio_correlation_status: str
    category_rotation_status: str
    team_memory_weight: Decimal
    expected_value_buffer: Decimal
    available_paper_budget: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        _require_member(
            "recommendation_gate_status",
            self.recommendation_gate_status,
            RECOMMENDATION_GATE_STATUSES,
        )
        _require_member(
            "portfolio_correlation_status",
            self.portfolio_correlation_status,
            PORTFOLIO_CORRELATION_STATUSES,
        )
        _require_member(
            "category_rotation_status",
            self.category_rotation_status,
            CATEGORY_ROTATION_STATUSES,
        )
        object.__setattr__(
            self,
            "team_memory_weight",
            _normalize_ratio("team_memory_weight", self.team_memory_weight),
        )
        object.__setattr__(
            self,
            "expected_value_buffer",
            _normalize_decimal("expected_value_buffer", self.expected_value_buffer),
        )
        object.__setattr__(
            self,
            "available_paper_budget",
            _normalize_nonnegative_decimal(
                "available_paper_budget",
                self.available_paper_budget,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyPaperAllocationGateReadinessRow:
    redacted_candidate_reference: str
    market_slug: str
    category: str
    evaluated_at: datetime
    recommendation_gate_status: str
    portfolio_correlation_status: str
    category_rotation_status: str
    team_memory_weight: Decimal
    expected_value_buffer: Decimal
    available_paper_budget: Decimal
    readiness_score: Decimal
    suggested_paper_allocation_fraction: Decimal
    allocation_readiness_status: str
    reason_codes: tuple[str, ...]
    _allocation_fraction_ceiling: Decimal = field(default=ZERO, repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference(self.redacted_candidate_reference)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        _require_member(
            "recommendation_gate_status",
            self.recommendation_gate_status,
            RECOMMENDATION_GATE_STATUSES,
        )
        _require_member(
            "portfolio_correlation_status",
            self.portfolio_correlation_status,
            PORTFOLIO_CORRELATION_STATUSES,
        )
        _require_member(
            "category_rotation_status",
            self.category_rotation_status,
            CATEGORY_ROTATION_STATUSES,
        )
        object.__setattr__(
            self,
            "team_memory_weight",
            _normalize_ratio("team_memory_weight", self.team_memory_weight),
        )
        object.__setattr__(
            self,
            "expected_value_buffer",
            _normalize_decimal("expected_value_buffer", self.expected_value_buffer),
        )
        object.__setattr__(
            self,
            "available_paper_budget",
            _normalize_nonnegative_decimal(
                "available_paper_budget",
                self.available_paper_budget,
            ),
        )
        object.__setattr__(
            self,
            "readiness_score",
            _normalize_ratio("readiness_score", self.readiness_score),
        )
        object.__setattr__(
            self,
            "suggested_paper_allocation_fraction",
            _normalize_ratio(
                "suggested_paper_allocation_fraction",
                self.suggested_paper_allocation_fraction,
            ),
        )
        object.__setattr__(
            self,
            "_allocation_fraction_ceiling",
            _normalize_ratio(
                "_allocation_fraction_ceiling",
                self._allocation_fraction_ceiling,
            ),
        )
        _require_member(
            "allocation_readiness_status",
            self.allocation_readiness_status,
            ALLOCATION_READINESS_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyPaperAllocationGateReadinessDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_available_paper_budget: Decimal
    max_suggested_paper_allocation_fraction: Decimal
    min_team_memory_weight: Decimal
    min_expected_value_buffer: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyPaperAllocationGateReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_available_paper_budget",
            "max_suggested_paper_allocation_fraction",
            "min_team_memory_weight",
            "min_expected_value_buffer",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ALLOCATION_READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_strategy_paper_allocation_gate_readiness_digest(
    candidates: Iterable[object],
    *,
    config: StrategyPaperAllocationGateReadinessDigestConfig,
    generated_at: datetime,
) -> StrategyPaperAllocationGateReadinessDigestReport:
    if type(config) is not StrategyPaperAllocationGateReadinessDigestConfig:
        raise ValueError(
            "config must be a StrategyPaperAllocationGateReadinessDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at,
                )
                for candidate in source_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyPaperAllocationGateReadinessDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_available_paper_budget=_sum_decimal(
            row.available_paper_budget for row in rows
        ),
        max_suggested_paper_allocation_fraction=_max_row_decimal(
            rows,
            "suggested_paper_allocation_fraction",
        ),
        min_team_memory_weight=_min_row_decimal(rows, "team_memory_weight"),
        min_expected_value_buffer=_min_row_decimal(rows, "expected_value_buffer"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_paper_allocation_gate_readiness_digest_payload(
    report: StrategyPaperAllocationGateReadinessDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyPaperAllocationGateReadinessDigestReport:
        raise ValueError(
            "report must be a StrategyPaperAllocationGateReadinessDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dictionary")
    return payload


def _row_from_candidate(
    candidate: StrategyPaperAllocationGateReadinessCandidate,
    *,
    config: StrategyPaperAllocationGateReadinessDigestConfig,
    generated_at: datetime,
) -> StrategyPaperAllocationGateReadinessRow:
    if candidate.evaluated_at > generated_at:
        raise ValueError("evaluated_at must not be after generated_at")
    status = _allocation_status(candidate, config)
    return StrategyPaperAllocationGateReadinessRow(
        redacted_candidate_reference=_redacted_reference(candidate.candidate_reference),
        market_slug=candidate.market_slug,
        category=candidate.category,
        evaluated_at=candidate.evaluated_at,
        recommendation_gate_status=candidate.recommendation_gate_status,
        portfolio_correlation_status=candidate.portfolio_correlation_status,
        category_rotation_status=candidate.category_rotation_status,
        team_memory_weight=candidate.team_memory_weight,
        expected_value_buffer=candidate.expected_value_buffer,
        available_paper_budget=candidate.available_paper_budget,
        readiness_score=_readiness_score(candidate, config),
        suggested_paper_allocation_fraction=_suggested_fraction(
            status,
            candidate.team_memory_weight,
            config,
        ),
        allocation_readiness_status=status,
        reason_codes=_row_reason_codes(candidate, config, status),
        _allocation_fraction_ceiling=_fraction_ceiling(status, config),
    )


def _allocation_status(
    candidate: StrategyPaperAllocationGateReadinessCandidate,
    config: StrategyPaperAllocationGateReadinessDigestConfig,
) -> str:
    states = (
        _status_gate_state(candidate.recommendation_gate_status),
        _status_gate_state(candidate.portfolio_correlation_status),
        _category_gate_state(candidate.category_rotation_status),
        _threshold_state(
            candidate.team_memory_weight,
            ready=config.min_ready_team_memory_weight,
            watch=config.min_watch_team_memory_weight,
        ),
        _threshold_state(
            candidate.expected_value_buffer,
            ready=config.min_ready_expected_value_buffer,
            watch=config.min_watch_expected_value_buffer,
        ),
        _threshold_state(
            candidate.available_paper_budget,
            ready=config.min_ready_available_paper_budget,
            watch=config.min_watch_available_paper_budget,
        ),
    )
    if "blocked" in states:
        return "blocked"
    if "watch" in states:
        return "watch"
    return "ready"


def _row_reason_codes(
    candidate: StrategyPaperAllocationGateReadinessCandidate,
    config: StrategyPaperAllocationGateReadinessDigestConfig,
    status: str,
) -> tuple[str, ...]:
    reason_codes = [
        *candidate.reason_codes,
        f"allocation_gate_{status}",
        _recommendation_reason_code(candidate.recommendation_gate_status),
        _portfolio_reason_code(candidate.portfolio_correlation_status),
        _category_reason_code(candidate.category_rotation_status),
        _threshold_reason_code(
            "team_memory_weight",
            candidate.team_memory_weight,
            ready=config.min_ready_team_memory_weight,
            watch=config.min_watch_team_memory_weight,
        ),
        _threshold_reason_code(
            "expected_value_buffer",
            candidate.expected_value_buffer,
            ready=config.min_ready_expected_value_buffer,
            watch=config.min_watch_expected_value_buffer,
        ),
        _threshold_reason_code(
            "paper_budget",
            candidate.available_paper_budget,
            ready=config.min_ready_available_paper_budget,
            watch=config.min_watch_available_paper_budget,
        ),
    ]
    return _unique_reason_codes(tuple(reason_codes))


def _recommendation_reason_code(status: str) -> str:
    if status == "pass":
        return "recommendation_gate_passed"
    return f"recommendation_gate_{status}"


def _portfolio_reason_code(status: str) -> str:
    if status == "pass":
        return "portfolio_correlation_passed"
    return f"portfolio_correlation_{status}"


def _category_reason_code(status: str) -> str:
    return f"category_rotation_{status}"


def _threshold_reason_code(
    prefix: str,
    value: Decimal,
    *,
    ready: Decimal,
    watch: Decimal,
) -> str:
    return f"{prefix}_{_threshold_state(value, ready=ready, watch=watch)}"


def _threshold_state(
    value: Decimal,
    *,
    ready: Decimal,
    watch: Decimal,
) -> str:
    if value >= ready:
        return "ready"
    if value >= watch:
        return "watch"
    return "blocked"


def _status_gate_state(status: str) -> str:
    if status == "pass":
        return "ready"
    return status


def _category_gate_state(status: str) -> str:
    if status == "hold":
        return "ready"
    if status == "watch":
        return "watch"
    return "blocked"


def _suggested_fraction(
    status: str,
    team_memory_weight: Decimal,
    config: StrategyPaperAllocationGateReadinessDigestConfig,
) -> Decimal:
    return _multiply_decimal(_fraction_ceiling(status, config), team_memory_weight)


def _fraction_ceiling(
    status: str,
    config: StrategyPaperAllocationGateReadinessDigestConfig,
) -> Decimal:
    if status == "blocked":
        return ZERO
    if status == "watch":
        return config.max_watch_allocation_fraction
    return config.max_ready_allocation_fraction


def _readiness_score(
    candidate: StrategyPaperAllocationGateReadinessCandidate,
    config: StrategyPaperAllocationGateReadinessDigestConfig,
) -> Decimal:
    return _divide_decimal(
        _add_decimal(
            _gate_score(candidate.recommendation_gate_status, pass_status="pass"),
            _gate_score(candidate.portfolio_correlation_status, pass_status="pass"),
            _gate_score(candidate.category_rotation_status, pass_status="hold"),
            candidate.team_memory_weight,
            _capped_ratio(
                candidate.expected_value_buffer,
                config.min_ready_expected_value_buffer,
            ),
            _capped_ratio(
                candidate.available_paper_budget,
                config.min_ready_available_paper_budget,
            ),
        ),
        SIX,
    )


def _gate_score(status: str, *, pass_status: str) -> Decimal:
    if status == pass_status:
        return ONE
    if status == "watch":
        return HALF
    return ZERO


def _capped_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    if value <= ZERO:
        return ZERO
    ratio = _divide_decimal(value, denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyPaperAllocationGateReadinessCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[StrategyPaperAllocationGateReadinessCandidate] = []
    for row in rows:
        if type(row) is not StrategyPaperAllocationGateReadinessCandidate:
            raise ValueError(
                "candidates must contain StrategyPaperAllocationGateReadinessCandidate",
            )
        _require_hard_flags("candidate", row)
        if row.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(row.candidate_reference)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(value: object) -> tuple[StrategyPaperAllocationGateReadinessRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyPaperAllocationGateReadinessRow:
            raise ValueError("rows must contain StrategyPaperAllocationGateReadinessRow")
        _require_hard_flags("row", row)
    return rows


def _row_sort_key(row: StrategyPaperAllocationGateReadinessRow) -> tuple[str, str]:
    return (row.market_slug, row.redacted_candidate_reference)


def _status_count(
    rows: tuple[StrategyPaperAllocationGateReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.allocation_readiness_status == status),
    )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _add_decimal(*tuple(values))


def _max_row_decimal(
    rows: tuple[StrategyPaperAllocationGateReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[StrategyPaperAllocationGateReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _report_status(rows: tuple[StrategyPaperAllocationGateReadinessRow, ...]) -> str:
    if any(row.allocation_readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.allocation_readiness_status == "watch" for row in rows) or not rows:
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[StrategyPaperAllocationGateReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    prioritized = tuple(code for code in REPORT_REASON_PRIORITY if code in observed)
    extras = tuple(sorted(code for code in observed if code not in prioritized))
    return (*prioritized, *extras)


def _validate_config(config: StrategyPaperAllocationGateReadinessDigestConfig) -> None:
    if config.max_watch_allocation_fraction > config.max_ready_allocation_fraction:
        raise ValueError(
            "max_watch_allocation_fraction must not exceed "
            "max_ready_allocation_fraction",
        )
    if config.min_watch_team_memory_weight > config.min_ready_team_memory_weight:
        raise ValueError(
            "min_watch_team_memory_weight must not exceed min_ready_team_memory_weight",
        )
    if config.min_watch_expected_value_buffer > config.min_ready_expected_value_buffer:
        raise ValueError(
            "min_watch_expected_value_buffer must not exceed "
            "min_ready_expected_value_buffer",
        )
    if config.min_watch_available_paper_budget > config.min_ready_available_paper_budget:
        raise ValueError(
            "min_watch_available_paper_budget must not exceed "
            "min_ready_available_paper_budget",
        )
    if config.min_ready_expected_value_buffer <= ZERO:
        raise ValueError("min_ready_expected_value_buffer must be positive")
    if config.min_ready_available_paper_budget <= ZERO:
        raise ValueError("min_ready_available_paper_budget must be positive")


def _validate_row(row: StrategyPaperAllocationGateReadinessRow) -> None:
    expected_status = _row_status_from_reason_codes(row.reason_codes)
    if row.allocation_readiness_status != expected_status:
        raise ValueError("allocation_readiness_status must match reason_codes")
    expected_fraction = _row_fraction_from_reason_codes(row)
    if row.suggested_paper_allocation_fraction != expected_fraction:
        raise ValueError(
            "suggested_paper_allocation_fraction must match allocation status",
        )
    if not ZERO <= row.readiness_score <= ONE:
        raise ValueError("readiness_score must be between 0 and 1")


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "allocation_gate_blocked" in reason_codes:
        return "blocked"
    if "allocation_gate_watch" in reason_codes:
        return "watch"
    if "allocation_gate_ready" in reason_codes:
        return "ready"
    raise ValueError("reason_codes must include allocation gate status")


def _row_fraction_from_reason_codes(
    row: StrategyPaperAllocationGateReadinessRow,
) -> Decimal:
    if row.allocation_readiness_status == "blocked":
        return ZERO
    return _multiply_decimal(row._allocation_fraction_ceiling, row.team_memory_weight)


def _validate_report(report: StrategyPaperAllocationGateReadinessDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    total_budget = _sum_decimal(row.available_paper_budget for row in report.rows)
    if report.total_available_paper_budget != total_budget:
        raise ValueError("total_available_paper_budget must match rows")
    max_fraction = _max_row_decimal(report.rows, "suggested_paper_allocation_fraction")
    if report.max_suggested_paper_allocation_fraction != max_fraction:
        raise ValueError("max_suggested_paper_allocation_fraction must match rows")
    if report.min_team_memory_weight != _min_row_decimal(report.rows, "team_memory_weight"):
        raise ValueError("min_team_memory_weight must match rows")
    if report.min_expected_value_buffer != _min_row_decimal(
        report.rows,
        "expected_value_buffer",
    ):
        raise ValueError("min_expected_value_buffer must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in values:
        raise ValueError(f"{field_name} must be one of {values}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_redacted_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("redacted_candidate_reference must be a string")
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 16
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError("redacted_candidate_reference must be a redacted candidate reference")


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _unique_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return _normalize_reason_codes(tuple(unique), require_nonempty=True)


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left / right).quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(type(value).__name__, value)
        return _payload_mapping(vars(value))
    if type(value) is dict:
        return _payload_mapping(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not serializable")


def _payload_mapping(value: dict[Any, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
        if key.startswith("_"):
            continue
        _reject_unsafe_public_text(key)
        payload[key] = _payload_value(item)
    return payload


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_PUBLIC_TEXT):
        raise ValueError("unsafe public text")


__all__ = (
    "DEFAULT_STRATEGY_PAPER_ALLOCATION_GATE_READINESS_DIGEST_CONFIG_VERSION",
    "StrategyPaperAllocationGateReadinessCandidate",
    "StrategyPaperAllocationGateReadinessDigestConfig",
    "StrategyPaperAllocationGateReadinessDigestReport",
    "StrategyPaperAllocationGateReadinessRow",
    "build_strategy_paper_allocation_gate_readiness_digest",
    "strategy_paper_allocation_gate_readiness_digest_payload",
)
