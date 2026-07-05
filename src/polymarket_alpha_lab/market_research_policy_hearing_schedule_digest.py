"""Pure Phase 1 policy hearing schedule digest reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_POLICY_HEARING_SCHEDULE_DIGEST_CONFIG_VERSION = (
    "market-research-policy-hearing-schedule-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"

REASON_PREFIX = "market_research_policy_hearing_schedule_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
LOW_AGREEMENT_REASON = f"{REASON_PREFIX}low_agreement"
MATERIAL_WATCH_REASON = f"{REASON_PREFIX}material_watch"
MATERIAL_BLOCK_REASON = f"{REASON_PREFIX}material_block"
MISSING_CONFIRMATION_REASON = f"{REASON_PREFIX}missing_confirmation"
NEAR_HEARING_REASON = f"{REASON_PREFIX}near_hearing"
PAST_HEARING_REASON = f"{REASON_PREFIX}past_hearing"
PROBABILITY_SHIFT_REASON = f"{REASON_PREFIX}probability_shift"
STALE_CONFIRMATION_REASON = f"{REASON_PREFIX}stale_confirmation"
STALE_SCHEDULE_REASON = f"{REASON_PREFIX}stale_schedule"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    MATERIAL_BLOCK_REASON,
    MISSING_CONFIRMATION_REASON,
    NEAR_HEARING_REASON,
    PROBABILITY_SHIFT_REASON,
    LOW_AGREEMENT_REASON,
    MATERIAL_WATCH_REASON,
    PAST_HEARING_REASON,
    STALE_CONFIRMATION_REASON,
    STALE_SCHEDULE_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    LOW_AGREEMENT_REASON,
    MATERIAL_BLOCK_REASON,
    MATERIAL_WATCH_REASON,
    MISSING_CONFIRMATION_REASON,
    NEAR_HEARING_REASON,
    PAST_HEARING_REASON,
    PROBABILITY_SHIFT_REASON,
    READY_REASON,
    STALE_CONFIRMATION_REASON,
    STALE_SCHEDULE_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_policy_hearing_schedule_digest",
    STATUS_WATCH: "watch_report_only_market_research_policy_hearing_schedule_digest",
    STATUS_BLOCKED: "block_report_only_market_research_policy_hearing_schedule_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_SHIFT_THRESHOLD = Decimal("0.100000")

_PUBLIC_REFERENCE_FRAGMENTS = ("public", "notice", "memo", "bulletin", "release")


@dataclass(frozen=True)
class MarketResearchPolicyHearingScheduleDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_HEARING_SCHEDULE_DIGEST_CONFIG_VERSION
    )
    fresh_schedule_max_age_seconds: Decimal = Decimal("86400.000000")
    min_public_source_count: Decimal = Decimal("2")
    near_hearing_window_seconds: Decimal = Decimal("172800.000000")
    stale_confirmation_after_seconds: Decimal = Decimal("21600.000000")
    min_cross_source_agreement: Decimal = Decimal("0.600000")
    materiality_watch_threshold: Decimal = Decimal("0.150000")
    materiality_block_threshold: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyHearingScheduleDigestConfig:
            raise TypeError(
                "MarketResearchPolicyHearingScheduleDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyHearingScheduleDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchPolicyHearingScheduleDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_schedule_max_age_seconds",
            "near_hearing_window_seconds",
            "stale_confirmation_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_nonnegative_count_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        for field_name in (
            "min_cross_source_agreement",
            "materiality_watch_threshold",
            "materiality_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.materiality_watch_threshold > self.materiality_block_threshold:
            raise ValueError(
                "materiality_block_threshold must be at least materiality_watch_threshold",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyHearingScheduleDigestInputRow:
    research_key: str
    condition_id: str
    policy_area: str
    hearing_id: str
    public_schedule_reference: str
    hearing_scheduled_at: datetime
    schedule_observed_at: datetime
    confirmed_at: datetime | None
    public_source_count: Decimal
    cross_source_agreement: Decimal
    schedule_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyHearingScheduleDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyHearingScheduleDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyHearingScheduleDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPolicyHearingScheduleDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "policy_area", "hearing_id"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_schedule_reference", self.public_schedule_reference)
        object.__setattr__(
            self,
            "hearing_scheduled_at",
            _as_utc("hearing_scheduled_at", self.hearing_scheduled_at),
        )
        object.__setattr__(
            self,
            "schedule_observed_at",
            _as_utc("schedule_observed_at", self.schedule_observed_at),
        )
        object.__setattr__(
            self,
            "confirmed_at",
            _optional_utc("confirmed_at", self.confirmed_at),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "cross_source_agreement",
            "schedule_materiality_score",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.confirmed_at is not None and self.confirmed_at < self.schedule_observed_at:
            raise ValueError("confirmed_at must be on or after schedule_observed_at")
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyHearingScheduleDigestRow:
    research_key: str
    condition_id: str
    policy_area: str
    hearing_id: str
    hearing_scheduled_at: datetime
    schedule_observed_at: datetime
    confirmed_at: datetime | None
    schedule_age_seconds: Decimal
    seconds_until_hearing: Decimal
    confirmation_lag_seconds: Decimal | None
    public_source_count: Decimal
    cross_source_agreement: Decimal
    schedule_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    hearing_status: str
    redacted_schedule_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyHearingScheduleDigestRow:
            raise TypeError(
                "MarketResearchPolicyHearingScheduleDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyHearingScheduleDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchPolicyHearingScheduleDigestRow",
            )
        for field_name in ("research_key", "condition_id", "policy_area", "hearing_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "hearing_scheduled_at",
            _as_utc("hearing_scheduled_at", self.hearing_scheduled_at),
        )
        object.__setattr__(
            self,
            "schedule_observed_at",
            _as_utc("schedule_observed_at", self.schedule_observed_at),
        )
        object.__setattr__(
            self,
            "confirmed_at",
            _optional_utc("confirmed_at", self.confirmed_at),
        )
        object.__setattr__(
            self,
            "schedule_age_seconds",
            _require_nonnegative_decimal("schedule_age_seconds", self.schedule_age_seconds),
        )
        object.__setattr__(
            self,
            "seconds_until_hearing",
            _require_finite_decimal("seconds_until_hearing", self.seconds_until_hearing),
        )
        object.__setattr__(
            self,
            "confirmation_lag_seconds",
            _require_optional_nonnegative_decimal(
                "confirmation_lag_seconds",
                self.confirmation_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "cross_source_agreement",
            "schedule_materiality_score",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_change",
            _require_probability_change("probability_change", self.probability_change),
        )
        _require_status("hearing_status", self.hearing_status)
        object.__setattr__(
            self,
            "redacted_schedule_reference",
            _require_redacted_reference(
                "redacted_schedule_reference",
                self.redacted_schedule_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyHearingScheduleDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    hearing_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyHearingScheduleDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyHearingScheduleDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyHearingScheduleDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchPolicyHearingScheduleDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "hearing_ratio",
            _require_ratio_decimal("hearing_ratio", self.hearing_ratio),
        )
        require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyHearingScheduleDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    hearing_count: Decimal
    ready_hearing_count: Decimal
    watch_hearing_count: Decimal
    blocked_hearing_count: Decimal
    material_hearing_count: Decimal
    near_hearing_count: Decimal
    past_hearing_count: Decimal
    stale_schedule_count: Decimal
    thin_source_count: Decimal
    low_agreement_count: Decimal
    missing_confirmation_count: Decimal
    stale_confirmation_count: Decimal
    average_materiality_score: Decimal
    min_seconds_until_hearing: Decimal
    average_public_source_count: Decimal
    rows: tuple[MarketResearchPolicyHearingScheduleDigestRow, ...]
    reason_code_counts: tuple[MarketResearchPolicyHearingScheduleDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyHearingScheduleDigestReport:
            raise TypeError(
                "MarketResearchPolicyHearingScheduleDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyHearingScheduleDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchPolicyHearingScheduleDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "hearing_count",
            "ready_hearing_count",
            "watch_hearing_count",
            "blocked_hearing_count",
            "material_hearing_count",
            "near_hearing_count",
            "past_hearing_count",
            "stale_schedule_count",
            "thin_source_count",
            "low_agreement_count",
            "missing_confirmation_count",
            "stale_confirmation_count",
            "average_materiality_score",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_seconds_until_hearing",
            _require_finite_decimal(
                "min_seconds_until_hearing",
                self.min_seconds_until_hearing,
            ),
        )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not MarketResearchPolicyHearingScheduleDigestRow:
                raise ValueError(
                    "rows must contain MarketResearchPolicyHearingScheduleDigestRow",
                )
            require_paper_only_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not MarketResearchPolicyHearingScheduleDigestReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "MarketResearchPolicyHearingScheduleDigestReasonCodeCount",
                )
            require_paper_only_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_market_research_policy_hearing_schedule_digest(
    input_rows: list[MarketResearchPolicyHearingScheduleDigestInputRow]
    | tuple[MarketResearchPolicyHearingScheduleDigestInputRow, ...],
    *,
    config: MarketResearchPolicyHearingScheduleDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchPolicyHearingScheduleDigestReport:
    cfg = (
        MarketResearchPolicyHearingScheduleDigestConfig()
        if config is None
        else config
    )
    if type(cfg) is not MarketResearchPolicyHearingScheduleDigestConfig:
        raise ValueError("config must be a MarketResearchPolicyHearingScheduleDigestConfig")
    require_paper_only_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    hearing_count = _count(len(ranked_rows))
    ready_hearing_count = _count(
        sum(1 for row in ranked_rows if row.hearing_status == STATUS_READY),
    )
    watch_hearing_count = _count(
        sum(1 for row in ranked_rows if row.hearing_status == STATUS_WATCH),
    )
    blocked_hearing_count = _count(
        sum(1 for row in ranked_rows if row.hearing_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                hearing_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_hearing_count=blocked_hearing_count,
        watch_hearing_count=watch_hearing_count,
    )
    return MarketResearchPolicyHearingScheduleDigestReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        hearing_count=hearing_count,
        ready_hearing_count=ready_hearing_count,
        watch_hearing_count=watch_hearing_count,
        blocked_hearing_count=blocked_hearing_count,
        material_hearing_count=_count(
            sum(
                1
                for row in ranked_rows
                if MATERIAL_BLOCK_REASON in row.reason_codes
                or MATERIAL_WATCH_REASON in row.reason_codes
            ),
        ),
        near_hearing_count=_count(
            sum(1 for row in ranked_rows if NEAR_HEARING_REASON in row.reason_codes),
        ),
        past_hearing_count=_count(
            sum(1 for row in ranked_rows if PAST_HEARING_REASON in row.reason_codes),
        ),
        stale_schedule_count=_count(
            sum(1 for row in ranked_rows if STALE_SCHEDULE_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        low_agreement_count=_count(
            sum(1 for row in ranked_rows if LOW_AGREEMENT_REASON in row.reason_codes),
        ),
        missing_confirmation_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_CONFIRMATION_REASON in row.reason_codes
            ),
        ),
        stale_confirmation_count=_count(
            sum(
                1
                for row in ranked_rows
                if STALE_CONFIRMATION_REASON in row.reason_codes
            ),
        ),
        average_materiality_score=_ratio(
            _sum_decimal(row.schedule_materiality_score for row in ranked_rows),
            hearing_count,
        ),
        min_seconds_until_hearing=min(
            (row.seconds_until_hearing for row in ranked_rows),
            default=ZERO,
        ),
        average_public_source_count=_ratio(
            _sum_decimal(row.public_source_count for row in ranked_rows),
            hearing_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_hearing_schedule_digest_payload(
    report: MarketResearchPolicyHearingScheduleDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyHearingScheduleDigestReport:
        raise ValueError(
            "report must be a MarketResearchPolicyHearingScheduleDigestReport",
        )
    payload = _payload_public_dataclass(report)
    reject_unsafe_surface_fields("policy hearing schedule digest payload", payload)
    ready = json_ready_no_floats(payload)
    if not isinstance(ready, dict):
        raise ValueError("payload must be a JSON object")
    return ready


def _payload_public_dataclass(value: object) -> dict[str, Any]:
    if type(value) is MarketResearchPolicyHearingScheduleDigestReport:
        return _report_payload(value)
    if type(value) is MarketResearchPolicyHearingScheduleDigestRow:
        return _row_payload(value)
    if type(value) is MarketResearchPolicyHearingScheduleDigestReasonCodeCount:
        return _reason_code_count_payload(value)
    raise ValueError(
        "payload helper only accepts policy hearing schedule digest report dataclasses",
    )


def _report_payload(
    report: MarketResearchPolicyHearingScheduleDigestReport,
) -> dict[str, Any]:
    require_paper_only_flags("report", report)
    generated_at = _payload_utc_datetime("generated_at", report.generated_at)
    _require_public_string("config_version", report.config_version)
    _require_status("digest_status", report.digest_status)
    _require_public_string("next_step", report.next_step)
    hearing_count = _payload_nonnegative_count_decimal(
        "hearing_count",
        report.hearing_count,
    )
    ready_hearing_count = _payload_nonnegative_count_decimal(
        "ready_hearing_count",
        report.ready_hearing_count,
    )
    watch_hearing_count = _payload_nonnegative_count_decimal(
        "watch_hearing_count",
        report.watch_hearing_count,
    )
    blocked_hearing_count = _payload_nonnegative_count_decimal(
        "blocked_hearing_count",
        report.blocked_hearing_count,
    )
    material_hearing_count = _payload_nonnegative_count_decimal(
        "material_hearing_count",
        report.material_hearing_count,
    )
    near_hearing_count = _payload_nonnegative_count_decimal(
        "near_hearing_count",
        report.near_hearing_count,
    )
    past_hearing_count = _payload_nonnegative_count_decimal(
        "past_hearing_count",
        report.past_hearing_count,
    )
    stale_schedule_count = _payload_nonnegative_count_decimal(
        "stale_schedule_count",
        report.stale_schedule_count,
    )
    thin_source_count = _payload_nonnegative_count_decimal(
        "thin_source_count",
        report.thin_source_count,
    )
    low_agreement_count = _payload_nonnegative_count_decimal(
        "low_agreement_count",
        report.low_agreement_count,
    )
    missing_confirmation_count = _payload_nonnegative_count_decimal(
        "missing_confirmation_count",
        report.missing_confirmation_count,
    )
    stale_confirmation_count = _payload_nonnegative_count_decimal(
        "stale_confirmation_count",
        report.stale_confirmation_count,
    )
    average_materiality_score = _payload_ratio_decimal(
        "average_materiality_score",
        report.average_materiality_score,
    )
    min_seconds_until_hearing = _payload_finite_decimal(
        "min_seconds_until_hearing",
        report.min_seconds_until_hearing,
    )
    average_public_source_count = _payload_nonnegative_decimal(
        "average_public_source_count",
        report.average_public_source_count,
    )
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(_payload_public_dataclass(row) for row in report.rows)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    reason_code_counts = tuple(
        _payload_public_dataclass(row) for row in report.reason_code_counts
    )
    reason_codes = _normalize_report_reason_codes(report.reason_codes)
    _validate_report(report)
    return {
        "generated_at": generated_at,
        "config_version": report.config_version,
        "digest_status": report.digest_status,
        "next_step": report.next_step,
        "hearing_count": hearing_count,
        "ready_hearing_count": ready_hearing_count,
        "watch_hearing_count": watch_hearing_count,
        "blocked_hearing_count": blocked_hearing_count,
        "material_hearing_count": material_hearing_count,
        "near_hearing_count": near_hearing_count,
        "past_hearing_count": past_hearing_count,
        "stale_schedule_count": stale_schedule_count,
        "thin_source_count": thin_source_count,
        "low_agreement_count": low_agreement_count,
        "missing_confirmation_count": missing_confirmation_count,
        "stale_confirmation_count": stale_confirmation_count,
        "average_materiality_score": average_materiality_score,
        "min_seconds_until_hearing": min_seconds_until_hearing,
        "average_public_source_count": average_public_source_count,
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: MarketResearchPolicyHearingScheduleDigestRow) -> dict[str, Any]:
    require_paper_only_flags("row", row)
    for field_name in ("research_key", "condition_id", "policy_area", "hearing_id"):
        _require_public_string(field_name, getattr(row, field_name))
    hearing_scheduled_at = _payload_utc_datetime(
        "hearing_scheduled_at",
        row.hearing_scheduled_at,
    )
    schedule_observed_at = _payload_utc_datetime(
        "schedule_observed_at",
        row.schedule_observed_at,
    )
    confirmed_at = _payload_optional_utc_datetime("confirmed_at", row.confirmed_at)
    schedule_age_seconds = _payload_nonnegative_decimal(
        "schedule_age_seconds",
        row.schedule_age_seconds,
    )
    seconds_until_hearing = _payload_finite_decimal(
        "seconds_until_hearing",
        row.seconds_until_hearing,
    )
    confirmation_lag_seconds = _payload_optional_nonnegative_decimal(
        "confirmation_lag_seconds",
        row.confirmation_lag_seconds,
    )
    public_source_count = _payload_nonnegative_count_decimal(
        "public_source_count",
        row.public_source_count,
    )
    cross_source_agreement = _payload_ratio_decimal(
        "cross_source_agreement",
        row.cross_source_agreement,
    )
    schedule_materiality_score = _payload_ratio_decimal(
        "schedule_materiality_score",
        row.schedule_materiality_score,
    )
    market_probability_before = _payload_ratio_decimal(
        "market_probability_before",
        row.market_probability_before,
    )
    market_probability_after = _payload_ratio_decimal(
        "market_probability_after",
        row.market_probability_after,
    )
    probability_change = _payload_probability_change_decimal(
        "probability_change",
        row.probability_change,
    )
    _require_status("hearing_status", row.hearing_status)
    redacted_schedule_reference = _require_redacted_reference(
        "redacted_schedule_reference",
        row.redacted_schedule_reference,
    )
    reason_codes = _normalize_row_reason_codes(row.reason_codes)
    _validate_row(row)
    return {
        "research_key": row.research_key,
        "condition_id": row.condition_id,
        "policy_area": row.policy_area,
        "hearing_id": row.hearing_id,
        "hearing_scheduled_at": hearing_scheduled_at,
        "schedule_observed_at": schedule_observed_at,
        "confirmed_at": confirmed_at,
        "schedule_age_seconds": schedule_age_seconds,
        "seconds_until_hearing": seconds_until_hearing,
        "confirmation_lag_seconds": confirmation_lag_seconds,
        "public_source_count": public_source_count,
        "cross_source_agreement": cross_source_agreement,
        "schedule_materiality_score": schedule_materiality_score,
        "market_probability_before": market_probability_before,
        "market_probability_after": market_probability_after,
        "probability_change": probability_change,
        "hearing_status": row.hearing_status,
        "redacted_schedule_reference": redacted_schedule_reference,
        "reason_codes": reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    reason_code_count: MarketResearchPolicyHearingScheduleDigestReasonCodeCount,
) -> dict[str, Any]:
    require_paper_only_flags("reason code count", reason_code_count)
    _require_reason_code(
        "reason_code",
        reason_code_count.reason_code,
        REASON_CODE_SEQUENCE,
    )
    count = _payload_positive_count_decimal("count", reason_code_count.count)
    hearing_ratio = _payload_ratio_decimal(
        "hearing_ratio",
        reason_code_count.hearing_ratio,
    )
    return {
        "reason_code": reason_code_count.reason_code,
        "count": count,
        "hearing_ratio": hearing_ratio,
        "paper_only": reason_code_count.paper_only,
        "report_only": reason_code_count.report_only,
        "readonly": reason_code_count.readonly,
    }


def _payload_utc_datetime(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be normalized to UTC")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value


def _payload_optional_utc_datetime(
    field_name: str,
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None
    return _payload_utc_datetime(field_name, value)


def _payload_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite six-decimal Decimal")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    return value


def _payload_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _payload_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _payload_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _payload_nonnegative_decimal(field_name, value)


def _payload_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _payload_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count Decimal")
    return normalized


def _payload_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _payload_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _payload_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _payload_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _payload_probability_change_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _payload_finite_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be in range -1 to 1")
    return normalized


def _build_row(
    row: MarketResearchPolicyHearingScheduleDigestInputRow,
    *,
    config: MarketResearchPolicyHearingScheduleDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyHearingScheduleDigestRow:
    schedule_age_seconds = _datetime_delta_seconds(generated_at, row.schedule_observed_at)
    seconds_until_hearing = _datetime_delta_seconds(row.hearing_scheduled_at, generated_at)
    confirmation_lag_seconds = (
        None
        if row.confirmed_at is None
        else _datetime_delta_seconds(row.confirmed_at, row.schedule_observed_at)
    )
    probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        schedule_age_seconds=schedule_age_seconds,
        seconds_until_hearing=seconds_until_hearing,
        confirmation_lag_seconds=confirmation_lag_seconds,
        probability_change=probability_change,
    )
    return MarketResearchPolicyHearingScheduleDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        policy_area=row.policy_area,
        hearing_id=row.hearing_id,
        hearing_scheduled_at=row.hearing_scheduled_at,
        schedule_observed_at=row.schedule_observed_at,
        confirmed_at=row.confirmed_at,
        schedule_age_seconds=schedule_age_seconds,
        seconds_until_hearing=seconds_until_hearing,
        confirmation_lag_seconds=confirmation_lag_seconds,
        public_source_count=row.public_source_count,
        cross_source_agreement=row.cross_source_agreement,
        schedule_materiality_score=row.schedule_materiality_score,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        hearing_status=_row_status(reason_codes),
        redacted_schedule_reference=_redact_reference(row.public_schedule_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchPolicyHearingScheduleDigestInputRow,
    *,
    config: MarketResearchPolicyHearingScheduleDigestConfig,
    schedule_age_seconds: Decimal,
    seconds_until_hearing: Decimal,
    confirmation_lag_seconds: Decimal | None,
    probability_change: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.cross_source_agreement < config.min_cross_source_agreement:
        reasons.append(LOW_AGREEMENT_REASON)
    if row.schedule_materiality_score >= config.materiality_block_threshold:
        reasons.append(MATERIAL_BLOCK_REASON)
    elif row.schedule_materiality_score >= config.materiality_watch_threshold:
        reasons.append(MATERIAL_WATCH_REASON)
    if row.confirmed_at is None:
        reasons.append(MISSING_CONFIRMATION_REASON)
    if ZERO <= seconds_until_hearing <= config.near_hearing_window_seconds:
        reasons.append(NEAR_HEARING_REASON)
    if seconds_until_hearing < ZERO:
        reasons.append(PAST_HEARING_REASON)
    if abs(probability_change) >= PROBABILITY_SHIFT_THRESHOLD:
        reasons.append(PROBABILITY_SHIFT_REASON)
    if (
        confirmation_lag_seconds is not None
        and confirmation_lag_seconds > config.stale_confirmation_after_seconds
    ):
        reasons.append(STALE_CONFIRMATION_REASON)
    if schedule_age_seconds > config.fresh_schedule_max_age_seconds:
        reasons.append(STALE_SCHEDULE_REASON)
    if row.public_source_count < config.min_public_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MATERIAL_BLOCK_REASON in reason_codes or MISSING_CONFIRMATION_REASON in reason_codes:
        return STATUS_BLOCKED
    if any(reason_code != READY_REASON for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchPolicyHearingScheduleDigestRow, ...],
) -> tuple[MarketResearchPolicyHearingScheduleDigestRow, ...]:
    status_rank = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_rank[row.hearing_status],
                -len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
                row.seconds_until_hearing,
                row.policy_area,
                row.hearing_id,
                row.research_key,
            ),
        ),
    )


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyHearingScheduleDigestRow, ...],
) -> tuple[MarketResearchPolicyHearingScheduleDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: list[MarketResearchPolicyHearingScheduleDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _count(sum(1 for row in rows if reason_code in row.reason_codes))
        if count > ZERO:
            counts.append(
                MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    hearing_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _report_status(
    *,
    has_inputs: bool,
    blocked_hearing_count: Decimal,
    watch_hearing_count: Decimal,
) -> str:
    if not has_inputs or blocked_hearing_count > ZERO:
        return STATUS_BLOCKED
    if watch_hearing_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _normalize_input_rows(
    input_rows: list[MarketResearchPolicyHearingScheduleDigestInputRow]
    | tuple[MarketResearchPolicyHearingScheduleDigestInputRow, ...],
    generated_at: datetime,
) -> tuple[MarketResearchPolicyHearingScheduleDigestInputRow, ...]:
    if type(input_rows) not in {list, tuple}:
        raise ValueError("input rows must be a list or tuple")
    normalized: list[MarketResearchPolicyHearingScheduleDigestInputRow] = []
    seen: set[tuple[str, str]] = set()
    for row in input_rows:
        if type(row) is not MarketResearchPolicyHearingScheduleDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchPolicyHearingScheduleDigestInputRow",
            )
        require_paper_only_flags("input row", row)
        if row.schedule_observed_at > generated_at:
            raise ValueError("schedule_observed_at must be on or before generated_at")
        key = (row.research_key, row.hearing_id)
        if key in seen:
            raise ValueError("input rows must be unique by research_key and hearing_id")
        seen.add(key)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.hearing_scheduled_at,
                row.policy_area,
                row.hearing_id,
                row.research_key,
            ),
        ),
    )


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if READY_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix ready with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _validate_row(row: MarketResearchPolicyHearingScheduleDigestRow) -> None:
    if row.confirmed_at is not None and row.confirmed_at < row.schedule_observed_at:
        raise ValueError("confirmed_at must be on or after schedule_observed_at")
    if row.confirmed_at is None:
        if row.confirmation_lag_seconds is not None:
            raise ValueError("confirmation_lag_seconds must be absent without confirmation")
    elif row.confirmation_lag_seconds != _datetime_delta_seconds(
        later=row.confirmed_at,
        datetime=row.schedule_observed_at,
    ):
        raise ValueError("confirmation_lag_seconds must match confirmation timing")
    expected_probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_change != expected_probability_change:
        raise ValueError("probability_change must match market probability delta")
    if row.hearing_status != _row_status(row.reason_codes):
        raise ValueError("hearing_status must match reason_codes")
    if "://" in row.redacted_schedule_reference or "token" in row.redacted_schedule_reference.lower():
        raise ValueError("redacted_schedule_reference must not expose unsafe references")


def _validate_report(report: MarketResearchPolicyHearingScheduleDigestReport) -> None:
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.hearing_count != _count(len(report.rows)):
        raise ValueError("hearing_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.hearing_status == STATUS_READY),
    )
    if report.ready_hearing_count != expected_ready:
        raise ValueError("ready_hearing_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.hearing_status == STATUS_WATCH),
    )
    if report.watch_hearing_count != expected_watch:
        raise ValueError("watch_hearing_count must match rows")
    expected_blocked = _count(
        sum(1 for row in report.rows if row.hearing_status == STATUS_BLOCKED),
    )
    if report.blocked_hearing_count != expected_blocked:
        raise ValueError("blocked_hearing_count must match rows")
    if tuple(report.rows) != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        if not (
            not report.rows
            and report.reason_code_counts
            == (
                MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
                    reason_code=NO_INPUTS_REASON,
                    count=ONE,
                    hearing_ratio=ZERO,
                ),
            )
        ):
            raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_hearing_count=report.blocked_hearing_count,
        watch_hearing_count=report.watch_hearing_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_text(field_name, value)


def _require_reference(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_redacted_reference(field_name: str, value: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    lowered = value.lower()
    if "://" in lowered or "token" in lowered or "credential" in lowered:
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_status(field_name: str, value: str) -> None:
    if value not in {STATUS_READY, STATUS_WATCH, STATUS_BLOCKED}:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(
    field_name: str,
    value: str,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} contains an unknown reason code")


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _require_probability_change(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be in range -1 to 1")
    return normalized


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _datetime_delta_seconds(later: datetime, datetime: datetime) -> Decimal:
    delta = later - datetime
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _redact_reference(reference: str) -> str:
    lowered = reference.lower()
    if any(fragment in lowered for fragment in _PUBLIC_REFERENCE_FRAGMENTS):
        return reference
    digest = sha256(reference.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "live" in lowered:
        raise ValueError(f"{field_name} contains unsafe surface text")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_HEARING_SCHEDULE_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyHearingScheduleDigestConfig",
    "MarketResearchPolicyHearingScheduleDigestInputRow",
    "MarketResearchPolicyHearingScheduleDigestReasonCodeCount",
    "MarketResearchPolicyHearingScheduleDigestReport",
    "MarketResearchPolicyHearingScheduleDigestRow",
    "build_market_research_policy_hearing_schedule_digest",
    "market_research_policy_hearing_schedule_digest_payload",
)
