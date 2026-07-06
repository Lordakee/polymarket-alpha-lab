"""Pure Phase 1 specialist market memory priority queue."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_MARKET_MEMORY_PRIORITY_QUEUE_V2_CONFIG_VERSION = (
    "team-specialist-market-memory-priority-queue-v2-phase-1"
)

QUEUE_STATUSES = ("clear", "watch", "urgent")

ROW_REASON_CODES = (
    "market_memory_priority_clear",
    "market_memory_priority_watch",
    "market_memory_priority_urgent",
    "memory_signal_strong",
    "memory_signal_watch",
    "confidence_signal_strong",
    "confidence_signal_watch",
    "feedback_impact_boost",
    "stale_lesson_penalty",
)
REPORT_REASON_CODES = (
    "market_memory_priority_empty",
    "market_memory_priority_clear",
    "market_memory_priority_watch",
    "market_memory_priority_urgent",
    "feedback_impact_boost",
    "stale_lesson_penalty",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SAFE_REF_PREFIXES = ("public:", "memory:", "source:", "lesson:")
PUBLIC_TEXT_HEXES = (
    "6c697665",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "6e6574776f726b",
    "6461746162617365",
    "70657273697374",
    "7369676e696e67",
    "6d75746174696f6e",
    "627579",
    "73656c6c",
    "7472616465",
)
PUBLIC_TEXT_BLOCKS = tuple(bytes.fromhex(value).decode("ascii") for value in PUBLIC_TEXT_HEXES)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_MARKET_MEMORY_PRIORITY_QUEUE_V2_CONFIG_VERSION",
    "QUEUE_STATUSES",
    "TeamSpecialistMarketMemoryPriorityQueueV2Config",
    "TeamSpecialistMarketMemoryPriorityQueueV2Input",
    "TeamSpecialistMarketMemoryPriorityQueueV2Row",
    "TeamSpecialistMarketMemoryPriorityQueueV2Report",
    "build_team_specialist_market_memory_priority_queue_v2",
    "team_specialist_market_memory_priority_queue_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistMarketMemoryPriorityQueueV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_MARKET_MEMORY_PRIORITY_QUEUE_V2_CONFIG_VERSION
    market_memory_weight: Decimal = Decimal("0.400000")
    confidence_weight: Decimal = Decimal("0.200000")
    feedback_impact_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.100000")
    stale_lesson_penalty_weight: Decimal = Decimal("0.200000")
    max_lesson_age_days: Decimal = Decimal("30.000000")
    watch_priority_score: Decimal = Decimal("0.300000")
    urgent_priority_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "market_memory_weight",
            "confidence_weight",
            "feedback_impact_weight",
            "freshness_weight",
            "stale_lesson_penalty_weight",
            "watch_priority_score",
            "urgent_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_lesson_age_days",
            _normalize_positive_decimal("max_lesson_age_days", self.max_lesson_age_days),
        )
        _require_ratio_total(
            self.market_memory_weight,
            self.confidence_weight,
            self.feedback_impact_weight,
            self.freshness_weight,
        )
        if self.watch_priority_score > self.urgent_priority_score:
            raise ValueError("watch_priority_score must be less than or equal to urgent_priority_score")
        _require_hard_flags("market memory priority config", self)
        _reject_public_payload("market memory priority config", _json_ready(self))


@dataclass(frozen=True)
class TeamSpecialistMarketMemoryPriorityQueueV2Input:
    team_id: str
    specialist_id: str
    market_key: str
    memory_key: str
    observed_at: datetime
    lesson_last_validated_at: datetime
    market_memory_score: Decimal
    confidence_score: Decimal
    feedback_impact_score: Decimal
    public_evidence_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "market_key", "memory_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "lesson_last_validated_at",
            _as_utc("lesson_last_validated_at", self.lesson_last_validated_at),
        )
        for field_name in (
            "market_memory_score",
            "confidence_score",
            "feedback_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_evidence_refs",
            _normalize_public_refs("public_evidence_refs", self.public_evidence_refs),
        )
        _require_hard_flags("market memory priority input", self)
        _reject_public_payload("market memory priority input", _json_ready(self))


@dataclass(frozen=True)
class TeamSpecialistMarketMemoryPriorityQueueV2Row:
    queue_rank: Decimal
    team_id: str
    specialist_id: str
    market_key: str
    memory_key: str
    observed_at: datetime
    lesson_last_validated_at: datetime
    lesson_age_days: Decimal
    freshness_score: Decimal
    stale_lesson_penalty: Decimal
    market_memory_score: Decimal
    confidence_score: Decimal
    feedback_impact_score: Decimal
    priority_score: Decimal
    queue_status: str
    public_evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "queue_rank", _normalize_positive_count("queue_rank", self.queue_rank))
        for field_name in ("team_id", "specialist_id", "market_key", "memory_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "lesson_last_validated_at",
            _as_utc("lesson_last_validated_at", self.lesson_last_validated_at),
        )
        object.__setattr__(
            self,
            "lesson_age_days",
            _normalize_nonnegative_decimal("lesson_age_days", self.lesson_age_days),
        )
        for field_name in (
            "freshness_score",
            "stale_lesson_penalty",
            "market_memory_score",
            "confidence_score",
            "feedback_impact_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "public_evidence_refs",
            _normalize_public_refs("public_evidence_refs", self.public_evidence_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("market memory priority row", self)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match row fields")
        _reject_public_payload("market memory priority row", _json_ready(self))


@dataclass(frozen=True)
class TeamSpecialistMarketMemoryPriorityQueueV2Report:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    urgent_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    average_priority_score: Decimal
    top_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[TeamSpecialistMarketMemoryPriorityQueueV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("item_count", "urgent_count", "watch_count", "clear_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_priority_score", "top_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "priority_rows",
            _normalize_priority_rows(self.priority_rows),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("market memory priority report", self)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)
        _reject_public_payload("market memory priority report", _json_ready(self))

    @property
    def payload(self) -> dict[str, Any]:
        payload = team_specialist_market_memory_priority_queue_v2_payload(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


def build_team_specialist_market_memory_priority_queue_v2(
    inputs: list[TeamSpecialistMarketMemoryPriorityQueueV2Input]
    | tuple[TeamSpecialistMarketMemoryPriorityQueueV2Input, ...],
    *,
    config: TeamSpecialistMarketMemoryPriorityQueueV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistMarketMemoryPriorityQueueV2Report:
    if config is None:
        config = TeamSpecialistMarketMemoryPriorityQueueV2Config()
    if type(config) is not TeamSpecialistMarketMemoryPriorityQueueV2Config:
        raise ValueError("config must be a TeamSpecialistMarketMemoryPriorityQueueV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    _validate_input_dates(input_rows, generated_at_utc)
    rows_without_rank = tuple(
        sorted(
            (_priority_row(item, config, generated_at_utc) for item in input_rows),
            key=_priority_row_sort_key,
        ),
    )
    priority_rows = tuple(
        _with_rank(row, Decimal(index).quantize(COUNT_QUANTUM))
        for index, row in enumerate(rows_without_rank, start=1)
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        item_count=_count(len(priority_rows)),
        urgent_count=_count(sum(1 for row in priority_rows if row.queue_status == "urgent")),
        watch_count=_count(sum(1 for row in priority_rows if row.queue_status == "watch")),
        clear_count=_count(sum(1 for row in priority_rows if row.queue_status == "clear")),
        average_priority_score=_average_priority_score(priority_rows),
        top_priority_score=_top_priority_score(priority_rows),
        status=_report_status(priority_rows),
        reason_codes=_report_reason_codes(priority_rows),
        priority_rows=priority_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistMarketMemoryPriorityQueueV2Report(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_market_memory_priority_queue_v2_payload(
    report: TeamSpecialistMarketMemoryPriorityQueueV2Report,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistMarketMemoryPriorityQueueV2Report:
        raise ValueError("report must be a TeamSpecialistMarketMemoryPriorityQueueV2Report")
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_public_payload("market memory priority payload", payload)
    return payload


def _normalize_inputs(
    inputs: list[TeamSpecialistMarketMemoryPriorityQueueV2Input]
    | tuple[TeamSpecialistMarketMemoryPriorityQueueV2Input, ...],
) -> tuple[TeamSpecialistMarketMemoryPriorityQueueV2Input, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistMarketMemoryPriorityQueueV2Input:
            raise ValueError("inputs must contain TeamSpecialistMarketMemoryPriorityQueueV2Input values")
        _require_hard_flags("input", row)
        key = (row.team_id, row.specialist_id, row.market_key, row.memory_key)
        if key in seen:
            raise ValueError("inputs must contain unique team, specialist, market, and memory keys")
        seen.add(key)
    return rows


def _validate_input_dates(
    rows: tuple[TeamSpecialistMarketMemoryPriorityQueueV2Input, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if row.lesson_last_validated_at > generated_at:
            raise ValueError("lesson_last_validated_at must be on or before generated_at")


def _priority_row(
    item: TeamSpecialistMarketMemoryPriorityQueueV2Input,
    config: TeamSpecialistMarketMemoryPriorityQueueV2Config,
    generated_at: datetime,
) -> TeamSpecialistMarketMemoryPriorityQueueV2Row:
    lesson_age_days = _age_days(generated_at, item.lesson_last_validated_at)
    stale_lesson_penalty = _stale_lesson_penalty(lesson_age_days, config)
    freshness_score = _clamp_ratio(ONE_RATIO - stale_lesson_penalty)
    priority_score = _priority_score(
        item.market_memory_score,
        item.confidence_score,
        item.feedback_impact_score,
        freshness_score,
        stale_lesson_penalty,
        config,
    )
    status = _queue_status(priority_score, config)
    row_parts = dict(
        queue_rank=Decimal("1"),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        market_key=item.market_key,
        memory_key=item.memory_key,
        observed_at=item.observed_at,
        lesson_last_validated_at=item.lesson_last_validated_at,
        lesson_age_days=lesson_age_days,
        freshness_score=freshness_score,
        stale_lesson_penalty=stale_lesson_penalty,
        market_memory_score=item.market_memory_score,
        confidence_score=item.confidence_score,
        feedback_impact_score=item.feedback_impact_score,
        priority_score=priority_score,
        queue_status=status,
        public_evidence_refs=item.public_evidence_refs,
        reason_codes=_row_reason_codes(
            status,
            item.market_memory_score,
            item.confidence_score,
            item.feedback_impact_score,
            stale_lesson_penalty,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistMarketMemoryPriorityQueueV2Row(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _with_rank(
    row: TeamSpecialistMarketMemoryPriorityQueueV2Row,
    queue_rank: Decimal,
) -> TeamSpecialistMarketMemoryPriorityQueueV2Row:
    row_parts = _row_digest_parts(row)
    row_parts["queue_rank"] = queue_rank
    return TeamSpecialistMarketMemoryPriorityQueueV2Row(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _priority_score(
    market_memory_score: Decimal,
    confidence_score: Decimal,
    feedback_impact_score: Decimal,
    freshness_score: Decimal,
    stale_lesson_penalty: Decimal,
    config: TeamSpecialistMarketMemoryPriorityQueueV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            market_memory_score * config.market_memory_weight
            + confidence_score * config.confidence_weight
            + feedback_impact_score * config.feedback_impact_weight
            + freshness_score * config.freshness_weight
            - stale_lesson_penalty * config.stale_lesson_penalty_weight,
        )


def _stale_lesson_penalty(
    lesson_age_days: Decimal,
    config: TeamSpecialistMarketMemoryPriorityQueueV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(lesson_age_days / config.max_lesson_age_days)


def _queue_status(
    priority_score: Decimal,
    config: TeamSpecialistMarketMemoryPriorityQueueV2Config,
) -> str:
    if priority_score >= config.urgent_priority_score:
        return "urgent"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "clear"


def _row_reason_codes(
    status: str,
    market_memory_score: Decimal,
    confidence_score: Decimal,
    feedback_impact_score: Decimal,
    stale_lesson_penalty: Decimal,
) -> tuple[str, ...]:
    codes: set[str] = {f"market_memory_priority_{status}"}
    if market_memory_score >= Decimal("0.750000"):
        codes.add("memory_signal_strong")
    elif market_memory_score >= Decimal("0.500000"):
        codes.add("memory_signal_watch")
    if confidence_score >= Decimal("0.750000"):
        codes.add("confidence_signal_strong")
    elif confidence_score >= Decimal("0.500000"):
        codes.add("confidence_signal_watch")
    if feedback_impact_score >= Decimal("0.500000"):
        codes.add("feedback_impact_boost")
    if stale_lesson_penalty >= Decimal("0.500000"):
        codes.add("stale_lesson_penalty")
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistMarketMemoryPriorityQueueV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_memory_priority_empty",)
    codes = {f"market_memory_priority_{_report_status(rows)}"}
    for row in rows:
        if "feedback_impact_boost" in row.reason_codes:
            codes.add("feedback_impact_boost")
        if "stale_lesson_penalty" in row.reason_codes:
            codes.add("stale_lesson_penalty")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _report_status(rows: tuple[TeamSpecialistMarketMemoryPriorityQueueV2Row, ...]) -> str:
    if not rows:
        return "clear"
    if any(row.queue_status == "urgent" for row in rows):
        return "urgent"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _priority_row_sort_key(
    row: TeamSpecialistMarketMemoryPriorityQueueV2Row,
) -> tuple[int, Decimal, Decimal, str, str, str, str]:
    return (
        -_status_rank(row.queue_status),
        -row.priority_score,
        -row.feedback_impact_score,
        row.team_id,
        row.specialist_id,
        row.market_key,
        row.memory_key,
    )


def _status_rank(status: str) -> int:
    if status == "urgent":
        return 2
    if status == "watch":
        return 1
    return 0


def _average_priority_score(
    rows: tuple[TeamSpecialistMarketMemoryPriorityQueueV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.priority_score for row in rows), ZERO_RATIO) / Decimal(len(rows)),
        )


def _top_priority_score(rows: tuple[TeamSpecialistMarketMemoryPriorityQueueV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.priority_score for row in rows).quantize(RATIO_QUANTUM)


def _validate_report(report: TeamSpecialistMarketMemoryPriorityQueueV2Report) -> None:
    if report.item_count != _count(len(report.priority_rows)):
        raise ValueError("item_count must match priority_rows")
    if report.urgent_count != _count(sum(1 for row in report.priority_rows if row.queue_status == "urgent")):
        raise ValueError("urgent_count must match priority_rows")
    if report.watch_count != _count(sum(1 for row in report.priority_rows if row.queue_status == "watch")):
        raise ValueError("watch_count must match priority_rows")
    if report.clear_count != _count(sum(1 for row in report.priority_rows if row.queue_status == "clear")):
        raise ValueError("clear_count must match priority_rows")
    if report.average_priority_score != _average_priority_score(report.priority_rows):
        raise ValueError("average_priority_score must match priority_rows")
    if report.top_priority_score != _top_priority_score(report.priority_rows):
        raise ValueError("top_priority_score must match priority_rows")
    if report.status != _report_status(report.priority_rows):
        raise ValueError("status must match priority_rows")
    if report.reason_codes != _report_reason_codes(report.priority_rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.priority_rows != tuple(sorted(report.priority_rows, key=_priority_row_sort_key)):
        raise ValueError("priority_rows must use deterministic sequence")


def _normalize_priority_rows(
    rows: tuple[TeamSpecialistMarketMemoryPriorityQueueV2Row, ...],
) -> tuple[TeamSpecialistMarketMemoryPriorityQueueV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("priority_rows must be a tuple")
    for row in rows:
        if type(row) is not TeamSpecialistMarketMemoryPriorityQueueV2Row:
            raise ValueError("priority_rows must contain TeamSpecialistMarketMemoryPriorityQueueV2Row values")
        _require_hard_flags("priority row", row)
        if row.derived_validation_digest != _row_digest(row):
            raise ValueError("derived_validation_digest must match row fields")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    expected = tuple(code for code in allowed_reason_codes if code in seen)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _normalize_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = []
    seen: set[str] = set()
    for item in value:
        _require_public_string(field_name, item)
        if not item.startswith(SAFE_REF_PREFIXES):
            raise ValueError(f"{field_name} contains an unsupported public reference")
        if item not in seen:
            normalized.append(item)
            seen.add(item)
    return tuple(normalized)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    value = _normalize_count(field_name, value)
    if value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(RATIO_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        value = ZERO_RATIO
    if value > ONE_RATIO:
        value = ONE_RATIO
    return value.quantize(RATIO_QUANTUM)


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        if sum(values, ZERO_RATIO).quantize(RATIO_QUANTUM) != ONE_RATIO:
            raise ValueError("positive priority weights must sum to 1")


def _require_status(field_name: str, value: object) -> None:
    if value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or urgent")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_text(field_name, value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _row_digest(row: TeamSpecialistMarketMemoryPriorityQueueV2Row) -> str:
    return _digest_public(_row_digest_parts(row))


def _report_digest(report: TeamSpecialistMarketMemoryPriorityQueueV2Report) -> str:
    return _digest_public(_report_digest_parts(report))


def _row_digest_parts(row: TeamSpecialistMarketMemoryPriorityQueueV2Row) -> dict[str, object]:
    return {
        "queue_rank": row.queue_rank,
        "team_id": row.team_id,
        "specialist_id": row.specialist_id,
        "market_key": row.market_key,
        "memory_key": row.memory_key,
        "observed_at": row.observed_at,
        "lesson_last_validated_at": row.lesson_last_validated_at,
        "lesson_age_days": row.lesson_age_days,
        "freshness_score": row.freshness_score,
        "stale_lesson_penalty": row.stale_lesson_penalty,
        "market_memory_score": row.market_memory_score,
        "confidence_score": row.confidence_score,
        "feedback_impact_score": row.feedback_impact_score,
        "priority_score": row.priority_score,
        "queue_status": row.queue_status,
        "public_evidence_refs": row.public_evidence_refs,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_parts(report: TeamSpecialistMarketMemoryPriorityQueueV2Report) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "item_count": report.item_count,
        "urgent_count": report.urgent_count,
        "watch_count": report.watch_count,
        "clear_count": report.clear_count,
        "average_priority_score": report.average_priority_score,
        "top_priority_score": report.top_priority_score,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "priority_rows": report.priority_rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _digest_public(values: object) -> str:
    payload = _json_ready(values)
    _reject_public_payload("derived validation digest payload", payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("payload contains a non-Decimal public number")
    if type(value) is float:
        raise ValueError("payload contains a non-Decimal public number")
    raise ValueError("payload contains unsupported value")


def _reject_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            try:
                _reject_public_text(label, key)
            except ValueError as exc:
                raise ValueError(f"unsafe public payload in {label}") from exc
            _reject_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_public_text(label, value)
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")


def _reject_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(block in normalized for block in PUBLIC_TEXT_BLOCKS):
        raise ValueError(f"unsafe public value in {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_days(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days)
            + Decimal(delta.seconds) / SECONDS_PER_DAY
            + Decimal(delta.microseconds) / Decimal("86400000000")
        ).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)
