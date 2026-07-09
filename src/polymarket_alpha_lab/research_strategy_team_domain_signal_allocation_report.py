"""Report-only domain team attention allocation reducer.

This module scores sanitized domain teams for analyst review using information
yield, calibration freshness, event urgency, cost pressure, and evidence gaps.
It is deterministic, readonly, paper-only, and exposes only safe public payloads.
"""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION = (
    "research-strategy-team-domain-signal-allocation-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_ATTENTION_SCORE_PASS = "attention_score_pass"
REASON_ATTENTION_SCORE_WATCH = "attention_score_watch"
REASON_ATTENTION_SCORE_BLOCK = "attention_score_block"
REASON_HIGH_INFORMATION_YIELD = "high_information_yield"
REASON_CALIBRATION_FRESHNESS_CURRENT = "calibration_freshness_current"
REASON_EVENT_URGENCY_HIGH = "event_urgency_high"
REASON_LIQUIDITY_COST_PRESSURE_HIGH = "liquidity_cost_pressure_high"
REASON_EVIDENCE_GAP_UNRESOLVED = "evidence_gap_unresolved"

_ROW_REASON_CODE_SEQUENCE = (
    REASON_ATTENTION_SCORE_PASS,
    REASON_ATTENTION_SCORE_WATCH,
    REASON_ATTENTION_SCORE_BLOCK,
    REASON_HIGH_INFORMATION_YIELD,
    REASON_CALIBRATION_FRESHNESS_CURRENT,
    REASON_EVENT_URGENCY_HIGH,
    REASON_LIQUIDITY_COST_PRESSURE_HIGH,
    REASON_EVIDENCE_GAP_UNRESOLVED,
)
_REPORT_REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_ATTENTION_SCORE_PASS,
    REASON_ATTENTION_SCORE_WATCH,
    REASON_ATTENTION_SCORE_BLOCK,
    REASON_HIGH_INFORMATION_YIELD,
    REASON_CALIBRATION_FRESHNESS_CURRENT,
    REASON_EVENT_URGENCY_HIGH,
    REASON_LIQUIDITY_COST_PRESSURE_HIGH,
    REASON_EVIDENCE_GAP_UNRESOLVED,
)
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_DIGEST_FIELD = "validation_digest"
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_HOUR = Decimal("3600.000000")
_MICROSECOND_DIVISOR = Decimal("1000000.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL_TEXT_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth_",
    "auth-",
    "auth ",
    "authentication",
    "credential",
    "secret",
    "private key",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "live",
    "http://",
    "https://",
    "://",
    "www.",
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "domain_team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_attention_need_score",
        "highest_attention_need_score",
        "average_information_yield_score",
        "average_calibration_freshness_score",
        "average_event_urgency_score",
        "average_liquidity_cost_pressure_score",
        "average_unresolved_evidence_gap_score",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "domain_team",
        "analyst_lane",
        "calibration_checked_at",
        "calibration_age_hours",
        "information_yield_score",
        "calibration_freshness_score",
        "event_urgency_score",
        "liquidity_cost_pressure_score",
        "unresolved_evidence_gap_score",
        "attention_need_score",
        "allocation_rank",
        "status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION",
    "ResearchStrategyTeamDomainSignalAllocationConfig",
    "ResearchStrategyTeamDomainSignalAllocationInput",
    "ResearchStrategyTeamDomainSignalAllocationReasonCodeCount",
    "ResearchStrategyTeamDomainSignalAllocationReport",
    "ResearchStrategyTeamDomainSignalAllocationRow",
    "build_research_strategy_team_domain_signal_allocation_report",
    "research_strategy_team_domain_signal_allocation_report_public_payload",
)


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
class ResearchStrategyTeamDomainSignalAllocationConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION
    )
    attention_block_threshold: Decimal = Decimal("0.750000")
    attention_watch_threshold: Decimal = Decimal("0.500000")
    calibration_decay_window_hours: Decimal = Decimal("72.000000")
    high_information_yield_threshold: Decimal = Decimal("0.800000")
    fresh_calibration_threshold: Decimal = Decimal("0.700000")
    event_urgency_threshold: Decimal = Decimal("0.700000")
    liquidity_cost_pressure_threshold: Decimal = Decimal("0.650000")
    evidence_gap_threshold: Decimal = Decimal("0.600000")
    information_yield_weight: Decimal = Decimal("0.300000")
    calibration_freshness_weight: Decimal = Decimal("0.200000")
    event_urgency_weight: Decimal = Decimal("0.200000")
    liquidity_cost_pressure_weight: Decimal = Decimal("0.150000")
    evidence_gap_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainSignalAllocationConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "attention_block_threshold",
            "attention_watch_threshold",
            "high_information_yield_threshold",
            "fresh_calibration_threshold",
            "event_urgency_threshold",
            "liquidity_cost_pressure_threshold",
            "evidence_gap_threshold",
            "information_yield_weight",
            "calibration_freshness_weight",
            "event_urgency_weight",
            "liquidity_cost_pressure_weight",
            "evidence_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_decay_window_hours",
            _require_positive_decimal(
                "calibration_decay_window_hours",
                self.calibration_decay_window_hours,
            ),
        )
        if self.attention_block_threshold < self.attention_watch_threshold:
            raise ValueError(
                "attention_block_threshold must be at least attention_watch_threshold",
            )
        weight_sum = _quantize(
            self.information_yield_weight
            + self.calibration_freshness_weight
            + self.event_urgency_weight
            + self.liquidity_cost_pressure_weight
            + self.evidence_gap_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDomainSignalAllocationInput(_FinalPublicDataclass):
    domain_team: str
    analyst_lane: str
    calibration_checked_at: datetime
    information_yield_score: Decimal
    event_urgency_score: Decimal
    liquidity_cost_pressure_score: Decimal
    unresolved_evidence_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainSignalAllocationInput, "input")
        object.__setattr__(
            self,
            "domain_team",
            _require_public_identifier("domain_team", self.domain_team),
        )
        object.__setattr__(
            self,
            "analyst_lane",
            _require_public_identifier("analyst_lane", self.analyst_lane),
        )
        object.__setattr__(
            self,
            "calibration_checked_at",
            _as_utc("calibration_checked_at", self.calibration_checked_at),
        )
        for field_name in (
            "information_yield_score",
            "event_urgency_score",
            "liquidity_cost_pressure_score",
            "unresolved_evidence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDomainSignalAllocationRow(_FinalPublicDataclass):
    domain_team: str
    analyst_lane: str
    calibration_checked_at: datetime
    calibration_age_hours: Decimal
    information_yield_score: Decimal
    calibration_freshness_score: Decimal
    event_urgency_score: Decimal
    liquidity_cost_pressure_score: Decimal
    unresolved_evidence_gap_score: Decimal
    attention_need_score: Decimal
    allocation_rank: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyTeamDomainSignalAllocationConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyTeamDomainSignalAllocationConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainSignalAllocationRow, "row")
        object.__setattr__(
            self,
            "domain_team",
            _require_public_identifier("domain_team", self.domain_team),
        )
        object.__setattr__(
            self,
            "analyst_lane",
            _require_public_identifier("analyst_lane", self.analyst_lane),
        )
        object.__setattr__(
            self,
            "calibration_checked_at",
            _as_utc("calibration_checked_at", self.calibration_checked_at),
        )
        object.__setattr__(
            self,
            "calibration_age_hours",
            _require_nonnegative_decimal("calibration_age_hours", self.calibration_age_hours),
        )
        for field_name in (
            "information_yield_score",
            "calibration_freshness_score",
            "event_urgency_score",
            "liquidity_cost_pressure_score",
            "unresolved_evidence_gap_score",
            "attention_need_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "allocation_rank",
            _require_positive_count_decimal("allocation_rank", self.allocation_rank),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        expected_digest = _digest_from_dataclass(self)
        if self.validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.validation_digest != expected_digest:
            raise ValueError("validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.validation_digest)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDomainSignalAllocationReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamDomainSignalAllocationReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDomainSignalAllocationReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_attention_need_score: Decimal
    highest_attention_need_score: Decimal
    average_information_yield_score: Decimal
    average_calibration_freshness_score: Decimal
    average_event_urgency_score: Decimal
    average_liquidity_cost_pressure_score: Decimal
    average_unresolved_evidence_gap_score: Decimal
    rows: tuple[ResearchStrategyTeamDomainSignalAllocationRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamDomainSignalAllocationReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainSignalAllocationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_attention_need_score",
            "highest_attention_need_score",
            "average_information_yield_score",
            "average_calibration_freshness_score",
            "average_event_urgency_score",
            "average_liquidity_cost_pressure_score",
            "average_unresolved_evidence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _digest_from_dataclass(self)
        if self.validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.validation_digest != expected_digest:
            raise ValueError("validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.validation_digest)
        _reject_unsafe_public_payload("report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return research_strategy_team_domain_signal_allocation_report_public_payload(self)


def build_research_strategy_team_domain_signal_allocation_report(
    inputs: Sequence[ResearchStrategyTeamDomainSignalAllocationInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamDomainSignalAllocationConfig | None = None,
) -> ResearchStrategyTeamDomainSignalAllocationReport:
    cfg = config or ResearchStrategyTeamDomainSignalAllocationConfig()
    if type(cfg) is not ResearchStrategyTeamDomainSignalAllocationConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamDomainSignalAllocationConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for value in normalized_inputs:
        if value.calibration_checked_at > report_time:
            raise ValueError("calibration_checked_at must not be after generated_at")
    row_inputs = tuple(
        sorted(
            (_row_input_for_value(value, generated_at=report_time, config=cfg) for value in normalized_inputs),
            key=_row_input_sort_key,
        ),
    )
    rows = tuple(
        _row_from_row_input(
            value,
            allocation_rank=_decimal_count(index + 1),
            config=cfg,
        )
        for index, value in enumerate(row_inputs)
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyTeamDomainSignalAllocationReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "domain_team_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_attention_need_score": _average_ratio(
            tuple(row.attention_need_score for row in rows),
        ),
        "highest_attention_need_score": max(
            (row.attention_need_score for row in rows),
            default=_ZERO,
        ),
        "average_information_yield_score": _average_ratio(
            tuple(row.information_yield_score for row in rows),
        ),
        "average_calibration_freshness_score": _average_ratio(
            tuple(row.calibration_freshness_score for row in rows),
        ),
        "average_event_urgency_score": _average_ratio(
            tuple(row.event_urgency_score for row in rows),
        ),
        "average_liquidity_cost_pressure_score": _average_ratio(
            tuple(row.liquidity_cost_pressure_score for row in rows),
        ),
        "average_unresolved_evidence_gap_score": _average_ratio(
            tuple(row.unresolved_evidence_gap_score for row in rows),
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyTeamDomainSignalAllocationReport(
        **values,
        validation_digest=_digest_from_mapping(values),
    )


def research_strategy_team_domain_signal_allocation_report_public_payload(
    value: ResearchStrategyTeamDomainSignalAllocationReport | Mapping[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyTeamDomainSignalAllocationReport:
        _require_hard_flags("report", value)
        payload = _json_ready(value, omit_digest=False)
    elif isinstance(value, Mapping):
        payload = _json_ready(value, omit_digest=False)
    else:
        raise ValueError(
            "value must be a ResearchStrategyTeamDomainSignalAllocationReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_schema(payload)
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _RowInput:
    value: ResearchStrategyTeamDomainSignalAllocationInput
    calibration_age_hours: Decimal
    calibration_freshness_score: Decimal
    attention_need_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _row_input_for_value(
    value: ResearchStrategyTeamDomainSignalAllocationInput,
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamDomainSignalAllocationConfig,
) -> _RowInput:
    calibration_age_hours = _age_hours(value.calibration_checked_at, generated_at)
    freshness = _calibration_freshness_score(calibration_age_hours, config)
    attention_need_score = _attention_need_score(
        information_yield_score=value.information_yield_score,
        calibration_freshness_score=freshness,
        event_urgency_score=value.event_urgency_score,
        liquidity_cost_pressure_score=value.liquidity_cost_pressure_score,
        unresolved_evidence_gap_score=value.unresolved_evidence_gap_score,
        config=config,
    )
    return _RowInput(
        value=value,
        calibration_age_hours=calibration_age_hours,
        calibration_freshness_score=freshness,
        attention_need_score=attention_need_score,
        status=_row_status(attention_need_score, config),
        reason_codes=_row_reason_codes(
            attention_need_score=attention_need_score,
            information_yield_score=value.information_yield_score,
            calibration_freshness_score=freshness,
            event_urgency_score=value.event_urgency_score,
            liquidity_cost_pressure_score=value.liquidity_cost_pressure_score,
            unresolved_evidence_gap_score=value.unresolved_evidence_gap_score,
            config=config,
        ),
    )


def _row_from_row_input(
    value: _RowInput,
    *,
    allocation_rank: Decimal,
    config: ResearchStrategyTeamDomainSignalAllocationConfig,
) -> ResearchStrategyTeamDomainSignalAllocationRow:
    return ResearchStrategyTeamDomainSignalAllocationRow(
        domain_team=value.value.domain_team,
        analyst_lane=value.value.analyst_lane,
        calibration_checked_at=value.value.calibration_checked_at,
        calibration_age_hours=value.calibration_age_hours,
        information_yield_score=value.value.information_yield_score,
        calibration_freshness_score=value.calibration_freshness_score,
        event_urgency_score=value.value.event_urgency_score,
        liquidity_cost_pressure_score=value.value.liquidity_cost_pressure_score,
        unresolved_evidence_gap_score=value.value.unresolved_evidence_gap_score,
        attention_need_score=value.attention_need_score,
        allocation_rank=allocation_rank,
        status=value.status,
        reason_codes=value.reason_codes,
        validation_config=config,
    )


def _calibration_freshness_score(
    calibration_age_hours: Decimal,
    config: ResearchStrategyTeamDomainSignalAllocationConfig,
) -> Decimal:
    return _clamp_ratio(
        _ONE - _safe_divide(calibration_age_hours, config.calibration_decay_window_hours),
    )


def _attention_need_score(
    *,
    information_yield_score: Decimal,
    calibration_freshness_score: Decimal,
    event_urgency_score: Decimal,
    liquidity_cost_pressure_score: Decimal,
    unresolved_evidence_gap_score: Decimal,
    config: ResearchStrategyTeamDomainSignalAllocationConfig,
) -> Decimal:
    return _quantize(
        information_yield_score * config.information_yield_weight
        + calibration_freshness_score * config.calibration_freshness_weight
        + event_urgency_score * config.event_urgency_weight
        + liquidity_cost_pressure_score * config.liquidity_cost_pressure_weight
        + unresolved_evidence_gap_score * config.evidence_gap_weight,
    )


def _row_status(
    attention_need_score: Decimal,
    config: ResearchStrategyTeamDomainSignalAllocationConfig,
) -> str:
    if attention_need_score >= config.attention_block_threshold:
        return STATUS_BLOCK
    if attention_need_score >= config.attention_watch_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    attention_need_score: Decimal,
    information_yield_score: Decimal,
    calibration_freshness_score: Decimal,
    event_urgency_score: Decimal,
    liquidity_cost_pressure_score: Decimal,
    unresolved_evidence_gap_score: Decimal,
    config: ResearchStrategyTeamDomainSignalAllocationConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    status = _row_status(attention_need_score, config)
    if status == STATUS_BLOCK:
        codes.append(REASON_ATTENTION_SCORE_BLOCK)
    elif status == STATUS_WATCH:
        codes.append(REASON_ATTENTION_SCORE_WATCH)
    else:
        codes.append(REASON_ATTENTION_SCORE_PASS)
    if information_yield_score >= config.high_information_yield_threshold:
        codes.append(REASON_HIGH_INFORMATION_YIELD)
    if calibration_freshness_score >= config.fresh_calibration_threshold:
        codes.append(REASON_CALIBRATION_FRESHNESS_CURRENT)
    if event_urgency_score >= config.event_urgency_threshold:
        codes.append(REASON_EVENT_URGENCY_HIGH)
    if liquidity_cost_pressure_score >= config.liquidity_cost_pressure_threshold:
        codes.append(REASON_LIQUIDITY_COST_PRESSURE_HIGH)
    if unresolved_evidence_gap_score >= config.evidence_gap_threshold:
        codes.append(REASON_EVIDENCE_GAP_UNRESOLVED)
    return _normalize_reason_codes("reason_codes", tuple(codes), _ROW_REASON_CODE_SEQUENCE)


def _report_status(
    rows: tuple[ResearchStrategyTeamDomainSignalAllocationRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_input_sort_key(value: _RowInput) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value.status],
        -value.attention_need_score,
        value.value.domain_team,
    )


def _row_sort_key(
    row: ResearchStrategyTeamDomainSignalAllocationRow,
) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        -row.attention_need_score,
        row.domain_team,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyTeamDomainSignalAllocationInput],
) -> tuple[ResearchStrategyTeamDomainSignalAllocationInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a sequence")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be a sequence") from exc
    seen_domains: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyTeamDomainSignalAllocationInput:
            raise ValueError(
                "inputs must contain only ResearchStrategyTeamDomainSignalAllocationInput values",
            )
        _require_hard_flags("input", value)
        if value.domain_team in seen_domains:
            raise ValueError("inputs must not contain duplicate domain_team values")
        seen_domains.add(value.domain_team)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyTeamDomainSignalAllocationRow],
) -> tuple[ResearchStrategyTeamDomainSignalAllocationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a sequence") from exc
    seen_domains: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyTeamDomainSignalAllocationRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamDomainSignalAllocationRow values",
            )
        _require_hard_flags("row", row)
        if row.domain_team in seen_domains:
            raise ValueError("rows must not contain duplicate domain_team values")
        seen_domains.add(row.domain_team)
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyTeamDomainSignalAllocationReasonCodeCount],
) -> tuple[ResearchStrategyTeamDomainSignalAllocationReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be a sequence")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a sequence") from exc
    seen_codes: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchStrategyTeamDomainSignalAllocationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamDomainSignalAllocationReasonCodeCount values",
            )
        _require_hard_flags("reason count", count)
        if count.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate codes")
        seen_codes.add(count.reason_code)
    if tuple(sorted(normalized, key=lambda item: item.reason_code)) != normalized:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _validate_row(
    row: ResearchStrategyTeamDomainSignalAllocationRow,
    config: ResearchStrategyTeamDomainSignalAllocationConfig | None,
) -> None:
    active_config = config or ResearchStrategyTeamDomainSignalAllocationConfig()
    expected_freshness = _calibration_freshness_score(
        row.calibration_age_hours,
        active_config,
    )
    if row.calibration_freshness_score != expected_freshness:
        raise ValueError("calibration_freshness_score must match calibration_age_hours")
    expected_score = _attention_need_score(
        information_yield_score=row.information_yield_score,
        calibration_freshness_score=row.calibration_freshness_score,
        event_urgency_score=row.event_urgency_score,
        liquidity_cost_pressure_score=row.liquidity_cost_pressure_score,
        unresolved_evidence_gap_score=row.unresolved_evidence_gap_score,
        config=active_config,
    )
    if row.attention_need_score != expected_score:
        raise ValueError("attention_need_score does not match inputs")
    if row.status != _row_status(row.attention_need_score, active_config):
        raise ValueError("status does not match attention_need_score")
    expected_codes = _row_reason_codes(
        attention_need_score=row.attention_need_score,
        information_yield_score=row.information_yield_score,
        calibration_freshness_score=row.calibration_freshness_score,
        event_urgency_score=row.event_urgency_score,
        liquidity_cost_pressure_score=row.liquidity_cost_pressure_score,
        unresolved_evidence_gap_score=row.unresolved_evidence_gap_score,
        config=active_config,
    )
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes do not match inputs")


def _validate_report(report: ResearchStrategyTeamDomainSignalAllocationReport) -> None:
    if report.domain_team_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_team_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.domain_team_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match domain_team_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_reason_counts = (
            ResearchStrategyTeamDomainSignalAllocationReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")
    expected_ranks = tuple(_decimal_count(index + 1) for index in range(len(report.rows)))
    if tuple(row.allocation_rank for row in report.rows) != expected_ranks:
        raise ValueError("allocation_rank must match row sequence")
    if report.average_attention_need_score != _average_ratio(
        tuple(row.attention_need_score for row in report.rows),
    ):
        raise ValueError("average_attention_need_score must match rows")
    if report.highest_attention_need_score != max(
        (row.attention_need_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("highest_attention_need_score must match rows")
    if report.average_information_yield_score != _average_ratio(
        tuple(row.information_yield_score for row in report.rows),
    ):
        raise ValueError("average_information_yield_score must match rows")
    if report.average_calibration_freshness_score != _average_ratio(
        tuple(row.calibration_freshness_score for row in report.rows),
    ):
        raise ValueError("average_calibration_freshness_score must match rows")
    if report.average_event_urgency_score != _average_ratio(
        tuple(row.event_urgency_score for row in report.rows),
    ):
        raise ValueError("average_event_urgency_score must match rows")
    if report.average_liquidity_cost_pressure_score != _average_ratio(
        tuple(row.liquidity_cost_pressure_score for row in report.rows),
    ):
        raise ValueError("average_liquidity_cost_pressure_score must match rows")
    if report.average_unresolved_evidence_gap_score != _average_ratio(
        tuple(row.unresolved_evidence_gap_score for row in report.rows),
    ):
        raise ValueError("average_unresolved_evidence_gap_score must match rows")


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamDomainSignalAllocationRow, ...],
) -> tuple[ResearchStrategyTeamDomainSignalAllocationReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyTeamDomainSignalAllocationReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_safe_divide(_decimal_count(counts[reason_code]), denominator),
        )
        for reason_code in sorted(counts)
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamDomainSignalAllocationRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _safe_divide(sum(values, _ZERO), _decimal_count(len(values)))


def _age_hours(earlier: datetime, later: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("calibration age must be nonnegative")
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / _MICROSECOND_DIVISOR
    return _quantize(seconds / _SECONDS_PER_HOUR)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(_QUANT):
        raise ValueError(f"{name} must be a whole-count Decimal")
    return normalized


def _require_positive_count_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_public_identifier(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a str")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} contains unsafe public text")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a digest")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a digest")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be an allowed reason code")
    return value


def _normalize_reason_codes(
    name: str,
    values: Sequence[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence") from exc
    for value in normalized:
        _require_reason_code(name, value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    order = {code: index for index, code in enumerate(allowed)}
    return tuple(sorted(normalized, key=order.__getitem__))


def _normalize_report_reason_codes(
    name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence") from exc
    for value in normalized:
        _require_reason_code(name, value, _REPORT_REASON_CODE_SEQUENCE)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    if tuple(sorted(normalized)) != normalized:
        raise ValueError(f"{name} must use deterministic sequence")
    return normalized


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _digest_from_dataclass(value: object) -> str:
    return _digest_from_mapping(_json_ready(value, omit_digest=True))


def _digest_from_mapping(value: object) -> str:
    encoded = json.dumps(
        _json_ready(value, omit_digest=True),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object, *, omit_digest: bool) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), omit_digest=omit_digest)
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        raise ValueError("numeric payload values must use Decimal")
    if isinstance(value, float):
        raise ValueError("numeric payload values must use Decimal")
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if omit_digest and key == _DIGEST_FIELD:
                continue
            ready[key] = _json_ready(item, omit_digest=omit_digest)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item, omit_digest=omit_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, omit_digest=omit_digest) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_payload_statuses(payload: dict[str, object]) -> None:
    _require_status("payload.status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _require_status(f"payload.rows[{index}].status", row.get("status"))


def _validate_payload_schema(payload: dict[str, object]) -> None:
    _require_payload_fields("payload", payload, _REPORT_PAYLOAD_FIELDS)
    _require_payload_flags("payload", payload)
    _require_utc_datetime_text("payload.generated_at", payload["generated_at"])
    config_version = _require_public_identifier(
        "payload.config_version",
        payload["config_version"],
    )
    if (
        config_version
        != DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION
    ):
        raise ValueError("payload.config_version must be the supported config version")
    _require_status("payload.status", payload["status"])
    for field_name in (
        "domain_team_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_count_decimal_text(f"payload.{field_name}", payload[field_name])
    for field_name in (
        "average_attention_need_score",
        "highest_attention_need_score",
        "average_information_yield_score",
        "average_calibration_freshness_score",
        "average_event_urgency_score",
        "average_liquidity_cost_pressure_score",
        "average_unresolved_evidence_gap_score",
    ):
        _require_ratio_decimal_text(f"payload.{field_name}", payload[field_name])
    _require_digest("payload.validation_digest", payload["validation_digest"])
    _validate_reason_code_texts("payload.reason_codes", payload["reason_codes"])

    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        _validate_row_payload_schema(f"payload.rows[{index}]", row)

    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("payload.reason_code_counts must be a list")
    for index, row in enumerate(reason_code_counts):
        _validate_reason_count_payload_schema(
            f"payload.reason_code_counts[{index}]",
            row,
        )


def _validate_row_payload_schema(label: str, row: object) -> None:
    if type(row) is not dict:
        raise ValueError("payload.rows must contain JSON objects")
    _require_payload_fields(label, row, _ROW_PAYLOAD_FIELDS)
    _require_payload_flags(label, row)
    _require_public_identifier(f"{label}.domain_team", row["domain_team"])
    _require_public_identifier(f"{label}.analyst_lane", row["analyst_lane"])
    _require_utc_datetime_text(
        f"{label}.calibration_checked_at",
        row["calibration_checked_at"],
    )
    _require_nonnegative_decimal_text(
        f"{label}.calibration_age_hours",
        row["calibration_age_hours"],
    )
    for field_name in (
        "information_yield_score",
        "calibration_freshness_score",
        "event_urgency_score",
        "liquidity_cost_pressure_score",
        "unresolved_evidence_gap_score",
        "attention_need_score",
    ):
        _require_ratio_decimal_text(f"{label}.{field_name}", row[field_name])
    _require_positive_count_decimal_text(f"{label}.allocation_rank", row["allocation_rank"])
    _require_status(f"{label}.status", row["status"])
    _validate_row_reason_code_texts(f"{label}.reason_codes", row["reason_codes"])
    _require_digest(f"{label}.validation_digest", row["validation_digest"])


def _validate_reason_count_payload_schema(label: str, row: object) -> None:
    if type(row) is not dict:
        raise ValueError("payload.reason_code_counts must contain JSON objects")
    _require_payload_fields(label, row, _REASON_COUNT_PAYLOAD_FIELDS)
    _require_payload_flags(label, row)
    _require_reason_code(
        f"{label}.reason_code",
        row["reason_code"],
        _REPORT_REASON_CODE_SEQUENCE,
    )
    _require_count_decimal_text(f"{label}.count", row["count"])
    _require_ratio_decimal_text(f"{label}.row_ratio", row["row_ratio"])


def _validate_payload_digest(payload: dict[str, object]) -> None:
    _validate_one_payload_digest("payload", payload)
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _validate_one_payload_digest(f"payload.rows[{index}]", row)


def _validate_one_payload_digest(label: str, payload: dict[str, object]) -> None:
    provided = payload.get(_DIGEST_FIELD)
    _require_digest(f"{label}.{_DIGEST_FIELD}", provided)
    digest_input = dict(payload)
    digest_input.pop(_DIGEST_FIELD, None)
    expected = _digest_from_mapping(digest_input)
    if provided != expected:
        raise ValueError("validation_digest does not match public payload")


def _require_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(f"unexpected public payload field in {label}")


def _require_payload_flags(label: str, payload: dict[str, object]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_utc_datetime_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO UTC datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be an ISO UTC datetime string")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{name} must be an ISO UTC datetime string")
    return value


def _require_nonnegative_decimal_text(name: str, value: object) -> Decimal:
    if type(value) is not str or not _DECIMAL_TEXT_RE.fullmatch(value):
        raise ValueError(f"{name} must be a Decimal string")
    return _require_nonnegative_decimal(name, Decimal(value))


def _require_count_decimal_text(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal_text(name, value)
    return _require_nonnegative_count_decimal(name, normalized)


def _require_positive_count_decimal_text(name: str, value: object) -> Decimal:
    normalized = _require_count_decimal_text(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal_text(name: str, value: object) -> Decimal:
    if type(value) is not str or not _DECIMAL_TEXT_RE.fullmatch(value):
        raise ValueError(f"{name} must be a Decimal string")
    return _require_ratio_decimal(name, Decimal(value))


def _validate_reason_code_texts(name: str, values: object) -> None:
    if type(values) is not list:
        raise ValueError(f"{name} must be a list")
    normalized = tuple(values)
    if _normalize_report_reason_codes(name, normalized) != normalized:
        raise ValueError(f"{name} must use deterministic sequence")


def _validate_row_reason_code_texts(name: str, values: object) -> None:
    if type(values) is not list:
        raise ValueError(f"{name} must be a list")
    normalized = tuple(values)
    if (
        _normalize_reason_codes(name, normalized, _ROW_REASON_CODE_SEQUENCE)
        != normalized
    ):
        raise ValueError(f"{name} must use deterministic sequence")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple) or (allow_json_containers and isinstance(value, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list):
        raise ValueError(f"{label} must use immutable sequences")
    if type(value) is str:
        if _DIGEST_RE.fullmatch(value):
            return
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
