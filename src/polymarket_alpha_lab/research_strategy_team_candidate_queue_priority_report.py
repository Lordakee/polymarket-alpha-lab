"""Team candidate queue priority report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_CANDIDATE_QUEUE_PRIORITY_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchStrategyTeamCandidateQueuePriorityConfig",
    "ResearchStrategyTeamCandidateQueuePriorityInput",
    "ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount",
    "ResearchStrategyTeamCandidateQueuePriorityReport",
    "ResearchStrategyTeamCandidateQueuePriorityRow",
    "build_research_strategy_team_candidate_queue_priority_report",
    "research_strategy_team_candidate_queue_priority_report_digest",
    "research_strategy_team_candidate_queue_priority_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_TEAM_CANDIDATE_QUEUE_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-strategy-team-candidate-queue-priority-report-v0"
)
STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "team_candidate_queue_priority_empty"
PUBLIC_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("raw", "_candidate", "_id"),
    _join_parts("queue", "_key"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("pri", "vate", "_to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("posi", "tion", "_si", "ze"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
    _join_parts("rec", "ommend"),
    _join_parts("siz", "ing"),
    _join_parts("au", "th"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("req", "uests"),
    _join_parts("ht", "tp"),
    _join_parts("so", "cket"),
    _join_parts("sub", "process"),
    _join_parts("sec", "ret"),
    _join_parts("api", "_key"),
    "://",
)
REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "team_candidate_queue_priority_evidence_completeness_block",
    "team_candidate_queue_priority_source_freshness_block",
    "team_candidate_queue_priority_team_coverage_block",
    "team_candidate_queue_priority_queue_age_block",
    "team_candidate_queue_priority_review_load_block",
    "team_candidate_queue_priority_evidence_completeness_watch",
    "team_candidate_queue_priority_source_freshness_watch",
    "team_candidate_queue_priority_team_coverage_watch",
    "team_candidate_queue_priority_queue_age_watch",
    "team_candidate_queue_priority_review_load_watch",
    "team_candidate_queue_priority_clear",
)
REPORT_REASON_PRIORITY = (
    "team_candidate_queue_priority_block",
    "team_candidate_queue_priority_watch",
    "team_candidate_queue_priority_pass",
    *REASON_CODE_SEQUENCE,
)
REASON_CODE_RANK = {
    reason_code: index for index, reason_code in enumerate(REPORT_REASON_PRIORITY)
}


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyTeamCandidateQueuePriorityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_CANDIDATE_QUEUE_PRIORITY_REPORT_CONFIG_VERSION
    )
    evidence_completeness_pass_floor: Decimal = Decimal("0.800000")
    evidence_completeness_block_floor: Decimal = Decimal("0.600000")
    source_freshness_pass_floor: Decimal = Decimal("0.800000")
    source_freshness_block_floor: Decimal = Decimal("0.600000")
    team_coverage_pass_floor: Decimal = Decimal("0.800000")
    team_coverage_block_floor: Decimal = Decimal("0.600000")
    queue_age_watch_seconds: Decimal = Decimal("86400.000000")
    queue_age_block_seconds: Decimal = Decimal("172800.000000")
    review_load_watch: Decimal = Decimal("0.400000")
    review_load_block: Decimal = Decimal("0.750000")
    resolution_learning_priority_cap: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamCandidateQueuePriorityConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_CANDIDATE_QUEUE_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_completeness_pass_floor",
            "evidence_completeness_block_floor",
            "source_freshness_pass_floor",
            "source_freshness_block_floor",
            "team_coverage_pass_floor",
            "team_coverage_block_floor",
            "review_load_watch",
            "review_load_block",
            "resolution_learning_priority_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("queue_age_watch_seconds", "queue_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_completeness_pass_floor",
            self.evidence_completeness_pass_floor,
            self.evidence_completeness_block_floor,
        )
        _require_at_least(
            "source_freshness_pass_floor",
            self.source_freshness_pass_floor,
            self.source_freshness_block_floor,
        )
        _require_at_least(
            "team_coverage_pass_floor",
            self.team_coverage_pass_floor,
            self.team_coverage_block_floor,
        )
        _require_at_most(
            "queue_age_watch_seconds",
            self.queue_age_watch_seconds,
            self.queue_age_block_seconds,
        )
        _require_at_most(
            "review_load_watch",
            self.review_load_watch,
            self.review_load_block,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamCandidateQueuePriorityInput(_FinalPublicDataclass):
    queue_key: str
    team_bucket: str
    candidate_bucket: str
    queued_at: datetime
    last_reviewed_at: datetime | None
    evidence_completeness_score: Decimal
    source_freshness_score: Decimal
    team_coverage_score: Decimal
    resolution_learning_score: Decimal
    review_load_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamCandidateQueuePriorityInput,
            "input",
        )
        for field_name in ("queue_key", "team_bucket", "candidate_bucket"):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "last_reviewed_at",
            _as_optional_utc("last_reviewed_at", self.last_reviewed_at),
        )
        for field_name in (
            "evidence_completeness_score",
            "source_freshness_score",
            "team_coverage_score",
            "resolution_learning_score",
            "review_load_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.last_reviewed_at is not None and self.last_reviewed_at < self.queued_at:
            raise ValueError("last_reviewed_at must not be before queued_at")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamCandidateQueuePriorityRow(_FinalPublicDataclass):
    queue_rank: Decimal
    public_candidate_digest: str
    team_bucket: str
    candidate_bucket: str
    status: str
    queue_priority_score: Decimal
    queue_age_seconds: Decimal
    evidence_completeness_score: Decimal
    source_freshness_score: Decimal
    team_coverage_score: Decimal
    resolution_learning_score: Decimal
    review_load_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamCandidateQueuePriorityRow, "row")
        object.__setattr__(
            self,
            "queue_rank",
            _normalize_positive_count("queue_rank", self.queue_rank),
        )
        _require_public_digest("public_candidate_digest", self.public_candidate_digest)
        for field_name in ("team_bucket", "candidate_bucket"):
            _require_public_text(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        for field_name in (
            "queue_priority_score",
            "evidence_completeness_score",
            "source_freshness_score",
            "team_coverage_score",
            "resolution_learning_score",
            "review_load_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_age_seconds",
            _normalize_nonnegative_decimal("queue_age_seconds", self.queue_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_text("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must use supported diagnostics")
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyTeamCandidateQueuePriorityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    queue_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    evidence_completeness_attention_count: Decimal
    source_freshness_attention_count: Decimal
    team_coverage_attention_count: Decimal
    queue_age_attention_count: Decimal
    review_load_attention_count: Decimal
    mean_evidence_completeness_score: Decimal
    mean_source_freshness_score: Decimal
    mean_team_coverage_score: Decimal
    mean_resolution_learning_score: Decimal
    mean_review_load_score: Decimal
    mean_queue_priority_score: Decimal
    max_queue_priority_score: Decimal
    max_queue_age_seconds: Decimal
    max_review_load_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamCandidateQueuePriorityReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "queue_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "evidence_completeness_attention_count",
            "source_freshness_attention_count",
            "team_coverage_attention_count",
            "queue_age_attention_count",
            "review_load_attention_count",
            "max_queue_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_completeness_score",
            "mean_source_freshness_score",
            "mean_team_coverage_score",
            "mean_resolution_learning_score",
            "mean_review_load_score",
            "mean_queue_priority_score",
            "max_queue_priority_score",
            "max_review_load_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_public_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _computed_report_digest(self):
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_team_candidate_queue_priority_report(
    candidates: Iterable[ResearchStrategyTeamCandidateQueuePriorityInput],
    *,
    config: ResearchStrategyTeamCandidateQueuePriorityConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamCandidateQueuePriorityReport:
    if type(config) is not ResearchStrategyTeamCandidateQueuePriorityConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamCandidateQueuePriorityConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    _validate_input_times(inputs, generated_at_utc)
    row_values = sorted(
        (
            _row_values_for_input(value, config=config, generated_at=generated_at_utc)
            for value in inputs
        ),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchStrategyTeamCandidateQueuePriorityReport(
        **values,
        derived_validation_digest=_digest_from_mapping(values),
    )


def research_strategy_team_candidate_queue_priority_report_digest(
    report: ResearchStrategyTeamCandidateQueuePriorityReport,
) -> str:
    payload = research_strategy_team_candidate_queue_priority_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def research_strategy_team_candidate_queue_priority_report_payload(
    report: ResearchStrategyTeamCandidateQueuePriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyTeamCandidateQueuePriorityReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamCandidateQueuePriorityReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    if report.derived_validation_digest != _computed_report_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    if payload["derived_validation_digest"] != _digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


@dataclass(frozen=True)
class _RowValues:
    public_candidate_digest: str
    team_bucket: str
    candidate_bucket: str
    status: str
    queue_priority_score: Decimal
    queue_age_seconds: Decimal
    evidence_completeness_score: Decimal
    source_freshness_score: Decimal
    team_coverage_score: Decimal
    resolution_learning_score: Decimal
    review_load_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_for_input(
    value: ResearchStrategyTeamCandidateQueuePriorityInput,
    *,
    config: ResearchStrategyTeamCandidateQueuePriorityConfig,
    generated_at: datetime,
) -> _RowValues:
    queue_age_seconds = _duration_seconds(value.queued_at, generated_at)
    reason_codes = _row_reason_codes(
        value,
        queue_age_seconds=queue_age_seconds,
        config=config,
    )
    return _RowValues(
        public_candidate_digest=_public_hash(value.queue_key),
        team_bucket=value.team_bucket,
        candidate_bucket=value.candidate_bucket,
        status=_row_status(reason_codes),
        queue_priority_score=_queue_priority_score(
            value,
            queue_age_seconds=queue_age_seconds,
            config=config,
        ),
        queue_age_seconds=queue_age_seconds,
        evidence_completeness_score=value.evidence_completeness_score,
        source_freshness_score=value.source_freshness_score,
        team_coverage_score=value.team_coverage_score,
        resolution_learning_score=value.resolution_learning_score,
        review_load_score=value.review_load_score,
        reason_codes=reason_codes,
    )


def _row_from_values(
    queue_rank: Decimal,
    values: _RowValues,
) -> ResearchStrategyTeamCandidateQueuePriorityRow:
    return ResearchStrategyTeamCandidateQueuePriorityRow(
        queue_rank=queue_rank,
        public_candidate_digest=values.public_candidate_digest,
        team_bucket=values.team_bucket,
        candidate_bucket=values.candidate_bucket,
        status=values.status,
        queue_priority_score=values.queue_priority_score,
        queue_age_seconds=values.queue_age_seconds,
        evidence_completeness_score=values.evidence_completeness_score,
        source_freshness_score=values.source_freshness_score,
        team_coverage_score=values.team_coverage_score,
        resolution_learning_score=values.resolution_learning_score,
        review_load_score=values.review_load_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    value: ResearchStrategyTeamCandidateQueuePriorityInput,
    *,
    queue_age_seconds: Decimal,
    config: ResearchStrategyTeamCandidateQueuePriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_score_floor_reason(
        reason_codes,
        "evidence_completeness",
        value.evidence_completeness_score,
        config.evidence_completeness_pass_floor,
        config.evidence_completeness_block_floor,
    )
    _append_score_floor_reason(
        reason_codes,
        "source_freshness",
        value.source_freshness_score,
        config.source_freshness_pass_floor,
        config.source_freshness_block_floor,
    )
    _append_score_floor_reason(
        reason_codes,
        "team_coverage",
        value.team_coverage_score,
        config.team_coverage_pass_floor,
        config.team_coverage_block_floor,
    )
    _append_ceiling_reason(
        reason_codes,
        "queue_age",
        queue_age_seconds,
        config.queue_age_watch_seconds,
        config.queue_age_block_seconds,
    )
    _append_ceiling_reason(
        reason_codes,
        "review_load",
        value.review_load_score,
        config.review_load_watch,
        config.review_load_block,
    )
    if not reason_codes:
        reason_codes.append("team_candidate_queue_priority_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_score_floor_reason(
    reason_codes: list[str],
    prefix: str,
    score: Decimal,
    pass_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if score < block_floor:
        reason_codes.append(f"team_candidate_queue_priority_{prefix}_block")
    elif score < pass_floor:
        reason_codes.append(f"team_candidate_queue_priority_{prefix}_watch")


def _append_ceiling_reason(
    reason_codes: list[str],
    prefix: str,
    value: Decimal,
    watch: Decimal,
    block: Decimal,
) -> None:
    if value >= block:
        reason_codes.append(f"team_candidate_queue_priority_{prefix}_block")
    elif value >= watch:
        reason_codes.append(f"team_candidate_queue_priority_{prefix}_watch")


def _queue_priority_score(
    value: ResearchStrategyTeamCandidateQueuePriorityInput,
    *,
    queue_age_seconds: Decimal,
    config: ResearchStrategyTeamCandidateQueuePriorityConfig,
) -> Decimal:
    return _max_probability(
        (
            _floor_priority(
                value.evidence_completeness_score,
                config.evidence_completeness_pass_floor,
                config.evidence_completeness_block_floor,
            ),
            _floor_priority(
                value.source_freshness_score,
                config.source_freshness_pass_floor,
                config.source_freshness_block_floor,
            ),
            _floor_priority(
                value.team_coverage_score,
                config.team_coverage_pass_floor,
                config.team_coverage_block_floor,
            ),
            _ratio_to_cap(queue_age_seconds, config.queue_age_block_seconds),
            _ratio_to_cap(value.review_load_score, config.review_load_block),
            _ratio_to_cap(
                value.resolution_learning_score,
                config.resolution_learning_priority_cap,
            ),
        ),
    )


def _floor_priority(score: Decimal, pass_floor: Decimal, block_floor: Decimal) -> Decimal:
    if score >= pass_floor:
        return ZERO
    if score <= block_floor:
        return ONE
    return _clamp_probability((pass_floor - score) / (pass_floor - block_floor))


def _ratio_to_cap(value: Decimal, cap: Decimal) -> Decimal:
    if cap <= ZERO:
        raise ValueError("cap must be positive")
    return _clamp_probability(value / cap)


def _row_values_sort_key(values: _RowValues) -> tuple[object, ...]:
    return (
        -_status_rank(values.status),
        -values.queue_priority_score,
        -values.queue_age_seconds,
        -values.review_load_score,
        values.public_candidate_digest,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_rank(status: str) -> int:
    if status == "block":
        return 2
    if status == "watch":
        return 1
    return 0


def _rollup_status(
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes = [f"team_candidate_queue_priority_{_rollup_status(rows)}"]
    row_reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    reason_codes.extend(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in row_reason_codes
    )
    return _normalize_report_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...],
) -> tuple[ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "queue_item_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "evidence_completeness_attention_count": _kind_count(
            rows,
            "team_candidate_queue_priority_evidence_completeness_",
        ),
        "source_freshness_attention_count": _kind_count(
            rows,
            "team_candidate_queue_priority_source_freshness_",
        ),
        "team_coverage_attention_count": _kind_count(
            rows,
            "team_candidate_queue_priority_team_coverage_",
        ),
        "queue_age_attention_count": _kind_count(
            rows,
            "team_candidate_queue_priority_queue_age_",
        ),
        "review_load_attention_count": _kind_count(
            rows,
            "team_candidate_queue_priority_review_load_",
        ),
        "mean_evidence_completeness_score": _mean(
            tuple(row.evidence_completeness_score for row in rows),
        ),
        "mean_source_freshness_score": _mean(
            tuple(row.source_freshness_score for row in rows),
        ),
        "mean_team_coverage_score": _mean(
            tuple(row.team_coverage_score for row in rows),
        ),
        "mean_resolution_learning_score": _mean(
            tuple(row.resolution_learning_score for row in rows),
        ),
        "mean_review_load_score": _mean(tuple(row.review_load_score for row in rows)),
        "mean_queue_priority_score": _mean(
            tuple(row.queue_priority_score for row in rows),
        ),
        "max_queue_priority_score": _max_probability(
            tuple(row.queue_priority_score for row in rows),
        ),
        "max_queue_age_seconds": _max_decimal(
            tuple(row.queue_age_seconds for row in rows),
        ),
        "max_review_load_score": _max_probability(
            tuple(row.review_load_score for row in rows),
        ),
        "status": _rollup_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    candidates: Iterable[ResearchStrategyTeamCandidateQueuePriorityInput],
) -> tuple[ResearchStrategyTeamCandidateQueuePriorityInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamCandidateQueuePriorityInput:
            raise ValueError(
                "candidates must contain ResearchStrategyTeamCandidateQueuePriorityInput values",
            )
        _require_hard_flags("input", row)
        if row.queue_key in seen_keys:
            raise ValueError("queue_key values must be unique")
        seen_keys.add(row.queue_key)
    return rows


def _validate_input_times(
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.queued_at > generated_at:
            raise ValueError("queued_at must not be after generated_at")
        if row.last_reviewed_at is not None and row.last_reviewed_at > generated_at:
            raise ValueError("last_reviewed_at must not be after generated_at")


def _normalize_rows(
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...],
) -> tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_digests: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyTeamCandidateQueuePriorityRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamCandidateQueuePriorityRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.public_candidate_digest in seen_digests:
            raise ValueError("public_candidate_digest values must be unique")
        seen_digests.add(row.public_candidate_digest)
    return tuple(sorted(normalized, key=lambda row: row.queue_rank))


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount, ...],
) -> tuple[ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    seen_codes: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_codes.add(item.reason_code)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
    supported_values: tuple[str, ...] = REASON_CODE_SEQUENCE,
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_public_text(field_name, reason_code)
        if reason_code not in supported_values:
            raise ValueError(f"{field_name} must use supported diagnostics")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(
        sorted(
            normalized,
            key=lambda code: (REASON_CODE_RANK.get(code, len(REASON_CODE_RANK)), code),
        ),
    )


def _normalize_report_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        values,
        supported_values=REPORT_REASON_PRIORITY,
    )


def _validate_report(report: ResearchStrategyTeamCandidateQueuePriorityReport) -> None:
    rows = report.rows
    if report.queue_item_count != _count(len(rows)):
        raise ValueError("queue_item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.evidence_completeness_attention_count != _kind_count(
        rows,
        "team_candidate_queue_priority_evidence_completeness_",
    ):
        raise ValueError("evidence_completeness_attention_count must match rows")
    if report.source_freshness_attention_count != _kind_count(
        rows,
        "team_candidate_queue_priority_source_freshness_",
    ):
        raise ValueError("source_freshness_attention_count must match rows")
    if report.team_coverage_attention_count != _kind_count(
        rows,
        "team_candidate_queue_priority_team_coverage_",
    ):
        raise ValueError("team_coverage_attention_count must match rows")
    if report.queue_age_attention_count != _kind_count(
        rows,
        "team_candidate_queue_priority_queue_age_",
    ):
        raise ValueError("queue_age_attention_count must match rows")
    if report.review_load_attention_count != _kind_count(
        rows,
        "team_candidate_queue_priority_review_load_",
    ):
        raise ValueError("review_load_attention_count must match rows")
    if report.mean_evidence_completeness_score != _mean(
        tuple(row.evidence_completeness_score for row in rows),
    ):
        raise ValueError("mean_evidence_completeness_score must match rows")
    if report.mean_source_freshness_score != _mean(
        tuple(row.source_freshness_score for row in rows),
    ):
        raise ValueError("mean_source_freshness_score must match rows")
    if report.mean_team_coverage_score != _mean(
        tuple(row.team_coverage_score for row in rows),
    ):
        raise ValueError("mean_team_coverage_score must match rows")
    if report.mean_resolution_learning_score != _mean(
        tuple(row.resolution_learning_score for row in rows),
    ):
        raise ValueError("mean_resolution_learning_score must match rows")
    if report.mean_review_load_score != _mean(tuple(row.review_load_score for row in rows)):
        raise ValueError("mean_review_load_score must match rows")
    if report.mean_queue_priority_score != _mean(
        tuple(row.queue_priority_score for row in rows),
    ):
        raise ValueError("mean_queue_priority_score must match rows")
    if report.max_queue_priority_score != _max_probability(
        tuple(row.queue_priority_score for row in rows),
    ):
        raise ValueError("max_queue_priority_score must match rows")
    if report.max_queue_age_seconds != _max_decimal(
        tuple(row.queue_age_seconds for row in rows),
    ):
        raise ValueError("max_queue_age_seconds must match rows")
    if report.max_review_load_score != _max_probability(
        tuple(row.review_load_score for row in rows),
    ):
        raise ValueError("max_review_load_score must match rows")
    if report.status != _rollup_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _kind_count(
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...],
    prefix: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(prefix) for reason_code in row.reason_codes)
        ),
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamCandidateQueuePriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability_decimal("mean", sum(values, ZERO) / _count(len(values)))


def _max_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_probability_decimal("max", max(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_nonnegative_decimal("max", max(values))


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    if finished_at < started_at:
        raise ValueError("finished_at must not be before started_at")
    return _normalize_nonnegative_decimal(
        "duration_seconds",
        Decimal(str((finished_at - started_at).total_seconds())),
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_generated_at_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")
    return value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized % COUNT_QUANTUM != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _normalize_decimal("probability", value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _require_at_least(field_name: str, left: Decimal, right: Decimal) -> None:
    if left < right:
        raise ValueError(f"{field_name} must be at least comparison floor")


def _require_at_most(field_name: str, left: Decimal, right: Decimal) -> None:
    if left > right:
        raise ValueError(f"{field_name} must be at most comparison ceiling")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_TEXT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be public text")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a SHA-256 digest")


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{context} {field_name} must be True")


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyTeamCandidateQueuePriorityReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return _digest_from_mapping(values)


def _digest_from_payload(payload: Mapping[str, Any]) -> str:
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_from_mapping(values: Mapping[str, Any]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(_normalize_decimal("decimal", value), "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is float:
        raise ValueError("floats are not allowed")
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def _reject_unsafe_public_payload(
    context: str,
    value: object,
    *,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                context,
                getattr(value, field.name),
                path=_join_path(path, field.name),
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _is_unsafe_public_text(key_text):
                raise ValueError(f"{context} contains unsafe public field {key_text}")
            _reject_unsafe_public_payload(
                context,
                item,
                path=_join_path(path, key_text),
            )
        return
    if isinstance(value, tuple | list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(context, item, path=_join_path(path, str(index)))
        return
    if type(value) is str and _is_unsafe_public_text(value):
        raise ValueError(f"{context} contains unsafe public value at {path or '<root>'}")


def _join_path(prefix: str, child: str) -> str:
    if not prefix:
        return child
    return f"{prefix}.{child}"


def _is_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)
