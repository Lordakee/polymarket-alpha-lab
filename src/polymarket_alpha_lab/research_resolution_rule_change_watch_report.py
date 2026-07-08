"""Pure report for public-safe resolution rule change risk."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
from typing import Any


DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_WATCH_CONFIG_VERSION = (
    "research-resolution-rule-change-watch-report-v0"
)
STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "research_resolution_rule_change_watch_passed"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
DECIMAL_PLACES = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

RULE_VERSION_DRIFT_BLOCK_REASON = "rule_version_drift_block"
ORACLE_SOURCE_CONSISTENCY_BLOCK_REASON = "oracle_source_consistency_block"
AMBIGUITY_BLOCK_REASON = "resolution_rule_ambiguity_block"
DEADLINE_PRESSURE_BLOCK_REASON = "deadline_pressure_block"
EVIDENCE_FRESHNESS_BLOCK_REASON = "evidence_freshness_block"
RULE_VERSION_DRIFT_WATCH_REASON = "rule_version_drift_watch"
ORACLE_SOURCE_CONSISTENCY_WATCH_REASON = "oracle_source_consistency_watch"
AMBIGUITY_WATCH_REASON = "resolution_rule_ambiguity_watch"
DEADLINE_PRESSURE_WATCH_REASON = "deadline_pressure_watch"
EVIDENCE_FRESHNESS_WATCH_REASON = "evidence_freshness_watch"

REASON_CODE_SEQUENCE = (
    RULE_VERSION_DRIFT_BLOCK_REASON,
    ORACLE_SOURCE_CONSISTENCY_BLOCK_REASON,
    AMBIGUITY_BLOCK_REASON,
    DEADLINE_PRESSURE_BLOCK_REASON,
    EVIDENCE_FRESHNESS_BLOCK_REASON,
    RULE_VERSION_DRIFT_WATCH_REASON,
    ORACLE_SOURCE_CONSISTENCY_WATCH_REASON,
    AMBIGUITY_WATCH_REASON,
    DEADLINE_PRESSURE_WATCH_REASON,
    EVIDENCE_FRESHNESS_WATCH_REASON,
    PASS_REASON_CODE,
)
BLOCK_REASONS = (
    RULE_VERSION_DRIFT_BLOCK_REASON,
    ORACLE_SOURCE_CONSISTENCY_BLOCK_REASON,
    AMBIGUITY_BLOCK_REASON,
    DEADLINE_PRESSURE_BLOCK_REASON,
    EVIDENCE_FRESHNESS_BLOCK_REASON,
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "observation_count",
    "rule_version_drift_count",
    "oracle_source_consistency_gap_count",
    "ambiguity_count",
    "deadline_pressure_count",
    "stale_evidence_count",
    "max_rule_version_drift",
    "min_oracle_source_consistency",
    "min_seconds_until_resolution_deadline",
    "max_evidence_age_seconds",
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
    "recommend",
    "siz" + "ing",
    "private",
    "credential",
    "secret",
    "token",
)

__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_WATCH_CONFIG_VERSION",
    "STATUSES",
    "ResearchResolutionRuleChangeWatchConfig",
    "ResearchResolutionRuleChangeWatchInput",
    "ResearchResolutionRuleChangeWatchReport",
    "ResearchResolutionRuleChangeWatchRow",
    "build_research_resolution_rule_change_watch_report",
    "research_resolution_rule_change_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchResolutionRuleChangeWatchConfig:
    config_version: str = DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_WATCH_CONFIG_VERSION
    rule_version_drift_watch_threshold: Decimal = Decimal("1")
    rule_version_drift_block_threshold: Decimal = Decimal("3")
    min_oracle_source_consistency_watch: Decimal = Decimal("0.80")
    min_oracle_source_consistency_block: Decimal = Decimal("0.60")
    ambiguity_watch_threshold: Decimal = Decimal("2")
    ambiguity_block_threshold: Decimal = Decimal("5")
    deadline_watch_seconds: Decimal = Decimal("86400")
    deadline_block_seconds: Decimal = Decimal("3600")
    max_evidence_age_watch_seconds: Decimal = Decimal("86400")
    max_evidence_age_block_seconds: Decimal = Decimal("172800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleChangeWatchConfig:
            raise TypeError(
                "ResearchResolutionRuleChangeWatchConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleChangeWatchConfig:
            raise ValueError(
                "config must be exactly ResearchResolutionRuleChangeWatchConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "rule_version_drift_watch_threshold",
            "rule_version_drift_block_threshold",
            "ambiguity_watch_threshold",
            "ambiguity_block_threshold",
            "deadline_watch_seconds",
            "deadline_block_seconds",
            "max_evidence_age_watch_seconds",
            "max_evidence_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_oracle_source_consistency_watch",
            "min_oracle_source_consistency_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.rule_version_drift_block_threshold
            < self.rule_version_drift_watch_threshold
        ):
            raise ValueError(
                "rule_version_drift_block_threshold must be >= "
                "rule_version_drift_watch_threshold",
            )
        if (
            self.min_oracle_source_consistency_block
            > self.min_oracle_source_consistency_watch
        ):
            raise ValueError(
                "min_oracle_source_consistency_block must be <= "
                "min_oracle_source_consistency_watch",
            )
        if self.ambiguity_block_threshold < self.ambiguity_watch_threshold:
            raise ValueError(
                "ambiguity_block_threshold must be >= ambiguity_watch_threshold",
            )
        if self.deadline_block_seconds > self.deadline_watch_seconds:
            raise ValueError(
                "deadline_block_seconds must be <= deadline_watch_seconds",
            )
        if (
            self.max_evidence_age_block_seconds
            < self.max_evidence_age_watch_seconds
        ):
            raise ValueError(
                "max_evidence_age_block_seconds must be >= "
                "max_evidence_age_watch_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionRuleChangeWatchInput:
    rule_scope: str
    baseline_rule_version: Decimal
    observed_rule_version: Decimal
    oracle_source_consistency: Decimal
    ambiguity_count: Decimal
    seconds_until_resolution_deadline: Decimal
    evidence_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleChangeWatchInput:
            raise TypeError(
                "ResearchResolutionRuleChangeWatchInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleChangeWatchInput:
            raise ValueError(
                "input must be exactly ResearchResolutionRuleChangeWatchInput",
            )
        object.__setattr__(
            self,
            "rule_scope",
            _normalize_rule_scope("rule_scope", self.rule_scope),
        )
        for field_name in (
            "baseline_rule_version",
            "observed_rule_version",
            "ambiguity_count",
            "seconds_until_resolution_deadline",
            "evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oracle_source_consistency",
            _normalize_probability_decimal(
                "oracle_source_consistency",
                self.oracle_source_consistency,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchResolutionRuleChangeWatchRow:
    rule_scope: str
    rule_version_drift: Decimal
    oracle_source_consistency: Decimal
    ambiguity_count: Decimal
    seconds_until_resolution_deadline: Decimal
    evidence_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleChangeWatchRow:
            raise TypeError(
                "ResearchResolutionRuleChangeWatchRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleChangeWatchRow:
            raise ValueError("row must be exactly ResearchResolutionRuleChangeWatchRow")
        object.__setattr__(
            self,
            "rule_scope",
            _normalize_rule_scope("rule_scope", self.rule_scope),
        )
        for field_name in (
            "rule_version_drift",
            "ambiguity_count",
            "seconds_until_resolution_deadline",
            "evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oracle_source_consistency",
            _normalize_probability_decimal(
                "oracle_source_consistency",
                self.oracle_source_consistency,
            ),
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
class ResearchResolutionRuleChangeWatchReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    rule_version_drift_count: Decimal
    oracle_source_consistency_gap_count: Decimal
    ambiguity_count: Decimal
    deadline_pressure_count: Decimal
    stale_evidence_count: Decimal
    max_rule_version_drift: Decimal
    min_oracle_source_consistency: Decimal
    min_seconds_until_resolution_deadline: Decimal
    max_evidence_age_seconds: Decimal
    rows: tuple[ResearchResolutionRuleChangeWatchRow, ...]
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionRuleChangeWatchReport:
            raise TypeError(
                "ResearchResolutionRuleChangeWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleChangeWatchReport:
            raise ValueError(
                "report must be exactly ResearchResolutionRuleChangeWatchReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "rule_version_drift_count",
            "oracle_source_consistency_gap_count",
            "ambiguity_count",
            "deadline_pressure_count",
            "stale_evidence_count",
            "max_rule_version_drift",
            "min_seconds_until_resolution_deadline",
            "max_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_oracle_source_consistency",
            _normalize_probability_decimal(
                "min_oracle_source_consistency",
                self.min_oracle_source_consistency,
            ),
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


def build_research_resolution_rule_change_watch_report(
    observations: tuple[ResearchResolutionRuleChangeWatchInput, ...],
    *,
    config: ResearchResolutionRuleChangeWatchConfig,
    generated_at: datetime,
) -> ResearchResolutionRuleChangeWatchReport:
    if type(config) is not ResearchResolutionRuleChangeWatchConfig:
        raise ValueError(
            "config must be a ResearchResolutionRuleChangeWatchConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_observations(observations)
    rows = tuple(_build_row(row, config) for row in inputs)
    report_reason_codes = _report_reason_codes(rows)
    return ResearchResolutionRuleChangeWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count_decimal(len(rows)),
        rule_version_drift_count=_count_decimal(
            sum(
                1
                for row in rows
                if row.rule_version_drift
                >= config.rule_version_drift_watch_threshold
            ),
        ),
        oracle_source_consistency_gap_count=_count_decimal(
            sum(
                1
                for row in rows
                if row.oracle_source_consistency
                < config.min_oracle_source_consistency_watch
            ),
        ),
        ambiguity_count=_sum_decimal(row.ambiguity_count for row in rows),
        deadline_pressure_count=_count_decimal(
            sum(
                1
                for row in rows
                if row.seconds_until_resolution_deadline
                <= config.deadline_watch_seconds
            ),
        ),
        stale_evidence_count=_count_decimal(
            sum(
                1
                for row in rows
                if row.evidence_age_seconds
                >= config.max_evidence_age_watch_seconds
            ),
        ),
        max_rule_version_drift=max(
            (row.rule_version_drift for row in rows),
            default=ZERO,
        ),
        min_oracle_source_consistency=min(
            (row.oracle_source_consistency for row in rows),
            default=ONE,
        ),
        min_seconds_until_resolution_deadline=min(
            (row.seconds_until_resolution_deadline for row in rows),
            default=ZERO,
        ),
        max_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        status=_status_from_reason_codes(report_reason_codes),
        reason_codes=report_reason_codes,
    )


def research_resolution_rule_change_watch_report_payload(
    report: ResearchResolutionRuleChangeWatchReport | dict[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchResolutionRuleChangeWatchReport:
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
        "report must be a ResearchResolutionRuleChangeWatchReport",
    )


def _build_row(
    observation: ResearchResolutionRuleChangeWatchInput,
    config: ResearchResolutionRuleChangeWatchConfig,
) -> ResearchResolutionRuleChangeWatchRow:
    rule_version_drift = _quantized(
        _abs_decimal(observation.observed_rule_version - observation.baseline_rule_version),
    )
    reason_codes = _row_reason_codes(
        rule_version_drift=rule_version_drift,
        oracle_source_consistency=observation.oracle_source_consistency,
        ambiguity_count=observation.ambiguity_count,
        seconds_until_resolution_deadline=observation.seconds_until_resolution_deadline,
        evidence_age_seconds=observation.evidence_age_seconds,
        config=config,
    )
    return ResearchResolutionRuleChangeWatchRow(
        rule_scope=observation.rule_scope,
        rule_version_drift=rule_version_drift,
        oracle_source_consistency=_quantized(observation.oracle_source_consistency),
        ambiguity_count=observation.ambiguity_count,
        seconds_until_resolution_deadline=_quantized(
            observation.seconds_until_resolution_deadline,
        ),
        evidence_age_seconds=_quantized(observation.evidence_age_seconds),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    rule_version_drift: Decimal,
    oracle_source_consistency: Decimal,
    ambiguity_count: Decimal,
    seconds_until_resolution_deadline: Decimal,
    evidence_age_seconds: Decimal,
    config: ResearchResolutionRuleChangeWatchConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if rule_version_drift >= config.rule_version_drift_block_threshold:
        reason_codes.append(RULE_VERSION_DRIFT_BLOCK_REASON)
    elif rule_version_drift >= config.rule_version_drift_watch_threshold:
        reason_codes.append(RULE_VERSION_DRIFT_WATCH_REASON)
    if oracle_source_consistency <= config.min_oracle_source_consistency_block:
        reason_codes.append(ORACLE_SOURCE_CONSISTENCY_BLOCK_REASON)
    elif oracle_source_consistency < config.min_oracle_source_consistency_watch:
        reason_codes.append(ORACLE_SOURCE_CONSISTENCY_WATCH_REASON)
    if ambiguity_count >= config.ambiguity_block_threshold:
        reason_codes.append(AMBIGUITY_BLOCK_REASON)
    elif ambiguity_count >= config.ambiguity_watch_threshold:
        reason_codes.append(AMBIGUITY_WATCH_REASON)
    if seconds_until_resolution_deadline <= config.deadline_block_seconds:
        reason_codes.append(DEADLINE_PRESSURE_BLOCK_REASON)
    elif seconds_until_resolution_deadline <= config.deadline_watch_seconds:
        reason_codes.append(DEADLINE_PRESSURE_WATCH_REASON)
    if evidence_age_seconds >= config.max_evidence_age_block_seconds:
        reason_codes.append(EVIDENCE_FRESHNESS_BLOCK_REASON)
    elif evidence_age_seconds >= config.max_evidence_age_watch_seconds:
        reason_codes.append(EVIDENCE_FRESHNESS_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _report_reason_codes(
    rows: tuple[ResearchResolutionRuleChangeWatchRow, ...],
) -> tuple[str, ...]:
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
) -> tuple[ResearchResolutionRuleChangeWatchInput, ...]:
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    normalized = tuple(observations)
    seen_rule_scopes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchResolutionRuleChangeWatchInput:
            raise ValueError(
                "observations must contain exact resolution rule watch inputs",
            )
        _require_hard_flags("observation", row)
        if row.rule_scope in seen_rule_scopes:
            raise ValueError("observations must contain unique rule scopes")
        seen_rule_scopes.add(row.rule_scope)
    return tuple(sorted(normalized, key=lambda row: row.rule_scope))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchResolutionRuleChangeWatchRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    previous_scope: str | None = None
    for row in normalized:
        if type(row) is not ResearchResolutionRuleChangeWatchRow:
            raise ValueError(
                "rows must contain exact resolution rule watch rows",
            )
        _require_hard_flags("row", row)
        if previous_scope is not None and row.rule_scope <= previous_scope:
            raise ValueError("rows must be deterministic")
        previous_scope = row.rule_scope
    return normalized


def _validate_report_consistency(
    report: ResearchResolutionRuleChangeWatchReport,
) -> None:
    _validate_status_reason_codes(report.status, report.reason_codes, "report")
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.rule_version_drift_count != _count_decimal(
        sum(1 for row in report.rows if RULE_VERSION_DRIFT_WATCH_REASON in row.reason_codes)
        + sum(1 for row in report.rows if RULE_VERSION_DRIFT_BLOCK_REASON in row.reason_codes),
    ):
        raise ValueError("rule_version_drift_count must match rows")
    if report.oracle_source_consistency_gap_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if ORACLE_SOURCE_CONSISTENCY_WATCH_REASON in row.reason_codes
            or ORACLE_SOURCE_CONSISTENCY_BLOCK_REASON in row.reason_codes
        ),
    ):
        raise ValueError("oracle_source_consistency_gap_count must match rows")
    if report.deadline_pressure_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if DEADLINE_PRESSURE_WATCH_REASON in row.reason_codes
            or DEADLINE_PRESSURE_BLOCK_REASON in row.reason_codes
        ),
    ):
        raise ValueError("deadline_pressure_count must match rows")
    if report.stale_evidence_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if EVIDENCE_FRESHNESS_WATCH_REASON in row.reason_codes
            or EVIDENCE_FRESHNESS_BLOCK_REASON in row.reason_codes
        ),
    ):
        raise ValueError("stale_evidence_count must match rows")


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
    report: ResearchResolutionRuleChangeWatchReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "observation_count": _decimal_payload(report.observation_count),
        "rule_version_drift_count": _decimal_payload(report.rule_version_drift_count),
        "oracle_source_consistency_gap_count": _decimal_payload(
            report.oracle_source_consistency_gap_count,
        ),
        "ambiguity_count": _decimal_payload(report.ambiguity_count),
        "deadline_pressure_count": _decimal_payload(report.deadline_pressure_count),
        "stale_evidence_count": _decimal_payload(report.stale_evidence_count),
        "max_rule_version_drift": _decimal_payload(report.max_rule_version_drift),
        "min_oracle_source_consistency": _decimal_payload(
            report.min_oracle_source_consistency,
        ),
        "min_seconds_until_resolution_deadline": _decimal_payload(
            report.min_seconds_until_resolution_deadline,
        ),
        "max_evidence_age_seconds": _decimal_payload(report.max_evidence_age_seconds),
        "rows": [
            [
                row.rule_scope,
                _decimal_payload(row.rule_version_drift),
                _decimal_payload(row.oracle_source_consistency),
                _decimal_payload(row.ambiguity_count),
                _decimal_payload(row.seconds_until_resolution_deadline),
                _decimal_payload(row.evidence_age_seconds),
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
    report: ResearchResolutionRuleChangeWatchReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: ResearchResolutionRuleChangeWatchReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    digest_input = (
        "research_resolution_rule_change_watch_report_derived|"
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
        "observation_count",
        "rule_version_drift_count",
        "oracle_source_consistency_gap_count",
        "ambiguity_count",
        "deadline_pressure_count",
        "stale_evidence_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "max_rule_version_drift",
        "min_oracle_source_consistency",
        "min_seconds_until_resolution_deadline",
        "max_evidence_age_seconds",
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
    previous_scope: str | None = None
    for item in value:
        if type(item) is not list or len(item) != 8:
            raise ValueError("rows must contain public row lists")
        (
            rule_scope,
            rule_version_drift,
            oracle_source_consistency,
            ambiguity_count,
            seconds_until_resolution_deadline,
            evidence_age_seconds,
            status,
            reason_codes,
        ) = item
        scope_value = _normalize_rule_scope("rows", rule_scope)
        if previous_scope is not None and scope_value <= previous_scope:
            raise ValueError("rows must be deterministic")
        previous_scope = scope_value
        _require_decimal_payload_string("rows", rule_version_drift, places=True)
        _require_decimal_payload_string("rows", oracle_source_consistency, places=True)
        _require_decimal_payload_string("rows", ambiguity_count, whole=True)
        _require_decimal_payload_string(
            "rows",
            seconds_until_resolution_deadline,
            places=True,
        )
        _require_decimal_payload_string("rows", evidence_age_seconds, places=True)
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


def _normalize_rule_scope(field_name: str, value: object) -> str:
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


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total


def _abs_decimal(value: Decimal) -> Decimal:
    return value.copy_abs()


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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(token in normalized for token in UNSAFE_PUBLIC_TEXT_TOKENS):
        raise ValueError(f"unsafe public payload text in {label}")
