"""Supplied-input paper research packet reduction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION",
    "DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS",
    "DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE",
    "PaperResearchPacketConfig",
    "PaperResearchPacketInputRow",
    "PaperResearchPacketRow",
    "PaperResearchPacketReport",
    "build_paper_research_packet",
    "build_paper_research_packet_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
LOW_SCORE = Decimal("0.600000")
HIGH_SCORE = Decimal("0.800000")
MEDIUM_EDGE = Decimal("0.025000")
HIGH_EDGE = Decimal("0.050000")
QUANTUM = Decimal("0.000001")
DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION = "paper-research-packet-v0"
DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS = 25
DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE = Decimal("0.600000")

ACTIONS = ("recommend", "watch", "reject")
QUEUE_STATUSES = ("ready", "watch", "blocked")
RESEARCH_PRIORITIES = ("high", "medium", "low", "skip")
SIDES = ("yes", "no", "none")
REQUIRED_CHECKS = (
    "outcome_definition",
    "liquidity_depth",
    "cost_sensitivity",
    "settlement_timing",
)
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2, "skip": 3}
NO_REASON_CODE = "no_reason_code"


@dataclass(frozen=True)
class PaperResearchPacketConfig:
    config_version: str = DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION
    max_packet_rows: int = DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS
    min_score: Decimal = DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("max_packet_rows", self.max_packet_rows)
        object.__setattr__(
            self,
            "min_score",
            _quantize_score("min_score", self.min_score),
        )
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperResearchPacketInputRow:
    market_slug: str
    question: str
    side: str
    action: str
    queue_status: str
    recommendation_score: Decimal
    net_edge: Decimal
    allocated_notional: Decimal | None = None
    requested_notional: Decimal | None = None
    reason_codes: tuple[str, ...] = (NO_REASON_CODE,)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("side", self.side)
        _require_action("action", self.action)
        _require_queue_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "recommendation_score",
            _quantize_score("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(self, "net_edge", _quantize_decimal("net_edge", self.net_edge))
        object.__setattr__(
            self,
            "allocated_notional",
            _quantize_optional_notional(
                "allocated_notional",
                self.allocated_notional,
            ),
        )
        object.__setattr__(
            self,
            "requested_notional",
            _quantize_optional_notional(
                "requested_notional",
                self.requested_notional,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_input_row_consistency(self)
        _validate_hard_flags("input row", self)


@dataclass(frozen=True)
class PaperResearchPacketRow:
    packet_rank: int
    market_slug: str
    question: str
    side: str
    research_priority: str
    required_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    recommendation_score: Decimal
    net_edge: Decimal
    allocated_notional: Decimal | None = None
    requested_notional: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("packet_rank", self.packet_rank)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("side", self.side)
        _require_research_priority("research_priority", self.research_priority)
        object.__setattr__(
            self,
            "required_checks",
            _normalize_required_checks(self.required_checks),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "recommendation_score",
            _quantize_score("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(self, "net_edge", _quantize_decimal("net_edge", self.net_edge))
        object.__setattr__(
            self,
            "allocated_notional",
            _quantize_optional_notional(
                "allocated_notional",
                self.allocated_notional,
            ),
        )
        object.__setattr__(
            self,
            "requested_notional",
            _quantize_optional_notional(
                "requested_notional",
                self.requested_notional,
            ),
        )
        _validate_packet_row_consistency(self)
        _validate_hard_flags("packet row", self)


@dataclass(frozen=True)
class PaperResearchPacketReport:
    generated_at: datetime
    config_version: str
    input_row_count: int
    packet_row_count: int
    included_count: int
    skipped_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    packet_rows: tuple[PaperResearchPacketRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_row_count",
            "packet_row_count",
            "included_count",
            "skipped_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "packet_rows",
            _normalize_packet_rows(self.packet_rows),
        )
        _validate_report_consistency(self)
        _validate_hard_flags("packet report", self)


def build_paper_research_packet_report(
    rows: Iterable[PaperResearchPacketInputRow],
    *,
    config: PaperResearchPacketConfig,
    generated_at: datetime,
) -> PaperResearchPacketReport:
    """Build a readonly analyst packet from already-supplied recommendation rows."""

    if type(config) is not PaperResearchPacketConfig:
        raise ValueError("config must be a PaperResearchPacketConfig")
    _validate_hard_flags("config", config)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    input_rows = _normalize_input_rows(rows)
    candidates = _packet_candidates(input_rows, config=config)
    packet_rows = tuple(
        PaperResearchPacketRow(
            packet_rank=index,
            market_slug=row.market_slug,
            question=row.question,
            side=row.side,
            research_priority=priority,
            required_checks=_required_checks(row, priority),
            reason_codes=row.reason_codes,
            recommendation_score=row.recommendation_score,
            net_edge=row.net_edge,
            allocated_notional=row.allocated_notional,
            requested_notional=row.requested_notional,
        )
        for index, (priority, row) in enumerate(
            candidates[: config.max_packet_rows],
            start=1,
        )
    )

    return PaperResearchPacketReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_row_count=len(input_rows),
        packet_row_count=len(packet_rows),
        included_count=_packet_priority_count(packet_rows, "high")
        + _packet_priority_count(packet_rows, "medium")
        + _packet_priority_count(packet_rows, "low"),
        skipped_count=_packet_priority_count(packet_rows, "skip"),
        high_priority_count=_packet_priority_count(packet_rows, "high"),
        medium_priority_count=_packet_priority_count(packet_rows, "medium"),
        low_priority_count=_packet_priority_count(packet_rows, "low"),
        packet_rows=packet_rows,
    )


def build_paper_research_packet(
    rows: Iterable[PaperResearchPacketInputRow],
    *,
    config: PaperResearchPacketConfig,
    generated_at: datetime,
) -> PaperResearchPacketReport:
    """Alias for callers that name the reducer by the packet artifact."""

    return build_paper_research_packet_report(
        rows,
        config=config,
        generated_at=generated_at,
    )


def _packet_candidates(
    rows: tuple[PaperResearchPacketInputRow, ...],
    *,
    config: PaperResearchPacketConfig,
) -> tuple[tuple[str, PaperResearchPacketInputRow], ...]:
    candidates: list[tuple[str, PaperResearchPacketInputRow]] = []
    for row in rows:
        priority = _research_priority(row, min_score=config.min_score)
        if priority != "skip" or _hard_skip(row):
            candidates.append((priority, row))
    return tuple(sorted(candidates, key=_candidate_sort_key))


def _candidate_sort_key(
    candidate: tuple[str, PaperResearchPacketInputRow],
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str, str, str]:
    priority, row = candidate
    return (
        PRIORITY_RANK[priority],
        -row.recommendation_score,
        -row.net_edge,
        -_notional_or_zero(row.allocated_notional),
        -_notional_or_zero(row.requested_notional),
        row.market_slug,
        row.question,
        row.side,
    )


def _research_priority(
    row: PaperResearchPacketInputRow,
    *,
    min_score: Decimal,
) -> str:
    if _hard_skip(row):
        return "skip"
    if row.recommendation_score < min_score:
        return "skip"
    if row.recommendation_score >= HIGH_SCORE or row.net_edge >= HIGH_EDGE:
        return "high"
    if row.recommendation_score >= LOW_SCORE or row.net_edge >= MEDIUM_EDGE:
        return "medium"
    return "low"


def _hard_skip(row: PaperResearchPacketInputRow) -> bool:
    return row.queue_status == "blocked" or row.action == "reject" or row.side == "none"


def _required_checks(
    row: PaperResearchPacketInputRow,
    priority: str,
) -> tuple[str, ...]:
    checks: list[str] = ["outcome_definition"]
    if priority == "skip":
        return tuple(checks)
    if priority in ("high", "medium") or _reason_mentions(
        row.reason_codes,
        ("liquidity", "depth", "thin_book"),
    ):
        checks.append("liquidity_depth")
    checks.append("cost_sensitivity")
    if priority == "high" or _reason_mentions(
        row.reason_codes,
        ("settlement", "timing", "resolution"),
    ):
        checks.append("settlement_timing")
    return tuple(checks)


def _reason_mentions(reason_codes: tuple[str, ...], needles: tuple[str, ...]) -> bool:
    return any(any(needle in reason_code for needle in needles) for reason_code in reason_codes)


def _normalize_input_rows(
    value: Iterable[PaperResearchPacketInputRow],
) -> tuple[PaperResearchPacketInputRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperResearchPacketInputRow:
            raise ValueError("rows must contain PaperResearchPacketInputRow values")
        _validate_hard_flags("input rows", row)
    return rows


def _normalize_packet_rows(
    value: Iterable[PaperResearchPacketRow],
) -> tuple[PaperResearchPacketRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("packet_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("packet_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperResearchPacketRow:
            raise ValueError("packet_rows must contain PaperResearchPacketRow values")
        _validate_hard_flags("packet rows", row)
    return rows


def _validate_report_consistency(report: PaperResearchPacketReport) -> None:
    if report.packet_row_count != len(report.packet_rows):
        raise ValueError("packet_row_count must match packet_rows")
    if report.input_row_count < report.packet_row_count:
        raise ValueError("input_row_count must cover packet_rows")
    if report.included_count != (
        _packet_priority_count(report.packet_rows, "high")
        + _packet_priority_count(report.packet_rows, "medium")
        + _packet_priority_count(report.packet_rows, "low")
    ):
        raise ValueError("included_count must match packet_rows")
    if report.skipped_count != _packet_priority_count(report.packet_rows, "skip"):
        raise ValueError("skipped_count must match packet_rows")
    if report.high_priority_count != _packet_priority_count(report.packet_rows, "high"):
        raise ValueError("high_priority_count must match packet_rows")
    if report.medium_priority_count != _packet_priority_count(report.packet_rows, "medium"):
        raise ValueError("medium_priority_count must match packet_rows")
    if report.low_priority_count != _packet_priority_count(report.packet_rows, "low"):
        raise ValueError("low_priority_count must match packet_rows")
    if report.included_count + report.skipped_count != report.packet_row_count:
        raise ValueError("packet priority counts must match packet_row_count")
    if tuple(row.packet_rank for row in report.packet_rows) != tuple(
        range(1, len(report.packet_rows) + 1),
    ):
        raise ValueError("packet_rank values must be contiguous")
    if report.packet_rows != _order_packet_rows(report.packet_rows):
        raise ValueError("packet_rows must use deterministic ordering")


def _validate_input_row_consistency(row: PaperResearchPacketInputRow) -> None:
    if row.action == "reject" and row.queue_status != "blocked":
        raise ValueError("reject input rows must be blocked")
    if row.queue_status == "blocked" and row.action != "reject":
        raise ValueError("blocked input rows must be reject rows")
    if row.queue_status == "ready" and row.side == "none":
        raise ValueError("ready input rows must include a yes or no side")


def _order_packet_rows(
    rows: tuple[PaperResearchPacketRow, ...],
) -> tuple[PaperResearchPacketRow, ...]:
    return tuple(sorted(rows, key=_packet_row_sort_key))


def _packet_row_sort_key(
    row: PaperResearchPacketRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str, str, str, int]:
    return (
        PRIORITY_RANK[row.research_priority],
        -row.recommendation_score,
        -row.net_edge,
        -_notional_or_zero(row.allocated_notional),
        -_notional_or_zero(row.requested_notional),
        row.market_slug,
        row.question,
        row.side,
        row.packet_rank,
    )


def _validate_packet_row_consistency(row: PaperResearchPacketRow) -> None:
    if row.research_priority == "skip":
        if row.required_checks != ("outcome_definition",):
            raise ValueError("skip packet rows require only outcome_definition")
        return
    if row.side == "none":
        raise ValueError("included packet rows must include a yes or no side")
    if "outcome_definition" not in row.required_checks:
        raise ValueError("required_checks must include outcome_definition")
    if "cost_sensitivity" not in row.required_checks:
        raise ValueError("included packet rows must include cost_sensitivity")


def _packet_priority_count(
    rows: Iterable[PaperResearchPacketRow],
    priority: str,
) -> int:
    return sum(1 for row in rows if row.research_priority == priority)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _normalize_required_checks(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("required_checks must be an iterable")
    try:
        checks = tuple(value)
    except TypeError as exc:
        raise ValueError("required_checks must be an iterable") from exc
    if not checks:
        raise ValueError("required_checks must not be empty")
    seen: set[str] = set()
    for check in checks:
        if type(check) is not str or check not in REQUIRED_CHECKS:
            raise ValueError("required_checks must contain known research checks")
        if check in seen:
            raise ValueError("required_checks must be unique")
        seen.add(check)
    expected = tuple(check for check in REQUIRED_CHECKS if check in set(checks))
    if checks != expected:
        raise ValueError("required_checks must use deterministic ordering")
    return checks


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_optional_notional(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _quantize_nonnegative_decimal(field_name, value)


def _quantize_score(field_name: str, value: object) -> Decimal:
    score = _quantize_nonnegative_decimal(field_name, value)
    if score > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return score


def _notional_or_zero(value: Decimal | None) -> Decimal:
    return ZERO if value is None else value


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_queue_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_research_priority(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_PRIORITIES:
        raise ValueError(f"{field_name} must be high, medium, low, or skip")


def _validate_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
