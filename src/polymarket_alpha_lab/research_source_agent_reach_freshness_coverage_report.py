"""Pure report-only agent-reach source freshness coverage reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_AGENT_REACH_FRESHNESS_COVERAGE_REPORT_CONFIG_VERSION = (
    "research-source-agent-reach-freshness-coverage-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
HALF = Decimal("0.500000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "agent_reach_freshness_coverage_no_inputs"
PASS_REASON = "freshness_coverage_pass"
WATCH_REASON = "freshness_coverage_watch"
BLOCK_REASON = "freshness_coverage_block"

REASON_CODE_SEQUENCE = (
    "successful_retrieval_ratio_below_block_threshold",
    "successful_retrieval_ratio_below_watch_threshold",
    "recency_lag_above_block_threshold",
    "recency_lag_above_watch_threshold",
    "authority_confidence_below_block_threshold",
    "authority_confidence_below_watch_threshold",
    "conflict_coverage_below_block_threshold",
    "conflict_coverage_below_watch_threshold",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
REASON_CODE_RANK = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)
}

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
    "avg_successful_retrieval_ratio",
    "max_recency_lag_seconds",
    "avg_authority_confidence",
    "avg_conflict_coverage_ratio",
    "min_freshness_coverage_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = PUBLIC_PAYLOAD_FIELDS[:-1]

ROW_PAYLOAD_FIELDS = (
    "source_class",
    "retrieval_attempt_count",
    "successful_retrieval_count",
    "successful_retrieval_ratio",
    "recency_lag_seconds",
    "recency_freshness_score",
    "authority_confidence",
    "conflict_count",
    "covered_conflict_count",
    "conflict_coverage_ratio",
    "freshness_coverage_score",
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
    "candidate_slug",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_id",
    "source id",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "raw_url",
    "raw text",
    "url",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table_name",
    "table name",
    "table",
    "token",
    "wallet",
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
    "DEFAULT_RESEARCH_SOURCE_AGENT_REACH_FRESHNESS_COVERAGE_REPORT_CONFIG_VERSION",
    "ResearchSourceAgentReachFreshnessCoverageConfig",
    "ResearchSourceAgentReachFreshnessCoverageInput",
    "ResearchSourceAgentReachFreshnessCoverageReport",
    "ResearchSourceAgentReachFreshnessCoverageRow",
    "STATUSES",
    "build_research_source_agent_reach_freshness_coverage_report",
    "research_source_agent_reach_freshness_coverage_report_public_payload",
    "validate_research_source_agent_reach_freshness_coverage_report_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceAgentReachFreshnessCoverageConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AGENT_REACH_FRESHNESS_COVERAGE_REPORT_CONFIG_VERSION
    )
    watch_successful_retrieval_ratio: Decimal = Decimal("0.800000")
    block_successful_retrieval_ratio: Decimal = Decimal("0.500000")
    watch_recency_lag_seconds: Decimal = Decimal("86400.000000")
    block_recency_lag_seconds: Decimal = Decimal("259200.000000")
    watch_authority_confidence: Decimal = Decimal("0.700000")
    block_authority_confidence: Decimal = Decimal("0.400000")
    watch_conflict_coverage_ratio: Decimal = Decimal("0.750000")
    block_conflict_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAgentReachFreshnessCoverageConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAgentReachFreshnessCoverageConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AGENT_REACH_FRESHNESS_COVERAGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_successful_retrieval_ratio",
            "block_successful_retrieval_ratio",
            "watch_authority_confidence",
            "block_authority_confidence",
            "watch_conflict_coverage_ratio",
            "block_conflict_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_recency_lag_seconds", "block_recency_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_successful_retrieval_ratio > self.watch_successful_retrieval_ratio:
            raise ValueError(
                "block_successful_retrieval_ratio must not exceed "
                "watch_successful_retrieval_ratio",
            )
        if self.watch_recency_lag_seconds >= self.block_recency_lag_seconds:
            raise ValueError(
                "watch_recency_lag_seconds must be below block_recency_lag_seconds",
            )
        if self.block_authority_confidence > self.watch_authority_confidence:
            raise ValueError(
                "block_authority_confidence must not exceed watch_authority_confidence",
            )
        if self.block_conflict_coverage_ratio > self.watch_conflict_coverage_ratio:
            raise ValueError(
                "block_conflict_coverage_ratio must not exceed "
                "watch_conflict_coverage_ratio",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceAgentReachFreshnessCoverageInput:
    source_class: str
    retrieval_attempt_count: Decimal
    successful_retrieval_count: Decimal
    recency_lag_seconds: Decimal
    authority_confidence: Decimal
    conflict_count: Decimal
    covered_conflict_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAgentReachFreshnessCoverageInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAgentReachFreshnessCoverageInput, "input")
        _require_public_string("source_class", self.source_class)
        _reject_unsafe_public_text("source_class", self.source_class)
        for field_name in (
            "successful_retrieval_count",
            "conflict_count",
            "covered_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "retrieval_attempt_count",
            _normalize_positive_count_decimal(
                "retrieval_attempt_count",
                self.retrieval_attempt_count,
            ),
        )
        object.__setattr__(
            self,
            "recency_lag_seconds",
            _normalize_nonnegative_decimal("recency_lag_seconds", self.recency_lag_seconds),
        )
        object.__setattr__(
            self,
            "authority_confidence",
            _normalize_ratio_decimal("authority_confidence", self.authority_confidence),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)
        _validate_input(self)


@dataclass(frozen=True)
class ResearchSourceAgentReachFreshnessCoverageRow:
    source_class: str
    retrieval_attempt_count: Decimal
    successful_retrieval_count: Decimal
    successful_retrieval_ratio: Decimal
    recency_lag_seconds: Decimal
    recency_freshness_score: Decimal
    authority_confidence: Decimal
    conflict_count: Decimal
    covered_conflict_count: Decimal
    conflict_coverage_ratio: Decimal
    freshness_coverage_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAgentReachFreshnessCoverageRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAgentReachFreshnessCoverageRow, "row")
        _require_public_string("source_class", self.source_class)
        _reject_unsafe_public_text("source_class", self.source_class)
        for field_name in (
            "successful_retrieval_count",
            "conflict_count",
            "covered_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "retrieval_attempt_count",
            _normalize_positive_count_decimal(
                "retrieval_attempt_count",
                self.retrieval_attempt_count,
            ),
        )
        object.__setattr__(
            self,
            "recency_lag_seconds",
            _normalize_nonnegative_decimal("recency_lag_seconds", self.recency_lag_seconds),
        )
        for field_name in (
            "successful_retrieval_ratio",
            "recency_freshness_score",
            "authority_confidence",
            "conflict_coverage_ratio",
            "freshness_coverage_score",
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
class ResearchSourceAgentReachFreshnessCoverageReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    avg_successful_retrieval_ratio: Decimal
    max_recency_lag_seconds: Decimal
    avg_authority_confidence: Decimal
    avg_conflict_coverage_ratio: Decimal
    min_freshness_coverage_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAgentReachFreshnessCoverageRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAgentReachFreshnessCoverageReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAgentReachFreshnessCoverageReport, "report")
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
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "avg_successful_retrieval_ratio",
            "avg_authority_confidence",
            "avg_conflict_coverage_ratio",
            "min_freshness_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recency_lag_seconds",
            _normalize_nonnegative_decimal(
                "max_recency_lag_seconds",
                self.max_recency_lag_seconds,
            ),
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


def build_research_source_agent_reach_freshness_coverage_report(
    inputs: Iterable[ResearchSourceAgentReachFreshnessCoverageInput],
    *,
    config: ResearchSourceAgentReachFreshnessCoverageConfig,
    generated_at: datetime,
) -> ResearchSourceAgentReachFreshnessCoverageReport:
    if type(config) is not ResearchSourceAgentReachFreshnessCoverageConfig:
        raise ValueError(
            "config must be a ResearchSourceAgentReachFreshnessCoverageConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    row_count = _decimal_count(len(rows))
    return ResearchSourceAgentReachFreshnessCoverageReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        attention_count=_status_count(rows, "watch") + _status_count(rows, "block"),
        avg_successful_retrieval_ratio=_safe_ratio(
            _sum_decimals(row.successful_retrieval_ratio for row in rows),
            row_count,
        ),
        max_recency_lag_seconds=_max_decimal(
            (row.recency_lag_seconds for row in rows),
            default=ZERO,
        ),
        avg_authority_confidence=_safe_ratio(
            _sum_decimals(row.authority_confidence for row in rows),
            row_count,
        ),
        avg_conflict_coverage_ratio=_safe_ratio(
            _sum_decimals(row.conflict_coverage_ratio for row in rows),
            row_count,
        ),
        min_freshness_coverage_score=_min_decimal(
            (row.freshness_coverage_score for row in rows),
            default=ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_agent_reach_freshness_coverage_report_public_payload(
    report: ResearchSourceAgentReachFreshnessCoverageReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_payload("public payload", report)
        validate_research_source_agent_reach_freshness_coverage_report_public_payload(
            report,
        )
        return dict(report)
    if type(report) is not ResearchSourceAgentReachFreshnessCoverageReport:
        raise ValueError(
            "report must be a ResearchSourceAgentReachFreshnessCoverageReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report(report)
    payload = _report_public_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_source_agent_reach_freshness_coverage_report_public_payload(payload)
    return payload


def validate_research_source_agent_reach_freshness_coverage_report_public_payload(
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
    ):
        _decimal_from_payload_string(field_name, payload[field_name], require_integral=True)
    for field_name in (
        "avg_successful_retrieval_ratio",
        "max_recency_lag_seconds",
        "avg_authority_confidence",
        "avg_conflict_coverage_ratio",
        "min_freshness_coverage_score",
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
    value: ResearchSourceAgentReachFreshnessCoverageInput,
    *,
    config: ResearchSourceAgentReachFreshnessCoverageConfig,
) -> ResearchSourceAgentReachFreshnessCoverageRow:
    successful_retrieval_ratio = _safe_ratio(
        value.successful_retrieval_count,
        value.retrieval_attempt_count,
    )
    recency_freshness_score = _recency_freshness_score(
        value.recency_lag_seconds,
        config=config,
    )
    conflict_coverage_ratio = _conflict_coverage_ratio(
        value.covered_conflict_count,
        value.conflict_count,
    )
    freshness_coverage_score = min(
        successful_retrieval_ratio,
        recency_freshness_score,
        value.authority_confidence,
        conflict_coverage_ratio,
    )
    reason_codes = _reason_codes_for_input(
        value,
        successful_retrieval_ratio=successful_retrieval_ratio,
        conflict_coverage_ratio=conflict_coverage_ratio,
        config=config,
    )
    return ResearchSourceAgentReachFreshnessCoverageRow(
        source_class=value.source_class,
        retrieval_attempt_count=value.retrieval_attempt_count,
        successful_retrieval_count=value.successful_retrieval_count,
        successful_retrieval_ratio=successful_retrieval_ratio,
        recency_lag_seconds=value.recency_lag_seconds,
        recency_freshness_score=recency_freshness_score,
        authority_confidence=value.authority_confidence,
        conflict_count=value.conflict_count,
        covered_conflict_count=value.covered_conflict_count,
        conflict_coverage_ratio=conflict_coverage_ratio,
        freshness_coverage_score=freshness_coverage_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _reason_codes_for_input(
    value: ResearchSourceAgentReachFreshnessCoverageInput,
    *,
    successful_retrieval_ratio: Decimal,
    conflict_coverage_ratio: Decimal,
    config: ResearchSourceAgentReachFreshnessCoverageConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if successful_retrieval_ratio < config.block_successful_retrieval_ratio:
        reasons.append("successful_retrieval_ratio_below_block_threshold")
    elif successful_retrieval_ratio < config.watch_successful_retrieval_ratio:
        reasons.append("successful_retrieval_ratio_below_watch_threshold")
    if value.recency_lag_seconds >= config.block_recency_lag_seconds:
        reasons.append("recency_lag_above_block_threshold")
    elif value.recency_lag_seconds >= config.watch_recency_lag_seconds:
        reasons.append("recency_lag_above_watch_threshold")
    if value.authority_confidence < config.block_authority_confidence:
        reasons.append("authority_confidence_below_block_threshold")
    elif value.authority_confidence < config.watch_authority_confidence:
        reasons.append("authority_confidence_below_watch_threshold")
    if conflict_coverage_ratio < config.block_conflict_coverage_ratio:
        reasons.append("conflict_coverage_below_block_threshold")
    elif conflict_coverage_ratio < config.watch_conflict_coverage_ratio:
        reasons.append("conflict_coverage_below_watch_threshold")

    preliminary_status = _status_from_reason_codes(tuple(reasons))
    if preliminary_status == "block":
        reasons.append(BLOCK_REASON)
    elif preliminary_status == "watch":
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _recency_freshness_score(
    recency_lag_seconds: Decimal,
    *,
    config: ResearchSourceAgentReachFreshnessCoverageConfig,
) -> Decimal:
    if recency_lag_seconds >= config.block_recency_lag_seconds:
        return ZERO
    if recency_lag_seconds >= config.watch_recency_lag_seconds:
        return HALF
    return ONE


def _normalize_inputs(
    values: Iterable[ResearchSourceAgentReachFreshnessCoverageInput],
) -> tuple[ResearchSourceAgentReachFreshnessCoverageInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_source_classes: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchSourceAgentReachFreshnessCoverageInput:
            raise ValueError(
                "inputs must contain ResearchSourceAgentReachFreshnessCoverageInput values",
            )
        _require_hard_flags("input", value)
        _reject_unsafe_public_payload("input", value)
        if value.source_class in seen_source_classes:
            raise ValueError("inputs must not contain duplicate source_class values")
        seen_source_classes.add(value.source_class)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchSourceAgentReachFreshnessCoverageRow],
) -> tuple[ResearchSourceAgentReachFreshnessCoverageRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchSourceAgentReachFreshnessCoverageRow:
            raise ValueError(
                "rows must contain ResearchSourceAgentReachFreshnessCoverageRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic order")
    if len({row.source_class for row in rows}) != len(rows):
        raise ValueError("rows must have unique source_class values")
    return rows


def _row_sort_key(
    row: ResearchSourceAgentReachFreshnessCoverageRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        row.freshness_coverage_score,
        -row.recency_lag_seconds,
        row.authority_confidence,
        row.source_class,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code.endswith("_block_threshold") or reason_code == BLOCK_REASON
        for reason_code in reason_codes
    ):
        return "block"
    if any(
        reason_code.endswith("_watch_threshold") or reason_code == WATCH_REASON
        for reason_code in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceAgentReachFreshnessCoverageRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAgentReachFreshnessCoverageRow, ...],
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
    rows: tuple[ResearchSourceAgentReachFreshnessCoverageRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _validate_input(value: ResearchSourceAgentReachFreshnessCoverageInput) -> None:
    if value.successful_retrieval_count > value.retrieval_attempt_count:
        raise ValueError(
            "successful_retrieval_count must be at most retrieval_attempt_count",
        )
    if value.covered_conflict_count > value.conflict_count:
        raise ValueError("covered_conflict_count must be at most conflict_count")


def _validate_row(row: ResearchSourceAgentReachFreshnessCoverageRow) -> None:
    _validate_input(
        ResearchSourceAgentReachFreshnessCoverageInput(
            source_class=row.source_class,
            retrieval_attempt_count=row.retrieval_attempt_count,
            successful_retrieval_count=row.successful_retrieval_count,
            recency_lag_seconds=row.recency_lag_seconds,
            authority_confidence=row.authority_confidence,
            conflict_count=row.conflict_count,
            covered_conflict_count=row.covered_conflict_count,
        ),
    )
    if row.successful_retrieval_ratio != _safe_ratio(
        row.successful_retrieval_count,
        row.retrieval_attempt_count,
    ):
        raise ValueError("successful_retrieval_ratio must match retrieval counts")
    if row.conflict_coverage_ratio != _conflict_coverage_ratio(
        row.covered_conflict_count,
        row.conflict_count,
    ):
        raise ValueError("conflict_coverage_ratio must match conflict counts")
    if row.freshness_coverage_score != min(
        row.successful_retrieval_ratio,
        row.recency_freshness_score,
        row.authority_confidence,
        row.conflict_coverage_ratio,
    ):
        raise ValueError("freshness_coverage_score must match row dimensions")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason code only")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason code")
    if row.status == "block" and BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows must include freshness coverage block reason")
    if row.status == "watch" and WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows must include freshness coverage watch reason")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchSourceAgentReachFreshnessCoverageReport) -> None:
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
    if report.avg_successful_retrieval_ratio != _safe_ratio(
        _sum_decimals(row.successful_retrieval_ratio for row in report.rows),
        report.row_count,
    ):
        raise ValueError("avg_successful_retrieval_ratio must match rows")
    if report.max_recency_lag_seconds != _max_decimal(
        (row.recency_lag_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_recency_lag_seconds must match rows")
    if report.avg_authority_confidence != _safe_ratio(
        _sum_decimals(row.authority_confidence for row in report.rows),
        report.row_count,
    ):
        raise ValueError("avg_authority_confidence must match rows")
    if report.avg_conflict_coverage_ratio != _safe_ratio(
        _sum_decimals(row.conflict_coverage_ratio for row in report.rows),
        report.row_count,
    ):
        raise ValueError("avg_conflict_coverage_ratio must match rows")
    if report.min_freshness_coverage_score != _min_decimal(
        (row.freshness_coverage_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_freshness_coverage_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload_report_consistency(payload: dict[str, Any]) -> None:
    rows = tuple(_row_from_payload(row) for row in payload["rows"])
    ResearchSourceAgentReachFreshnessCoverageReport(
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
        avg_successful_retrieval_ratio=_decimal_from_payload_string(
            "avg_successful_retrieval_ratio",
            payload["avg_successful_retrieval_ratio"],
        ),
        max_recency_lag_seconds=_decimal_from_payload_string(
            "max_recency_lag_seconds",
            payload["max_recency_lag_seconds"],
        ),
        avg_authority_confidence=_decimal_from_payload_string(
            "avg_authority_confidence",
            payload["avg_authority_confidence"],
        ),
        avg_conflict_coverage_ratio=_decimal_from_payload_string(
            "avg_conflict_coverage_ratio",
            payload["avg_conflict_coverage_ratio"],
        ),
        min_freshness_coverage_score=_decimal_from_payload_string(
            "min_freshness_coverage_score",
            payload["min_freshness_coverage_score"],
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


def _row_from_payload(payload: object) -> ResearchSourceAgentReachFreshnessCoverageRow:
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    _reject_unsafe_public_payload("row payload", payload)
    _require_exact_keys("row payload", payload, ROW_PAYLOAD_FIELDS)
    _require_payload_hard_flags("row payload", payload)
    expected_digest = _payload_derived_validation_digest(
        {
            field_name: payload[field_name]
            for field_name in ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST
        },
    )
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match row payload fields")
    return ResearchSourceAgentReachFreshnessCoverageRow(
        source_class=payload["source_class"],
        retrieval_attempt_count=_decimal_from_payload_string(
            "retrieval_attempt_count",
            payload["retrieval_attempt_count"],
            require_integral=True,
        ),
        successful_retrieval_count=_decimal_from_payload_string(
            "successful_retrieval_count",
            payload["successful_retrieval_count"],
            require_integral=True,
        ),
        successful_retrieval_ratio=_decimal_from_payload_string(
            "successful_retrieval_ratio",
            payload["successful_retrieval_ratio"],
        ),
        recency_lag_seconds=_decimal_from_payload_string(
            "recency_lag_seconds",
            payload["recency_lag_seconds"],
        ),
        recency_freshness_score=_decimal_from_payload_string(
            "recency_freshness_score",
            payload["recency_freshness_score"],
        ),
        authority_confidence=_decimal_from_payload_string(
            "authority_confidence",
            payload["authority_confidence"],
        ),
        conflict_count=_decimal_from_payload_string(
            "conflict_count",
            payload["conflict_count"],
            require_integral=True,
        ),
        covered_conflict_count=_decimal_from_payload_string(
            "covered_conflict_count",
            payload["covered_conflict_count"],
            require_integral=True,
        ),
        conflict_coverage_ratio=_decimal_from_payload_string(
            "conflict_coverage_ratio",
            payload["conflict_coverage_ratio"],
        ),
        freshness_coverage_score=_decimal_from_payload_string(
            "freshness_coverage_score",
            payload["freshness_coverage_score"],
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
    if len({row.source_class for row in rows}) != len(rows):
        raise ValueError("rows must have unique source_class values")


def _report_public_payload_without_digest(
    report: ResearchSourceAgentReachFreshnessCoverageReport,
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
        "avg_successful_retrieval_ratio": _decimal_payload_value(
            report.avg_successful_retrieval_ratio,
        ),
        "max_recency_lag_seconds": _decimal_payload_value(
            report.max_recency_lag_seconds,
        ),
        "avg_authority_confidence": _decimal_payload_value(
            report.avg_authority_confidence,
        ),
        "avg_conflict_coverage_ratio": _decimal_payload_value(
            report.avg_conflict_coverage_ratio,
        ),
        "min_freshness_coverage_score": _decimal_payload_value(
            report.min_freshness_coverage_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_public_payload(
    row: ResearchSourceAgentReachFreshnessCoverageRow,
) -> dict[str, Any]:
    payload = _row_public_payload_without_digest(row)
    payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchSourceAgentReachFreshnessCoverageRow,
) -> dict[str, Any]:
    return {
        "source_class": row.source_class,
        "retrieval_attempt_count": _decimal_payload_value(row.retrieval_attempt_count),
        "successful_retrieval_count": _decimal_payload_value(
            row.successful_retrieval_count,
        ),
        "successful_retrieval_ratio": _decimal_payload_value(
            row.successful_retrieval_ratio,
        ),
        "recency_lag_seconds": _decimal_payload_value(row.recency_lag_seconds),
        "recency_freshness_score": _decimal_payload_value(
            row.recency_freshness_score,
        ),
        "authority_confidence": _decimal_payload_value(row.authority_confidence),
        "conflict_count": _decimal_payload_value(row.conflict_count),
        "covered_conflict_count": _decimal_payload_value(row.covered_conflict_count),
        "conflict_coverage_ratio": _decimal_payload_value(row.conflict_coverage_ratio),
        "freshness_coverage_score": _decimal_payload_value(
            row.freshness_coverage_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_derived_validation_digest(
    row: ResearchSourceAgentReachFreshnessCoverageRow,
) -> str:
    return _payload_derived_validation_digest(_row_public_payload_without_digest(row))


def _report_derived_validation_digest(
    report: ResearchSourceAgentReachFreshnessCoverageReport,
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


def _conflict_coverage_ratio(covered_count: Decimal, conflict_count: Decimal) -> Decimal:
    if conflict_count == ZERO:
        return ONE
    return _safe_ratio(covered_count, conflict_count)


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
    public_terms = lowered.replace("_", " ").replace("-", " ").split()
    if "auth" in public_terms:
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
