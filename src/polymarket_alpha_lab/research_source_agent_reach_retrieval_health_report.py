"""Pure report-only agent-reach retrieval health reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_AGENT_REACH_RETRIEVAL_HEALTH_REPORT_CONFIG_VERSION = (
    "research-source-agent-reach-retrieval-health-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
STATUS_PRESSURE_WEIGHT = {"pass": 0, "watch": 1, "block": 2}

NO_INPUTS_REASON = "agent_reach_retrieval_health_no_inputs"
PASS_REASON = "retrieval_health_pass"
WATCH_REASON = "retrieval_health_watch"
BLOCK_REASON = "retrieval_health_block"

REASON_CODE_SEQUENCE = (
    "freshness_age_above_block_threshold",
    "freshness_age_above_watch_threshold",
    "evidence_diversity_below_block_threshold",
    "evidence_diversity_below_watch_threshold",
    "source_quorum_below_block_threshold",
    "source_quorum_below_watch_threshold",
    "failed_retrieval_pressure_block",
    "failed_retrieval_pressure_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)}

PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
    "max_freshness_age_seconds",
    "total_retrieval_attempt_count",
    "total_failed_retrieval_count",
    "failed_retrieval_pressure_ratio",
    "avg_evidence_diversity_ratio",
    "avg_source_quorum_ratio",
    "min_retrieval_health_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = PUBLIC_PAYLOAD_FIELDS[:-1]
ROW_PAYLOAD_FIELDS = (
    "retrieval_ref",
    "freshness_age_seconds",
    "evidence_family_count",
    "required_evidence_family_count",
    "evidence_diversity_ratio",
    "source_quorum_count",
    "required_source_quorum_count",
    "source_quorum_ratio",
    "retrieval_attempt_count",
    "failed_retrieval_count",
    "failed_retrieval_pressure_ratio",
    "retrieval_health_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = ROW_PAYLOAD_FIELDS[:-1]

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "url",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "live_trading",
    "live trading",
    "sizing",
    "recommendation",
    "buy",
    "sell",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AGENT_REACH_RETRIEVAL_HEALTH_REPORT_CONFIG_VERSION",
    "ResearchSourceAgentReachRetrievalHealthConfig",
    "ResearchSourceAgentReachRetrievalHealthInput",
    "ResearchSourceAgentReachRetrievalHealthReport",
    "ResearchSourceAgentReachRetrievalHealthRow",
    "STATUSES",
    "build_research_source_agent_reach_retrieval_health_report",
    "research_source_agent_reach_retrieval_health_report_payload",
    "validate_research_source_agent_reach_retrieval_health_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceAgentReachRetrievalHealthConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AGENT_REACH_RETRIEVAL_HEALTH_REPORT_CONFIG_VERSION
    )
    watch_freshness_age_seconds: Decimal = Decimal("86400.000000")
    block_freshness_age_seconds: Decimal = Decimal("259200.000000")
    min_evidence_diversity_watch_ratio: Decimal = Decimal("0.750000")
    min_evidence_diversity_block_ratio: Decimal = Decimal("0.500000")
    min_source_quorum_watch_ratio: Decimal = Decimal("0.750000")
    min_source_quorum_block_ratio: Decimal = Decimal("0.500000")
    max_failed_retrieval_watch_ratio: Decimal = Decimal("0.250000")
    max_failed_retrieval_block_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAgentReachRetrievalHealthConfig:
            raise TypeError(
                "ResearchSourceAgentReachRetrievalHealthConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAgentReachRetrievalHealthConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AGENT_REACH_RETRIEVAL_HEALTH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_freshness_age_seconds", "block_freshness_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_freshness_age_seconds >= self.block_freshness_age_seconds:
            raise ValueError(
                "watch_freshness_age_seconds must be below block_freshness_age_seconds",
            )
        for field_name in (
            "min_evidence_diversity_watch_ratio",
            "min_evidence_diversity_block_ratio",
            "min_source_quorum_watch_ratio",
            "min_source_quorum_block_ratio",
            "max_failed_retrieval_watch_ratio",
            "max_failed_retrieval_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_evidence_diversity_block_ratio
            > self.min_evidence_diversity_watch_ratio
        ):
            raise ValueError(
                "min_evidence_diversity_block_ratio must not exceed watch threshold",
            )
        if self.min_source_quorum_block_ratio > self.min_source_quorum_watch_ratio:
            raise ValueError(
                "min_source_quorum_block_ratio must not exceed watch threshold",
            )
        if self.max_failed_retrieval_block_ratio < self.max_failed_retrieval_watch_ratio:
            raise ValueError(
                "max_failed_retrieval_block_ratio must not be below watch threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceAgentReachRetrievalHealthInput:
    retrieval_batch_ref: str
    freshness_age_seconds: Decimal
    evidence_family_count: Decimal
    required_evidence_family_count: Decimal
    source_quorum_count: Decimal
    required_source_quorum_count: Decimal
    retrieval_attempt_count: Decimal
    failed_retrieval_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAgentReachRetrievalHealthInput:
            raise TypeError(
                "ResearchSourceAgentReachRetrievalHealthInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAgentReachRetrievalHealthInput, "input")
        _require_public_string("retrieval_batch_ref", self.retrieval_batch_ref)
        _reject_unsafe_public_text("retrieval_batch_ref", self.retrieval_batch_ref)
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _normalize_nonnegative_decimal(
                "freshness_age_seconds",
                self.freshness_age_seconds,
            ),
        )
        for field_name in (
            "evidence_family_count",
            "source_quorum_count",
            "failed_retrieval_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_evidence_family_count",
            "required_source_quorum_count",
            "retrieval_attempt_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)
        _validate_input(self)


@dataclass(frozen=True)
class ResearchSourceAgentReachRetrievalHealthRow:
    retrieval_ref: str
    freshness_age_seconds: Decimal
    evidence_family_count: Decimal
    required_evidence_family_count: Decimal
    evidence_diversity_ratio: Decimal
    source_quorum_count: Decimal
    required_source_quorum_count: Decimal
    source_quorum_ratio: Decimal
    retrieval_attempt_count: Decimal
    failed_retrieval_count: Decimal
    failed_retrieval_pressure_ratio: Decimal
    retrieval_health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAgentReachRetrievalHealthRow:
            raise TypeError(
                "ResearchSourceAgentReachRetrievalHealthRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAgentReachRetrievalHealthRow, "row")
        _require_public_string("retrieval_ref", self.retrieval_ref)
        _reject_unsafe_public_text("retrieval_ref", self.retrieval_ref)
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _normalize_nonnegative_decimal(
                "freshness_age_seconds",
                self.freshness_age_seconds,
            ),
        )
        for field_name in (
            "evidence_family_count",
            "source_quorum_count",
            "failed_retrieval_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_evidence_family_count",
            "required_source_quorum_count",
            "retrieval_attempt_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_diversity_ratio",
            "source_quorum_ratio",
            "failed_retrieval_pressure_ratio",
            "retrieval_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchSourceAgentReachRetrievalHealthReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_freshness_age_seconds: Decimal
    total_retrieval_attempt_count: Decimal
    total_failed_retrieval_count: Decimal
    failed_retrieval_pressure_ratio: Decimal
    avg_evidence_diversity_ratio: Decimal
    avg_source_quorum_ratio: Decimal
    min_retrieval_health_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAgentReachRetrievalHealthRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAgentReachRetrievalHealthReport:
            raise TypeError(
                "ResearchSourceAgentReachRetrievalHealthReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAgentReachRetrievalHealthReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "total_retrieval_attempt_count",
            "total_failed_retrieval_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_freshness_age_seconds",
            "failed_retrieval_pressure_ratio",
            "avg_evidence_diversity_ratio",
            "avg_source_quorum_ratio",
            "min_retrieval_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_or_measure_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_source_agent_reach_retrieval_health_report(
    inputs: Iterable[ResearchSourceAgentReachRetrievalHealthInput],
    *,
    config: ResearchSourceAgentReachRetrievalHealthConfig,
    generated_at: datetime,
) -> ResearchSourceAgentReachRetrievalHealthReport:
    if type(config) is not ResearchSourceAgentReachRetrievalHealthConfig:
        raise ValueError(
            "config must be a ResearchSourceAgentReachRetrievalHealthConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)

    unranked_rows = tuple(_row_from_input(value, config=config) for value in normalized_inputs)
    sorted_rows = tuple(sorted(unranked_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_public_ref(row, index)
        for index, row in enumerate(sorted_rows, start=1)
    )
    row_count = _decimal_count(len(rows))
    total_retrieval_attempt_count = _sum_decimals(
        row.retrieval_attempt_count for row in rows
    )
    total_failed_retrieval_count = _sum_decimals(row.failed_retrieval_count for row in rows)

    return ResearchSourceAgentReachRetrievalHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        attention_count=_status_count(rows, "watch") + _status_count(rows, "block"),
        max_freshness_age_seconds=_max_decimal(
            (row.freshness_age_seconds for row in rows),
            default=ZERO,
        ),
        total_retrieval_attempt_count=total_retrieval_attempt_count,
        total_failed_retrieval_count=total_failed_retrieval_count,
        failed_retrieval_pressure_ratio=_safe_ratio(
            total_failed_retrieval_count,
            total_retrieval_attempt_count,
        ),
        avg_evidence_diversity_ratio=_safe_ratio(
            _sum_decimals(row.evidence_diversity_ratio for row in rows),
            row_count,
        ),
        avg_source_quorum_ratio=_safe_ratio(
            _sum_decimals(row.source_quorum_ratio for row in rows),
            row_count,
        ),
        min_retrieval_health_score=_min_decimal(
            (row.retrieval_health_score for row in rows),
            default=ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_agent_reach_retrieval_health_report_payload(
    report: ResearchSourceAgentReachRetrievalHealthReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_payload("public payload", report)
        validate_research_source_agent_reach_retrieval_health_report_payload(report)
        return dict(report)
    if type(report) is not ResearchSourceAgentReachRetrievalHealthReport:
        raise ValueError(
            "report must be a ResearchSourceAgentReachRetrievalHealthReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report(report)
    payload = _report_public_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_source_agent_reach_retrieval_health_report_payload(payload)
    return payload


def validate_research_source_agent_reach_retrieval_health_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _require_exact_keys("payload", payload, PUBLIC_PAYLOAD_FIELDS)
    _require_public_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_member("status", payload["status"], STATUSES)
    for field_name in (
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "total_retrieval_attempt_count",
        "total_failed_retrieval_count",
    ):
        _decimal_from_payload_string(field_name, payload[field_name], require_integral=True)
    for field_name in (
        "max_freshness_age_seconds",
        "failed_retrieval_pressure_ratio",
        "avg_evidence_diversity_ratio",
        "avg_source_quorum_ratio",
        "min_retrieval_health_score",
    ):
        _decimal_from_payload_string(field_name, payload[field_name])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _validate_payload_rows(payload["rows"])
    _require_payload_hard_flags("payload", payload)
    expected_digest = _payload_derived_validation_digest(
        {
            field_name: payload[field_name]
            for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
        },
    )
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")
    _validate_payload_report_consistency(payload)
    return True


def _row_from_input(
    value: ResearchSourceAgentReachRetrievalHealthInput,
    *,
    config: ResearchSourceAgentReachRetrievalHealthConfig,
) -> ResearchSourceAgentReachRetrievalHealthRow:
    evidence_diversity_ratio = _safe_ratio(
        value.evidence_family_count,
        value.required_evidence_family_count,
    )
    source_quorum_ratio = _safe_ratio(
        value.source_quorum_count,
        value.required_source_quorum_count,
    )
    failed_retrieval_pressure_ratio = _safe_ratio(
        value.failed_retrieval_count,
        value.retrieval_attempt_count,
    )
    freshness_score = _freshness_score(value.freshness_age_seconds, config=config)
    failed_retrieval_score = _failed_retrieval_score(
        failed_retrieval_pressure_ratio,
        config=config,
    )
    retrieval_health_score = min(
        freshness_score,
        evidence_diversity_ratio,
        source_quorum_ratio,
        failed_retrieval_score,
    )
    reason_codes = _reason_codes_for_input(
        value,
        evidence_diversity_ratio=evidence_diversity_ratio,
        source_quorum_ratio=source_quorum_ratio,
        failed_retrieval_pressure_ratio=failed_retrieval_pressure_ratio,
        config=config,
    )
    return ResearchSourceAgentReachRetrievalHealthRow(
        retrieval_ref=value.retrieval_batch_ref,
        freshness_age_seconds=value.freshness_age_seconds,
        evidence_family_count=value.evidence_family_count,
        required_evidence_family_count=value.required_evidence_family_count,
        evidence_diversity_ratio=evidence_diversity_ratio,
        source_quorum_count=value.source_quorum_count,
        required_source_quorum_count=value.required_source_quorum_count,
        source_quorum_ratio=source_quorum_ratio,
        retrieval_attempt_count=value.retrieval_attempt_count,
        failed_retrieval_count=value.failed_retrieval_count,
        failed_retrieval_pressure_ratio=failed_retrieval_pressure_ratio,
        retrieval_health_score=retrieval_health_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_with_public_ref(
    row: ResearchSourceAgentReachRetrievalHealthRow,
    index: int,
) -> ResearchSourceAgentReachRetrievalHealthRow:
    return ResearchSourceAgentReachRetrievalHealthRow(
        retrieval_ref=f"redacted-agent-reach-retrieval-{index:06d}",
        freshness_age_seconds=row.freshness_age_seconds,
        evidence_family_count=row.evidence_family_count,
        required_evidence_family_count=row.required_evidence_family_count,
        evidence_diversity_ratio=row.evidence_diversity_ratio,
        source_quorum_count=row.source_quorum_count,
        required_source_quorum_count=row.required_source_quorum_count,
        source_quorum_ratio=row.source_quorum_ratio,
        retrieval_attempt_count=row.retrieval_attempt_count,
        failed_retrieval_count=row.failed_retrieval_count,
        failed_retrieval_pressure_ratio=row.failed_retrieval_pressure_ratio,
        retrieval_health_score=row.retrieval_health_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _reason_codes_for_input(
    value: ResearchSourceAgentReachRetrievalHealthInput,
    *,
    evidence_diversity_ratio: Decimal,
    source_quorum_ratio: Decimal,
    failed_retrieval_pressure_ratio: Decimal,
    config: ResearchSourceAgentReachRetrievalHealthConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if value.freshness_age_seconds >= config.block_freshness_age_seconds:
        reasons.append("freshness_age_above_block_threshold")
    elif value.freshness_age_seconds >= config.watch_freshness_age_seconds:
        reasons.append("freshness_age_above_watch_threshold")
    if evidence_diversity_ratio < config.min_evidence_diversity_block_ratio:
        reasons.append("evidence_diversity_below_block_threshold")
    elif evidence_diversity_ratio < config.min_evidence_diversity_watch_ratio:
        reasons.append("evidence_diversity_below_watch_threshold")
    if source_quorum_ratio < config.min_source_quorum_block_ratio:
        reasons.append("source_quorum_below_block_threshold")
    elif source_quorum_ratio < config.min_source_quorum_watch_ratio:
        reasons.append("source_quorum_below_watch_threshold")
    if failed_retrieval_pressure_ratio >= config.max_failed_retrieval_block_ratio:
        reasons.append("failed_retrieval_pressure_block")
    elif failed_retrieval_pressure_ratio >= config.max_failed_retrieval_watch_ratio:
        reasons.append("failed_retrieval_pressure_watch")

    preliminary_status = _status_from_reason_codes(tuple(reasons))
    if preliminary_status == "block":
        reasons.append(BLOCK_REASON)
    elif preliminary_status == "watch":
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _freshness_score(
    freshness_age_seconds: Decimal,
    *,
    config: ResearchSourceAgentReachRetrievalHealthConfig,
) -> Decimal:
    if freshness_age_seconds >= config.block_freshness_age_seconds:
        return ZERO
    if freshness_age_seconds >= config.watch_freshness_age_seconds:
        return HALF
    return ONE


def _failed_retrieval_score(
    failed_retrieval_pressure_ratio: Decimal,
    *,
    config: ResearchSourceAgentReachRetrievalHealthConfig,
) -> Decimal:
    if failed_retrieval_pressure_ratio >= config.max_failed_retrieval_block_ratio:
        return ZERO
    if failed_retrieval_pressure_ratio >= config.max_failed_retrieval_watch_ratio:
        return HALF
    return ONE


def _normalize_inputs(
    values: Iterable[ResearchSourceAgentReachRetrievalHealthInput],
) -> tuple[ResearchSourceAgentReachRetrievalHealthInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchSourceAgentReachRetrievalHealthInput:
            raise ValueError(
                "inputs must contain ResearchSourceAgentReachRetrievalHealthInput values",
            )
        _require_hard_flags("input", value)
        _reject_unsafe_public_payload("input", value)
        if value.retrieval_batch_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate retrieval_batch_ref values")
        seen_refs.add(value.retrieval_batch_ref)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchSourceAgentReachRetrievalHealthRow],
) -> tuple[ResearchSourceAgentReachRetrievalHealthRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchSourceAgentReachRetrievalHealthRow:
            raise ValueError(
                "rows must contain ResearchSourceAgentReachRetrievalHealthRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic order")
    if len({row.retrieval_ref for row in rows}) != len(rows):
        raise ValueError("rows must have unique retrieval_ref values")
    return rows


def _row_sort_key(
    row: ResearchSourceAgentReachRetrievalHealthRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        row.retrieval_health_score,
        -row.freshness_age_seconds,
        -row.failed_retrieval_pressure_ratio,
        row.retrieval_ref,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") or reason_code == BLOCK_REASON for reason_code in reason_codes):
        return "block"
    if any(
        reason_code.endswith("_watch")
        or reason_code == WATCH_REASON
        or reason_code.endswith("_watch_threshold")
        for reason_code in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceAgentReachRetrievalHealthRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAgentReachRetrievalHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not reason_codes:
        return (PASS_REASON,)
    return tuple(sorted(reason_codes, key=_reason_code_sort_key))


def _reason_code_sort_key(reason_code: str) -> tuple[int, str]:
    return (REASON_CODE_RANK.get(reason_code, len(REASON_CODE_RANK)), reason_code)


def _status_count(
    rows: tuple[ResearchSourceAgentReachRetrievalHealthRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _validate_input(value: ResearchSourceAgentReachRetrievalHealthInput) -> None:
    if value.evidence_family_count > value.required_evidence_family_count:
        raise ValueError(
            "evidence_family_count must be at most required_evidence_family_count",
        )
    if value.source_quorum_count > value.required_source_quorum_count:
        raise ValueError(
            "source_quorum_count must be at most required_source_quorum_count",
        )
    if value.failed_retrieval_count > value.retrieval_attempt_count:
        raise ValueError("failed_retrieval_count must be at most retrieval_attempt_count")


def _validate_row(row: ResearchSourceAgentReachRetrievalHealthRow) -> None:
    _validate_input(
        ResearchSourceAgentReachRetrievalHealthInput(
            retrieval_batch_ref=row.retrieval_ref,
            freshness_age_seconds=row.freshness_age_seconds,
            evidence_family_count=row.evidence_family_count,
            required_evidence_family_count=row.required_evidence_family_count,
            source_quorum_count=row.source_quorum_count,
            required_source_quorum_count=row.required_source_quorum_count,
            retrieval_attempt_count=row.retrieval_attempt_count,
            failed_retrieval_count=row.failed_retrieval_count,
        ),
    )
    if row.evidence_diversity_ratio != _safe_ratio(
        row.evidence_family_count,
        row.required_evidence_family_count,
    ):
        raise ValueError("evidence_diversity_ratio must match evidence counts")
    if row.source_quorum_ratio != _safe_ratio(
        row.source_quorum_count,
        row.required_source_quorum_count,
    ):
        raise ValueError("source_quorum_ratio must match source quorum counts")
    if row.failed_retrieval_pressure_ratio != _safe_ratio(
        row.failed_retrieval_count,
        row.retrieval_attempt_count,
    ):
        raise ValueError(
            "failed_retrieval_pressure_ratio must match retrieval counts",
        )
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason code only")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason code")
    if row.status == "block" and BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows must include retrieval health block reason")
    if row.status == "watch" and WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows must include retrieval health watch reason")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchSourceAgentReachRetrievalHealthReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.attention_count != report.watch_count + report.block_count:
        raise ValueError("attention_count must match watch and block counts")
    if report.max_freshness_age_seconds != _max_decimal(
        (row.freshness_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_freshness_age_seconds must match rows")
    if report.total_retrieval_attempt_count != _sum_decimals(
        row.retrieval_attempt_count for row in report.rows
    ):
        raise ValueError("total_retrieval_attempt_count must match rows")
    if report.total_failed_retrieval_count != _sum_decimals(
        row.failed_retrieval_count for row in report.rows
    ):
        raise ValueError("total_failed_retrieval_count must match rows")
    if report.failed_retrieval_pressure_ratio != _safe_ratio(
        report.total_failed_retrieval_count,
        report.total_retrieval_attempt_count,
    ):
        raise ValueError("failed_retrieval_pressure_ratio must match rows")
    if report.avg_evidence_diversity_ratio != _safe_ratio(
        _sum_decimals(row.evidence_diversity_ratio for row in report.rows),
        report.row_count,
    ):
        raise ValueError("avg_evidence_diversity_ratio must match rows")
    if report.avg_source_quorum_ratio != _safe_ratio(
        _sum_decimals(row.source_quorum_ratio for row in report.rows),
        report.row_count,
    ):
        raise ValueError("avg_source_quorum_ratio must match rows")
    if report.min_retrieval_health_score != _min_decimal(
        (row.retrieval_health_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_retrieval_health_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload_report_consistency(payload: dict[str, Any]) -> None:
    rows = tuple(_row_from_payload(row) for row in payload["rows"])
    ResearchSourceAgentReachRetrievalHealthReport(
        generated_at=_datetime_from_payload_string("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        status=payload["status"],
        input_count=_decimal_from_payload_string(
            "input_count",
            payload["input_count"],
            require_integral=True,
        ),
        row_count=_decimal_from_payload_string(
            "row_count",
            payload["row_count"],
            require_integral=True,
        ),
        pass_count=_decimal_from_payload_string(
            "pass_count",
            payload["pass_count"],
            require_integral=True,
        ),
        watch_count=_decimal_from_payload_string(
            "watch_count",
            payload["watch_count"],
            require_integral=True,
        ),
        block_count=_decimal_from_payload_string(
            "block_count",
            payload["block_count"],
            require_integral=True,
        ),
        attention_count=_decimal_from_payload_string(
            "attention_count",
            payload["attention_count"],
            require_integral=True,
        ),
        max_freshness_age_seconds=_decimal_from_payload_string(
            "max_freshness_age_seconds",
            payload["max_freshness_age_seconds"],
        ),
        total_retrieval_attempt_count=_decimal_from_payload_string(
            "total_retrieval_attempt_count",
            payload["total_retrieval_attempt_count"],
            require_integral=True,
        ),
        total_failed_retrieval_count=_decimal_from_payload_string(
            "total_failed_retrieval_count",
            payload["total_failed_retrieval_count"],
            require_integral=True,
        ),
        failed_retrieval_pressure_ratio=_decimal_from_payload_string(
            "failed_retrieval_pressure_ratio",
            payload["failed_retrieval_pressure_ratio"],
        ),
        avg_evidence_diversity_ratio=_decimal_from_payload_string(
            "avg_evidence_diversity_ratio",
            payload["avg_evidence_diversity_ratio"],
        ),
        avg_source_quorum_ratio=_decimal_from_payload_string(
            "avg_source_quorum_ratio",
            payload["avg_source_quorum_ratio"],
        ),
        min_retrieval_health_score=_decimal_from_payload_string(
            "min_retrieval_health_score",
            payload["min_retrieval_health_score"],
        ),
        reason_codes=_normalize_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        rows=rows,
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_payload(payload: object) -> ResearchSourceAgentReachRetrievalHealthRow:
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    _reject_unsafe_public_payload("row payload", payload)
    _require_exact_keys("row payload", payload, ROW_PAYLOAD_FIELDS)
    _require_payload_hard_flags("row payload", payload)
    expected_digest = _payload_derived_validation_digest(
        {field_name: payload[field_name] for field_name in ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST},
    )
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match row payload fields")
    return ResearchSourceAgentReachRetrievalHealthRow(
        retrieval_ref=payload["retrieval_ref"],
        freshness_age_seconds=_decimal_from_payload_string(
            "freshness_age_seconds",
            payload["freshness_age_seconds"],
        ),
        evidence_family_count=_decimal_from_payload_string(
            "evidence_family_count",
            payload["evidence_family_count"],
            require_integral=True,
        ),
        required_evidence_family_count=_decimal_from_payload_string(
            "required_evidence_family_count",
            payload["required_evidence_family_count"],
            require_integral=True,
        ),
        evidence_diversity_ratio=_decimal_from_payload_string(
            "evidence_diversity_ratio",
            payload["evidence_diversity_ratio"],
        ),
        source_quorum_count=_decimal_from_payload_string(
            "source_quorum_count",
            payload["source_quorum_count"],
            require_integral=True,
        ),
        required_source_quorum_count=_decimal_from_payload_string(
            "required_source_quorum_count",
            payload["required_source_quorum_count"],
            require_integral=True,
        ),
        source_quorum_ratio=_decimal_from_payload_string(
            "source_quorum_ratio",
            payload["source_quorum_ratio"],
        ),
        retrieval_attempt_count=_decimal_from_payload_string(
            "retrieval_attempt_count",
            payload["retrieval_attempt_count"],
            require_integral=True,
        ),
        failed_retrieval_count=_decimal_from_payload_string(
            "failed_retrieval_count",
            payload["failed_retrieval_count"],
            require_integral=True,
        ),
        failed_retrieval_pressure_ratio=_decimal_from_payload_string(
            "failed_retrieval_pressure_ratio",
            payload["failed_retrieval_pressure_ratio"],
        ),
        retrieval_health_score=_decimal_from_payload_string(
            "retrieval_health_score",
            payload["retrieval_health_score"],
        ),
        status=payload["status"],
        reason_codes=_normalize_public_reason_codes("reason_codes", payload["reason_codes"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _validate_payload_rows(payload: object) -> None:
    if type(payload) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_payload(row) for row in payload)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic order")
    if len({row.retrieval_ref for row in rows}) != len(rows):
        raise ValueError("rows must have unique retrieval_ref values")


def _report_public_payload_without_digest(
    report: ResearchSourceAgentReachRetrievalHealthReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload_value(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "input_count": _decimal_payload_value(report.input_count),
        "row_count": _decimal_payload_value(report.row_count),
        "pass_count": _decimal_payload_value(report.pass_count),
        "watch_count": _decimal_payload_value(report.watch_count),
        "block_count": _decimal_payload_value(report.block_count),
        "attention_count": _decimal_payload_value(report.attention_count),
        "max_freshness_age_seconds": _decimal_payload_value(
            report.max_freshness_age_seconds,
        ),
        "total_retrieval_attempt_count": _decimal_payload_value(
            report.total_retrieval_attempt_count,
        ),
        "total_failed_retrieval_count": _decimal_payload_value(
            report.total_failed_retrieval_count,
        ),
        "failed_retrieval_pressure_ratio": _decimal_payload_value(
            report.failed_retrieval_pressure_ratio,
        ),
        "avg_evidence_diversity_ratio": _decimal_payload_value(
            report.avg_evidence_diversity_ratio,
        ),
        "avg_source_quorum_ratio": _decimal_payload_value(report.avg_source_quorum_ratio),
        "min_retrieval_health_score": _decimal_payload_value(
            report.min_retrieval_health_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_public_payload(
    row: ResearchSourceAgentReachRetrievalHealthRow,
) -> dict[str, Any]:
    payload = _row_public_payload_without_digest(row)
    payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchSourceAgentReachRetrievalHealthRow,
) -> dict[str, Any]:
    return {
        "retrieval_ref": row.retrieval_ref,
        "freshness_age_seconds": _decimal_payload_value(row.freshness_age_seconds),
        "evidence_family_count": _decimal_payload_value(row.evidence_family_count),
        "required_evidence_family_count": _decimal_payload_value(
            row.required_evidence_family_count,
        ),
        "evidence_diversity_ratio": _decimal_payload_value(
            row.evidence_diversity_ratio,
        ),
        "source_quorum_count": _decimal_payload_value(row.source_quorum_count),
        "required_source_quorum_count": _decimal_payload_value(
            row.required_source_quorum_count,
        ),
        "source_quorum_ratio": _decimal_payload_value(row.source_quorum_ratio),
        "retrieval_attempt_count": _decimal_payload_value(row.retrieval_attempt_count),
        "failed_retrieval_count": _decimal_payload_value(row.failed_retrieval_count),
        "failed_retrieval_pressure_ratio": _decimal_payload_value(
            row.failed_retrieval_pressure_ratio,
        ),
        "retrieval_health_score": _decimal_payload_value(row.retrieval_health_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_derived_validation_digest(
    row: ResearchSourceAgentReachRetrievalHealthRow,
) -> str:
    return _payload_derived_validation_digest(_row_public_payload_without_digest(row))


def _report_derived_validation_digest(
    report: ResearchSourceAgentReachRetrievalHealthReport,
) -> str:
    return _payload_derived_validation_digest(_report_public_payload_without_digest(report))


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    return max(normalized)


def _min_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    return min(normalized)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _normalize_public_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(values))


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        _require_public_string(field_name, value)
        if value not in REASON_CODE_RANK:
            raise ValueError(f"{field_name} contains unsupported reason code")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")
    if tuple(sorted(values, key=_reason_code_sort_key)) != values:
        raise ValueError(f"{field_name} must use deterministic order")
    return values


def _normalize_ratio_or_measure_decimal(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_payload_value(value: Decimal) -> str:
    normalized = _normalize_decimal("payload Decimal", value)
    return format(normalized, "f")


def _decimal_from_payload_string(
    field_name: str,
    value: object,
    *,
    require_integral: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _normalize_nonnegative_decimal(field_name, parsed)
    if _decimal_payload_value(normalized) != value:
        raise ValueError(f"{field_name} must be canonical")
    if require_integral and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_payload_value(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _require_public_datetime_string(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    _datetime_from_payload_string(field_name, value)


def _datetime_from_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != expected_keys:
        raise ValueError(f"{label} must contain exact public payload fields")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for item in _surface_items(value):
        _reject_unsafe_public_text(label, item)


def _reject_unsafe_public_text(label: str, value: object) -> None:
    if type(value) is not str:
        return
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}: {value}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if type(value) is dict:
        items = []
        for key, item in value.items():
            items.extend(_surface_items(key))
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) in (list, tuple):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()
