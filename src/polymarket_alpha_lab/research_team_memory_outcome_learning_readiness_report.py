"""Pure public team memory outcome-learning readiness report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_CONFIG_VERSION = (
    "research-team-memory-outcome-learning-readiness-v0"
)
RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_STATUSES = ("pass", "watch", "block")

SAMPLE_GAP_REASON = "resolved_outcome_sample_gap"
ATTRIBUTION_GAP_REASON = "attribution_note_gap"
CORRECTION_GAP_REASON = "correction_action_gap"
FRESHNESS_GAP_REASON = "freshness_gap"
PASS_REASON = "memory_outcome_learning_readiness_pass"
WATCH_REASON = "memory_outcome_learning_readiness_watch"
BLOCK_REASON = "memory_outcome_learning_readiness_block"

ROW_REASON_CODES = (
    SAMPLE_GAP_REASON,
    ATTRIBUTION_GAP_REASON,
    CORRECTION_GAP_REASON,
    FRESHNESS_GAP_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    BLOCK_REASON,
    WATCH_REASON,
    SAMPLE_GAP_REASON,
    ATTRIBUTION_GAP_REASON,
    CORRECTION_GAP_REASON,
    FRESHNESS_GAP_REASON,
    PASS_REASON,
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DIGEST_FIELD = "derived_validation_digest"
PAYLOAD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "team_count",
    "memory_scope_count",
    "resolved_outcome_count",
    "attribution_note_count",
    "correction_action_count",
    "fresh_outcome_count",
    "block_count",
    "watch_count",
    "pass_count",
    "average_readiness_score",
    "min_readiness_score",
    "status",
    "reason_codes",
    "readiness_rows",
    DIGEST_FIELD,
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "team_label",
    "memory_scope_label",
    "resolved_outcome_count",
    "attribution_note_count",
    "correction_action_count",
    "fresh_outcome_count",
    "latest_outcome_age_hours",
    "attribution_note_ratio",
    "correction_action_ratio",
    "fresh_outcome_ratio",
    "freshness_score",
    "readiness_score",
    "status",
    "reason_codes",
    DIGEST_FIELD,
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_TEXT_HEXES = (
    "63616e646964617465",
    "6d61726b6574",
    "736c7567",
    "7175657374696f6e",
    "736f75726365",
    "75726c",
    "74657874",
    "64736e",
    "7461626c65",
    "746f6b656e",
    "77616c6c6574",
    "6f72646572",
    "7472616465",
    "73697a696e67",
    "6c697665",
    "61757468",
    "627579",
    "73656c6c",
    "68747470",
    "777777",
    "6e6574776f726b",
    "6461746162617365",
    "706f737467726573",
    "6d7973716c",
    "6d6f6e676f6462",
    "7265646973",
    "7265636f6d6d656e64",
    "657865637574696f6e",
    "65786563757465",
)
PUBLIC_TEXT_BLOCKS = tuple(bytes.fromhex(value).decode("ascii") for value in PUBLIC_TEXT_HEXES)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_CONFIG_VERSION",
    "RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_STATUSES",
    "ResearchTeamMemoryOutcomeLearningReadinessConfig",
    "ResearchTeamMemoryOutcomeLearningReadinessInput",
    "ResearchTeamMemoryOutcomeLearningReadinessRow",
    "ResearchTeamMemoryOutcomeLearningReadinessReport",
    "build_research_team_memory_outcome_learning_readiness_report",
    "research_team_memory_outcome_learning_readiness_report_payload",
    "validate_research_team_memory_outcome_learning_readiness_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamMemoryOutcomeLearningReadinessConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_CONFIG_VERSION
    min_pass_resolved_outcome_count: Decimal = Decimal("20")
    min_watch_resolved_outcome_count: Decimal = Decimal("10")
    min_pass_attribution_note_ratio: Decimal = Decimal("0.900000")
    min_watch_attribution_note_ratio: Decimal = Decimal("0.700000")
    min_pass_correction_action_ratio: Decimal = Decimal("0.800000")
    min_watch_correction_action_ratio: Decimal = Decimal("0.600000")
    min_pass_fresh_outcome_ratio: Decimal = Decimal("0.750000")
    min_watch_fresh_outcome_ratio: Decimal = Decimal("0.500000")
    max_pass_latest_outcome_age_hours: Decimal = Decimal("168.000000")
    max_watch_latest_outcome_age_hours: Decimal = Decimal("336.000000")
    min_pass_readiness_score: Decimal = Decimal("0.800000")
    min_watch_readiness_score: Decimal = Decimal("0.600000")
    resolved_outcome_weight: Decimal = Decimal("0.250000")
    attribution_note_weight: Decimal = Decimal("0.250000")
    correction_action_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.250000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryOutcomeLearningReadinessConfig:
            raise ValueError(
                "config must be exactly ResearchTeamMemoryOutcomeLearningReadinessConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_resolved_outcome_count",
            "min_watch_resolved_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_attribution_note_ratio",
            "min_watch_attribution_note_ratio",
            "min_pass_correction_action_ratio",
            "min_watch_correction_action_ratio",
            "min_pass_fresh_outcome_ratio",
            "min_watch_fresh_outcome_ratio",
            "min_pass_readiness_score",
            "min_watch_readiness_score",
            "resolved_outcome_weight",
            "attribution_note_weight",
            "correction_action_weight",
            "freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_latest_outcome_age_hours",
            "max_watch_latest_outcome_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_hours(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("memory outcome learning readiness config", self)
        _reject_public_payload("config", _public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchTeamMemoryOutcomeLearningReadinessInput:
    team_label: str
    memory_scope_label: str
    resolved_outcome_count: Decimal
    attribution_note_count: Decimal
    correction_action_count: Decimal
    fresh_outcome_count: Decimal
    latest_outcome_age_hours: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryOutcomeLearningReadinessInput:
            raise ValueError(
                "input must be exactly ResearchTeamMemoryOutcomeLearningReadinessInput",
            )
        for field_name in ("team_label", "memory_scope_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "resolved_outcome_count",
            "attribution_note_count",
            "correction_action_count",
            "fresh_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_outcome_age_hours",
            _normalize_hours("latest_outcome_age_hours", self.latest_outcome_age_hours),
        )
        _validate_input_counts(self)
        require_paper_only_flags("memory outcome learning readiness input", self)
        _reject_public_payload("input", _public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchTeamMemoryOutcomeLearningReadinessRow:
    team_label: str
    memory_scope_label: str
    resolved_outcome_count: Decimal
    attribution_note_count: Decimal
    correction_action_count: Decimal
    fresh_outcome_count: Decimal
    latest_outcome_age_hours: Decimal
    attribution_note_ratio: Decimal
    correction_action_ratio: Decimal
    fresh_outcome_ratio: Decimal
    freshness_score: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryOutcomeLearningReadinessRow:
            raise ValueError("row must be exactly ResearchTeamMemoryOutcomeLearningReadinessRow")
        for field_name in ("team_label", "memory_scope_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "resolved_outcome_count",
            "attribution_note_count",
            "correction_action_count",
            "fresh_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_outcome_age_hours",
            _normalize_hours("latest_outcome_age_hours", self.latest_outcome_age_hours),
        )
        for field_name in (
            "attribution_note_ratio",
            "correction_action_ratio",
            "fresh_outcome_ratio",
            "freshness_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_input_counts(self)
        _validate_row(self)
        require_paper_only_flags("memory outcome learning readiness row", self)
        _reject_public_payload("row", _public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchTeamMemoryOutcomeLearningReadinessReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    memory_scope_count: Decimal
    resolved_outcome_count: Decimal
    attribution_note_count: Decimal
    correction_action_count: Decimal
    fresh_outcome_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    average_readiness_score: Decimal
    min_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    readiness_rows: tuple[ResearchTeamMemoryOutcomeLearningReadinessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryOutcomeLearningReadinessReport:
            raise ValueError("report must be exactly ResearchTeamMemoryOutcomeLearningReadinessReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "memory_scope_count",
            "resolved_outcome_count",
            "attribution_note_count",
            "correction_action_count",
            "fresh_outcome_count",
            "block_count",
            "watch_count",
            "pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_readiness_score", "min_readiness_score"):
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
        object.__setattr__(self, "readiness_rows", _normalize_rows(self.readiness_rows))
        require_paper_only_flags("memory outcome learning readiness report", self)
        _reject_public_payload("report", _public_dict(self))
        _require_or_set_digest(self)
        _validate_report(self)


def build_research_team_memory_outcome_learning_readiness_report(
    inputs: Iterable[ResearchTeamMemoryOutcomeLearningReadinessInput],
    *,
    config: ResearchTeamMemoryOutcomeLearningReadinessConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryOutcomeLearningReadinessReport:
    if type(config) is not ResearchTeamMemoryOutcomeLearningReadinessConfig:
        raise ValueError("config must be a ResearchTeamMemoryOutcomeLearningReadinessConfig")
    require_paper_only_flags("config", config)
    _require_or_set_digest(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    readiness_rows = tuple(
        sorted(
            (_readiness_row(row, config) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len({row.team_label for row in readiness_rows})),
        memory_scope_count=_count(len(readiness_rows)),
        resolved_outcome_count=sum(
            (row.resolved_outcome_count for row in readiness_rows),
            ZERO_COUNT,
        ),
        attribution_note_count=sum(
            (row.attribution_note_count for row in readiness_rows),
            ZERO_COUNT,
        ),
        correction_action_count=sum(
            (row.correction_action_count for row in readiness_rows),
            ZERO_COUNT,
        ),
        fresh_outcome_count=sum(
            (row.fresh_outcome_count for row in readiness_rows),
            ZERO_COUNT,
        ),
        block_count=_count(sum(1 for row in readiness_rows if row.status == "block")),
        watch_count=_count(sum(1 for row in readiness_rows if row.status == "watch")),
        pass_count=_count(sum(1 for row in readiness_rows if row.status == "pass")),
        average_readiness_score=_average_readiness_score(readiness_rows),
        min_readiness_score=_min_readiness_score(readiness_rows),
        status=_report_status(readiness_rows),
        reason_codes=_report_reason_codes(readiness_rows),
        readiness_rows=readiness_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchTeamMemoryOutcomeLearningReadinessReport(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def research_team_memory_outcome_learning_readiness_report_payload(
    report: ResearchTeamMemoryOutcomeLearningReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemoryOutcomeLearningReadinessReport:
        raise ValueError("report must be a ResearchTeamMemoryOutcomeLearningReadinessReport")
    require_paper_only_flags("report", report)
    _require_or_set_digest(report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    validate_research_team_memory_outcome_learning_readiness_report_payload(payload)
    return payload


def validate_research_team_memory_outcome_learning_readiness_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload("payload", payload)
    _reject_public_numerics(payload)
    _require_payload_flags(payload)
    _require_payload_statuses(payload)
    _validate_report_payload_shape(payload)
    _validate_payload_digest_tree(payload)
    return True


def _readiness_row(
    row: ResearchTeamMemoryOutcomeLearningReadinessInput,
    config: ResearchTeamMemoryOutcomeLearningReadinessConfig,
) -> ResearchTeamMemoryOutcomeLearningReadinessRow:
    attribution_ratio = _safe_ratio(row.attribution_note_count, row.resolved_outcome_count)
    correction_ratio = _safe_ratio(row.correction_action_count, row.resolved_outcome_count)
    fresh_ratio = _safe_ratio(row.fresh_outcome_count, row.resolved_outcome_count)
    freshness_score = _freshness_score(row.latest_outcome_age_hours, fresh_ratio, config)
    score = _readiness_score(
        resolved_outcome_count=row.resolved_outcome_count,
        attribution_note_ratio=attribution_ratio,
        correction_action_ratio=correction_ratio,
        freshness_score=freshness_score,
        config=config,
    )
    status = _status_from_components(
        row=row,
        attribution_note_ratio=attribution_ratio,
        correction_action_ratio=correction_ratio,
        fresh_outcome_ratio=fresh_ratio,
        readiness_score=score,
        config=config,
    )
    row_parts = dict(
        team_label=row.team_label,
        memory_scope_label=row.memory_scope_label,
        resolved_outcome_count=row.resolved_outcome_count,
        attribution_note_count=row.attribution_note_count,
        correction_action_count=row.correction_action_count,
        fresh_outcome_count=row.fresh_outcome_count,
        latest_outcome_age_hours=row.latest_outcome_age_hours,
        attribution_note_ratio=attribution_ratio,
        correction_action_ratio=correction_ratio,
        fresh_outcome_ratio=fresh_ratio,
        freshness_score=freshness_score,
        readiness_score=score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            resolved_outcome_count=row.resolved_outcome_count,
            attribution_note_ratio=attribution_ratio,
            correction_action_ratio=correction_ratio,
            fresh_outcome_ratio=fresh_ratio,
            latest_outcome_age_hours=row.latest_outcome_age_hours,
            config=config,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchTeamMemoryOutcomeLearningReadinessRow(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _readiness_score(
    *,
    resolved_outcome_count: Decimal,
    attribution_note_ratio: Decimal,
    correction_action_ratio: Decimal,
    freshness_score: Decimal,
    config: ResearchTeamMemoryOutcomeLearningReadinessConfig,
) -> Decimal:
    resolved_score = _clamp_ratio(
        _safe_ratio(resolved_outcome_count, config.min_pass_resolved_outcome_count),
    )
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            resolved_score * config.resolved_outcome_weight
            + attribution_note_ratio * config.attribution_note_weight
            + correction_action_ratio * config.correction_action_weight
            + freshness_score * config.freshness_weight,
        )


def _freshness_score(
    latest_outcome_age_hours: Decimal,
    fresh_outcome_ratio: Decimal,
    config: ResearchTeamMemoryOutcomeLearningReadinessConfig,
) -> Decimal:
    age_score = _latest_age_score(latest_outcome_age_hours, config)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((fresh_outcome_ratio + age_score) / Decimal("2"))


def _latest_age_score(
    latest_outcome_age_hours: Decimal,
    config: ResearchTeamMemoryOutcomeLearningReadinessConfig,
) -> Decimal:
    if latest_outcome_age_hours <= config.max_pass_latest_outcome_age_hours:
        return ONE_RATIO
    if latest_outcome_age_hours >= config.max_watch_latest_outcome_age_hours:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        span = config.max_watch_latest_outcome_age_hours - config.max_pass_latest_outcome_age_hours
        return _clamp_ratio(
            (config.max_watch_latest_outcome_age_hours - latest_outcome_age_hours) / span,
        )


def _status_from_components(
    *,
    row: ResearchTeamMemoryOutcomeLearningReadinessInput,
    attribution_note_ratio: Decimal,
    correction_action_ratio: Decimal,
    fresh_outcome_ratio: Decimal,
    readiness_score: Decimal,
    config: ResearchTeamMemoryOutcomeLearningReadinessConfig,
) -> str:
    if (
        readiness_score < config.min_watch_readiness_score
        or row.resolved_outcome_count < config.min_watch_resolved_outcome_count
        or attribution_note_ratio < config.min_watch_attribution_note_ratio
        or correction_action_ratio < config.min_watch_correction_action_ratio
        or fresh_outcome_ratio < config.min_watch_fresh_outcome_ratio
        or row.latest_outcome_age_hours > config.max_watch_latest_outcome_age_hours
    ):
        return "block"
    if (
        readiness_score >= config.min_pass_readiness_score
        and row.resolved_outcome_count >= config.min_pass_resolved_outcome_count
        and attribution_note_ratio >= config.min_pass_attribution_note_ratio
        and correction_action_ratio >= config.min_pass_correction_action_ratio
        and fresh_outcome_ratio >= config.min_pass_fresh_outcome_ratio
        and row.latest_outcome_age_hours <= config.max_pass_latest_outcome_age_hours
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    resolved_outcome_count: Decimal,
    attribution_note_ratio: Decimal,
    correction_action_ratio: Decimal,
    fresh_outcome_ratio: Decimal,
    latest_outcome_age_hours: Decimal,
    config: ResearchTeamMemoryOutcomeLearningReadinessConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    requested_codes: set[str] = set()
    if resolved_outcome_count < config.min_pass_resolved_outcome_count:
        requested_codes.add(SAMPLE_GAP_REASON)
    if attribution_note_ratio < config.min_pass_attribution_note_ratio:
        requested_codes.add(ATTRIBUTION_GAP_REASON)
    if correction_action_ratio < config.min_pass_correction_action_ratio:
        requested_codes.add(CORRECTION_GAP_REASON)
    if (
        fresh_outcome_ratio < config.min_pass_fresh_outcome_ratio
        or latest_outcome_age_hours > config.max_pass_latest_outcome_age_hours
    ):
        requested_codes.add(FRESHNESS_GAP_REASON)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in requested_codes)


def _report_status(rows: tuple[ResearchTeamMemoryOutcomeLearningReadinessRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryOutcomeLearningReadinessRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "pass":
        return (PASS_REASON,)
    requested_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if status == "block":
        requested_codes.add(BLOCK_REASON)
    if status == "watch":
        requested_codes.add(WATCH_REASON)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in requested_codes)


def _row_sort_key(
    row: ResearchTeamMemoryOutcomeLearningReadinessRow,
) -> tuple[Decimal, str, str]:
    return (row.readiness_score, row.team_label, row.memory_scope_label)


def _normalize_inputs(
    inputs: Iterable[ResearchTeamMemoryOutcomeLearningReadinessInput],
) -> tuple[ResearchTeamMemoryOutcomeLearningReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamMemoryOutcomeLearningReadinessInput:
            raise ValueError(
                "inputs must contain ResearchTeamMemoryOutcomeLearningReadinessInput values",
            )
        require_paper_only_flags("input", row)
        _reject_public_payload("input", _public_dict(row))
        _require_or_set_digest(row)
        key = (row.team_label, row.memory_scope_label)
        if key in seen_keys:
            raise ValueError("duplicate memory readiness key")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    values: Iterable[ResearchTeamMemoryOutcomeLearningReadinessRow],
) -> tuple[ResearchTeamMemoryOutcomeLearningReadinessRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("readiness_rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("readiness_rows must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamMemoryOutcomeLearningReadinessRow:
            raise ValueError(
                "readiness_rows must contain ResearchTeamMemoryOutcomeLearningReadinessRow values",
            )
        require_paper_only_flags("row", row)
        _reject_public_payload("row", _public_dict(row))
        _require_or_set_digest(row)
        key = (row.team_label, row.memory_scope_label)
        if key in seen_keys:
            raise ValueError("readiness_rows must be unique")
        seen_keys.add(key)
    return rows


def _validate_config(config: ResearchTeamMemoryOutcomeLearningReadinessConfig) -> None:
    if config.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    if config.min_pass_resolved_outcome_count <= config.min_watch_resolved_outcome_count:
        raise ValueError(
            "min_pass_resolved_outcome_count must exceed min_watch_resolved_outcome_count",
        )
    if config.min_pass_attribution_note_ratio <= config.min_watch_attribution_note_ratio:
        raise ValueError(
            "min_pass_attribution_note_ratio must exceed min_watch_attribution_note_ratio",
        )
    if config.min_pass_correction_action_ratio <= config.min_watch_correction_action_ratio:
        raise ValueError(
            "min_pass_correction_action_ratio must exceed min_watch_correction_action_ratio",
        )
    if config.min_pass_fresh_outcome_ratio <= config.min_watch_fresh_outcome_ratio:
        raise ValueError("min_pass_fresh_outcome_ratio must exceed min_watch_fresh_outcome_ratio")
    if config.max_pass_latest_outcome_age_hours >= config.max_watch_latest_outcome_age_hours:
        raise ValueError(
            "max_pass_latest_outcome_age_hours must be less than "
            "max_watch_latest_outcome_age_hours",
        )
    if config.min_pass_readiness_score <= config.min_watch_readiness_score:
        raise ValueError("min_pass_readiness_score must exceed min_watch_readiness_score")
    _require_ratio_total(
        config.resolved_outcome_weight,
        config.attribution_note_weight,
        config.correction_action_weight,
        config.freshness_weight,
    )


def _validate_input_counts(value: object) -> None:
    resolved = getattr(value, "resolved_outcome_count")
    if getattr(value, "attribution_note_count") > resolved:
        raise ValueError("attribution_note_count must not exceed resolved_outcome_count")
    if getattr(value, "correction_action_count") > resolved:
        raise ValueError("correction_action_count must not exceed resolved_outcome_count")
    if getattr(value, "fresh_outcome_count") > resolved:
        raise ValueError("fresh_outcome_count must not exceed resolved_outcome_count")


def _validate_row(row: ResearchTeamMemoryOutcomeLearningReadinessRow) -> None:
    if row.attribution_note_ratio != _safe_ratio(
        row.attribution_note_count,
        row.resolved_outcome_count,
    ):
        raise ValueError("attribution_note_ratio must match counts")
    if row.correction_action_ratio != _safe_ratio(
        row.correction_action_count,
        row.resolved_outcome_count,
    ):
        raise ValueError("correction_action_ratio must match counts")
    if row.fresh_outcome_ratio != _safe_ratio(row.fresh_outcome_count, row.resolved_outcome_count):
        raise ValueError("fresh_outcome_ratio must match counts")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason")
    if row.status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("attention rows must explain readiness gaps")
    if row.derived_validation_digest != _digest_public(_public_dict(row, include_digest=False)):
        raise ValueError("derived_validation_digest payload mismatch")


def _validate_report(report: ResearchTeamMemoryOutcomeLearningReadinessReport) -> None:
    rows = report.readiness_rows
    if report.team_count != _count(len({row.team_label for row in rows})):
        raise ValueError("team_count must match readiness_rows")
    if report.memory_scope_count != _count(len(rows)):
        raise ValueError("memory_scope_count must match readiness_rows")
    if report.resolved_outcome_count != sum(
        (row.resolved_outcome_count for row in rows),
        ZERO_COUNT,
    ):
        raise ValueError("resolved_outcome_count must match readiness_rows")
    if report.attribution_note_count != sum(
        (row.attribution_note_count for row in rows),
        ZERO_COUNT,
    ):
        raise ValueError("attribution_note_count must match readiness_rows")
    if report.correction_action_count != sum(
        (row.correction_action_count for row in rows),
        ZERO_COUNT,
    ):
        raise ValueError("correction_action_count must match readiness_rows")
    if report.fresh_outcome_count != sum((row.fresh_outcome_count for row in rows), ZERO_COUNT):
        raise ValueError("fresh_outcome_count must match readiness_rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match readiness_rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match readiness_rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match readiness_rows")
    if report.average_readiness_score != _average_readiness_score(rows):
        raise ValueError("average_readiness_score must match readiness_rows")
    if report.min_readiness_score != _min_readiness_score(rows):
        raise ValueError("min_readiness_score must match readiness_rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match readiness_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match readiness_rows")
    if report.readiness_rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("readiness_rows must use stable sort")
    if report.derived_validation_digest != _digest_public(_public_dict(report, include_digest=False)):
        raise ValueError("derived_validation_digest payload mismatch")


def _average_readiness_score(
    rows: tuple[ResearchTeamMemoryOutcomeLearningReadinessRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum((row.readiness_score for row in rows), ZERO_RATIO) / Decimal(len(rows)))


def _min_readiness_score(
    rows: tuple[ResearchTeamMemoryOutcomeLearningReadinessRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return min(row.readiness_score for row in rows)


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    allowed_ranks = {reason_code: index for index, reason_code in enumerate(allowed_values)}
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_ranks:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_STATUSES:
        raise ValueError(f"{field_name} statuses must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_text(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_count(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_ratio(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_hours(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_ratio(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = _quantize_ratio(sum(values, ZERO_RATIO))
    if total != ONE_RATIO:
        raise ValueError("component weights must sum to 1.000000")


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_ratio(value)
    if normalized < ZERO_RATIO:
        return ZERO_RATIO
    if normalized > ONE_RATIO:
        return ONE_RATIO
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize_count(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, DIGEST_FIELD)
    expected = _digest_public(_public_dict(value, include_digest=False))
    if current == "":
        object.__setattr__(value, DIGEST_FIELD, expected)
        return
    if type(current) is not str or current != expected:
        raise ValueError("derived_validation_digest payload mismatch")


def _digest_public(value: object) -> str:
    ready = _strip_digest_fields(json_ready_no_floats(value))
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _public_dict(value: object, *, include_digest: bool = True) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: getattr(value, field.name)
            for field in fields(value)
            if include_digest or field.name != DIGEST_FIELD
        }
    if isinstance(value, dict):
        if include_digest:
            return dict(value)
        return {key: item for key, item in value.items() if key != DIGEST_FIELD}
    raise ValueError("value must be a public object")


def _strip_digest_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != DIGEST_FIELD
        }
    if isinstance(value, list):
        return [_strip_digest_fields(item) for item in value]
    return value


def _validate_report_payload_shape(payload: dict[str, Any]) -> None:
    _require_exact_keys("report", payload, REPORT_PAYLOAD_KEYS)
    rows_payload = payload["readiness_rows"]
    if type(rows_payload) is not list:
        raise ValueError("readiness_rows must be a JSON list")
    rows = tuple(_row_from_public_payload(item) for item in rows_payload)
    ResearchTeamMemoryOutcomeLearningReadinessReport(
        generated_at=_datetime_payload("generated_at", payload["generated_at"]),
        config_version=_public_string_payload("config_version", payload["config_version"]),
        team_count=_count_payload("team_count", payload["team_count"]),
        memory_scope_count=_count_payload("memory_scope_count", payload["memory_scope_count"]),
        resolved_outcome_count=_count_payload(
            "resolved_outcome_count",
            payload["resolved_outcome_count"],
        ),
        attribution_note_count=_count_payload(
            "attribution_note_count",
            payload["attribution_note_count"],
        ),
        correction_action_count=_count_payload(
            "correction_action_count",
            payload["correction_action_count"],
        ),
        fresh_outcome_count=_count_payload("fresh_outcome_count", payload["fresh_outcome_count"]),
        block_count=_count_payload("block_count", payload["block_count"]),
        watch_count=_count_payload("watch_count", payload["watch_count"]),
        pass_count=_count_payload("pass_count", payload["pass_count"]),
        average_readiness_score=_ratio_payload(
            "average_readiness_score",
            payload["average_readiness_score"],
        ),
        min_readiness_score=_ratio_payload("min_readiness_score", payload["min_readiness_score"]),
        status=_status_payload("status", payload["status"]),
        reason_codes=_reason_codes_payload(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        readiness_rows=rows,
        derived_validation_digest=_digest_payload(DIGEST_FIELD, payload[DIGEST_FIELD]),
        paper_only=_true_payload("paper_only", payload["paper_only"]),
        report_only=_true_payload("report_only", payload["report_only"]),
        readonly=_true_payload("readonly", payload["readonly"]),
    )


def _row_from_public_payload(value: object) -> ResearchTeamMemoryOutcomeLearningReadinessRow:
    if type(value) is not dict:
        raise ValueError("readiness_rows must contain JSON objects")
    _require_exact_keys("row", value, ROW_PAYLOAD_KEYS)
    return ResearchTeamMemoryOutcomeLearningReadinessRow(
        team_label=_public_string_payload("team_label", value["team_label"]),
        memory_scope_label=_public_string_payload("memory_scope_label", value["memory_scope_label"]),
        resolved_outcome_count=_count_payload(
            "resolved_outcome_count",
            value["resolved_outcome_count"],
        ),
        attribution_note_count=_count_payload(
            "attribution_note_count",
            value["attribution_note_count"],
        ),
        correction_action_count=_count_payload(
            "correction_action_count",
            value["correction_action_count"],
        ),
        fresh_outcome_count=_count_payload("fresh_outcome_count", value["fresh_outcome_count"]),
        latest_outcome_age_hours=_hours_payload(
            "latest_outcome_age_hours",
            value["latest_outcome_age_hours"],
        ),
        attribution_note_ratio=_ratio_payload(
            "attribution_note_ratio",
            value["attribution_note_ratio"],
        ),
        correction_action_ratio=_ratio_payload(
            "correction_action_ratio",
            value["correction_action_ratio"],
        ),
        fresh_outcome_ratio=_ratio_payload("fresh_outcome_ratio", value["fresh_outcome_ratio"]),
        freshness_score=_ratio_payload("freshness_score", value["freshness_score"]),
        readiness_score=_ratio_payload("readiness_score", value["readiness_score"]),
        status=_status_payload("status", value["status"]),
        reason_codes=_reason_codes_payload("reason_codes", value["reason_codes"], ROW_REASON_CODES),
        derived_validation_digest=_digest_payload(DIGEST_FIELD, value[DIGEST_FIELD]),
        paper_only=_true_payload("paper_only", value["paper_only"]),
        report_only=_true_payload("report_only", value["report_only"]),
        readonly=_true_payload("readonly", value["readonly"]),
    )


def _require_exact_keys(label: str, value: dict[str, Any], expected_keys: tuple[str, ...]) -> None:
    missing_keys = tuple(key for key in expected_keys if key not in value)
    if missing_keys:
        raise ValueError(f"{label} missing public field: {missing_keys[0]}")
    expected_key_set = set(expected_keys)
    extra_keys = tuple(key for key in value if key not in expected_key_set)
    if extra_keys:
        raise ValueError(f"{label} has unsupported public field: {extra_keys[0]}")


def _public_string_payload(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    return value


def _datetime_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _decimal_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc


def _count_payload(field_name: str, value: object) -> Decimal:
    parsed = _decimal_payload(field_name, value)
    normalized = _normalize_count(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _ratio_payload(field_name: str, value: object) -> Decimal:
    parsed = _decimal_payload(field_name, value)
    normalized = _normalize_ratio(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _hours_payload(field_name: str, value: object) -> Decimal:
    parsed = _decimal_payload(field_name, value)
    normalized = _normalize_hours(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _status_payload(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    return value


def _reason_codes_payload(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON list")
    return _normalize_reason_codes(field_name, value, allowed_values)


def _digest_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _true_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_payload_digest_tree(item)
        if DIGEST_FIELD in value:
            current = value[DIGEST_FIELD]
            if _digest_payload(DIGEST_FIELD, current) != _digest_public(value):
                raise ValueError("derived_validation_digest payload mismatch")
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _require_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        if DIGEST_FIELD in value or any(key in value for key in PAYLOAD_FLAG_FIELDS):
            for key in PAYLOAD_FLAG_FIELDS:
                _true_payload(key, value.get(key))
            _digest_payload(DIGEST_FIELD, value.get(DIGEST_FIELD))
        for item in value.values():
            _require_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_flags(item)


def _require_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        if "status" in value:
            _require_status("status", value["status"])
        for item in value.values():
            _require_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_statuses(item)


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, (float, Decimal)):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(label, _public_dict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public key")
            _reject_public_text(key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_public_text(value)


def _reject_public_text(value: str) -> None:
    if "://" in value.lower():
        raise ValueError("unsafe public value")
    normalized = "".join(character for character in value.lower() if character.isalnum())
    if any(fragment in normalized for fragment in PUBLIC_TEXT_BLOCKS):
        raise ValueError("unsafe public value")
