"""Pure public report for aggregate resolution-rule memory health."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
from typing import Any


DEFAULT_RESEARCH_RESOLUTION_RULE_MEMORY_HEALTH_CONFIG_VERSION = (
    "research-resolution-rule-memory-health-report-v0"
)
STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "resolution_rule_memory_health_passed"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
DECIMAL_PLACES = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

PATTERN_MEMORY_CONFIDENCE_BLOCK_REASON = "pattern_memory_confidence_block"
RULE_CHANGE_RISK_BLOCK_REASON = "rule_change_risk_block"
AMBIGUITY_BACKLOG_BLOCK_REASON = "ambiguity_backlog_block"
RECHECK_URGENCY_BLOCK_REASON = "recheck_urgency_block"
PATTERN_MEMORY_CONFIDENCE_WATCH_REASON = "pattern_memory_confidence_watch"
RULE_CHANGE_RISK_WATCH_REASON = "rule_change_risk_watch"
AMBIGUITY_BACKLOG_WATCH_REASON = "ambiguity_backlog_watch"
RECHECK_URGENCY_WATCH_REASON = "recheck_urgency_watch"
NO_PATTERNS_BLOCK_REASON = "no_resolution_rule_memory_patterns_block"

REASON_CODE_SEQUENCE = (
    PATTERN_MEMORY_CONFIDENCE_BLOCK_REASON,
    RULE_CHANGE_RISK_BLOCK_REASON,
    AMBIGUITY_BACKLOG_BLOCK_REASON,
    RECHECK_URGENCY_BLOCK_REASON,
    PATTERN_MEMORY_CONFIDENCE_WATCH_REASON,
    RULE_CHANGE_RISK_WATCH_REASON,
    AMBIGUITY_BACKLOG_WATCH_REASON,
    RECHECK_URGENCY_WATCH_REASON,
    NO_PATTERNS_BLOCK_REASON,
    PASS_REASON_CODE,
)
BLOCK_REASONS = (
    PATTERN_MEMORY_CONFIDENCE_BLOCK_REASON,
    RULE_CHANGE_RISK_BLOCK_REASON,
    AMBIGUITY_BACKLOG_BLOCK_REASON,
    RECHECK_URGENCY_BLOCK_REASON,
    NO_PATTERNS_BLOCK_REASON,
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "pattern_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_pattern_observation_count",
    "total_confirmed_resolution_count",
    "total_ambiguity_backlog_count",
    "rule_change_risk_count",
    "ambiguity_backlog_pattern_count",
    "urgent_recheck_pattern_count",
    "average_pattern_memory_confidence",
    "max_rule_change_risk_score",
    "max_recheck_urgency_score",
    "rows",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = (
    *PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "url",
    "uri",
    "raw",
    "ref",
    "source",
    "market",
    "condition",
    "question",
    "slug",
    "account",
    "balance",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "private",
    "credential",
    "secret",
    "token",
)
UNSAFE_PUBLIC_TEXT_TOKENS = (
    "://",
    "source_url",
    "raw_text",
    "raw_ref",
    "source",
    "market",
    "market_id",
    "condition_id",
    "question",
    "slug",
    "account",
    "balance",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "live",
    "execute",
    "re" + "commend",
    "siz" + "ing",
    "private",
    "credential",
    "secret",
    "token",
)

__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_RULE_MEMORY_HEALTH_CONFIG_VERSION",
    "STATUSES",
    "ResearchResolutionRuleMemoryHealthConfig",
    "ResearchResolutionRuleMemoryHealthObservation",
    "ResearchResolutionRuleMemoryHealthReport",
    "ResearchResolutionRuleMemoryHealthRow",
    "build_research_resolution_rule_memory_health_report",
    "research_resolution_rule_memory_health_report_payload",
)


@dataclass(frozen=True)
class ResearchResolutionRuleMemoryHealthConfig:
    config_version: str = DEFAULT_RESEARCH_RESOLUTION_RULE_MEMORY_HEALTH_CONFIG_VERSION
    min_pattern_memory_confidence_watch: Decimal = Decimal("0.700000")
    min_pattern_memory_confidence_block: Decimal = Decimal("0.400000")
    rule_change_risk_watch_score: Decimal = Decimal("0.300000")
    rule_change_risk_block_score: Decimal = Decimal("0.750000")
    ambiguity_backlog_watch_count: Decimal = Decimal("2")
    ambiguity_backlog_block_count: Decimal = Decimal("5")
    recheck_watch_age_seconds: Decimal = Decimal("604800")
    recheck_block_age_seconds: Decimal = Decimal("2592000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleMemoryHealthConfig:
            raise TypeError(
                "ResearchResolutionRuleMemoryHealthConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleMemoryHealthConfig:
            raise ValueError(
                "config must be exactly ResearchResolutionRuleMemoryHealthConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pattern_memory_confidence_watch",
            "min_pattern_memory_confidence_block",
            "rule_change_risk_watch_score",
            "rule_change_risk_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ambiguity_backlog_watch_count",
            "ambiguity_backlog_block_count",
            "recheck_watch_age_seconds",
            "recheck_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pattern_memory_confidence_block
            > self.min_pattern_memory_confidence_watch
        ):
            raise ValueError(
                "min_pattern_memory_confidence_block must be <= "
                "min_pattern_memory_confidence_watch",
            )
        if self.rule_change_risk_watch_score > self.rule_change_risk_block_score:
            raise ValueError(
                "rule_change_risk_watch_score must be <= "
                "rule_change_risk_block_score",
            )
        if self.ambiguity_backlog_watch_count > self.ambiguity_backlog_block_count:
            raise ValueError(
                "ambiguity_backlog_watch_count must be <= "
                "ambiguity_backlog_block_count",
            )
        if self.recheck_watch_age_seconds > self.recheck_block_age_seconds:
            raise ValueError(
                "recheck_watch_age_seconds must be <= recheck_block_age_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionRuleMemoryHealthObservation:
    rule_pattern: str
    pattern_observation_count: Decimal
    confirmed_resolution_count: Decimal
    rule_change_risk_score: Decimal
    ambiguity_backlog_count: Decimal
    last_rechecked_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleMemoryHealthObservation:
            raise TypeError(
                "ResearchResolutionRuleMemoryHealthObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleMemoryHealthObservation:
            raise ValueError(
                "observation must be exactly ResearchResolutionRuleMemoryHealthObservation",
            )
        object.__setattr__(
            self,
            "rule_pattern",
            _normalize_rule_pattern("rule_pattern", self.rule_pattern),
        )
        for field_name in (
            "pattern_observation_count",
            "confirmed_resolution_count",
            "ambiguity_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.pattern_observation_count == ZERO:
            raise ValueError("pattern_observation_count must be positive")
        if self.confirmed_resolution_count > self.pattern_observation_count:
            raise ValueError(
                "confirmed_resolution_count must be <= pattern_observation_count",
            )
        object.__setattr__(
            self,
            "rule_change_risk_score",
            _normalize_probability_decimal(
                "rule_change_risk_score",
                self.rule_change_risk_score,
            ),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_utc("last_rechecked_at", self.last_rechecked_at),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchResolutionRuleMemoryHealthRow:
    rule_pattern: str
    pattern_observation_count: Decimal
    confirmed_resolution_count: Decimal
    pattern_memory_confidence: Decimal
    rule_change_risk_score: Decimal
    ambiguity_backlog_count: Decimal
    seconds_since_recheck: Decimal
    recheck_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleMemoryHealthRow:
            raise TypeError(
                "ResearchResolutionRuleMemoryHealthRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleMemoryHealthRow:
            raise ValueError("row must be exactly ResearchResolutionRuleMemoryHealthRow")
        object.__setattr__(
            self,
            "rule_pattern",
            _normalize_rule_pattern("rule_pattern", self.rule_pattern),
        )
        for field_name in (
            "pattern_observation_count",
            "confirmed_resolution_count",
            "ambiguity_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "pattern_memory_confidence",
            "rule_change_risk_score",
            "recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seconds_since_recheck",
            _normalize_nonnegative_decimal(
                "seconds_since_recheck",
                self.seconds_since_recheck,
            ),
        )
        if self.pattern_observation_count == ZERO:
            raise ValueError("pattern_observation_count must be positive")
        if self.confirmed_resolution_count > self.pattern_observation_count:
            raise ValueError(
                "confirmed_resolution_count must be <= pattern_observation_count",
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_status_reason_codes(self.status, self.reason_codes, "row")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchResolutionRuleMemoryHealthReport:
    generated_at: datetime
    config_version: str
    pattern_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_pattern_observation_count: Decimal
    total_confirmed_resolution_count: Decimal
    total_ambiguity_backlog_count: Decimal
    rule_change_risk_count: Decimal
    ambiguity_backlog_pattern_count: Decimal
    urgent_recheck_pattern_count: Decimal
    average_pattern_memory_confidence: Decimal
    max_rule_change_risk_score: Decimal
    max_recheck_urgency_score: Decimal
    rows: tuple[ResearchResolutionRuleMemoryHealthRow, ...]
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleMemoryHealthReport:
            raise TypeError(
                "ResearchResolutionRuleMemoryHealthReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleMemoryHealthReport:
            raise ValueError(
                "report must be exactly ResearchResolutionRuleMemoryHealthReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pattern_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_pattern_observation_count",
            "total_confirmed_resolution_count",
            "total_ambiguity_backlog_count",
            "rule_change_risk_count",
            "ambiguity_backlog_pattern_count",
            "urgent_recheck_pattern_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_pattern_memory_confidence",
            "max_rule_change_risk_score",
            "max_recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_research_resolution_rule_memory_health_report(
    observations: tuple[ResearchResolutionRuleMemoryHealthObservation, ...],
    *,
    config: ResearchResolutionRuleMemoryHealthConfig,
    generated_at: datetime,
) -> ResearchResolutionRuleMemoryHealthReport:
    if type(config) is not ResearchResolutionRuleMemoryHealthConfig:
        raise ValueError(
            "config must be a ResearchResolutionRuleMemoryHealthConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_observations(observations)
    for item in inputs:
        if item.last_rechecked_at > generated_at_utc:
            raise ValueError("last_rechecked_at must not be after generated_at")
    rows = tuple(_build_row(item, config, generated_at_utc) for item in inputs)
    report_reason_codes = _report_reason_codes(rows)
    return ResearchResolutionRuleMemoryHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        pattern_count=_count_decimal(len(rows)),
        pass_count=_count_decimal(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count_decimal(sum(1 for row in rows if row.status == "watch")),
        block_count=_count_decimal(sum(1 for row in rows if row.status == "block")),
        total_pattern_observation_count=_sum_decimal(
            row.pattern_observation_count for row in rows
        ),
        total_confirmed_resolution_count=_sum_decimal(
            row.confirmed_resolution_count for row in rows
        ),
        total_ambiguity_backlog_count=_sum_decimal(
            row.ambiguity_backlog_count for row in rows
        ),
        rule_change_risk_count=_count_decimal(
            sum(
                1
                for row in rows
                if RULE_CHANGE_RISK_WATCH_REASON in row.reason_codes
                or RULE_CHANGE_RISK_BLOCK_REASON in row.reason_codes
            ),
        ),
        ambiguity_backlog_pattern_count=_count_decimal(
            sum(
                1
                for row in rows
                if AMBIGUITY_BACKLOG_WATCH_REASON in row.reason_codes
                or AMBIGUITY_BACKLOG_BLOCK_REASON in row.reason_codes
            ),
        ),
        urgent_recheck_pattern_count=_count_decimal(
            sum(
                1
                for row in rows
                if RECHECK_URGENCY_WATCH_REASON in row.reason_codes
                or RECHECK_URGENCY_BLOCK_REASON in row.reason_codes
            ),
        ),
        average_pattern_memory_confidence=_average_pattern_memory_confidence(rows),
        max_rule_change_risk_score=max(
            (row.rule_change_risk_score for row in rows),
            default=ZERO,
        ),
        max_recheck_urgency_score=max(
            (row.recheck_urgency_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        status=_status_from_reason_codes(report_reason_codes),
        reason_codes=report_reason_codes,
    )


def research_resolution_rule_memory_health_report_payload(
    report: ResearchResolutionRuleMemoryHealthReport | dict[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchResolutionRuleMemoryHealthReport:
        _require_hard_flags("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _reject_unsafe_public_payload("report payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a ResearchResolutionRuleMemoryHealthReport",
    )


def _build_row(
    observation: ResearchResolutionRuleMemoryHealthObservation,
    config: ResearchResolutionRuleMemoryHealthConfig,
    generated_at: datetime,
) -> ResearchResolutionRuleMemoryHealthRow:
    seconds_since_recheck = _age_seconds(generated_at, observation.last_rechecked_at)
    pattern_memory_confidence = _quantized(
        observation.confirmed_resolution_count / observation.pattern_observation_count,
    )
    recheck_urgency_score = _bounded_probability(
        seconds_since_recheck / config.recheck_block_age_seconds,
    )
    reason_codes = _row_reason_codes(
        pattern_memory_confidence=pattern_memory_confidence,
        rule_change_risk_score=observation.rule_change_risk_score,
        ambiguity_backlog_count=observation.ambiguity_backlog_count,
        seconds_since_recheck=seconds_since_recheck,
        config=config,
    )
    return ResearchResolutionRuleMemoryHealthRow(
        rule_pattern=observation.rule_pattern,
        pattern_observation_count=observation.pattern_observation_count,
        confirmed_resolution_count=observation.confirmed_resolution_count,
        pattern_memory_confidence=pattern_memory_confidence,
        rule_change_risk_score=_quantized(observation.rule_change_risk_score),
        ambiguity_backlog_count=observation.ambiguity_backlog_count,
        seconds_since_recheck=_quantized(seconds_since_recheck),
        recheck_urgency_score=recheck_urgency_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    pattern_memory_confidence: Decimal,
    rule_change_risk_score: Decimal,
    ambiguity_backlog_count: Decimal,
    seconds_since_recheck: Decimal,
    config: ResearchResolutionRuleMemoryHealthConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if pattern_memory_confidence < config.min_pattern_memory_confidence_block:
        reason_codes.append(PATTERN_MEMORY_CONFIDENCE_BLOCK_REASON)
    elif pattern_memory_confidence < config.min_pattern_memory_confidence_watch:
        reason_codes.append(PATTERN_MEMORY_CONFIDENCE_WATCH_REASON)
    if rule_change_risk_score >= config.rule_change_risk_block_score:
        reason_codes.append(RULE_CHANGE_RISK_BLOCK_REASON)
    elif rule_change_risk_score >= config.rule_change_risk_watch_score:
        reason_codes.append(RULE_CHANGE_RISK_WATCH_REASON)
    if ambiguity_backlog_count >= config.ambiguity_backlog_block_count:
        reason_codes.append(AMBIGUITY_BACKLOG_BLOCK_REASON)
    elif ambiguity_backlog_count >= config.ambiguity_backlog_watch_count:
        reason_codes.append(AMBIGUITY_BACKLOG_WATCH_REASON)
    if seconds_since_recheck >= config.recheck_block_age_seconds:
        reason_codes.append(RECHECK_URGENCY_BLOCK_REASON)
    elif seconds_since_recheck >= config.recheck_watch_age_seconds:
        reason_codes.append(RECHECK_URGENCY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _report_reason_codes(
    rows: tuple[ResearchResolutionRuleMemoryHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PATTERNS_BLOCK_REASON,)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    }
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _normalize_observations(
    observations: object,
) -> tuple[ResearchResolutionRuleMemoryHealthObservation, ...]:
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    normalized = tuple(observations)
    seen_patterns: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchResolutionRuleMemoryHealthObservation:
            raise ValueError(
                "observations must contain exact resolution rule memory inputs",
            )
        _require_hard_flags("observation", item)
        if item.rule_pattern in seen_patterns:
            raise ValueError("observations must contain unique rule patterns")
        seen_patterns.add(item.rule_pattern)
    return tuple(sorted(normalized, key=lambda item: item.rule_pattern))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchResolutionRuleMemoryHealthRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    previous_pattern: str | None = None
    for row in normalized:
        if type(row) is not ResearchResolutionRuleMemoryHealthRow:
            raise ValueError(
                "rows must contain exact resolution rule memory rows",
            )
        _require_hard_flags("row", row)
        if previous_pattern is not None and row.rule_pattern <= previous_pattern:
            raise ValueError("rows must be deterministic")
        previous_pattern = row.rule_pattern
    return normalized


def _validate_report_consistency(
    report: ResearchResolutionRuleMemoryHealthReport,
) -> None:
    _validate_status_reason_codes(report.status, report.reason_codes, "report")
    if report.pattern_count != _count_decimal(len(report.rows)):
        raise ValueError("pattern_count must match rows")
    if report.pass_count != _count_decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.total_pattern_observation_count != _sum_decimal(
        row.pattern_observation_count for row in report.rows
    ):
        raise ValueError("total_pattern_observation_count must match rows")
    if report.total_confirmed_resolution_count != _sum_decimal(
        row.confirmed_resolution_count for row in report.rows
    ):
        raise ValueError("total_confirmed_resolution_count must match rows")
    if report.total_ambiguity_backlog_count != _sum_decimal(
        row.ambiguity_backlog_count for row in report.rows
    ):
        raise ValueError("total_ambiguity_backlog_count must match rows")
    if report.rule_change_risk_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if RULE_CHANGE_RISK_WATCH_REASON in row.reason_codes
            or RULE_CHANGE_RISK_BLOCK_REASON in row.reason_codes
        ),
    ):
        raise ValueError("rule_change_risk_count must match rows")
    if report.ambiguity_backlog_pattern_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if AMBIGUITY_BACKLOG_WATCH_REASON in row.reason_codes
            or AMBIGUITY_BACKLOG_BLOCK_REASON in row.reason_codes
        ),
    ):
        raise ValueError("ambiguity_backlog_pattern_count must match rows")
    if report.urgent_recheck_pattern_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if RECHECK_URGENCY_WATCH_REASON in row.reason_codes
            or RECHECK_URGENCY_BLOCK_REASON in row.reason_codes
        ),
    ):
        raise ValueError("urgent_recheck_pattern_count must match rows")
    if report.average_pattern_memory_confidence != _average_pattern_memory_confidence(
        report.rows,
    ):
        raise ValueError("average_pattern_memory_confidence must match rows")
    if report.max_rule_change_risk_score != max(
        (row.rule_change_risk_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_rule_change_risk_score must match rows")
    if report.max_recheck_urgency_score != max(
        (row.recheck_urgency_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_recheck_urgency_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason codes")


def _validate_status_reason_codes(
    status: str,
    reason_codes: tuple[str, ...],
    label: str,
) -> None:
    expected_status = _status_from_reason_codes(reason_codes)
    if status != expected_status:
        raise ValueError(f"{label} status must match reason codes")
    if status == "pass" and reason_codes != (PASS_REASON_CODE,):
        raise ValueError(f"{label} pass status must use pass reason code")
    if status != "pass" and PASS_REASON_CODE in reason_codes:
        raise ValueError(f"{label} non-pass status cannot use pass reason code")


def _report_public_payload_values(
    report: ResearchResolutionRuleMemoryHealthReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "pattern_count": _decimal_payload(report.pattern_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "total_pattern_observation_count": _decimal_payload(
            report.total_pattern_observation_count,
        ),
        "total_confirmed_resolution_count": _decimal_payload(
            report.total_confirmed_resolution_count,
        ),
        "total_ambiguity_backlog_count": _decimal_payload(
            report.total_ambiguity_backlog_count,
        ),
        "rule_change_risk_count": _decimal_payload(report.rule_change_risk_count),
        "ambiguity_backlog_pattern_count": _decimal_payload(
            report.ambiguity_backlog_pattern_count,
        ),
        "urgent_recheck_pattern_count": _decimal_payload(
            report.urgent_recheck_pattern_count,
        ),
        "average_pattern_memory_confidence": _decimal_payload(
            report.average_pattern_memory_confidence,
        ),
        "max_rule_change_risk_score": _decimal_payload(
            report.max_rule_change_risk_score,
        ),
        "max_recheck_urgency_score": _decimal_payload(
            report.max_recheck_urgency_score,
        ),
        "rows": [
            [
                row.rule_pattern,
                _decimal_payload(row.pattern_observation_count),
                _decimal_payload(row.confirmed_resolution_count),
                _decimal_payload(row.pattern_memory_confidence),
                _decimal_payload(row.rule_change_risk_score),
                _decimal_payload(row.ambiguity_backlog_count),
                _decimal_payload(row.seconds_since_recheck),
                _decimal_payload(row.recheck_urgency_score),
                row.status,
                list(row.reason_codes),
            ]
            for row in report.rows
        ],
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: ResearchResolutionRuleMemoryHealthReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: ResearchResolutionRuleMemoryHealthReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    digest_input = (
        "research_resolution_rule_memory_health_report_derived|"
        + "|".join(values)
    )
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


def _digest_payload_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        encoded_items = tuple(_digest_payload_value(item) for item in value)
        return (
            "list:"
            + str(len(encoded_items))
            + ":"
            + "".join(f"{len(item)}:{item}" for item in encoded_items)
        )
    if type(value) is bool:
        return "bool:true" if value else "bool:false"
    string_value = str(value)
    return f"str:{len(string_value)}:{string_value}"


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in (
        "pattern_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_pattern_observation_count",
        "total_confirmed_resolution_count",
        "total_ambiguity_backlog_count",
        "rule_change_risk_count",
        "ambiguity_backlog_pattern_count",
        "urgent_recheck_pattern_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "average_pattern_memory_confidence",
        "max_rule_change_risk_score",
        "max_recheck_urgency_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], places=True)
    _validate_public_rows(payload["rows"])
    _require_status("status", payload["status"])
    reason_codes = _validate_public_reason_codes(payload["reason_codes"])
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    _validate_status_reason_codes(str(payload["status"]), reason_codes, "payload")


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    previous_pattern: str | None = None
    for item in value:
        if type(item) is not list or len(item) != 10:
            raise ValueError("rows must contain public row lists")
        (
            rule_pattern,
            pattern_observation_count,
            confirmed_resolution_count,
            pattern_memory_confidence,
            rule_change_risk_score,
            ambiguity_backlog_count,
            seconds_since_recheck,
            recheck_urgency_score,
            status,
            reason_codes,
        ) = item
        pattern_value = _normalize_rule_pattern("rows", rule_pattern)
        if previous_pattern is not None and pattern_value <= previous_pattern:
            raise ValueError("rows must be deterministic")
        previous_pattern = pattern_value
        _require_decimal_payload_string("rows", pattern_observation_count, whole=True)
        _require_decimal_payload_string("rows", confirmed_resolution_count, whole=True)
        _require_decimal_payload_string("rows", pattern_memory_confidence, places=True)
        _require_decimal_payload_string("rows", rule_change_risk_score, places=True)
        _require_decimal_payload_string("rows", ambiguity_backlog_count, whole=True)
        _require_decimal_payload_string("rows", seconds_since_recheck, places=True)
        _require_decimal_payload_string("rows", recheck_urgency_score, places=True)
        _require_status("rows", status)
        row_reason_codes = _validate_public_reason_codes(reason_codes)
        _validate_status_reason_codes(str(status), row_reason_codes, "row payload")


def _validate_public_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    normalized: list[str] = []
    previous_index = -1
    for item in value:
        _require_canonical_string("reason_codes", item)
        if item not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains an unknown code")
        index = REASON_CODE_SEQUENCE.index(item)
        if index <= previous_index:
            raise ValueError("reason_codes must be deterministic")
        previous_index = index
        normalized.append(item)
    if not normalized:
        raise ValueError("reason_codes is required")
    return tuple(normalized)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _average_pattern_memory_confidence(
    rows: tuple[ResearchResolutionRuleMemoryHealthRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantized(
        _sum_decimal(row.pattern_memory_confidence for row in rows)
        / Decimal(len(rows)),
    )


def _age_seconds(generated_at: datetime, checked_at: datetime) -> Decimal:
    delta = generated_at - checked_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_nonnegative_decimal("seconds_since_recheck", seconds)


def _bounded_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantized(ZERO)
    if value > ONE:
        return _quantized(ONE)
    return _quantized(value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    previous_index = -1
    for item in value:
        _require_canonical_string("reason_codes", item)
        if item not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains an unknown code")
        index = REASON_CODE_SEQUENCE.index(item)
        if index <= previous_index:
            raise ValueError("reason_codes must be deterministic")
        previous_index = index
        normalized.append(item)
    if not normalized:
        raise ValueError("reason_codes is required")
    return tuple(normalized)


def _normalize_rule_pattern(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    _reject_unsafe_public_text(field_name, normalized)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be a finite nonnegative Decimal")
    return value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantized(normalized)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total


def _quantized(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        return value.quantize(DECIMAL_PLACES)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be an exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("generated_at", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("payload decimal must be a finite exact Decimal")
    return format(value, "f")


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    whole: bool = False,
    places: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite() or decimal_value < ZERO:
        raise ValueError(f"{field_name} must be a finite nonnegative Decimal string")
    if format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal-derived string")
    if places and decimal_value.quantize(DECIMAL_PLACES) != decimal_value:
        raise ValueError(f"{field_name} must be a six-place Decimal-derived string")
    return decimal_value


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if (
                lowered_key == "id"
                or lowered_key.endswith("_id")
                or any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS)
            ):
                raise ValueError(f"unsafe public payload field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_TOKENS):
        raise ValueError(f"{field_name} has unsafe value")
