"""Read-only event resolution rule drift watch report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DRIFT_WATCH_REPORT_CONFIG_VERSION = (
    "research-event-resolution-rule-drift-watch-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = ("pass", "watch", "block")
_STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("raw", "_", "candidate")),
    "".join(("candidate", "_", "id")),
    "".join(("candidate", "-", "id")),
    "".join(("market", "_", "id")),
    "".join(("market", "-", "id")),
    "".join(("market", "_", "slug")),
    "".join(("market", "-", "slug")),
    "slug",
    "".join(("ques", "tion")),
    "".join(("source", "_", "url")),
    "".join(("source", "-", "url")),
    "".join(("source", " ", "url")),
    "".join(("source", "_", "text")),
    "".join(("source", "-", "text")),
    "".join(("source", " ", "text")),
    "raw",
    "url",
    "dsn",
    "".join(("table", "_", "name")),
    "table name",
    "token",
    "".join(("auth", "_")),
    "".join(("auth", "-")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("tra", "de")),
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "sqlite://",
)
_ROW_REASON_CODES = (
    "resolution_rule_drift_clear",
    "rule_interpretation_drift_watch",
    "rule_interpretation_drift_block",
    "evidence_authority_drift_watch",
    "evidence_authority_drift_block",
    "source_mapping_drift_watch",
    "source_mapping_drift_block",
    "fresh_review_required",
    "missing_fresh_review",
    "missing_fresh_review_block",
)
_REPORT_REASON_CODES = (
    "resolution_rule_drift_watch_clear",
    "rule_interpretation_drift_present",
    "evidence_authority_drift_present",
    "source_mapping_drift_present",
    "fresh_review_required_present",
    "missing_fresh_review_present",
    "resolution_rule_drift_block_present",
)
_REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "observed_event_count",
    "pass_event_count",
    "watch_event_count",
    "block_event_count",
    "drifted_event_count",
    "fresh_review_required_count",
    "missing_fresh_review_count",
    "max_rule_interpretation_drift_score",
    "max_evidence_authority_drift_score",
    "max_source_mapping_drift_score",
    "max_drift_score",
    "max_drift_age_seconds",
    "watch_ratio",
    "block_ratio",
)
_ROW_DECIMAL_PAYLOAD_FIELDS = (
    "rule_interpretation_drift_score",
    "evidence_authority_drift_score",
    "source_mapping_drift_score",
    "source_mapping_gap_count",
    "max_drift_score",
    "drift_age_seconds",
)
_ROW_BOOL_PAYLOAD_FIELDS = (
    "rule_interpretation_drifted",
    "evidence_authority_drifted",
    "source_mapping_drifted",
    "fresh_review_required",
    "missing_fresh_review",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *_REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "event_key",
    "status",
    *_ROW_DECIMAL_PAYLOAD_FIELDS,
    *_ROW_BOOL_PAYLOAD_FIELDS,
    "reason_codes",
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DRIFT_WATCH_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionRuleDriftWatchConfig",
    "ResearchEventResolutionRuleDriftWatchInput",
    "ResearchEventResolutionRuleDriftWatchReport",
    "ResearchEventResolutionRuleDriftWatchRow",
    "build_research_event_resolution_rule_drift_watch_report",
    "research_event_resolution_rule_drift_watch_report_payload",
    "validate_research_event_resolution_rule_drift_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDriftWatchConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DRIFT_WATCH_REPORT_CONFIG_VERSION
    )
    watch_rule_interpretation_drift_score: Decimal = Decimal("0.250000")
    block_rule_interpretation_drift_score: Decimal = Decimal("0.600000")
    watch_evidence_authority_drift_score: Decimal = Decimal("0.250000")
    block_evidence_authority_drift_score: Decimal = Decimal("0.600000")
    watch_source_mapping_drift_score: Decimal = Decimal("0.250000")
    block_source_mapping_drift_score: Decimal = Decimal("0.600000")
    watch_source_mapping_gap_count: Decimal = Decimal("1.000000")
    block_source_mapping_gap_count: Decimal = Decimal("2.000000")
    max_missing_review_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventResolutionRuleDriftWatchConfig)
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DRIFT_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_rule_interpretation_drift_score",
            "block_rule_interpretation_drift_score",
            "watch_evidence_authority_drift_score",
            "block_evidence_authority_drift_score",
            "watch_source_mapping_drift_score",
            "block_source_mapping_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_source_mapping_gap_count",
            "block_source_mapping_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_missing_review_age_seconds",
            _normalize_nonnegative_decimal(
                "max_missing_review_age_seconds",
                self.max_missing_review_age_seconds,
            ),
        )
        _require_threshold_pair(
            "watch_rule_interpretation_drift_score",
            self.watch_rule_interpretation_drift_score,
            "block_rule_interpretation_drift_score",
            self.block_rule_interpretation_drift_score,
        )
        _require_threshold_pair(
            "watch_evidence_authority_drift_score",
            self.watch_evidence_authority_drift_score,
            "block_evidence_authority_drift_score",
            self.block_evidence_authority_drift_score,
        )
        _require_threshold_pair(
            "watch_source_mapping_drift_score",
            self.watch_source_mapping_drift_score,
            "block_source_mapping_drift_score",
            self.block_source_mapping_drift_score,
        )
        _require_threshold_pair(
            "watch_source_mapping_gap_count",
            self.watch_source_mapping_gap_count,
            "block_source_mapping_gap_count",
            self.block_source_mapping_gap_count,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDriftWatchInput:
    event_key: str
    rule_interpretation_drift_score: Decimal
    evidence_authority_drift_score: Decimal
    source_mapping_drift_score: Decimal
    source_mapping_gap_count: Decimal
    drift_observed_at: datetime
    fresh_review_completed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchEventResolutionRuleDriftWatchInput)
        _require_public_identifier("event_key", self.event_key)
        for field_name in (
            "rule_interpretation_drift_score",
            "evidence_authority_drift_score",
            "source_mapping_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_mapping_gap_count",
            _normalize_count("source_mapping_gap_count", self.source_mapping_gap_count),
        )
        object.__setattr__(
            self,
            "drift_observed_at",
            _as_utc("drift_observed_at", self.drift_observed_at),
        )
        if type(self.fresh_review_completed) is not bool:
            raise ValueError("fresh_review_completed must be a bool")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDriftWatchRow:
    event_key: str
    status: str
    rule_interpretation_drift_score: Decimal
    evidence_authority_drift_score: Decimal
    source_mapping_drift_score: Decimal
    source_mapping_gap_count: Decimal
    max_drift_score: Decimal
    drift_age_seconds: Decimal
    rule_interpretation_drifted: bool
    evidence_authority_drifted: bool
    source_mapping_drifted: bool
    fresh_review_required: bool
    missing_fresh_review: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventResolutionRuleDriftWatchRow)
        _require_public_identifier("event_key", self.event_key)
        _require_status("status", self.status)
        for field_name in (
            "rule_interpretation_drift_score",
            "evidence_authority_drift_score",
            "source_mapping_drift_score",
            "max_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_mapping_gap_count",
            _normalize_count("source_mapping_gap_count", self.source_mapping_gap_count),
        )
        object.__setattr__(
            self,
            "drift_age_seconds",
            _normalize_nonnegative_decimal("drift_age_seconds", self.drift_age_seconds),
        )
        for field_name in (
            "rule_interpretation_drifted",
            "evidence_authority_drifted",
            "source_mapping_drifted",
            "fresh_review_required",
            "missing_fresh_review",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDriftWatchReport:
    generated_at: datetime
    config_version: str
    observed_event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    block_event_count: Decimal
    drifted_event_count: Decimal
    fresh_review_required_count: Decimal
    missing_fresh_review_count: Decimal
    max_rule_interpretation_drift_score: Decimal
    max_evidence_authority_drift_score: Decimal
    max_source_mapping_drift_score: Decimal
    max_drift_score: Decimal
    max_drift_age_seconds: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionRuleDriftWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventResolutionRuleDriftWatchReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "observed_event_count",
            "pass_event_count",
            "watch_event_count",
            "block_event_count",
            "drifted_event_count",
            "fresh_review_required_count",
            "missing_fresh_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_rule_interpretation_drift_score",
            "max_evidence_authority_drift_score",
            "max_source_mapping_drift_score",
            "max_drift_score",
            "watch_ratio",
            "block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_drift_age_seconds",
            _normalize_nonnegative_decimal(
                "max_drift_age_seconds",
                self.max_drift_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        _require_or_set_digest(self)


def build_research_event_resolution_rule_drift_watch_report(
    inputs: Iterable[ResearchEventResolutionRuleDriftWatchInput],
    *,
    config: ResearchEventResolutionRuleDriftWatchConfig,
    generated_at: datetime,
) -> ResearchEventResolutionRuleDriftWatchReport:
    if type(config) is not ResearchEventResolutionRuleDriftWatchConfig:
        raise ValueError("config must be a ResearchEventResolutionRuleDriftWatchConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_payload("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config, generated_at=generated_at)
                for value in _normalize_inputs(inputs, generated_at)
            ),
            key=_row_sort_key,
        ),
    )
    observed_event_count = _decimal_count(len(rows))
    pass_event_count = _status_total(rows, "pass")
    watch_event_count = _status_total(rows, "watch")
    block_event_count = _status_total(rows, "block")
    drifted_event_count = _flag_total(rows, "fresh_review_required")
    fresh_review_required_count = _flag_total(rows, "fresh_review_required")
    missing_fresh_review_count = _flag_total(rows, "missing_fresh_review")
    max_rule_interpretation_drift_score = _max_ratio(
        row.rule_interpretation_drift_score for row in rows
    )
    max_evidence_authority_drift_score = _max_ratio(
        row.evidence_authority_drift_score for row in rows
    )
    max_source_mapping_drift_score = _max_ratio(
        row.source_mapping_drift_score for row in rows
    )
    max_drift_score = _max_ratio(row.max_drift_score for row in rows)
    max_drift_age_seconds = _max_decimal(
        row.drift_age_seconds for row in rows if row.fresh_review_required
    )
    watch_ratio = _ratio(drifted_event_count, observed_event_count)
    block_ratio = _ratio(block_event_count, observed_event_count)
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchEventResolutionRuleDriftWatchReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observed_event_count=observed_event_count,
        pass_event_count=pass_event_count,
        watch_event_count=watch_event_count,
        block_event_count=block_event_count,
        drifted_event_count=drifted_event_count,
        fresh_review_required_count=fresh_review_required_count,
        missing_fresh_review_count=missing_fresh_review_count,
        max_rule_interpretation_drift_score=max_rule_interpretation_drift_score,
        max_evidence_authority_drift_score=max_evidence_authority_drift_score,
        max_source_mapping_drift_score=max_source_mapping_drift_score,
        max_drift_score=max_drift_score,
        max_drift_age_seconds=max_drift_age_seconds,
        watch_ratio=watch_ratio,
        block_ratio=block_ratio,
        status=status,
        reason_codes=reason_codes,
        rows=rows,
    )


def research_event_resolution_rule_drift_watch_report_payload(
    report: ResearchEventResolutionRuleDriftWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionRuleDriftWatchReport:
        _require_hard_flags(report)
        _reject_unsafe_public_payload("report", report)
        _require_or_set_digest(report)
        payload = _payload_value(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionRuleDriftWatchReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_resolution_rule_drift_watch_report_payload(payload)
    return payload


def validate_research_event_resolution_rule_drift_watch_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_schema(payload)
    _require_public_payload_values(payload)
    _validate_payload_digest(payload)
    return True


def _normalize_inputs(
    values: Iterable[ResearchEventResolutionRuleDriftWatchInput],
    generated_at: datetime,
) -> tuple[ResearchEventResolutionRuleDriftWatchInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        inputs = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for value in inputs:
        if type(value) is not ResearchEventResolutionRuleDriftWatchInput:
            raise ValueError(
                "inputs must contain ResearchEventResolutionRuleDriftWatchInput values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_payload("input", value)
        if value.event_key in seen:
            raise ValueError("event_key values must be unique")
        if value.drift_observed_at > generated_at:
            raise ValueError("drift_observed_at must not be after generated_at")
        seen.add(value.event_key)
    return inputs


def _row_from_input(
    value: ResearchEventResolutionRuleDriftWatchInput,
    *,
    config: ResearchEventResolutionRuleDriftWatchConfig,
    generated_at: datetime,
) -> ResearchEventResolutionRuleDriftWatchRow:
    rule_status = _score_status(
        value.rule_interpretation_drift_score,
        watch_threshold=config.watch_rule_interpretation_drift_score,
        block_threshold=config.block_rule_interpretation_drift_score,
    )
    evidence_status = _score_status(
        value.evidence_authority_drift_score,
        watch_threshold=config.watch_evidence_authority_drift_score,
        block_threshold=config.block_evidence_authority_drift_score,
    )
    source_status = _source_mapping_status(value, config=config)
    rule_interpretation_drifted = rule_status != "pass"
    evidence_authority_drifted = evidence_status != "pass"
    source_mapping_drifted = source_status != "pass"
    fresh_review_required = (
        rule_interpretation_drifted
        or evidence_authority_drifted
        or source_mapping_drifted
    )
    missing_fresh_review = fresh_review_required and not value.fresh_review_completed
    drift_age_seconds = _age_seconds(generated_at, value.drift_observed_at)
    status = _row_status(
        rule_status=rule_status,
        evidence_status=evidence_status,
        source_status=source_status,
        drift_age_seconds=drift_age_seconds,
        missing_fresh_review=missing_fresh_review,
        config=config,
    )
    return ResearchEventResolutionRuleDriftWatchRow(
        event_key=value.event_key,
        status=status,
        rule_interpretation_drift_score=value.rule_interpretation_drift_score,
        evidence_authority_drift_score=value.evidence_authority_drift_score,
        source_mapping_drift_score=value.source_mapping_drift_score,
        source_mapping_gap_count=value.source_mapping_gap_count,
        max_drift_score=_max_ratio(
            (
                value.rule_interpretation_drift_score,
                value.evidence_authority_drift_score,
                value.source_mapping_drift_score,
            ),
        ),
        drift_age_seconds=drift_age_seconds,
        rule_interpretation_drifted=rule_interpretation_drifted,
        evidence_authority_drifted=evidence_authority_drifted,
        source_mapping_drifted=source_mapping_drifted,
        fresh_review_required=fresh_review_required,
        missing_fresh_review=missing_fresh_review,
        reason_codes=_row_reason_codes(
            rule_status=rule_status,
            evidence_status=evidence_status,
            source_status=source_status,
            drift_age_seconds=drift_age_seconds,
            fresh_review_required=fresh_review_required,
            missing_fresh_review=missing_fresh_review,
            config=config,
        ),
    )


def _score_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return "block"
    if value >= watch_threshold:
        return "watch"
    return "pass"


def _source_mapping_status(
    value: ResearchEventResolutionRuleDriftWatchInput,
    *,
    config: ResearchEventResolutionRuleDriftWatchConfig,
) -> str:
    if (
        value.source_mapping_drift_score >= config.block_source_mapping_drift_score
        or value.source_mapping_gap_count >= config.block_source_mapping_gap_count
    ):
        return "block"
    if (
        value.source_mapping_drift_score >= config.watch_source_mapping_drift_score
        or value.source_mapping_gap_count >= config.watch_source_mapping_gap_count
    ):
        return "watch"
    return "pass"


def _row_status(
    *,
    rule_status: str,
    evidence_status: str,
    source_status: str,
    drift_age_seconds: Decimal,
    missing_fresh_review: bool,
    config: ResearchEventResolutionRuleDriftWatchConfig,
) -> str:
    if (rule_status, evidence_status, source_status) == ("pass", "pass", "pass"):
        return "pass"
    if "block" in (rule_status, evidence_status, source_status):
        return "block"
    if (
        missing_fresh_review
        and drift_age_seconds >= config.max_missing_review_age_seconds
    ):
        return "block"
    return "watch"


def _row_reason_codes(
    *,
    rule_status: str,
    evidence_status: str,
    source_status: str,
    drift_age_seconds: Decimal,
    fresh_review_required: bool,
    missing_fresh_review: bool,
    config: ResearchEventResolutionRuleDriftWatchConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if rule_status != "pass":
        codes.append(f"rule_interpretation_drift_{rule_status}")
    if evidence_status != "pass":
        codes.append(f"evidence_authority_drift_{evidence_status}")
    if source_status != "pass":
        codes.append(f"source_mapping_drift_{source_status}")
    if fresh_review_required:
        codes.append("fresh_review_required")
    if missing_fresh_review:
        if drift_age_seconds >= config.max_missing_review_age_seconds:
            codes.append("missing_fresh_review_block")
        else:
            codes.append("missing_fresh_review")
    return tuple(codes) if codes else ("resolution_rule_drift_clear",)


def _report_status(rows: tuple[ResearchEventResolutionRuleDriftWatchRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionRuleDriftWatchRow, ...],
) -> tuple[str, ...]:
    if not any(row.fresh_review_required for row in rows):
        return ("resolution_rule_drift_watch_clear",)
    codes: list[str] = []
    if any(row.rule_interpretation_drifted for row in rows):
        codes.append("rule_interpretation_drift_present")
    if any(row.evidence_authority_drifted for row in rows):
        codes.append("evidence_authority_drift_present")
    if any(row.source_mapping_drifted for row in rows):
        codes.append("source_mapping_drift_present")
    if any(row.fresh_review_required for row in rows):
        codes.append("fresh_review_required_present")
    if any(row.missing_fresh_review for row in rows):
        codes.append("missing_fresh_review_present")
    if any(row.status == "block" for row in rows):
        codes.append("resolution_rule_drift_block_present")
    return tuple(codes)


def _row_sort_key(
    row: ResearchEventResolutionRuleDriftWatchRow,
) -> tuple[Decimal, bool, Decimal, Decimal, str]:
    return (
        -_STATUS_WEIGHT[row.status],
        not row.missing_fresh_review,
        -row.max_drift_score,
        -row.source_mapping_gap_count,
        row.event_key,
    )


def _validate_row(row: ResearchEventResolutionRuleDriftWatchRow) -> None:
    if row.max_drift_score != _max_ratio(
        (
            row.rule_interpretation_drift_score,
            row.evidence_authority_drift_score,
            row.source_mapping_drift_score,
        ),
    ):
        raise ValueError("max_drift_score must match row scores")
    expected_fresh_review_required = (
        row.rule_interpretation_drifted
        or row.evidence_authority_drifted
        or row.source_mapping_drifted
    )
    if row.fresh_review_required != expected_fresh_review_required:
        raise ValueError("fresh_review_required must match row drift flags")
    if row.missing_fresh_review and not row.fresh_review_required:
        raise ValueError("missing_fresh_review requires fresh_review_required")
    if row.reason_codes != _expected_row_reason_codes_from_flags(row):
        raise ValueError("reason_codes must match row flags")
    if row.status != _expected_row_status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _expected_row_reason_codes_from_flags(
    row: ResearchEventResolutionRuleDriftWatchRow,
) -> tuple[str, ...]:
    codes: list[str] = []
    if row.rule_interpretation_drifted:
        codes.append(_drift_reason_code("rule_interpretation_drift", row.reason_codes))
    if row.evidence_authority_drifted:
        codes.append(_drift_reason_code("evidence_authority_drift", row.reason_codes))
    if row.source_mapping_drifted:
        codes.append(_drift_reason_code("source_mapping_drift", row.reason_codes))
    if row.fresh_review_required:
        codes.append("fresh_review_required")
    if row.missing_fresh_review:
        if "missing_fresh_review_block" in row.reason_codes:
            codes.append("missing_fresh_review_block")
        else:
            codes.append("missing_fresh_review")
    return tuple(codes) if codes else ("resolution_rule_drift_clear",)


def _drift_reason_code(prefix: str, reason_codes: tuple[str, ...]) -> str:
    for status in ("block", "watch"):
        reason_code = f"{prefix}_{status}"
        if reason_code in reason_codes:
            return reason_code
    raise ValueError("reason_codes must include row drift status")


def _expected_row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if "missing_fresh_review" in reason_codes:
        return "watch"
    return "pass"


def _validate_report(report: ResearchEventResolutionRuleDriftWatchReport) -> None:
    if report.observed_event_count != _decimal_count(len(report.rows)):
        raise ValueError("observed_event_count must match rows")
    for field_name, status in (
        ("pass_event_count", "pass"),
        ("watch_event_count", "watch"),
        ("block_event_count", "block"),
    ):
        if getattr(report, field_name) != _status_total(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.drifted_event_count != _flag_total(report.rows, "fresh_review_required"):
        raise ValueError("drifted_event_count must match rows")
    if report.fresh_review_required_count != _flag_total(
        report.rows,
        "fresh_review_required",
    ):
        raise ValueError("fresh_review_required_count must match rows")
    if report.missing_fresh_review_count != _flag_total(
        report.rows,
        "missing_fresh_review",
    ):
        raise ValueError("missing_fresh_review_count must match rows")
    if report.max_rule_interpretation_drift_score != _max_ratio(
        row.rule_interpretation_drift_score for row in report.rows
    ):
        raise ValueError("max_rule_interpretation_drift_score must match rows")
    if report.max_evidence_authority_drift_score != _max_ratio(
        row.evidence_authority_drift_score for row in report.rows
    ):
        raise ValueError("max_evidence_authority_drift_score must match rows")
    if report.max_source_mapping_drift_score != _max_ratio(
        row.source_mapping_drift_score for row in report.rows
    ):
        raise ValueError("max_source_mapping_drift_score must match rows")
    if report.max_drift_score != _max_ratio(row.max_drift_score for row in report.rows):
        raise ValueError("max_drift_score must match rows")
    if report.max_drift_age_seconds != _max_decimal(
        row.drift_age_seconds for row in report.rows if row.fresh_review_required
    ):
        raise ValueError("max_drift_age_seconds must match rows")
    if report.watch_ratio != _ratio(report.drifted_event_count, report.observed_event_count):
        raise ValueError("watch_ratio must match counts")
    if report.block_ratio != _ratio(report.block_event_count, report.observed_event_count):
        raise ValueError("block_ratio must match counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")


def _normalize_rows(
    values: object,
) -> tuple[ResearchEventResolutionRuleDriftWatchRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(values)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionRuleDriftWatchRow:
            raise ValueError("rows must contain watch row values")
        _require_hard_flags(row)
        _reject_unsafe_public_payload("row", row)
        if row.event_key in seen:
            raise ValueError("rows must be unique by event_key")
        seen.add(row.event_key)
    return rows


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_public_identifier(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_public_payload_schema(payload: dict[str, Any]) -> None:
    _reject_unknown_payload_keys("report payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_public_identifier("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DRIFT_WATCH_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    for field_name in _REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _normalize_reason_codes("reason_codes", payload["reason_codes"], _REPORT_REASON_CODES)
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _require_public_row_payload_schema(row)
    _require_digest_string("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_row_payload_schema(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _reject_unknown_payload_keys("row payload", value, _ROW_PAYLOAD_KEYS)
    _require_public_identifier("event_key", value["event_key"])
    _require_status("status", value["status"])
    for field_name in _ROW_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in _ROW_BOOL_PAYLOAD_FIELDS:
        if type(value[field_name]) is not bool:
            raise ValueError(f"{field_name} must be a bool")
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_reason_codes("reason_codes", value["reason_codes"], _ROW_REASON_CODES)


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys and set(payload.keys()) != set(allowed_keys):
        raise ValueError(f"{label} must use the public readonly schema")


def _require_public_payload_values(value: object, path: str = "payload") -> None:
    if value is None:
        return
    if type(value) is bool:
        return
    if type(value) is float:
        raise ValueError(f"{path} must not contain float values")
    if type(value) is int:
        raise ValueError(f"{path} must use Decimal-derived string values")
    if type(value) is str:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _require_public_payload_values(item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_values(item, f"{path}[{index}]")
        return
    raise ValueError(f"{path} is not JSON serializable")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    current = payload["derived_validation_digest"]
    if current != _derived_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    encoded = json.dumps(
        _canonical_digest_value(value),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_fragment(label, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_fragment(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_threshold_pair(
    watch_field_name: str,
    watch_threshold: Decimal,
    block_field_name: str,
    block_threshold: Decimal,
) -> None:
    if watch_threshold <= _ZERO:
        raise ValueError(f"{watch_field_name} must be positive")
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _status_total(
    rows: tuple[ResearchEventResolutionRuleDriftWatchRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _flag_total(
    rows: tuple[ResearchEventResolutionRuleDriftWatchRow, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _max_ratio(values: Iterable[Decimal]) -> Decimal:
    return _normalize_ratio("max_ratio", max(tuple(values) or (_ZERO,)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return _normalize_nonnegative_decimal("max_decimal", max(tuple(values) or (_ZERO,)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    return _normalize_nonnegative_decimal("drift_age_seconds", seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not contain float values")
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _is_sha256_hex(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
