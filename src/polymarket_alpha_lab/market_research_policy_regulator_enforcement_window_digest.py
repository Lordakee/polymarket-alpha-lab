"""Pure Phase 1 policy regulator enforcement window digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_REGULATOR_ENFORCEMENT_WINDOW_DIGEST_CONFIG_VERSION = (
    "market-research-policy-regulator-enforcement-window-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"

WINDOW_STATE_UPCOMING = "upcoming"
WINDOW_STATE_ACTIVE = "active"
WINDOW_STATE_CLOSED = "closed"

REASON_PREFIX = "market_research_policy_regulator_enforcement_window_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
CLOSED_WINDOW_REASON = f"{REASON_PREFIX}closed_window"
ACTIVE_WINDOW_REASON = f"{REASON_PREFIX}active_window"
NEAR_WINDOW_REASON = f"{REASON_PREFIX}near_window"
MATERIAL_BLOCK_REASON = f"{REASON_PREFIX}material_block"
MATERIAL_WATCH_REASON = f"{REASON_PREFIX}material_watch"
PROBABILITY_SHIFT_REASON = f"{REASON_PREFIX}probability_shift"
LOW_AGREEMENT_REASON = f"{REASON_PREFIX}low_agreement"
STALE_EVIDENCE_REASON = f"{REASON_PREFIX}stale_evidence"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
THIN_SOURCE_FAMILIES_REASON = f"{REASON_PREFIX}thin_source_families"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    CLOSED_WINDOW_REASON,
    ACTIVE_WINDOW_REASON,
    NEAR_WINDOW_REASON,
    MATERIAL_BLOCK_REASON,
    MATERIAL_WATCH_REASON,
    PROBABILITY_SHIFT_REASON,
    LOW_AGREEMENT_REASON,
    STALE_EVIDENCE_REASON,
    THIN_SOURCES_REASON,
    THIN_SOURCE_FAMILIES_REASON,
    READY_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    CLOSED_WINDOW_REASON,
    ACTIVE_WINDOW_REASON,
    NEAR_WINDOW_REASON,
    MATERIAL_BLOCK_REASON,
    MATERIAL_WATCH_REASON,
    PROBABILITY_SHIFT_REASON,
    LOW_AGREEMENT_REASON,
    STALE_EVIDENCE_REASON,
    THIN_SOURCES_REASON,
    THIN_SOURCE_FAMILIES_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_policy_regulator_enforcement_window_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_policy_regulator_enforcement_window_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_policy_regulator_enforcement_window_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_SHIFT_THRESHOLD = Decimal("0.100000")

SENSITIVE_TEXT_FRAGMENTS = (
    "credential",
    "hidden",
    "access=",
    "https://",
    "http://",
    "vendor.",
    "live",
)
PUBLIC_REFERENCE_FRAGMENTS = ("public", "regulator", "notice", "docket", "memo")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_REGULATOR_ENFORCEMENT_WINDOW_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyRegulatorEnforcementWindowDigestConfig",
    "MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow",
    "MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount",
    "MarketResearchPolicyRegulatorEnforcementWindowDigestReport",
    "MarketResearchPolicyRegulatorEnforcementWindowDigestRow",
    "build_market_research_policy_regulator_enforcement_window_digest",
    "market_research_policy_regulator_enforcement_window_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyRegulatorEnforcementWindowDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_REGULATOR_ENFORCEMENT_WINDOW_DIGEST_CONFIG_VERSION
    )
    near_window_seconds: Decimal = Decimal("604800.000000")
    stale_evidence_after_seconds: Decimal = Decimal("21600.000000")
    min_public_source_count: Decimal = Decimal("2.000000")
    min_independent_source_family_count: Decimal = Decimal("2.000000")
    min_cross_source_agreement: Decimal = Decimal("0.650000")
    materiality_watch_threshold: Decimal = Decimal("0.150000")
    materiality_block_threshold: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRegulatorEnforcementWindowDigestConfig:
            raise TypeError(
                "MarketResearchPolicyRegulatorEnforcementWindowDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRegulatorEnforcementWindowDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in ("near_window_seconds", "stale_evidence_after_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_public_source_count",
            "min_independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
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
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow:
    research_key: str
    condition_id: str
    policy_area: str
    regulator_name: str
    public_notice_reference: str
    enforcement_window_starts_at: datetime
    enforcement_window_ends_at: datetime
    observed_at: datetime
    public_source_count: Decimal
    independent_source_family_count: Decimal
    cross_source_agreement: Decimal
    enforcement_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "policy_area",
            "regulator_name",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_notice_reference", self.public_notice_reference)
        object.__setattr__(
            self,
            "enforcement_window_starts_at",
            _as_utc(
                "enforcement_window_starts_at",
                self.enforcement_window_starts_at,
            ),
        )
        object.__setattr__(
            self,
            "enforcement_window_ends_at",
            _as_utc("enforcement_window_ends_at", self.enforcement_window_ends_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.enforcement_window_ends_at < self.enforcement_window_starts_at:
            raise ValueError(
                "enforcement_window_ends_at must be on or after "
                "enforcement_window_starts_at",
            )
        for field_name in (
            "public_source_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cross_source_agreement",
            "enforcement_materiality_score",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyRegulatorEnforcementWindowDigestRow:
    research_key: str
    condition_id: str
    policy_area: str
    regulator_name: str
    enforcement_window_starts_at: datetime
    enforcement_window_ends_at: datetime
    observed_at: datetime
    window_state: str
    seconds_until_window_start: Decimal
    seconds_until_window_end: Decimal
    observation_age_seconds: Decimal
    public_source_count: Decimal
    independent_source_family_count: Decimal
    cross_source_agreement: Decimal
    enforcement_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    window_status: str
    redacted_notice_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRegulatorEnforcementWindowDigestRow:
            raise TypeError(
                "MarketResearchPolicyRegulatorEnforcementWindowDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRegulatorEnforcementWindowDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "policy_area",
            "regulator_name",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "enforcement_window_starts_at",
            _as_utc(
                "enforcement_window_starts_at",
                self.enforcement_window_starts_at,
            ),
        )
        object.__setattr__(
            self,
            "enforcement_window_ends_at",
            _as_utc("enforcement_window_ends_at", self.enforcement_window_ends_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_window_state("window_state", self.window_state)
        for field_name in ("seconds_until_window_start", "seconds_until_window_end"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        for field_name in (
            "public_source_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cross_source_agreement",
            "enforcement_materiality_score",
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
        _require_status("window_status", self.window_status)
        object.__setattr__(
            self,
            "redacted_notice_reference",
            _require_redacted_reference(
                "redacted_notice_reference",
                self.redacted_notice_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    window_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "window_ratio",
            _require_ratio_decimal("window_ratio", self.window_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyRegulatorEnforcementWindowDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    window_count: Decimal
    ready_window_count: Decimal
    watch_window_count: Decimal
    blocked_window_count: Decimal
    active_window_count: Decimal
    upcoming_window_count: Decimal
    closed_window_count: Decimal
    near_window_count: Decimal
    material_window_count: Decimal
    stale_evidence_count: Decimal
    thin_source_count: Decimal
    thin_source_family_count: Decimal
    low_agreement_count: Decimal
    probability_shift_count: Decimal
    average_materiality_score: Decimal
    max_observation_age_seconds: Decimal
    min_seconds_until_window_start: Decimal | None
    rows: tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRegulatorEnforcementWindowDigestReport:
            raise TypeError(
                "MarketResearchPolicyRegulatorEnforcementWindowDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRegulatorEnforcementWindowDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "window_count",
            "ready_window_count",
            "watch_window_count",
            "blocked_window_count",
            "active_window_count",
            "upcoming_window_count",
            "closed_window_count",
            "near_window_count",
            "material_window_count",
            "stale_evidence_count",
            "thin_source_count",
            "thin_source_family_count",
            "low_agreement_count",
            "probability_shift_count",
            "average_materiality_score",
            "max_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_materiality_score > ONE:
            raise ValueError("average_materiality_score must be a ratio")
        if self.min_seconds_until_window_start is not None:
            object.__setattr__(
                self,
                "min_seconds_until_window_start",
                _require_decimal(
                    "min_seconds_until_window_start",
                    self.min_seconds_until_window_start,
                ),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_regulator_enforcement_window_digest(
    input_rows: list[MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow]
    | tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow, ...],
    *,
    config: MarketResearchPolicyRegulatorEnforcementWindowDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchPolicyRegulatorEnforcementWindowDigestReport:
    cfg = config or MarketResearchPolicyRegulatorEnforcementWindowDigestConfig()
    if type(cfg) is not MarketResearchPolicyRegulatorEnforcementWindowDigestConfig:
        raise ValueError(
            "config must be a "
            "MarketResearchPolicyRegulatorEnforcementWindowDigestConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(
        _build_row(row, config=cfg, generated_at=report_time)
        for row in normalized_rows
    )
    ranked_rows = _ranked_rows(built_rows)
    window_count = _count(len(ranked_rows))
    ready_window_count = _count(
        sum(1 for row in ranked_rows if row.window_status == STATUS_READY),
    )
    watch_window_count = _count(
        sum(1 for row in ranked_rows if row.window_status == STATUS_WATCH),
    )
    blocked_window_count = _count(
        sum(1 for row in ranked_rows if row.window_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                window_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_window_count=blocked_window_count,
        watch_window_count=watch_window_count,
    )
    return MarketResearchPolicyRegulatorEnforcementWindowDigestReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        window_count=window_count,
        ready_window_count=ready_window_count,
        watch_window_count=watch_window_count,
        blocked_window_count=blocked_window_count,
        active_window_count=_count(
            sum(1 for row in ranked_rows if row.window_state == WINDOW_STATE_ACTIVE),
        ),
        upcoming_window_count=_count(
            sum(1 for row in ranked_rows if row.window_state == WINDOW_STATE_UPCOMING),
        ),
        closed_window_count=_count(
            sum(1 for row in ranked_rows if row.window_state == WINDOW_STATE_CLOSED),
        ),
        near_window_count=_count(
            sum(1 for row in ranked_rows if NEAR_WINDOW_REASON in row.reason_codes),
        ),
        material_window_count=_count(
            sum(
                1
                for row in ranked_rows
                if MATERIAL_BLOCK_REASON in row.reason_codes
                or MATERIAL_WATCH_REASON in row.reason_codes
            ),
        ),
        stale_evidence_count=_count(
            sum(1 for row in ranked_rows if STALE_EVIDENCE_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        thin_source_family_count=_count(
            sum(
                1
                for row in ranked_rows
                if THIN_SOURCE_FAMILIES_REASON in row.reason_codes
            ),
        ),
        low_agreement_count=_count(
            sum(1 for row in ranked_rows if LOW_AGREEMENT_REASON in row.reason_codes),
        ),
        probability_shift_count=_count(
            sum(1 for row in ranked_rows if PROBABILITY_SHIFT_REASON in row.reason_codes),
        ),
        average_materiality_score=_ratio(
            _sum_decimal(row.enforcement_materiality_score for row in ranked_rows),
            window_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        min_seconds_until_window_start=(
            min((row.seconds_until_window_start for row in ranked_rows), default=None)
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_regulator_enforcement_window_digest_payload(
    report: MarketResearchPolicyRegulatorEnforcementWindowDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyRegulatorEnforcementWindowDigestReport:
        raise ValueError(
            "report must be a "
            "MarketResearchPolicyRegulatorEnforcementWindowDigestReport",
        )
    _require_hard_flags("report", report)
    _reject_sensitive_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_sensitive_payload("payload", payload)
    return payload


def _build_row(
    row: MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow,
    *,
    config: MarketResearchPolicyRegulatorEnforcementWindowDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyRegulatorEnforcementWindowDigestRow:
    seconds_until_window_start = _datetime_delta_seconds(
        row.enforcement_window_starts_at,
        generated_at,
    )
    seconds_until_window_end = _datetime_delta_seconds(
        row.enforcement_window_ends_at,
        generated_at,
    )
    observation_age_seconds = _datetime_delta_seconds(generated_at, row.observed_at)
    probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    window_state = _window_state(
        starts_at=row.enforcement_window_starts_at,
        ends_at=row.enforcement_window_ends_at,
        generated_at=generated_at,
    )
    reason_codes = _row_reason_codes(
        window_state=window_state,
        seconds_until_window_start=seconds_until_window_start,
        observation_age_seconds=observation_age_seconds,
        public_source_count=row.public_source_count,
        independent_source_family_count=row.independent_source_family_count,
        cross_source_agreement=row.cross_source_agreement,
        enforcement_materiality_score=row.enforcement_materiality_score,
        probability_change=probability_change,
        config=config,
    )
    return MarketResearchPolicyRegulatorEnforcementWindowDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        policy_area=row.policy_area,
        regulator_name=row.regulator_name,
        enforcement_window_starts_at=row.enforcement_window_starts_at,
        enforcement_window_ends_at=row.enforcement_window_ends_at,
        observed_at=row.observed_at,
        window_state=window_state,
        seconds_until_window_start=seconds_until_window_start,
        seconds_until_window_end=seconds_until_window_end,
        observation_age_seconds=observation_age_seconds,
        public_source_count=row.public_source_count,
        independent_source_family_count=row.independent_source_family_count,
        cross_source_agreement=row.cross_source_agreement,
        enforcement_materiality_score=row.enforcement_materiality_score,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        window_status=_row_status(reason_codes),
        redacted_notice_reference=_redacted_reference(row.public_notice_reference),
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow",
            )
        _require_hard_flags("input row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        key = (row.research_key, row.condition_id)
        if key in seen_keys:
            raise ValueError("input rows must not contain duplicate research keys")
        seen_keys.add(key)
    return normalized


def _row_reason_codes(
    *,
    window_state: str,
    seconds_until_window_start: Decimal,
    observation_age_seconds: Decimal,
    public_source_count: Decimal,
    independent_source_family_count: Decimal,
    cross_source_agreement: Decimal,
    enforcement_materiality_score: Decimal,
    probability_change: Decimal,
    config: MarketResearchPolicyRegulatorEnforcementWindowDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if window_state == WINDOW_STATE_CLOSED:
        reason_codes.append(CLOSED_WINDOW_REASON)
    elif window_state == WINDOW_STATE_ACTIVE:
        reason_codes.append(ACTIVE_WINDOW_REASON)
    elif seconds_until_window_start <= config.near_window_seconds:
        reason_codes.append(NEAR_WINDOW_REASON)
    if enforcement_materiality_score >= config.materiality_block_threshold:
        reason_codes.append(MATERIAL_BLOCK_REASON)
    elif enforcement_materiality_score >= config.materiality_watch_threshold:
        reason_codes.append(MATERIAL_WATCH_REASON)
    if _abs_decimal(probability_change) >= PROBABILITY_SHIFT_THRESHOLD:
        reason_codes.append(PROBABILITY_SHIFT_REASON)
    if cross_source_agreement < config.min_cross_source_agreement:
        reason_codes.append(LOW_AGREEMENT_REASON)
    if observation_age_seconds > config.stale_evidence_after_seconds:
        reason_codes.append(STALE_EVIDENCE_REASON)
    if public_source_count < config.min_public_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if independent_source_family_count < config.min_independent_source_family_count:
        reason_codes.append(THIN_SOURCE_FAMILIES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _window_state(*, starts_at: datetime, ends_at: datetime, generated_at: datetime) -> str:
    if ends_at <= generated_at:
        return WINDOW_STATE_CLOSED
    if starts_at <= generated_at:
        return WINDOW_STATE_ACTIVE
    return WINDOW_STATE_UPCOMING


def _window_state_from_offsets(
    *,
    seconds_until_window_start: Decimal,
    seconds_until_window_end: Decimal,
) -> str:
    if seconds_until_window_end <= ZERO:
        return WINDOW_STATE_CLOSED
    if seconds_until_window_start <= ZERO:
        return WINDOW_STATE_ACTIVE
    return WINDOW_STATE_UPCOMING


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if CLOSED_WINDOW_REASON in reason_codes or MATERIAL_BLOCK_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_window_count: Decimal,
    watch_window_count: Decimal,
) -> str:
    if not has_inputs or blocked_window_count > ZERO:
        return STATUS_BLOCKED
    if watch_window_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestRow, ...],
) -> tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.window_status),
                -row.enforcement_materiality_score,
                row.seconds_until_window_start,
                row.policy_area,
                row.research_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[value]


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestRow, ...],
) -> tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            window_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPolicyRegulatorEnforcementWindowDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_index = -1
    for row in rows:
        if (
            type(row)
            is not MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        sequence_index = REASON_CODE_SEQUENCE.index(row.reason_code)
        if sequence_index <= previous_index:
            raise ValueError("reason_code_counts must be unique and sorted")
        previous_index = sequence_index
    return rows


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


def _validate_row(row: MarketResearchPolicyRegulatorEnforcementWindowDigestRow) -> None:
    if row.enforcement_window_ends_at < row.enforcement_window_starts_at:
        raise ValueError(
            "enforcement_window_ends_at must be on or after "
            "enforcement_window_starts_at",
        )
    expected_window_span = _datetime_delta_seconds(
        row.enforcement_window_ends_at,
        row.enforcement_window_starts_at,
    )
    reported_window_span = _quantize(
        row.seconds_until_window_end - row.seconds_until_window_start,
    )
    if reported_window_span != expected_window_span:
        raise ValueError(
            "seconds_until_window_start must align with seconds_until_window_end "
            "and window bounds",
        )
    expected_window_state = _window_state_from_offsets(
        seconds_until_window_start=row.seconds_until_window_start,
        seconds_until_window_end=row.seconds_until_window_end,
    )
    if row.window_state != expected_window_state:
        raise ValueError("window_state must match window offsets")
    expected_probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_change != expected_probability_change:
        raise ValueError("probability_change must match probability inputs")
    if row.window_status != _row_status(row.reason_codes):
        raise ValueError("window_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_notice_reference):
        raise ValueError("redacted_notice_reference must be redacted or public")


def _validate_report(
    report: MarketResearchPolicyRegulatorEnforcementWindowDigestReport,
) -> None:
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.window_count != _count(len(report.rows)):
        raise ValueError("window_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.window_status == STATUS_READY),
    )
    if report.ready_window_count != expected_ready:
        raise ValueError("ready_window_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.window_status == STATUS_WATCH),
    )
    if report.watch_window_count != expected_watch:
        raise ValueError("watch_window_count must match rows")
    expected_blocked = _count(
        sum(1 for row in report.rows if row.window_status == STATUS_BLOCKED),
    )
    if report.blocked_window_count != expected_blocked:
        raise ValueError("blocked_window_count must match rows")
    if report.active_window_count != _count(
        sum(1 for row in report.rows if row.window_state == WINDOW_STATE_ACTIVE),
    ):
        raise ValueError("active_window_count must match rows")
    if report.upcoming_window_count != _count(
        sum(1 for row in report.rows if row.window_state == WINDOW_STATE_UPCOMING),
    ):
        raise ValueError("upcoming_window_count must match rows")
    if report.closed_window_count != _count(
        sum(1 for row in report.rows if row.window_state == WINDOW_STATE_CLOSED),
    ):
        raise ValueError("closed_window_count must match rows")
    if report.near_window_count != _count(
        sum(1 for row in report.rows if NEAR_WINDOW_REASON in row.reason_codes),
    ):
        raise ValueError("near_window_count must match rows")
    if report.material_window_count != _count(
        sum(
            1
            for row in report.rows
            if MATERIAL_BLOCK_REASON in row.reason_codes
            or MATERIAL_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("material_window_count must match rows")
    if report.stale_evidence_count != _count(
        sum(1 for row in report.rows if STALE_EVIDENCE_REASON in row.reason_codes),
    ):
        raise ValueError("stale_evidence_count must match rows")
    if report.thin_source_count != _count(
        sum(1 for row in report.rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.thin_source_family_count != _count(
        sum(1 for row in report.rows if THIN_SOURCE_FAMILIES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_family_count must match rows")
    if report.low_agreement_count != _count(
        sum(1 for row in report.rows if LOW_AGREEMENT_REASON in row.reason_codes),
    ):
        raise ValueError("low_agreement_count must match rows")
    if report.probability_shift_count != _count(
        sum(1 for row in report.rows if PROBABILITY_SHIFT_REASON in row.reason_codes),
    ):
        raise ValueError("probability_shift_count must match rows")
    if report.average_materiality_score != _ratio(
        _sum_decimal(row.enforcement_materiality_score for row in report.rows),
        report.window_count,
    ):
        raise ValueError("average_materiality_score must match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds must match rows")
    expected_min_start = min(
        (row.seconds_until_window_start for row in report.rows),
        default=None,
    )
    if report.min_seconds_until_window_start != expected_min_start:
        raise ValueError("min_seconds_until_window_start must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                window_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_window_count=report.blocked_window_count,
        watch_window_count=report.watch_window_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED):
        raise ValueError(f"{field_name} must be a supported status")


def _require_window_state(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (
        WINDOW_STATE_UPCOMING,
        WINDOW_STATE_ACTIVE,
        WINDOW_STATE_CLOSED,
    ):
        raise ValueError(f"{field_name} must be a supported window state")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_sensitive_text(field_name, value)
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _reject_sensitive_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public report text")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized % ONE != ZERO:
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a ratio")
    return normalized


def _require_probability_change(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _redacted_reference(value: str) -> str:
    if _is_public_reference(value):
        return value
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not _is_redacted_reference(value):
        raise ValueError(f"{field_name} must be redacted or public")
    return value


def _is_redacted_reference(value: str) -> bool:
    if _is_public_reference(value):
        return True
    if not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 12 and all(character in "0123456789abcdef" for character in suffix)


def _is_public_reference(value: str) -> bool:
    if type(value) is not str or not value.strip() or value != value.strip():
        return False
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_TEXT_FRAGMENTS):
        return False
    return any(fragment in lowered for fragment in PUBLIC_REFERENCE_FRAGMENTS)


def _reject_sensitive_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_sensitive_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_sensitive_payload(label, key)
            _reject_sensitive_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_sensitive_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in SENSITIVE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains non-public text")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {_json_ready(key): _json_ready(item) for key, item in value.items()}
    return value


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(whole_seconds + microseconds)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT) as context:
        return _quantize(context.divide(numerator, denominator))


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    return _require_nonnegative_count_decimal("count", value)


def _abs_decimal(value: Decimal) -> Decimal:
    return value.copy_abs()


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT) as context:
        return value.quantize(QUANT, context=context)
