"""Pure candidate source quorum repair priority v10 reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUORUM_REPAIR_PRIORITY_V10_CONFIG_VERSION = (
    "strategy-candidate-source-quorum-repair-priority-v10"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE = Decimal("1.000000")
MISSING_SOURCE_WEIGHT = Decimal("0.350000")
SOURCE_DISAGREEMENT_WEIGHT = Decimal("0.200000")
SOURCE_RECENCY_WEIGHT = Decimal("0.150000")
RESOLUTION_URGENCY_WEIGHT = Decimal("0.150000")
CONFIDENCE_IMPACT_WEIGHT = Decimal("0.150000")
MEDIUM_PRIORITY_SCORE_THRESHOLD = Decimal("0.150000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PRIORITY_BANDS = ("low", "medium", "high", "critical")
PRIORITY_STATUSES = ("clear", "low", "medium", "high", "critical")
REPAIR_ACTIONS = (
    "monitor_sources",
    "queue_source_refresh",
    "repair_source_quorum",
    "pause_probability_signal",
)
ROW_REASON_CODES = (
    "candidate_source_quorum_repair_priority_v10_missing_independent_sources",
    "candidate_source_quorum_repair_priority_v10_source_disagreement",
    "candidate_source_quorum_repair_priority_v10_stale_sources",
    "candidate_source_quorum_repair_priority_v10_resolution_urgency",
    "candidate_source_quorum_repair_priority_v10_confidence_impact",
    "candidate_source_quorum_repair_priority_v10_repair_not_needed",
)
REPORT_REASON_CODES = (
    "candidate_source_quorum_repair_priority_v10_clear",
    "candidate_source_quorum_repair_priority_v10_missing_independent_sources",
    "candidate_source_quorum_repair_priority_v10_source_disagreement",
    "candidate_source_quorum_repair_priority_v10_stale_sources",
    "candidate_source_quorum_repair_priority_v10_resolution_urgency",
    "candidate_source_quorum_repair_priority_v10_confidence_impact",
    "candidate_source_quorum_repair_priority_v10_medium_priority_present",
    "candidate_source_quorum_repair_priority_v10_high_priority_present",
    "candidate_source_quorum_repair_priority_v10_critical_priority_present",
)


@dataclass(frozen=True)
class StrategyCandidateSourceQuorumRepairPriorityV10Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUORUM_REPAIR_PRIORITY_V10_CONFIG_VERSION
    )
    required_independent_sources: Decimal = Decimal("3")
    max_source_age_hours: Decimal = Decimal("12.000000")
    urgent_resolution_hours: Decimal = Decimal("6.000000")
    near_resolution_hours: Decimal = Decimal("24.000000")
    source_disagreement_watch_threshold: Decimal = Decimal("0.150000")
    confidence_impact_threshold: Decimal = Decimal("0.100000")
    high_priority_score_threshold: Decimal = Decimal("0.350000")
    critical_priority_score_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyCandidateSourceQuorumRepairPriorityV10Config,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_independent_sources",
            _normalize_positive_count(
                "required_independent_sources",
                self.required_independent_sources,
            ),
        )
        for field_name in (
            "max_source_age_hours",
            "urgent_resolution_hours",
            "near_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_disagreement_watch_threshold",
            "confidence_impact_threshold",
            "high_priority_score_threshold",
            "critical_priority_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.urgent_resolution_hours >= self.near_resolution_hours:
            raise ValueError("near_resolution_hours must exceed urgent_resolution_hours")
        if self.high_priority_score_threshold > self.critical_priority_score_threshold:
            raise ValueError(
                "critical_priority_score_threshold must be at least "
                "high_priority_score_threshold",
            )
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateSourceQuorumRepairPriorityV10Input:
    candidate_id: str
    market_slug: str
    independent_source_count: Decimal
    source_disagreement: Decimal
    source_age_hours: Decimal
    time_to_resolution_hours: Decimal
    confidence_impact: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            StrategyCandidateSourceQuorumRepairPriorityV10Input,
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_nonnegative_count(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "source_disagreement",
            _normalize_probability("source_disagreement", self.source_disagreement),
        )
        object.__setattr__(
            self,
            "source_age_hours",
            _normalize_nonnegative_ratio("source_age_hours", self.source_age_hours),
        )
        object.__setattr__(
            self,
            "time_to_resolution_hours",
            _normalize_nonnegative_ratio(
                "time_to_resolution_hours",
                self.time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "confidence_impact",
            _normalize_probability("confidence_impact", self.confidence_impact),
        )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidateSourceQuorumRepairPriorityV10Row:
    candidate_id: str
    market_slug: str
    independent_source_count: Decimal
    missing_independent_source_count: Decimal
    source_disagreement: Decimal
    source_age_hours: Decimal
    source_recency_pressure: Decimal
    time_to_resolution_hours: Decimal
    resolution_urgency: Decimal
    confidence_impact: Decimal
    required_independent_sources: Decimal
    max_source_age_hours: Decimal
    urgent_resolution_hours: Decimal
    near_resolution_hours: Decimal
    source_disagreement_watch_threshold: Decimal
    confidence_impact_threshold: Decimal
    high_priority_score_threshold: Decimal
    critical_priority_score_threshold: Decimal
    repair_priority_score: Decimal
    priority_band: str
    repair_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyCandidateSourceQuorumRepairPriorityV10Row)
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "independent_source_count",
            "missing_independent_source_count",
            "required_independent_sources",
        ):
            object.__setattr__(
                self,
                field_name,
                (
                    _normalize_positive_count
                    if field_name == "required_independent_sources"
                    else _normalize_nonnegative_count
                )(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_disagreement",
            "source_recency_pressure",
            "resolution_urgency",
            "confidence_impact",
            "source_disagreement_watch_threshold",
            "confidence_impact_threshold",
            "high_priority_score_threshold",
            "critical_priority_score_threshold",
            "repair_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_hours",
            "time_to_resolution_hours",
            "max_source_age_hours",
            "urgent_resolution_hours",
            "near_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                (
                    _normalize_positive_ratio
                    if field_name
                    in (
                        "max_source_age_hours",
                        "urgent_resolution_hours",
                        "near_resolution_hours",
                    )
                    else _normalize_nonnegative_ratio
                )(field_name, getattr(self, field_name)),
            )
        if self.urgent_resolution_hours >= self.near_resolution_hours:
            raise ValueError("near_resolution_hours must exceed urgent_resolution_hours")
        if self.high_priority_score_threshold > self.critical_priority_score_threshold:
            raise ValueError(
                "critical_priority_score_threshold must be at least "
                "high_priority_score_threshold",
            )
        _require_member("priority_band", self.priority_band, PRIORITY_BANDS)
        _require_member("repair_action", self.repair_action, REPAIR_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateSourceQuorumRepairPriorityV10Report:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    candidate_count: Decimal
    critical_priority_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    max_repair_priority_score: Decimal
    mean_repair_priority_score: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            StrategyCandidateSourceQuorumRepairPriorityV10Report,
        )
        object.__setattr__(self, "generated_at", _as_exact_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "candidate_count",
            "critical_priority_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_repair_priority_score", "mean_repair_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("priority_status", self.priority_status, PRIORITY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("report", self)


def build_strategy_candidate_source_quorum_repair_priority_v10(
    candidates: list[StrategyCandidateSourceQuorumRepairPriorityV10Input]
    | tuple[StrategyCandidateSourceQuorumRepairPriorityV10Input, ...],
    *,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
    generated_at: datetime,
) -> StrategyCandidateSourceQuorumRepairPriorityV10Report:
    if type(config) is not StrategyCandidateSourceQuorumRepairPriorityV10Config:
        raise ValueError(
            "config must be a StrategyCandidateSourceQuorumRepairPriorityV10Config",
        )
    _require_safety_flags("config", config)
    generated_at_utc = _as_exact_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (_candidate_row(candidate_row, config) for candidate_row in input_rows),
            key=_row_sort_key,
        ),
    )
    return StrategyCandidateSourceQuorumRepairPriorityV10Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(input_rows)),
        candidate_count=_count(len(rows)),
        critical_priority_count=_priority_count(rows, "critical"),
        high_priority_count=_priority_count(rows, "high"),
        medium_priority_count=_priority_count(rows, "medium"),
        low_priority_count=_priority_count(rows, "low"),
        max_repair_priority_score=_max_repair_priority_score(rows),
        mean_repair_priority_score=_mean_repair_priority_score(rows),
        priority_status=_report_priority_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_candidate_source_quorum_repair_priority_v10_payload(
    report: StrategyCandidateSourceQuorumRepairPriorityV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateSourceQuorumRepairPriorityV10Report:
        raise ValueError(
            "report must be a StrategyCandidateSourceQuorumRepairPriorityV10Report",
        )
    _require_safety_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _candidate_row(
    candidate_row: StrategyCandidateSourceQuorumRepairPriorityV10Input,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
) -> StrategyCandidateSourceQuorumRepairPriorityV10Row:
    missing_count = _missing_independent_source_count(candidate_row, config)
    recency_pressure = _source_recency_pressure(candidate_row, config)
    urgency = _resolution_urgency(candidate_row, config)
    score = _repair_priority_score(
        missing_count=missing_count,
        source_disagreement=candidate_row.source_disagreement,
        source_recency_pressure=recency_pressure,
        resolution_urgency=urgency,
        confidence_impact=candidate_row.confidence_impact,
        config=config,
    )
    priority_band = _priority_band(score, config)
    return StrategyCandidateSourceQuorumRepairPriorityV10Row(
        candidate_id=candidate_row.candidate_id,
        market_slug=candidate_row.market_slug,
        independent_source_count=candidate_row.independent_source_count,
        missing_independent_source_count=missing_count,
        source_disagreement=candidate_row.source_disagreement,
        source_age_hours=candidate_row.source_age_hours,
        source_recency_pressure=recency_pressure,
        time_to_resolution_hours=candidate_row.time_to_resolution_hours,
        resolution_urgency=urgency,
        confidence_impact=candidate_row.confidence_impact,
        required_independent_sources=config.required_independent_sources,
        max_source_age_hours=config.max_source_age_hours,
        urgent_resolution_hours=config.urgent_resolution_hours,
        near_resolution_hours=config.near_resolution_hours,
        source_disagreement_watch_threshold=config.source_disagreement_watch_threshold,
        confidence_impact_threshold=config.confidence_impact_threshold,
        high_priority_score_threshold=config.high_priority_score_threshold,
        critical_priority_score_threshold=config.critical_priority_score_threshold,
        repair_priority_score=score,
        priority_band=priority_band,
        repair_action=_repair_action(priority_band),
        reason_codes=_row_reason_codes(
            missing_independent_source_count=missing_count,
            source_disagreement=candidate_row.source_disagreement,
            source_age_hours=candidate_row.source_age_hours,
            time_to_resolution_hours=candidate_row.time_to_resolution_hours,
            confidence_impact=candidate_row.confidence_impact,
            config=config,
        ),
    )


def _missing_independent_source_count(
    candidate_row: StrategyCandidateSourceQuorumRepairPriorityV10Input,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
) -> Decimal:
    missing_count = config.required_independent_sources - candidate_row.independent_source_count
    if missing_count <= ZERO_COUNT:
        return ZERO_COUNT
    return _normalize_nonnegative_count("missing_independent_source_count", missing_count)


def _source_recency_pressure(
    candidate_row: StrategyCandidateSourceQuorumRepairPriorityV10Input,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _cap_probability(candidate_row.source_age_hours / config.max_source_age_hours)


def _resolution_urgency(
    candidate_row: StrategyCandidateSourceQuorumRepairPriorityV10Input,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
) -> Decimal:
    if candidate_row.time_to_resolution_hours <= config.urgent_resolution_hours:
        return ONE
    if candidate_row.time_to_resolution_hours >= config.near_resolution_hours:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        span = config.near_resolution_hours - config.urgent_resolution_hours
        remaining = config.near_resolution_hours - candidate_row.time_to_resolution_hours
        return _cap_probability(remaining / span)


def _repair_priority_score(
    *,
    missing_count: Decimal,
    source_disagreement: Decimal,
    source_recency_pressure: Decimal,
    resolution_urgency: Decimal,
    confidence_impact: Decimal,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        missing_pressure = missing_count / config.required_independent_sources
        score = (
            (missing_pressure * MISSING_SOURCE_WEIGHT)
            + (source_disagreement * SOURCE_DISAGREEMENT_WEIGHT)
            + (source_recency_pressure * SOURCE_RECENCY_WEIGHT)
            + (resolution_urgency * RESOLUTION_URGENCY_WEIGHT)
            + (confidence_impact * CONFIDENCE_IMPACT_WEIGHT)
        )
        return _cap_probability(score)


def _priority_band(
    score: Decimal,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
) -> str:
    if score >= config.critical_priority_score_threshold:
        return "critical"
    if score >= config.high_priority_score_threshold:
        return "high"
    if score >= MEDIUM_PRIORITY_SCORE_THRESHOLD:
        return "medium"
    return "low"


def _repair_action(priority_band: str) -> str:
    if priority_band == "critical":
        return "pause_probability_signal"
    if priority_band == "high":
        return "repair_source_quorum"
    if priority_band == "medium":
        return "queue_source_refresh"
    return "monitor_sources"


def _row_reason_codes(
    *,
    missing_independent_source_count: Decimal,
    source_disagreement: Decimal,
    source_age_hours: Decimal,
    time_to_resolution_hours: Decimal,
    confidence_impact: Decimal,
    config: StrategyCandidateSourceQuorumRepairPriorityV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing_independent_source_count > ZERO_COUNT:
        codes.append(
            "candidate_source_quorum_repair_priority_v10_missing_independent_sources",
        )
    if source_disagreement >= config.source_disagreement_watch_threshold:
        codes.append("candidate_source_quorum_repair_priority_v10_source_disagreement")
    if source_age_hours > config.max_source_age_hours:
        codes.append("candidate_source_quorum_repair_priority_v10_stale_sources")
    if time_to_resolution_hours <= config.near_resolution_hours:
        codes.append("candidate_source_quorum_repair_priority_v10_resolution_urgency")
    if confidence_impact >= config.confidence_impact_threshold:
        codes.append("candidate_source_quorum_repair_priority_v10_confidence_impact")
    if not codes:
        codes.append("candidate_source_quorum_repair_priority_v10_repair_not_needed")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("candidate_source_quorum_repair_priority_v10_clear",)
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    codes = [
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code in row_codes
        and reason_code != "candidate_source_quorum_repair_priority_v10_repair_not_needed"
    ]
    if any(row.priority_band == "medium" for row in rows):
        codes.append("candidate_source_quorum_repair_priority_v10_medium_priority_present")
    if any(row.priority_band == "high" for row in rows):
        codes.append("candidate_source_quorum_repair_priority_v10_high_priority_present")
    if any(row.priority_band == "critical" for row in rows):
        codes.append("candidate_source_quorum_repair_priority_v10_critical_priority_present")
    if not codes:
        codes.append("candidate_source_quorum_repair_priority_v10_clear")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_priority_status(
    rows: tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...],
) -> str:
    if not rows:
        return "clear"
    if any(row.priority_band == "critical" for row in rows):
        return "critical"
    if any(row.priority_band == "high" for row in rows):
        return "high"
    if any(row.priority_band == "medium" for row in rows):
        return "medium"
    return "low"


def _row_sort_key(
    row: StrategyCandidateSourceQuorumRepairPriorityV10Row,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -row.repair_priority_score,
        -row.missing_independent_source_count,
        -row.confidence_impact,
        row.candidate_id,
        row.market_slug,
    )


def _normalize_inputs(
    candidates: list[StrategyCandidateSourceQuorumRepairPriorityV10Input]
    | tuple[StrategyCandidateSourceQuorumRepairPriorityV10Input, ...],
) -> tuple[StrategyCandidateSourceQuorumRepairPriorityV10Input, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    seen: set[tuple[str, str]] = set()
    for candidate_row in normalized:
        if type(candidate_row) is not StrategyCandidateSourceQuorumRepairPriorityV10Input:
            raise ValueError(
                "candidates must contain "
                "StrategyCandidateSourceQuorumRepairPriorityV10Input values",
            )
        _require_safety_flags("candidate", candidate_row)
        key = (candidate_row.candidate_id, candidate_row.market_slug)
        if key in seen:
            raise ValueError("duplicate candidate market pair")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...],
) -> tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyCandidateSourceQuorumRepairPriorityV10Row:
            raise ValueError(
                "rows must contain "
                "StrategyCandidateSourceQuorumRepairPriorityV10Row values",
            )
        _require_safety_flags("row", row)
    return rows


def _priority_count(
    rows: tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...],
    priority_band: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.priority_band == priority_band))


def _max_repair_priority_score(
    rows: tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.repair_priority_score for row in rows)


def _mean_repair_priority_score(
    rows: tuple[StrategyCandidateSourceQuorumRepairPriorityV10Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            sum((row.repair_priority_score for row in rows), ZERO_RATIO)
            / Decimal(len(rows)),
        )


def _validate_row(row: StrategyCandidateSourceQuorumRepairPriorityV10Row) -> None:
    config = _config_from_row(row)
    input_row = StrategyCandidateSourceQuorumRepairPriorityV10Input(
        candidate_id=row.candidate_id,
        market_slug=row.market_slug,
        independent_source_count=row.independent_source_count,
        source_disagreement=row.source_disagreement,
        source_age_hours=row.source_age_hours,
        time_to_resolution_hours=row.time_to_resolution_hours,
        confidence_impact=row.confidence_impact,
    )
    expected_missing_count = _missing_independent_source_count(input_row, config)
    if row.missing_independent_source_count != expected_missing_count:
        raise ValueError("missing_independent_source_count must match row inputs")
    expected_recency_pressure = _source_recency_pressure(input_row, config)
    if row.source_recency_pressure != expected_recency_pressure:
        raise ValueError("source_recency_pressure must match row inputs")
    expected_urgency = _resolution_urgency(input_row, config)
    if row.resolution_urgency != expected_urgency:
        raise ValueError("resolution_urgency must match row inputs")
    expected_score = _repair_priority_score(
        missing_count=expected_missing_count,
        source_disagreement=row.source_disagreement,
        source_recency_pressure=expected_recency_pressure,
        resolution_urgency=expected_urgency,
        confidence_impact=row.confidence_impact,
        config=config,
    )
    if row.repair_priority_score != expected_score:
        raise ValueError("repair_priority_score must match row inputs")
    expected_band = _priority_band(expected_score, config)
    if row.priority_band != expected_band:
        raise ValueError("priority_band must match repair_priority_score")
    expected_action = _repair_action(expected_band)
    if row.repair_action != expected_action:
        raise ValueError("repair_action must match priority_band")
    expected_reason_codes = _row_reason_codes(
        missing_independent_source_count=expected_missing_count,
        source_disagreement=row.source_disagreement,
        source_age_hours=row.source_age_hours,
        time_to_resolution_hours=row.time_to_resolution_hours,
        confidence_impact=row.confidence_impact,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")


def _config_from_row(
    row: StrategyCandidateSourceQuorumRepairPriorityV10Row,
) -> StrategyCandidateSourceQuorumRepairPriorityV10Config:
    return StrategyCandidateSourceQuorumRepairPriorityV10Config(
        required_independent_sources=row.required_independent_sources,
        max_source_age_hours=row.max_source_age_hours,
        urgent_resolution_hours=row.urgent_resolution_hours,
        near_resolution_hours=row.near_resolution_hours,
        source_disagreement_watch_threshold=row.source_disagreement_watch_threshold,
        confidence_impact_threshold=row.confidence_impact_threshold,
        high_priority_score_threshold=row.high_priority_score_threshold,
        critical_priority_score_threshold=row.critical_priority_score_threshold,
    )


def _validate_report(report: StrategyCandidateSourceQuorumRepairPriorityV10Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.input_count != report.candidate_count:
        raise ValueError("input_count must match candidate_count")
    if report.critical_priority_count != _priority_count(report.rows, "critical"):
        raise ValueError("critical_priority_count must match rows")
    if report.high_priority_count != _priority_count(report.rows, "high"):
        raise ValueError("high_priority_count must match rows")
    if report.medium_priority_count != _priority_count(report.rows, "medium"):
        raise ValueError("medium_priority_count must match rows")
    if report.low_priority_count != _priority_count(report.rows, "low"):
        raise ValueError("low_priority_count must match rows")
    if report.max_repair_priority_score != _max_repair_priority_score(report.rows):
        raise ValueError("max_repair_priority_score must match rows")
    if report.mean_repair_priority_score != _mean_repair_priority_score(report.rows):
        raise ValueError("mean_repair_priority_score must match rows")
    if report.priority_status != _report_priority_status(report.rows):
        raise ValueError("priority_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported value")
        if value in seen:
            raise ValueError(f"{field_name} contains duplicate value")
        seen.add(value)
    return tuple(value for value in allowed_values if value in seen)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    integral_value = decimal_value.to_integral_value()
    if decimal_value != integral_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return integral_value.quantize(COUNT_QUANTUM)


def _normalize_positive_ratio(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _normalize_nonnegative_ratio(field_name, value)
    if decimal_value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_ratio(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _normalize_nonnegative_ratio(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _cap_probability(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    if value < ZERO_RATIO:
        return ZERO_RATIO
    return _quantize_ratio(value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_exact_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC timezone-aware")
    return value


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is not UTC:
            raise ValueError("JSON datetime value must be UTC timezone-aware")
        return value.isoformat()
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUORUM_REPAIR_PRIORITY_V10_CONFIG_VERSION",
    "StrategyCandidateSourceQuorumRepairPriorityV10Config",
    "StrategyCandidateSourceQuorumRepairPriorityV10Input",
    "StrategyCandidateSourceQuorumRepairPriorityV10Row",
    "StrategyCandidateSourceQuorumRepairPriorityV10Report",
    "build_strategy_candidate_source_quorum_repair_priority_v10",
    "strategy_candidate_source_quorum_repair_priority_v10_payload",
)
