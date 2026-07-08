"""Pure readonly event research news signal freshness gate report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_NEWS_SIGNAL_FRESHNESS_GATE_CONFIG_VERSION = (
    "research-news-signal-freshness-gate-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
SECONDS_PER_HOUR = Decimal("3600.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64)

STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "news_signal_freshness_gate_no_inputs",
    "news_signal_freshness_gate_status_pass",
    "news_signal_freshness_gate_status_watch",
    "news_signal_freshness_gate_status_block",
    "news_update_stale_watch",
    "news_update_stale_block",
    "corroboration_missing_block",
    "corroboration_stale_watch",
    "corroboration_stale_block",
    "corroboration_insufficient_watch",
    "corroboration_insufficient_block",
    "conflict_check_missing_block",
    "conflict_check_stale_watch",
    "conflict_check_stale_block",
    "unresolved_conflict_watch",
    "unresolved_conflict_block",
    "recheck_overdue_watch",
    "recheck_overdue_block",
)
REASON_CODE_PRIORITY = REASON_CODES
BLOCK_REASONS = frozenset(
    (
        "news_update_stale_block",
        "corroboration_missing_block",
        "corroboration_stale_block",
        "corroboration_insufficient_block",
        "conflict_check_missing_block",
        "conflict_check_stale_block",
        "unresolved_conflict_block",
        "recheck_overdue_block",
    ),
)
WATCH_REASONS = frozenset(
    (
        "news_update_stale_watch",
        "corroboration_stale_watch",
        "corroboration_insufficient_watch",
        "conflict_check_stale_watch",
        "unresolved_conflict_watch",
        "recheck_overdue_watch",
    ),
)
STATUS_REASON = {
    "pass": "news_signal_freshness_gate_status_pass",
    "watch": "news_signal_freshness_gate_status_watch",
    "block": "news_signal_freshness_gate_status_block",
}
REPORT_NEXT_STEPS = {
    "pass": "use_news_signals_for_event_research",
    "watch": "review_news_signal_freshness_before_event_research",
    "block": "pause_event_research_for_news_signal_refresh",
}
ROW_ACTIONS = {
    "pass": "news_signal_freshness_clear",
    "watch": "review_news_signal_freshness",
    "block": "refresh_news_signals_before_research",
}
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

_CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "max_pass_update_age_hours",
    "max_watch_update_age_hours",
    "max_pass_corroboration_age_hours",
    "max_watch_corroboration_age_hours",
    "max_pass_conflict_check_age_hours",
    "max_watch_conflict_check_age_hours",
    "max_watch_recheck_overdue_hours",
    "min_pass_fresh_corroborating_signal_count",
    "min_watch_fresh_corroborating_signal_count",
    "max_watch_unresolved_conflict_count",
    "paper_only",
    "report_only",
    "readonly",
)
_INPUT_PAYLOAD_FIELDS = (
    "research_scope_ref",
    "latest_update_at",
    "latest_corroboration_at",
    "latest_conflict_check_at",
    "next_recheck_due_at",
    "corroborating_signal_count",
    "fresh_corroborating_signal_count",
    "unresolved_conflict_count",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "research_scope_ref",
    "latest_update_at",
    "latest_corroboration_at",
    "latest_conflict_check_at",
    "next_recheck_due_at",
    "corroborating_signal_count",
    "fresh_corroborating_signal_count",
    "unresolved_conflict_count",
    "update_age_hours",
    "corroboration_age_hours",
    "conflict_check_age_hours",
    "recheck_overdue_hours",
    "recheck_urgency_score",
    "gate_status",
    "recommended_research_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "recommended_next_step",
    "input_count",
    "block_count",
    "watch_count",
    "pass_count",
    "stale_update_count",
    "stale_corroboration_count",
    "stale_conflict_check_count",
    "urgent_recheck_count",
    "unresolved_conflict_scope_count",
    "highest_recheck_urgency_score",
    "max_update_age_hours",
    "max_corroboration_age_hours",
    "max_conflict_check_age_hours",
    "max_recheck_overdue_hours",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_NEWS_SIGNAL_FRESHNESS_GATE_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchNewsSignalFreshnessGateConfig",
    "ResearchNewsSignalFreshnessGateInput",
    "ResearchNewsSignalFreshnessGateReport",
    "ResearchNewsSignalFreshnessGateRow",
    "STATUSES",
    "build_research_news_signal_freshness_gate_report",
    "research_news_signal_freshness_gate_report_payload",
)


@dataclass(frozen=True)
class ResearchNewsSignalFreshnessGateConfig:
    config_version: str = DEFAULT_RESEARCH_NEWS_SIGNAL_FRESHNESS_GATE_CONFIG_VERSION
    max_pass_update_age_hours: Decimal = Decimal("6.000000")
    max_watch_update_age_hours: Decimal = Decimal("24.000000")
    max_pass_corroboration_age_hours: Decimal = Decimal("12.000000")
    max_watch_corroboration_age_hours: Decimal = Decimal("36.000000")
    max_pass_conflict_check_age_hours: Decimal = Decimal("12.000000")
    max_watch_conflict_check_age_hours: Decimal = Decimal("24.000000")
    max_watch_recheck_overdue_hours: Decimal = Decimal("6.000000")
    min_pass_fresh_corroborating_signal_count: Decimal = Decimal("2.000000")
    min_watch_fresh_corroborating_signal_count: Decimal = Decimal("1.000000")
    max_watch_unresolved_conflict_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSignalFreshnessGateConfig:
            raise ValueError("config must be a ResearchNewsSignalFreshnessGateConfig")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_NEWS_SIGNAL_FRESHNESS_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_update_age_hours",
            "max_watch_update_age_hours",
            "max_pass_corroboration_age_hours",
            "max_watch_corroboration_age_hours",
            "max_pass_conflict_check_age_hours",
            "max_watch_conflict_check_age_hours",
            "max_watch_recheck_overdue_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_fresh_corroborating_signal_count",
            "min_watch_fresh_corroborating_signal_count",
            "max_watch_unresolved_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("config payload", payload)
        if type(payload) is not dict:
            raise ValueError("config payload must be an object")
        _require_payload_fields(payload, _CONFIG_PAYLOAD_FIELDS)
        return payload


@dataclass(frozen=True)
class ResearchNewsSignalFreshnessGateInput:
    research_scope_ref: str
    latest_update_at: datetime
    latest_corroboration_at: datetime | None
    latest_conflict_check_at: datetime | None
    next_recheck_due_at: datetime
    corroborating_signal_count: Decimal
    fresh_corroborating_signal_count: Decimal
    unresolved_conflict_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSignalFreshnessGateInput:
            raise ValueError("subject must be a ResearchNewsSignalFreshnessGateInput")
        _require_identifier("research_scope_ref", self.research_scope_ref)
        object.__setattr__(
            self,
            "latest_update_at",
            _as_utc("latest_update_at", self.latest_update_at),
        )
        object.__setattr__(
            self,
            "latest_corroboration_at",
            _optional_utc("latest_corroboration_at", self.latest_corroboration_at),
        )
        object.__setattr__(
            self,
            "latest_conflict_check_at",
            _optional_utc("latest_conflict_check_at", self.latest_conflict_check_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        for field_name in (
            "corroborating_signal_count",
            "fresh_corroborating_signal_count",
            "unresolved_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.fresh_corroborating_signal_count > self.corroborating_signal_count:
            raise ValueError(
                "fresh_corroborating_signal_count must be at most "
                "corroborating_signal_count",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("subject", self)
        _reject_unsafe_public_payload("news signal freshness input", asdict(self))


@dataclass(frozen=True)
class ResearchNewsSignalFreshnessGateRow:
    research_scope_ref: str
    latest_update_at: datetime
    latest_corroboration_at: datetime | None
    latest_conflict_check_at: datetime | None
    next_recheck_due_at: datetime
    corroborating_signal_count: Decimal
    fresh_corroborating_signal_count: Decimal
    unresolved_conflict_count: Decimal
    update_age_hours: Decimal
    corroboration_age_hours: Decimal
    conflict_check_age_hours: Decimal
    recheck_overdue_hours: Decimal
    recheck_urgency_score: Decimal
    gate_status: str
    recommended_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSignalFreshnessGateRow:
            raise ValueError("row must be a ResearchNewsSignalFreshnessGateRow")
        _require_identifier("research_scope_ref", self.research_scope_ref)
        object.__setattr__(
            self,
            "latest_update_at",
            _as_utc("latest_update_at", self.latest_update_at),
        )
        object.__setattr__(
            self,
            "latest_corroboration_at",
            _optional_utc("latest_corroboration_at", self.latest_corroboration_at),
        )
        object.__setattr__(
            self,
            "latest_conflict_check_at",
            _optional_utc("latest_conflict_check_at", self.latest_conflict_check_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        for field_name in (
            "corroborating_signal_count",
            "fresh_corroborating_signal_count",
            "unresolved_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "update_age_hours",
            "corroboration_age_hours",
            "conflict_check_age_hours",
            "recheck_overdue_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recheck_urgency_score",
            _normalize_probability("recheck_urgency_score", self.recheck_urgency_score),
        )
        _require_choice("gate_status", self.gate_status, STATUSES)
        _require_choice(
            "recommended_research_action",
            self.recommended_research_action,
            tuple(ROW_ACTIONS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("news signal freshness row", asdict(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchNewsSignalFreshnessGateReport:
    generated_at: datetime
    config_version: str
    status: str
    recommended_next_step: str
    input_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_update_count: Decimal
    stale_corroboration_count: Decimal
    stale_conflict_check_count: Decimal
    urgent_recheck_count: Decimal
    unresolved_conflict_scope_count: Decimal
    highest_recheck_urgency_score: Decimal
    max_update_age_hours: Decimal
    max_corroboration_age_hours: Decimal
    max_conflict_check_age_hours: Decimal
    max_recheck_overdue_hours: Decimal
    rows: tuple[ResearchNewsSignalFreshnessGateRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSignalFreshnessGateReport:
            raise ValueError("report must be a ResearchNewsSignalFreshnessGateReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_NEWS_SIGNAL_FRESHNESS_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        _require_choice("status", self.status, STATUSES)
        _require_choice(
            "recommended_next_step",
            self.recommended_next_step,
            tuple(REPORT_NEXT_STEPS.values()),
        )
        for field_name in (
            "input_count",
            "block_count",
            "watch_count",
            "pass_count",
            "stale_update_count",
            "stale_corroboration_count",
            "stale_conflict_check_count",
            "urgent_recheck_count",
            "unresolved_conflict_scope_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_update_age_hours",
            "max_corroboration_age_hours",
            "max_conflict_check_age_hours",
            "max_recheck_overdue_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_recheck_urgency_score",
            _normalize_probability(
                "highest_recheck_urgency_score",
                self.highest_recheck_urgency_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("news signal freshness report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _derived_validation_digest(self),
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
        _validate_report(self)
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("news signal freshness payload", payload)
        if type(payload) is not dict:
            raise ValueError("news signal freshness payload must be an object")
        _require_payload_fields(payload, _REPORT_PAYLOAD_FIELDS)
        _validate_report_derived_validation_digest(self)
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> ResearchNewsSignalFreshnessGateReport:
        _reject_unsafe_public_payload("news signal freshness payload", payload)
        payload_dict = _payload_dict("news signal freshness payload", payload)
        _require_payload_fields(payload_dict, _REPORT_PAYLOAD_FIELDS)
        rows_value = payload_dict["rows"]
        if type(rows_value) is not list:
            raise ValueError("rows must be a list")
        rows = tuple(_row_from_payload(item) for item in rows_value)
        return cls(
            generated_at=_datetime_from_payload("generated_at", payload_dict["generated_at"]),
            config_version=_payload_string("config_version", payload_dict["config_version"]),
            status=_payload_string("status", payload_dict["status"]),
            recommended_next_step=_payload_string(
                "recommended_next_step",
                payload_dict["recommended_next_step"],
            ),
            input_count=_decimal_from_payload("input_count", payload_dict["input_count"]),
            block_count=_decimal_from_payload("block_count", payload_dict["block_count"]),
            watch_count=_decimal_from_payload("watch_count", payload_dict["watch_count"]),
            pass_count=_decimal_from_payload("pass_count", payload_dict["pass_count"]),
            stale_update_count=_decimal_from_payload(
                "stale_update_count",
                payload_dict["stale_update_count"],
            ),
            stale_corroboration_count=_decimal_from_payload(
                "stale_corroboration_count",
                payload_dict["stale_corroboration_count"],
            ),
            stale_conflict_check_count=_decimal_from_payload(
                "stale_conflict_check_count",
                payload_dict["stale_conflict_check_count"],
            ),
            urgent_recheck_count=_decimal_from_payload(
                "urgent_recheck_count",
                payload_dict["urgent_recheck_count"],
            ),
            unresolved_conflict_scope_count=_decimal_from_payload(
                "unresolved_conflict_scope_count",
                payload_dict["unresolved_conflict_scope_count"],
            ),
            highest_recheck_urgency_score=_decimal_from_payload(
                "highest_recheck_urgency_score",
                payload_dict["highest_recheck_urgency_score"],
            ),
            max_update_age_hours=_decimal_from_payload(
                "max_update_age_hours",
                payload_dict["max_update_age_hours"],
            ),
            max_corroboration_age_hours=_decimal_from_payload(
                "max_corroboration_age_hours",
                payload_dict["max_corroboration_age_hours"],
            ),
            max_conflict_check_age_hours=_decimal_from_payload(
                "max_conflict_check_age_hours",
                payload_dict["max_conflict_check_age_hours"],
            ),
            max_recheck_overdue_hours=_decimal_from_payload(
                "max_recheck_overdue_hours",
                payload_dict["max_recheck_overdue_hours"],
            ),
            rows=rows,
            reason_codes=_payload_reason_codes("reason_codes", payload_dict["reason_codes"]),
            derived_validation_digest=_payload_string(
                DERIVED_VALIDATION_DIGEST_FIELD,
                payload_dict[DERIVED_VALIDATION_DIGEST_FIELD],
            ),
            paper_only=_payload_true("paper_only", payload_dict["paper_only"]),
            report_only=_payload_true("report_only", payload_dict["report_only"]),
            readonly=_payload_true("readonly", payload_dict["readonly"]),
        )


def build_research_news_signal_freshness_gate_report(
    rows: object,
    *,
    config: ResearchNewsSignalFreshnessGateConfig,
    generated_at: datetime,
) -> ResearchNewsSignalFreshnessGateReport:
    if type(config) is not ResearchNewsSignalFreshnessGateConfig:
        raise ValueError("config must be a ResearchNewsSignalFreshnessGateConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rows)
    built_rows = tuple(_build_row(item, config=config, generated_at=generated_at_utc) for item in inputs)
    ranked_rows = _rank_rows(built_rows)
    status = _report_status(ranked_rows)
    return ResearchNewsSignalFreshnessGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        recommended_next_step=REPORT_NEXT_STEPS[status],
        input_count=_count(len(ranked_rows)),
        block_count=_count(sum(1 for row in ranked_rows if row.gate_status == "block")),
        watch_count=_count(sum(1 for row in ranked_rows if row.gate_status == "watch")),
        pass_count=_count(sum(1 for row in ranked_rows if row.gate_status == "pass")),
        stale_update_count=_count(
            sum(
                1
                for row in ranked_rows
                if "news_update_stale_watch" in row.reason_codes
                or "news_update_stale_block" in row.reason_codes
            ),
        ),
        stale_corroboration_count=_count(
            sum(
                1
                for row in ranked_rows
                if "corroboration_missing_block" in row.reason_codes
                or "corroboration_stale_watch" in row.reason_codes
                or "corroboration_stale_block" in row.reason_codes
            ),
        ),
        stale_conflict_check_count=_count(
            sum(
                1
                for row in ranked_rows
                if "conflict_check_missing_block" in row.reason_codes
                or "conflict_check_stale_watch" in row.reason_codes
                or "conflict_check_stale_block" in row.reason_codes
            ),
        ),
        urgent_recheck_count=_count(
            sum(
                1
                for row in ranked_rows
                if "recheck_overdue_watch" in row.reason_codes
                or "recheck_overdue_block" in row.reason_codes
            ),
        ),
        unresolved_conflict_scope_count=_count(
            sum(
                1
                for row in ranked_rows
                if "unresolved_conflict_watch" in row.reason_codes
                or "unresolved_conflict_block" in row.reason_codes
            ),
        ),
        highest_recheck_urgency_score=_max_decimal(
            row.recheck_urgency_score for row in ranked_rows
        ),
        max_update_age_hours=_max_decimal(row.update_age_hours for row in ranked_rows),
        max_corroboration_age_hours=_max_decimal(
            row.corroboration_age_hours for row in ranked_rows
        ),
        max_conflict_check_age_hours=_max_decimal(
            row.conflict_check_age_hours for row in ranked_rows
        ),
        max_recheck_overdue_hours=_max_decimal(
            row.recheck_overdue_hours for row in ranked_rows
        ),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_news_signal_freshness_gate_report_payload(
    report: ResearchNewsSignalFreshnessGateReport,
) -> dict[str, object]:
    if type(report) is not ResearchNewsSignalFreshnessGateReport:
        raise ValueError("report must be a ResearchNewsSignalFreshnessGateReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    _validate_report_derived_validation_digest(report)
    return report.payload


def _build_row(
    item: ResearchNewsSignalFreshnessGateInput,
    *,
    config: ResearchNewsSignalFreshnessGateConfig,
    generated_at: datetime,
) -> ResearchNewsSignalFreshnessGateRow:
    _validate_input_timestamps(item, generated_at)
    update_age_hours = _hours_between(item.latest_update_at, generated_at)
    corroboration_age_hours = _optional_age_hours(
        item.latest_corroboration_at,
        missing_age_hours=config.max_watch_corroboration_age_hours + ONE,
        generated_at=generated_at,
    )
    conflict_check_age_hours = _optional_age_hours(
        item.latest_conflict_check_at,
        missing_age_hours=config.max_watch_conflict_check_age_hours + ONE,
        generated_at=generated_at,
    )
    recheck_overdue_hours = _recheck_overdue_hours(item.next_recheck_due_at, generated_at)
    reason_codes = [
        *item.reason_codes,
        *_freshness_reason_codes(
            latest_corroboration_at=item.latest_corroboration_at,
            latest_conflict_check_at=item.latest_conflict_check_at,
            update_age_hours=update_age_hours,
            corroboration_age_hours=corroboration_age_hours,
            conflict_check_age_hours=conflict_check_age_hours,
            recheck_overdue_hours=recheck_overdue_hours,
            fresh_corroborating_signal_count=item.fresh_corroborating_signal_count,
            unresolved_conflict_count=item.unresolved_conflict_count,
            config=config,
        ),
    ]
    gate_status = _row_status(reason_codes)
    reason_codes.append(STATUS_REASON[gate_status])
    return ResearchNewsSignalFreshnessGateRow(
        research_scope_ref=item.research_scope_ref,
        latest_update_at=item.latest_update_at,
        latest_corroboration_at=item.latest_corroboration_at,
        latest_conflict_check_at=item.latest_conflict_check_at,
        next_recheck_due_at=item.next_recheck_due_at,
        corroborating_signal_count=item.corroborating_signal_count,
        fresh_corroborating_signal_count=item.fresh_corroborating_signal_count,
        unresolved_conflict_count=item.unresolved_conflict_count,
        update_age_hours=update_age_hours,
        corroboration_age_hours=corroboration_age_hours,
        conflict_check_age_hours=conflict_check_age_hours,
        recheck_overdue_hours=recheck_overdue_hours,
        recheck_urgency_score=_risk_score_for_status(gate_status),
        gate_status=gate_status,
        recommended_research_action=ROW_ACTIONS[gate_status],
        reason_codes=_sort_reason_codes(tuple(reason_codes)),
    )


def _freshness_reason_codes(
    *,
    latest_corroboration_at: datetime | None,
    latest_conflict_check_at: datetime | None,
    update_age_hours: Decimal,
    corroboration_age_hours: Decimal,
    conflict_check_age_hours: Decimal,
    recheck_overdue_hours: Decimal,
    fresh_corroborating_signal_count: Decimal,
    unresolved_conflict_count: Decimal,
    config: ResearchNewsSignalFreshnessGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if update_age_hours > config.max_watch_update_age_hours:
        reason_codes.append("news_update_stale_block")
    elif update_age_hours > config.max_pass_update_age_hours:
        reason_codes.append("news_update_stale_watch")

    if latest_corroboration_at is None:
        reason_codes.append("corroboration_missing_block")
    elif corroboration_age_hours > config.max_watch_corroboration_age_hours:
        reason_codes.append("corroboration_stale_block")
    elif corroboration_age_hours > config.max_pass_corroboration_age_hours:
        reason_codes.append("corroboration_stale_watch")

    if fresh_corroborating_signal_count < config.min_watch_fresh_corroborating_signal_count:
        reason_codes.append("corroboration_insufficient_block")
    elif fresh_corroborating_signal_count < config.min_pass_fresh_corroborating_signal_count:
        reason_codes.append("corroboration_insufficient_watch")

    if latest_conflict_check_at is None:
        reason_codes.append("conflict_check_missing_block")
    elif conflict_check_age_hours > config.max_watch_conflict_check_age_hours:
        reason_codes.append("conflict_check_stale_block")
    elif conflict_check_age_hours > config.max_pass_conflict_check_age_hours:
        reason_codes.append("conflict_check_stale_watch")

    if unresolved_conflict_count > config.max_watch_unresolved_conflict_count:
        reason_codes.append("unresolved_conflict_block")
    elif unresolved_conflict_count > ZERO:
        reason_codes.append("unresolved_conflict_watch")

    if recheck_overdue_hours > config.max_watch_recheck_overdue_hours:
        reason_codes.append("recheck_overdue_block")
    elif recheck_overdue_hours > ZERO:
        reason_codes.append("recheck_overdue_watch")
    return tuple(reason_codes)


def _validate_config(config: ResearchNewsSignalFreshnessGateConfig) -> None:
    if config.max_pass_update_age_hours > config.max_watch_update_age_hours:
        raise ValueError("max_pass_update_age_hours must be at most max_watch_update_age_hours")
    if config.max_pass_corroboration_age_hours > config.max_watch_corroboration_age_hours:
        raise ValueError(
            "max_pass_corroboration_age_hours must be at most "
            "max_watch_corroboration_age_hours",
        )
    if config.max_pass_conflict_check_age_hours > config.max_watch_conflict_check_age_hours:
        raise ValueError(
            "max_pass_conflict_check_age_hours must be at most "
            "max_watch_conflict_check_age_hours",
        )
    if (
        config.min_pass_fresh_corroborating_signal_count
        < config.min_watch_fresh_corroborating_signal_count
    ):
        raise ValueError(
            "min_pass_fresh_corroborating_signal_count must be at least "
            "min_watch_fresh_corroborating_signal_count",
        )


def _validate_row(row: ResearchNewsSignalFreshnessGateRow) -> None:
    if row.fresh_corroborating_signal_count > row.corroborating_signal_count:
        raise ValueError(
            "fresh_corroborating_signal_count must be at most corroborating_signal_count",
        )
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.recheck_urgency_score != _risk_score_for_status(row.gate_status):
        raise ValueError("recheck_urgency_score must match gate_status")
    if row.recommended_research_action != ROW_ACTIONS[row.gate_status]:
        raise ValueError("recommended_research_action must match gate_status")
    if STATUS_REASON[row.gate_status] not in row.reason_codes:
        raise ValueError("reason_codes must include gate_status reason")


def _validate_report(report: ResearchNewsSignalFreshnessGateReport) -> None:
    rows = report.rows
    for row in rows:
        _validate_row(row)
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.gate_status == "block")):
        raise ValueError("block_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.gate_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.gate_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.stale_update_count != _count(
        sum(
            1
            for row in rows
            if "news_update_stale_watch" in row.reason_codes
            or "news_update_stale_block" in row.reason_codes
        ),
    ):
        raise ValueError("stale_update_count must match rows")
    if report.stale_corroboration_count != _count(
        sum(
            1
            for row in rows
            if "corroboration_missing_block" in row.reason_codes
            or "corroboration_stale_watch" in row.reason_codes
            or "corroboration_stale_block" in row.reason_codes
        ),
    ):
        raise ValueError("stale_corroboration_count must match rows")
    if report.stale_conflict_check_count != _count(
        sum(
            1
            for row in rows
            if "conflict_check_missing_block" in row.reason_codes
            or "conflict_check_stale_watch" in row.reason_codes
            or "conflict_check_stale_block" in row.reason_codes
        ),
    ):
        raise ValueError("stale_conflict_check_count must match rows")
    if report.urgent_recheck_count != _count(
        sum(
            1
            for row in rows
            if "recheck_overdue_watch" in row.reason_codes
            or "recheck_overdue_block" in row.reason_codes
        ),
    ):
        raise ValueError("urgent_recheck_count must match rows")
    if report.unresolved_conflict_scope_count != _count(
        sum(
            1
            for row in rows
            if "unresolved_conflict_watch" in row.reason_codes
            or "unresolved_conflict_block" in row.reason_codes
        ),
    ):
        raise ValueError("unresolved_conflict_scope_count must match rows")
    if report.highest_recheck_urgency_score != _max_decimal(
        row.recheck_urgency_score for row in rows
    ):
        raise ValueError("highest_recheck_urgency_score must match rows")
    if report.max_update_age_hours != _max_decimal(row.update_age_hours for row in rows):
        raise ValueError("max_update_age_hours must match rows")
    if report.max_corroboration_age_hours != _max_decimal(
        row.corroboration_age_hours for row in rows
    ):
        raise ValueError("max_corroboration_age_hours must match rows")
    if report.max_conflict_check_age_hours != _max_decimal(
        row.conflict_check_age_hours for row in rows
    ):
        raise ValueError("max_conflict_check_age_hours must match rows")
    if report.max_recheck_overdue_hours != _max_decimal(
        row.recheck_overdue_hours for row in rows
    ):
        raise ValueError("max_recheck_overdue_hours must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.recommended_next_step != REPORT_NEXT_STEPS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_derived_validation_digest(
    report: ResearchNewsSignalFreshnessGateReport,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _validate_input_timestamps(
    item: ResearchNewsSignalFreshnessGateInput,
    generated_at: datetime,
) -> None:
    if item.latest_update_at > generated_at:
        raise ValueError("latest_update_at must not be after generated_at")
    if item.latest_corroboration_at is not None and item.latest_corroboration_at > generated_at:
        raise ValueError("latest_corroboration_at must not be after generated_at")
    if item.latest_conflict_check_at is not None and item.latest_conflict_check_at > generated_at:
        raise ValueError("latest_conflict_check_at must not be after generated_at")


def _normalize_inputs(rows: object) -> tuple[ResearchNewsSignalFreshnessGateInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchNewsSignalFreshnessGateInput:
            raise ValueError("rows must contain ResearchNewsSignalFreshnessGateInput")
        _require_hard_flags("subject", row)
    return normalized


def _normalize_rows(rows: object) -> tuple[ResearchNewsSignalFreshnessGateRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchNewsSignalFreshnessGateRow:
            raise ValueError("rows must contain ResearchNewsSignalFreshnessGateRow")
        _require_hard_flags("row", row)
    return _rank_rows(normalized)


def _rank_rows(
    rows: tuple[ResearchNewsSignalFreshnessGateRow, ...],
) -> tuple[ResearchNewsSignalFreshnessGateRow, ...]:
    status_rank = {"block": Decimal("0.000000"), "watch": Decimal("1.000000"), "pass": Decimal("2.000000")}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_rank[row.gate_status],
                -row.recheck_urgency_score,
                -row.update_age_hours,
                row.research_scope_ref,
            ),
        ),
    )


def _report_status(rows: tuple[ResearchNewsSignalFreshnessGateRow, ...]) -> str:
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_status(reason_codes: Iterable[str]) -> str:
    values = tuple(reason_codes)
    if any(reason_code in BLOCK_REASONS for reason_code in values):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in values):
        return "watch"
    return "pass"


def _risk_score_for_status(status: str) -> Decimal:
    if status == "block":
        return ONE
    if status == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _report_reason_codes(
    rows: tuple[ResearchNewsSignalFreshnessGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            "news_signal_freshness_gate_no_inputs",
            "news_signal_freshness_gate_status_pass",
        )
    values: list[str] = [STATUS_REASON[_report_status(rows)]]
    for row in rows:
        values.extend(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in REASON_CODES
            and not reason_code.startswith("news_signal_freshness_gate_status_")
        )
    return _normalize_report_reason_codes("reason_codes", tuple(values))


def _row_from_payload(payload: object) -> ResearchNewsSignalFreshnessGateRow:
    payload_dict = _payload_dict("row", payload)
    _require_payload_fields(payload_dict, _ROW_PAYLOAD_FIELDS)
    return ResearchNewsSignalFreshnessGateRow(
        research_scope_ref=_payload_string("research_scope_ref", payload_dict["research_scope_ref"]),
        latest_update_at=_datetime_from_payload("latest_update_at", payload_dict["latest_update_at"]),
        latest_corroboration_at=_optional_datetime_from_payload(
            "latest_corroboration_at",
            payload_dict["latest_corroboration_at"],
        ),
        latest_conflict_check_at=_optional_datetime_from_payload(
            "latest_conflict_check_at",
            payload_dict["latest_conflict_check_at"],
        ),
        next_recheck_due_at=_datetime_from_payload(
            "next_recheck_due_at",
            payload_dict["next_recheck_due_at"],
        ),
        corroborating_signal_count=_decimal_from_payload(
            "corroborating_signal_count",
            payload_dict["corroborating_signal_count"],
        ),
        fresh_corroborating_signal_count=_decimal_from_payload(
            "fresh_corroborating_signal_count",
            payload_dict["fresh_corroborating_signal_count"],
        ),
        unresolved_conflict_count=_decimal_from_payload(
            "unresolved_conflict_count",
            payload_dict["unresolved_conflict_count"],
        ),
        update_age_hours=_decimal_from_payload("update_age_hours", payload_dict["update_age_hours"]),
        corroboration_age_hours=_decimal_from_payload(
            "corroboration_age_hours",
            payload_dict["corroboration_age_hours"],
        ),
        conflict_check_age_hours=_decimal_from_payload(
            "conflict_check_age_hours",
            payload_dict["conflict_check_age_hours"],
        ),
        recheck_overdue_hours=_decimal_from_payload(
            "recheck_overdue_hours",
            payload_dict["recheck_overdue_hours"],
        ),
        recheck_urgency_score=_decimal_from_payload(
            "recheck_urgency_score",
            payload_dict["recheck_urgency_score"],
        ),
        gate_status=_payload_string("gate_status", payload_dict["gate_status"]),
        recommended_research_action=_payload_string(
            "recommended_research_action",
            payload_dict["recommended_research_action"],
        ),
        reason_codes=_payload_reason_codes("reason_codes", payload_dict["reason_codes"]),
        paper_only=_payload_true("paper_only", payload_dict["paper_only"]),
        report_only=_payload_true("report_only", payload_dict["report_only"]),
        readonly=_payload_true("readonly", payload_dict["readonly"]),
    )


def _optional_age_hours(
    value: datetime | None,
    *,
    missing_age_hours: Decimal,
    generated_at: datetime,
) -> Decimal:
    if value is None:
        return _quantize(missing_age_hours)
    return _hours_between(value, generated_at)


def _recheck_overdue_hours(next_recheck_due_at: datetime, generated_at: datetime) -> Decimal:
    if next_recheck_due_at >= generated_at:
        return ZERO
    return _hours_between(next_recheck_due_at, generated_at)


def _hours_between(earlier: datetime, later: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("timestamp must not be after generated_at")
    with localcontext(DECIMAL_CONTEXT):
        whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
        fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _quantize((whole_seconds + fractional_seconds) / SECONDS_PER_HOUR)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
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


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _optional_datetime_from_payload(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _datetime_from_payload(field_name, value)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    return _normalize_decimal(field_name, decimal_value)


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_row_reason_codes(field_name, tuple(value))


def _payload_dict(field_name: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be an object")
    return value


def _require_payload_fields(payload: dict[str, object], expected_fields: tuple[str, ...]) -> None:
    if tuple(payload.keys()) != expected_fields:
        raise ValueError("payload fields must match schema")


def _normalize_source_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        _reject_unsafe_public_payload("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _normalize_row_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        _reject_unsafe_public_payload("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return _sort_reason_codes(tuple(normalized))


def _normalize_report_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("report reason_codes must be known")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in normalized
    )


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unknown = tuple(reason_code for reason_code in reason_codes if reason_code not in REASON_CODES)
    known = tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in reason_codes)
    return (*unknown, *known)


def _require_hard_flags(label: str, value: object) -> None:
    del label
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be a supported value")


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if _contains_raw_identifier(lowered):
        raise ValueError("raw identifiers are not allowed")
    if _contains_restricted_identifier(lowered):
        raise ValueError("market identifiers are not allowed")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _contains_raw_identifier(value: str) -> bool:
    return any(term in value for term in _raw_identifier_terms())


def _contains_restricted_identifier(value: str) -> bool:
    return any(term in value for term in _restricted_identifier_terms())


def _raw_identifier_terms() -> tuple[str, ...]:
    return (
        "://",
        "www.",
        "@",
        "?",
        "=",
        "source" + "_text",
        "raw" + "_url",
    )


def _restricted_identifier_terms() -> tuple[str, ...]:
    return (
        "market" + "_slug",
        "market" + "_id",
        "condition" + "_id",
        "token" + "_id",
        "poly" + "market",
    )


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            lowered_key = key.lower()
            if _contains_raw_identifier(lowered_key):
                raise ValueError("raw identifiers are not allowed")
            if _contains_restricted_identifier(lowered_key):
                raise ValueError("market identifiers are not allowed")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if _contains_raw_identifier(lowered_value):
            raise ValueError("raw identifiers are not allowed")
        if _contains_restricted_identifier(lowered_value):
            raise ValueError("market identifiers are not allowed")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _derived_validation_digest(report: ResearchNewsSignalFreshnessGateReport) -> str:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = ""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_payload_value(item) for item in value]
    return value
