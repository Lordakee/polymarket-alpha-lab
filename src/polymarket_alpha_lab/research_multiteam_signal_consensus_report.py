"""Pure in-memory multiteam signal consensus research report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_MULTITEAM_SIGNAL_CONSENSUS_CONFIG_VERSION = (
    "research-multiteam-signal-consensus-v0"
)

SIGNAL_DIRECTIONS = ("supports_yes", "supports_no", "neutral")
ALIGNMENT_STATUSES = ("aligned", "conflict", "review")
REPORT_STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "team_signal_aligned",
    "team_signal_conflict",
    "team_signal_neutral",
    "team_review_requested",
)
REPORT_REASON_CODES = (
    "signal_consensus_pass",
    "signal_consensus_watch",
    "insufficient_team_coverage",
    "cross_team_conflict_block",
    "cross_team_conflict_watch",
    "consensus_ratio_watch",
    "neutral_team_signal_present",
    "team_review_requested",
    "average_confidence_watch",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ALIGNMENT_RANK = {"conflict": 0, "review": 1, "aligned": 2}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("can", "didate_id"),
        _join_parts("mar", "ket_id"),
        _join_parts("mar", "ket_slug"),
        _join_parts("slug"),
        _join_parts("que", "stion"),
        _join_parts("sou", "rce_url"),
        _join_parts("sou", "rce_text"),
        _join_parts("http", "://"),
        _join_parts("https", "://"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("po", "sition"),
        _join_parts("reco", "mmend"),
    ),
)


@dataclass(frozen=True)
class ResearchMultiteamSignalConsensusConfig:
    config_version: str = DEFAULT_RESEARCH_MULTITEAM_SIGNAL_CONSENSUS_CONFIG_VERSION
    min_team_count: Decimal = Decimal("3")
    pass_min_consensus_ratio: Decimal = Decimal("0.700000")
    review_conflict_strength: Decimal = Decimal("0.250000")
    block_conflict_strength: Decimal = Decimal("0.600000")
    min_average_confidence_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_team_count",
            _require_positive_count_decimal("min_team_count", self.min_team_count),
        )
        for field_name in (
            "pass_min_consensus_ratio",
            "review_conflict_strength",
            "block_conflict_strength",
            "min_average_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.review_conflict_strength > self.block_conflict_strength:
            raise ValueError(
                "review_conflict_strength must be <= block_conflict_strength",
            )
        require_paper_only_flags("multiteam signal consensus config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchMultiteamSignal:
    team_id: str
    category_id: str
    observed_at: datetime
    signal_direction: str
    signal_strength: Decimal
    confidence_score: Decimal
    review_required: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_signal_direction("signal_direction", self.signal_direction)
        for field_name in ("signal_strength", "confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_bool("review_required", self.review_required)
        require_paper_only_flags("multiteam signal", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchMultiteamSignalConsensusTeamRow:
    team_id: str
    category_id: str
    observed_at: datetime
    signal_direction: str
    alignment_status: str
    signal_strength: Decimal
    confidence_score: Decimal
    signal_weight: Decimal
    review_required: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_signal_direction("signal_direction", self.signal_direction)
        _require_alignment_status("alignment_status", self.alignment_status)
        for field_name in ("signal_strength", "confidence_score", "signal_weight"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_bool("review_required", self.review_required)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("multiteam signal consensus row", self)
        _reject_unsafe_public_payload(self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMultiteamSignalConsensusReport:
    generated_at: datetime
    config_version: str
    status: str
    team_count: Decimal
    category_count: Decimal
    aligned_team_count: Decimal
    conflicting_team_count: Decimal
    review_required_count: Decimal
    dominant_signal_direction: str | None
    consensus_ratio: Decimal
    conflict_strength: Decimal
    review_need_score: Decimal
    average_confidence_score: Decimal | None
    rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_report_status("status", self.status)
        for field_name in (
            "team_count",
            "category_count",
            "aligned_team_count",
            "conflicting_team_count",
            "review_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.dominant_signal_direction is not None:
            _require_directional_signal(
                "dominant_signal_direction",
                self.dominant_signal_direction,
            )
        for field_name in ("consensus_ratio", "conflict_strength", "review_need_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_confidence_score",
            _require_optional_ratio(
                "average_confidence_score",
                self.average_confidence_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("multiteam signal consensus report", self)
        _reject_unsafe_public_payload(self)
        _validate_report(self)


def build_research_multiteam_signal_consensus_report(
    signals: Iterable[ResearchMultiteamSignal | ResearchMultiteamSignalConsensusTeamRow],
    *,
    config: ResearchMultiteamSignalConsensusConfig,
    generated_at: datetime,
) -> ResearchMultiteamSignalConsensusReport:
    if type(config) is not ResearchMultiteamSignalConsensusConfig:
        raise ValueError("config must be a ResearchMultiteamSignalConsensusConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_signal_inputs(signals)
    _validate_signal_times(normalized, generated_at_utc)

    dominant_signal_direction = _dominant_signal_direction(normalized)
    rows = _sort_rows(
        tuple(
            _team_row(signal, dominant_signal_direction=dominant_signal_direction)
            for signal in normalized
        ),
    )
    reason_codes = _report_reason_codes(rows, config=config)

    return ResearchMultiteamSignalConsensusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(reason_codes),
        team_count=_count(len(rows)),
        category_count=_count(len({row.category_id for row in rows})),
        aligned_team_count=_count(
            sum(1 for row in rows if row.alignment_status == "aligned"),
        ),
        conflicting_team_count=_count(
            sum(1 for row in rows if row.alignment_status == "conflict"),
        ),
        review_required_count=_count(sum(1 for row in rows if row.review_required)),
        dominant_signal_direction=dominant_signal_direction,
        consensus_ratio=_consensus_ratio(rows, dominant_signal_direction),
        conflict_strength=_conflict_strength(rows),
        review_need_score=_review_need_score(rows, config=config),
        average_confidence_score=_average_confidence_score(rows),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_multiteam_signal_consensus_report_to_payload(
    report: ResearchMultiteamSignalConsensusReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMultiteamSignalConsensusReport:
        raise ValueError("report must be a ResearchMultiteamSignalConsensusReport")
    require_paper_only_flags("report", report)
    _reject_unsafe_public_payload(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _team_row(
    signal: ResearchMultiteamSignal,
    *,
    dominant_signal_direction: str | None,
) -> ResearchMultiteamSignalConsensusTeamRow:
    alignment_status = _alignment_status(
        signal.signal_direction,
        dominant_signal_direction=dominant_signal_direction,
    )
    reason_codes = _row_reason_codes(
        alignment_status=alignment_status,
        review_required=signal.review_required,
    )
    return ResearchMultiteamSignalConsensusTeamRow(
        team_id=signal.team_id,
        category_id=signal.category_id,
        observed_at=signal.observed_at,
        signal_direction=signal.signal_direction,
        alignment_status=alignment_status,
        signal_strength=signal.signal_strength,
        confidence_score=signal.confidence_score,
        signal_weight=_signal_weight(signal.signal_strength, signal.confidence_score),
        review_required=signal.review_required,
        reason_codes=reason_codes,
    )


def _alignment_status(
    signal_direction: str,
    *,
    dominant_signal_direction: str | None,
) -> str:
    if signal_direction == "neutral" or dominant_signal_direction is None:
        return "review"
    if signal_direction == dominant_signal_direction:
        return "aligned"
    return "conflict"


def _row_reason_codes(
    *,
    alignment_status: str,
    review_required: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if alignment_status == "aligned":
        reason_codes.append("team_signal_aligned")
    elif alignment_status == "conflict":
        reason_codes.append("team_signal_conflict")
    else:
        reason_codes.append("team_signal_neutral")
    if review_required:
        reason_codes.append("team_review_requested")
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...],
    *,
    config: ResearchMultiteamSignalConsensusConfig,
) -> tuple[str, ...]:
    if _count(len(rows)) < config.min_team_count:
        return ("insufficient_team_coverage",)
    conflict_strength = _conflict_strength(rows)
    review_requested = any(row.review_required for row in rows)
    if conflict_strength >= config.block_conflict_strength:
        reason_codes = ["cross_team_conflict_block"]
        if review_requested:
            reason_codes.append("team_review_requested")
        return tuple(reason_codes)

    reason_codes: list[str] = []
    if _consensus_ratio(rows, _dominant_from_rows(rows)) < config.pass_min_consensus_ratio:
        reason_codes.append("consensus_ratio_watch")
    if conflict_strength >= config.review_conflict_strength:
        reason_codes.append("cross_team_conflict_watch")
    if any(row.signal_direction == "neutral" for row in rows):
        reason_codes.append("neutral_team_signal_present")
    if review_requested:
        reason_codes.append("team_review_requested")
    average_confidence_score = _average_confidence_score(rows)
    if (
        average_confidence_score is not None
        and average_confidence_score < config.min_average_confidence_score
    ):
        reason_codes.append("average_confidence_watch")
    if reason_codes:
        return tuple(reason_codes)
    return ("signal_consensus_pass",)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "insufficient_team_coverage" in reason_codes
        or "cross_team_conflict_block" in reason_codes
    ):
        return "block"
    if reason_codes == ("signal_consensus_pass",):
        return "pass"
    return "watch"


def _dominant_signal_direction(
    signals: tuple[ResearchMultiteamSignal, ...],
) -> str | None:
    weights = {
        direction: _sum_decimals(
            _signal_weight(signal.signal_strength, signal.confidence_score)
            for signal in signals
            if signal.signal_direction == direction
        )
        for direction in ("supports_yes", "supports_no")
    }
    if weights["supports_yes"] == ZERO and weights["supports_no"] == ZERO:
        return None
    if weights["supports_yes"] == weights["supports_no"]:
        return "supports_yes"
    if weights["supports_yes"] > weights["supports_no"]:
        return "supports_yes"
    return "supports_no"


def _dominant_from_rows(
    rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...],
) -> str | None:
    weights = {
        direction: _sum_decimals(
            row.signal_weight for row in rows if row.signal_direction == direction
        )
        for direction in ("supports_yes", "supports_no")
    }
    if weights["supports_yes"] == ZERO and weights["supports_no"] == ZERO:
        return None
    if weights["supports_yes"] == weights["supports_no"]:
        return "supports_yes"
    if weights["supports_yes"] > weights["supports_no"]:
        return "supports_yes"
    return "supports_no"


def _consensus_ratio(
    rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...],
    dominant_signal_direction: str | None,
) -> Decimal:
    total_weight = _sum_decimals(row.signal_weight for row in rows)
    if total_weight == ZERO or dominant_signal_direction is None:
        return ZERO
    dominant_weight = _sum_decimals(
        row.signal_weight
        for row in rows
        if row.signal_direction == dominant_signal_direction
    )
    return _ratio(dominant_weight, total_weight)


def _conflict_strength(rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...]) -> Decimal:
    yes_weight = _sum_decimals(
        row.signal_weight for row in rows if row.signal_direction == "supports_yes"
    )
    no_weight = _sum_decimals(
        row.signal_weight for row in rows if row.signal_direction == "supports_no"
    )
    support_weight = yes_weight + no_weight
    if support_weight == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        numerator = min(yes_weight, no_weight) * Decimal("2.000000")
    return _ratio(numerator, support_weight)


def _review_need_score(
    rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...],
    *,
    config: ResearchMultiteamSignalConsensusConfig,
) -> Decimal:
    if _count(len(rows)) < config.min_team_count:
        return ONE
    review_ratio = _ratio(
        _count(sum(1 for row in rows if row.review_required)),
        _count(len(rows)),
    )
    return max(_conflict_strength(rows), review_ratio)


def _average_confidence_score(
    rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    total = _sum_decimals(row.confidence_score for row in rows)
    return _ratio(total, _count(len(rows)))


def _signal_weight(signal_strength: Decimal, confidence_score: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(signal_strength * confidence_score)


def _sort_rows(
    rows: tuple[ResearchMultiteamSignalConsensusTeamRow, ...],
) -> tuple[ResearchMultiteamSignalConsensusTeamRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                ALIGNMENT_RANK[row.alignment_status],
                row.team_id,
                row.category_id,
                row.observed_at,
            ),
        ),
    )


def _normalize_signal_inputs(
    signals: Iterable[ResearchMultiteamSignal | ResearchMultiteamSignalConsensusTeamRow],
) -> tuple[ResearchMultiteamSignal, ...]:
    if isinstance(signals, str | bytes):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    result: list[ResearchMultiteamSignal] = []
    seen: set[str] = set()
    for item in normalized:
        signal = _coerce_signal(item)
        require_paper_only_flags("signal", signal)
        if signal.team_id in seen:
            raise ValueError("team_id values must be unique")
        seen.add(signal.team_id)
        result.append(signal)
    return tuple(
        sorted(
            result,
            key=lambda signal: (
                signal.team_id,
                signal.category_id,
                signal.observed_at,
            ),
        ),
    )


def _coerce_signal(
    value: ResearchMultiteamSignal | ResearchMultiteamSignalConsensusTeamRow,
) -> ResearchMultiteamSignal:
    if type(value) is ResearchMultiteamSignal:
        return value
    if type(value) is ResearchMultiteamSignalConsensusTeamRow:
        require_paper_only_flags("row", value)
        return ResearchMultiteamSignal(
            team_id=value.team_id,
            category_id=value.category_id,
            observed_at=value.observed_at,
            signal_direction=value.signal_direction,
            signal_strength=value.signal_strength,
            confidence_score=value.confidence_score,
            review_required=value.review_required,
        )
    raise ValueError("signals must contain multiteam signal values")


def _normalize_rows(
    rows: Iterable[ResearchMultiteamSignalConsensusTeamRow],
) -> tuple[ResearchMultiteamSignalConsensusTeamRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMultiteamSignalConsensusTeamRow:
            raise ValueError("rows must contain ResearchMultiteamSignalConsensusTeamRow values")
        require_paper_only_flags("row", row)
        if row.team_id in seen:
            raise ValueError("rows team_id values must be unique")
        seen.add(row.team_id)
    if normalized != _sort_rows(normalized):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _validate_signal_times(
    signals: tuple[ResearchMultiteamSignal, ...],
    generated_at: datetime,
) -> None:
    for signal in signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must be <= generated_at")


def _validate_row(row: ResearchMultiteamSignalConsensusTeamRow) -> None:
    if row.signal_weight != _signal_weight(row.signal_strength, row.confidence_score):
        raise ValueError("signal_weight must match signal_strength and confidence_score")
    expected_reasons = _row_reason_codes(
        alignment_status=row.alignment_status,
        review_required=row.review_required,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("row reason_codes must match row fields")


def _validate_report(report: ResearchMultiteamSignalConsensusReport) -> None:
    if report.team_count != _count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.category_count != _count(len({row.category_id for row in report.rows})):
        raise ValueError("category_count must match rows")
    if report.aligned_team_count != _count(
        sum(1 for row in report.rows if row.alignment_status == "aligned"),
    ):
        raise ValueError("aligned_team_count must match rows")
    if report.conflicting_team_count != _count(
        sum(1 for row in report.rows if row.alignment_status == "conflict"),
    ):
        raise ValueError("conflicting_team_count must match rows")
    if report.review_required_count != _count(
        sum(1 for row in report.rows if row.review_required),
    ):
        raise ValueError("review_required_count must match rows")
    if report.dominant_signal_direction != _dominant_from_rows(report.rows):
        raise ValueError("dominant_signal_direction must match rows")
    if report.consensus_ratio != _consensus_ratio(
        report.rows,
        report.dominant_signal_direction,
    ):
        raise ValueError("consensus_ratio must match rows")
    if report.conflict_strength != _conflict_strength(report.rows):
        raise ValueError("conflict_strength must match rows")
    if report.average_confidence_score != _average_confidence_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a public string")
    _reject_unsafe_public_payload(value)


def _require_signal_direction(field_name: str, value: object) -> None:
    _require_member(field_name, value, SIGNAL_DIRECTIONS)


def _require_directional_signal(field_name: str, value: object) -> None:
    _require_member(field_name, value, ("supports_yes", "supports_no"))


def _require_alignment_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, ALIGNMENT_STATUSES)


def _require_report_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, REPORT_STATUSES)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    _reject_unsafe_public_payload(value)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _count_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _count_decimal(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_member(field_name, reason_code, allowed)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(reason_code for reason_code in allowed if reason_code in normalized)
    if normalized != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT or denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    return _quantize(total)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError("public payload contains unsafe text")
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_payload(key)
            _reject_unsafe_public_payload(nested)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(json_ready_no_floats(value))


__all__ = (
    "DEFAULT_RESEARCH_MULTITEAM_SIGNAL_CONSENSUS_CONFIG_VERSION",
    "ResearchMultiteamSignal",
    "ResearchMultiteamSignalConsensusConfig",
    "ResearchMultiteamSignalConsensusReport",
    "ResearchMultiteamSignalConsensusTeamRow",
    "build_research_multiteam_signal_consensus_report",
    "research_multiteam_signal_consensus_report_to_payload",
)
