"""Public-safe event team assignment confidence report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVENT_TEAM_ASSIGNMENT_CONFIDENCE_CONFIG_VERSION = (
    "research-strategy-event-team-assignment-confidence-report-v0"
)
ASSIGNMENT_CONFIDENCE_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SCORE_COMPONENT_COUNT = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

PAPER_ACTION_BY_STATUS = {
    "pass": "paper_assignment_confidence_monitor",
    "watch": "paper_assignment_confidence_watch",
    "block": "paper_assignment_confidence_block",
}
REASON_SEQUENCE = (
    "assignment_confidence_block",
    "assignment_confidence_score_block",
    "evidence_coverage_block",
    "independence_block",
    "team_domain_fit_block",
    "workload_headroom_block",
    "calibration_memory_block",
    "assignment_confidence_watch",
    "assignment_confidence_score_watch",
    "evidence_coverage_watch",
    "independence_watch",
    "team_domain_fit_watch",
    "workload_headroom_watch",
    "calibration_memory_watch",
    "assignment_confidence_pass",
)
REPORT_REASON_SEQUENCE = (
    "assignment_confidence_no_events",
    *REASON_SEQUENCE,
)
UNSAFE_PAYLOAD_KEYS = frozenset(
    (
        "candidate_id",
        "candidate_key",
        "raw_candidate_id",
        "market_id",
        "market_key",
        "raw_market_id",
        "market_slug",
        "slug",
        "question",
        "market_question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "order_ticket",
        "trade",
        "sizing",
        "recommendation",
        "live",
    ),
)
UNSAFE_PAYLOAD_VALUE_FRAGMENTS = frozenset(
    (
        "raw-candidate",
        "raw-market",
        "market-slug",
        "private question",
        "example.test",
        "super-secret",
        "source text",
        "candidate",
        "market",
        "slug",
        "question",
        "https://",
        "http://",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "sizing",
        "recommendation",
        " live ",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVENT_TEAM_ASSIGNMENT_CONFIDENCE_CONFIG_VERSION",
    "ASSIGNMENT_CONFIDENCE_STATUSES",
    "ResearchStrategyEventTeamAssignmentConfidenceConfig",
    "ResearchStrategyEventTeamAssignmentConfidenceInput",
    "ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount",
    "ResearchStrategyEventTeamAssignmentConfidenceReport",
    "ResearchStrategyEventTeamAssignmentConfidenceRow",
    "build_research_strategy_event_team_assignment_confidence_report",
    "research_strategy_event_team_assignment_confidence_report_digest",
    "research_strategy_event_team_assignment_confidence_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchStrategyEventTeamAssignmentConfidenceConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_TEAM_ASSIGNMENT_CONFIDENCE_CONFIG_VERSION
    )
    min_pass_confidence_score: Decimal = Decimal("0.750000")
    min_watch_confidence_score: Decimal = Decimal("0.550000")
    min_pass_component_score: Decimal = Decimal("0.700000")
    min_watch_component_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventTeamAssignmentConfidenceConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_TEAM_ASSIGNMENT_CONFIDENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_confidence_score",
            "min_watch_confidence_score",
            "min_pass_component_score",
            "min_watch_component_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_confidence_score > self.min_pass_confidence_score:
            raise ValueError(
                "min_watch_confidence_score must be at most "
                "min_pass_confidence_score",
            )
        if self.min_watch_component_score > self.min_pass_component_score:
            raise ValueError(
                "min_watch_component_score must be at most min_pass_component_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventTeamAssignmentConfidenceInput(_FinalDataclass):
    raw_candidate_id: str
    raw_market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    domain_label: str
    assigned_team_label: str
    assignment_confidence_score: Decimal
    evidence_coverage_score: Decimal
    independence_score: Decimal
    team_domain_fit_score: Decimal
    workload_headroom_score: Decimal
    calibration_memory_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventTeamAssignmentConfidenceInput,
            "input",
        )
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_raw_string(field_name, getattr(self, field_name))
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("assigned_team_label", self.assigned_team_label)
        for field_name in (
            "assignment_confidence_score",
            "evidence_coverage_score",
            "independence_score",
            "team_domain_fit_score",
            "workload_headroom_score",
            "calibration_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=False),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEventTeamAssignmentConfidenceRow(_FinalDataclass):
    assignment_rank: Decimal
    event_ref: str
    domain_label: str
    assigned_team_label: str
    status: str
    confidence_score: Decimal
    confidence_shortfall_score: Decimal
    assignment_confidence_score: Decimal
    evidence_coverage_score: Decimal
    independence_score: Decimal
    team_domain_fit_score: Decimal
    workload_headroom_score: Decimal
    calibration_memory_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventTeamAssignmentConfidenceRow,
            "row",
        )
        object.__setattr__(
            self,
            "assignment_rank",
            _require_count_decimal("assignment_rank", self.assignment_rank),
        )
        _require_public_string("event_ref", self.event_ref)
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("assigned_team_label", self.assigned_team_label)
        _require_status("status", self.status)
        for field_name in (
            "confidence_score",
            "confidence_shortfall_score",
            "assignment_confidence_score",
            "evidence_coverage_score",
            "independence_score",
            "team_domain_fit_score",
            "workload_headroom_score",
            "calibration_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyEventTeamAssignmentConfidenceReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    avg_confidence_score: Decimal
    avg_evidence_coverage_score: Decimal
    avg_team_domain_fit_score: Decimal
    max_confidence_shortfall_score: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyEventTeamAssignmentConfidenceRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventTeamAssignmentConfidenceReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_TEAM_ASSIGNMENT_CONFIDENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "avg_confidence_score",
            "avg_evidence_coverage_score",
            "avg_team_domain_fit_score",
            "max_confidence_shortfall_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_event_team_assignment_confidence_report(
    inputs: Iterable[ResearchStrategyEventTeamAssignmentConfidenceInput],
    *,
    config: ResearchStrategyEventTeamAssignmentConfidenceConfig,
    generated_at: datetime,
) -> ResearchStrategyEventTeamAssignmentConfidenceReport:
    _require_exact_type(
        config,
        ResearchStrategyEventTeamAssignmentConfidenceConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "event_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "avg_confidence_score": _avg_decimal(
            tuple(row.confidence_score for row in rows),
        ),
        "avg_evidence_coverage_score": _avg_decimal(
            tuple(row.evidence_coverage_score for row in rows),
        ),
        "avg_team_domain_fit_score": _avg_decimal(
            tuple(row.team_domain_fit_score for row in rows),
        ),
        "max_confidence_shortfall_score": _max_decimal(
            tuple(row.confidence_shortfall_score for row in rows),
        ),
        "status": status,
        "paper_queue_action": PAPER_ACTION_BY_STATUS[status],
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEventTeamAssignmentConfidenceReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_strategy_event_team_assignment_confidence_report_payload(
    report: ResearchStrategyEventTeamAssignmentConfidenceReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchStrategyEventTeamAssignmentConfidenceReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyEventTeamAssignmentConfidenceReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_public_numeric_primitives(payload)
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    _ensure_json_safe(payload)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_strategy_event_team_assignment_confidence_report_digest(
    report: ResearchStrategyEventTeamAssignmentConfidenceReport | Mapping[str, object],
) -> str:
    payload = research_strategy_event_team_assignment_confidence_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchStrategyEventTeamAssignmentConfidenceInput,
    config: ResearchStrategyEventTeamAssignmentConfidenceConfig,
) -> ResearchStrategyEventTeamAssignmentConfidenceRow:
    confidence_score = _confidence_score(item)
    reason_codes = _row_reason_codes(
        item=item,
        confidence_score=confidence_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchStrategyEventTeamAssignmentConfidenceRow(
        assignment_rank=ONE,
        event_ref=_event_ref(item),
        domain_label=item.domain_label,
        assigned_team_label=item.assigned_team_label,
        status=status,
        confidence_score=confidence_score,
        confidence_shortfall_score=_confidence_shortfall(confidence_score, config),
        assignment_confidence_score=item.assignment_confidence_score,
        evidence_coverage_score=item.evidence_coverage_score,
        independence_score=item.independence_score,
        team_domain_fit_score=item.team_domain_fit_score,
        workload_headroom_score=item.workload_headroom_score,
        calibration_memory_score=item.calibration_memory_score,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchStrategyEventTeamAssignmentConfidenceRow,
    rank: int,
) -> ResearchStrategyEventTeamAssignmentConfidenceRow:
    return ResearchStrategyEventTeamAssignmentConfidenceRow(
        assignment_rank=_count(rank),
        event_ref=row.event_ref,
        domain_label=row.domain_label,
        assigned_team_label=row.assigned_team_label,
        status=row.status,
        confidence_score=row.confidence_score,
        confidence_shortfall_score=row.confidence_shortfall_score,
        assignment_confidence_score=row.assignment_confidence_score,
        evidence_coverage_score=row.evidence_coverage_score,
        independence_score=row.independence_score,
        team_domain_fit_score=row.team_domain_fit_score,
        workload_headroom_score=row.workload_headroom_score,
        calibration_memory_score=row.calibration_memory_score,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _confidence_score(
    item: ResearchStrategyEventTeamAssignmentConfidenceInput,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.assignment_confidence_score
            + item.evidence_coverage_score
            + item.independence_score
            + item.team_domain_fit_score
            + item.workload_headroom_score
            + item.calibration_memory_score
        ) / SCORE_COMPONENT_COUNT
    return _clamp_ratio(score)


def _confidence_shortfall(
    confidence_score: Decimal,
    config: ResearchStrategyEventTeamAssignmentConfidenceConfig,
) -> Decimal:
    return _clamp_ratio(config.min_pass_confidence_score - confidence_score)


def _row_reason_codes(
    *,
    item: ResearchStrategyEventTeamAssignmentConfidenceInput,
    confidence_score: Decimal,
    config: ResearchStrategyEventTeamAssignmentConfidenceConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_threshold_reason(
        reasons,
        metric=item.assignment_confidence_score,
        watch=config.min_pass_confidence_score,
        block=config.min_watch_confidence_score,
        watch_code="assignment_confidence_score_watch",
        block_code="assignment_confidence_score_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.evidence_coverage_score,
        watch=config.min_pass_component_score,
        block=config.min_watch_component_score,
        watch_code="evidence_coverage_watch",
        block_code="evidence_coverage_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.independence_score,
        watch=config.min_pass_component_score,
        block=config.min_watch_component_score,
        watch_code="independence_watch",
        block_code="independence_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.team_domain_fit_score,
        watch=config.min_pass_component_score,
        block=config.min_watch_component_score,
        watch_code="team_domain_fit_watch",
        block_code="team_domain_fit_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.workload_headroom_score,
        watch=config.min_pass_component_score,
        block=config.min_watch_component_score,
        watch_code="workload_headroom_watch",
        block_code="workload_headroom_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.calibration_memory_score,
        watch=config.min_pass_component_score,
        block=config.min_watch_component_score,
        watch_code="calibration_memory_watch",
        block_code="calibration_memory_block",
    )
    for reason_code in item.reason_codes:
        reasons.append(f"input_{reason_code}")

    metric_status = _metric_status(reasons, confidence_score, config)
    reasons.insert(0, f"assignment_confidence_{metric_status}")
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
        return
    if metric < watch:
        reasons.append(watch_code)


def _metric_status(
    reasons: tuple[str, ...] | list[str],
    confidence_score: Decimal,
    config: ResearchStrategyEventTeamAssignmentConfidenceConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reasons):
        return "block"
    if confidence_score < config.min_watch_confidence_score:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reasons):
        return "watch"
    if confidence_score < config.min_pass_confidence_score:
        return "watch"
    return "pass"


def _event_ref(item: ResearchStrategyEventTeamAssignmentConfidenceInput) -> str:
    value = "|".join((item.raw_candidate_id, item.raw_market_id, item.market_slug))
    digest = sha256(value.encode("utf-8")).hexdigest()
    return f"event_ref_{digest}"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "assignment_confidence_block" in reason_codes:
        return "block"
    if "assignment_confidence_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyEventTeamAssignmentConfidenceRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(
    row: ResearchStrategyEventTeamAssignmentConfidenceRow,
) -> tuple[int, Decimal, str, str]:
    return (
        _status_rank(row.status),
        -row.confidence_shortfall_score,
        row.assigned_team_label,
        row.event_ref,
    )


def _status_rank(status: str) -> int:
    return {"block": 0, "watch": 1, "pass": 2}[status]


def _status_count(
    rows: tuple[ResearchStrategyEventTeamAssignmentConfidenceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventTeamAssignmentConfidenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("assignment_confidence_no_events",)
    reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(sorted(reason_codes, key=_reason_sort_key))


def _reason_code_counts(
    rows: tuple[ResearchStrategyEventTeamAssignmentConfidenceRow, ...],
) -> tuple[ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount, ...]:
    if not rows:
        return ()
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            event_ratio=_ratio(_count(counter[reason_code]), total),
        )
        for reason_code in sorted(counter, key=_reason_sort_key)
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyEventTeamAssignmentConfidenceInput],
) -> tuple[ResearchStrategyEventTeamAssignmentConfidenceInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        if type(item) is not ResearchStrategyEventTeamAssignmentConfidenceInput:
            raise ValueError(
                "inputs must contain "
                "ResearchStrategyEventTeamAssignmentConfidenceInput",
            )
        _require_hard_flags("input", item)
        key = (item.raw_candidate_id, item.raw_market_id, item.market_slug)
        if key in seen:
            raise ValueError("raw event keys must be unique")
        seen.add(key)
    return items


def _require_rows(
    rows: tuple[ResearchStrategyEventTeamAssignmentConfidenceRow, ...],
) -> tuple[ResearchStrategyEventTeamAssignmentConfidenceRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    event_refs: set[str] = set()
    expected_ranks = tuple(_count(index) for index in range(1, len(normalized) + 1))
    if tuple(row.assignment_rank for row in normalized) != expected_ranks:
        raise ValueError("assignment_rank values must be sequential")
    for row in normalized:
        if type(row) is not ResearchStrategyEventTeamAssignmentConfidenceRow:
            raise ValueError(
                "rows must contain ResearchStrategyEventTeamAssignmentConfidenceRow",
            )
        _require_hard_flags("row", row)
        if row.event_ref in event_refs:
            raise ValueError("event_ref values must be unique")
        event_refs.add(row.event_ref)
    return normalized


def _require_reason_code_counts(
    value: tuple[ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount, ...],
) -> tuple[ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(value)
    expected = tuple(sorted(normalized, key=lambda item: _reason_sort_key(item.reason_code)))
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    reason_codes: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEventTeamAssignmentConfidenceReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in reason_codes:
            raise ValueError("reason_code_counts must be unique")
        reason_codes.add(item.reason_code)
    return normalized


def _require_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    reason_codes = _require_reason_codes(value, require_nonempty=True)
    expected = tuple(sorted(reason_codes, key=_reason_sort_key))
    if reason_codes != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return reason_codes


def _validate_row(row: ResearchStrategyEventTeamAssignmentConfidenceRow) -> None:
    expected_score = _clamp_ratio(
        (
            row.assignment_confidence_score
            + row.evidence_coverage_score
            + row.independence_score
            + row.team_domain_fit_score
            + row.workload_headroom_score
            + row.calibration_memory_score
        )
        / SCORE_COMPONENT_COUNT,
    )
    if row.confidence_score != expected_score:
        raise ValueError("confidence_score must match assignment confidence components")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchStrategyEventTeamAssignmentConfidenceReport,
) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.avg_confidence_score != _avg_decimal(
        tuple(row.confidence_score for row in rows),
    ):
        raise ValueError("avg_confidence_score must match rows")
    if report.avg_evidence_coverage_score != _avg_decimal(
        tuple(row.evidence_coverage_score for row in rows),
    ):
        raise ValueError("avg_evidence_coverage_score must match rows")
    if report.avg_team_domain_fit_score != _avg_decimal(
        tuple(row.team_domain_fit_score for row in rows),
    ):
        raise ValueError("avg_team_domain_fit_score must match rows")
    if report.max_confidence_shortfall_score != _max_decimal(
        tuple(row.confidence_shortfall_score for row in rows),
    ):
        raise ValueError("max_confidence_shortfall_score must match rows")


def _report_values_without_digest(
    report: ResearchStrategyEventTeamAssignmentConfidenceReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        raise ValueError("public payload must not contain floats")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _avg_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    return total.quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            return ZERO
        if value > ONE:
            return ONE
        return value.quantize(QUANTUM)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return value.quantize(QUANTUM)


def _require_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    quantized = value.quantize(QUANTUM)
    if quantized != value:
        raise ValueError(f"{name} must use six decimal places or fewer")
    return quantized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be UTC")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in ASSIGNMENT_CONFIDENCE_STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")
    return value


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_raw_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    return value


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if _contains_unsafe_value(value):
        raise ValueError(f"{name} contains unsafe public value")
    return value


def _require_public_label(name: str, value: object) -> str:
    text = _require_public_string(name, value)
    if PUBLIC_LABEL_RE.fullmatch(text) is None:
        raise ValueError(f"{name} must be a public label")
    return text


def _require_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(_require_reason_code(item) for item in value)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(reason_codes, key=_reason_sort_key))


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if not value or value.strip() != value or value.lower() != value:
        raise ValueError("reason_codes must contain canonical lowercase strings")
    if _contains_unsafe_value(value):
        raise ValueError("reason_codes contain unsafe public value")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError("reason_codes must contain canonical reason code strings")
    return value


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REPORT_REASON_SEQUENCE:
        return (REPORT_REASON_SEQUENCE.index(reason_code), reason_code)
    if reason_code in REASON_SEQUENCE:
        return (REASON_SEQUENCE.index(reason_code), reason_code)
    return (len(REPORT_REASON_SEQUENCE), reason_code)


def _require_sha256(name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    if value.lower() != value or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_public_numeric_primitives(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_primitives(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_primitives(item)
        return
    if type(value) in (int, float):
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("public payload values must be JSON-safe")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must use concrete public payload containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            normalized_key = key.lower()
            if key in UNSAFE_PAYLOAD_KEYS or any(
                fragment == normalized_key for fragment in UNSAFE_PAYLOAD_KEYS
            ):
                raise ValueError(f"unsafe public surface in {label}: {key}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _contains_unsafe_value(value):
        raise ValueError(f"unsafe public surface in {label}")


def _contains_unsafe_value(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PAYLOAD_VALUE_FRAGMENTS)


def _ensure_json_safe(value: object) -> None:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("public payload values must be JSON-safe") from exc
