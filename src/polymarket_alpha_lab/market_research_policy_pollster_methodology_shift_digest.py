"""Pure Phase 1 pollster methodology shift risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_POLLSTER_METHODOLOGY_SHIFT_DIGEST_CONFIG_VERSION",
    "PolicyPollsterMethodologyShiftDigestConfig",
    "PolicyPollsterMethodologyShiftObservation",
    "PolicyPollsterMethodologyShiftDigestRow",
    "PolicyPollsterMethodologyShiftReasonCodeCount",
    "PolicyPollsterMethodologyShiftDigestReport",
    "build_market_research_policy_pollster_methodology_shift_digest",
    "market_research_policy_pollster_methodology_shift_digest_payload",
)


DEFAULT_MARKET_RESEARCH_POLICY_POLLSTER_METHODOLOGY_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-policy-pollster-methodology-shift-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
SHIFT_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_pollster_methodology_shift_screening",
    WATCH_STATUS: "monitor_report_only_pollster_methodology_shift_screening",
    PASS_STATUS: "allow_report_only_pollster_methodology_shift_screening",
}

SAMPLE_MODE_SHIFT_RISK_WEIGHT = Decimal("0.450000")
WEIGHTING_CHANGE_RISK_WEIGHT = Decimal("0.200000")
LIKELY_VOTER_SCREEN_RISK_WEIGHT = Decimal("0.250000")
NEAR_EVENT_RISK_WEIGHT = Decimal("0.100000")

GENERATED_REASON_CODE_PREFIX = "pollster_methodology_shift_"
EMPTY_REASON_CODE = "pollster_methodology_shift_digest_empty"
BLOCKED_REASON_CODE = "pollster_methodology_shift_blocked"
WATCH_REASON_CODE = "pollster_methodology_shift_watch"
BELOW_THRESHOLD_REASON_CODE = "pollster_methodology_shift_below_threshold"
SOURCE_FRESH_REASON_CODE = "pollster_methodology_shift_source_fresh"
SOURCE_STALE_REASON_CODE = "pollster_methodology_shift_source_stale"
SAMPLE_MODE_MATERIAL_REASON_CODE = (
    "pollster_methodology_shift_sample_mode_material"
)
SAMPLE_MODE_HIGH_REASON_CODE = "pollster_methodology_shift_sample_mode_high"
WEIGHTING_CHANGED_REASON_CODE = "pollster_methodology_shift_weighting_changed"
MANY_WEIGHTING_CHANGES_REASON_CODE = (
    "pollster_methodology_shift_many_weighting_changes"
)
LIKELY_VOTER_SCREEN_CHANGED_REASON_CODE = (
    "pollster_methodology_shift_likely_voter_screen_changed"
)
NEAR_EVENT_REASON_CODE = "pollster_methodology_shift_near_event"


@dataclass(frozen=True)
class PolicyPollsterMethodologyShiftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_POLLSTER_METHODOLOGY_SHIFT_DIGEST_CONFIG_VERSION
    )
    watch_methodology_shift_risk_score: Decimal = Decimal("0.350000")
    blocked_methodology_shift_risk_score: Decimal = Decimal("0.700000")
    material_sample_mode_shift_share: Decimal = Decimal("0.200000")
    high_sample_mode_shift_share: Decimal = Decimal("0.500000")
    material_weighting_change_count: Decimal = Decimal("1.000000")
    high_weighting_change_count: Decimal = Decimal("2.000000")
    near_event_days: Decimal = Decimal("21.000000")
    max_source_age_seconds: Decimal = Decimal("172800.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    clear_confidence_cap: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollsterMethodologyShiftDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_POLLSTER_METHODOLOGY_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_methodology_shift_risk_score",
            "blocked_methodology_shift_risk_score",
            "material_sample_mode_shift_share",
            "stale_confidence_cap",
            "clear_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_sample_mode_shift_share",
            "material_weighting_change_count",
            "high_weighting_change_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "high_sample_mode_shift_share",
            _normalize_positive_probability(
                "high_sample_mode_shift_share",
                self.high_sample_mode_shift_share,
            ),
        )
        object.__setattr__(
            self,
            "near_event_days",
            _normalize_nonnegative_decimal("near_event_days", self.near_event_days),
        )
        if (
            self.watch_methodology_shift_risk_score
            > self.blocked_methodology_shift_risk_score
        ):
            raise ValueError(
                "watch_methodology_shift_risk_score must not exceed "
                "blocked_methodology_shift_risk_score",
            )
        if self.material_sample_mode_shift_share > self.high_sample_mode_shift_share:
            raise ValueError(
                "material_sample_mode_shift_share must not exceed "
                "high_sample_mode_shift_share",
            )
        if self.material_weighting_change_count > self.high_weighting_change_count:
            raise ValueError(
                "material_weighting_change_count must not exceed "
                "high_weighting_change_count",
            )
        _require_hard_flags(self, "config")


@dataclass(frozen=True)
class PolicyPollsterMethodologyShiftObservation:
    source_id: str
    market_slug: str
    pollster_id: str
    contest_key: str
    methodology_family: str
    sample_mode_shift_share: Decimal
    weighting_change_count: Decimal
    likely_voter_screen_change: bool
    days_until_event: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollsterMethodologyShiftObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "pollster_id",
            "contest_key",
            "methodology_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "sample_mode_shift_share",
            _normalize_probability(
                "sample_mode_shift_share",
                self.sample_mode_shift_share,
            ),
        )
        object.__setattr__(
            self,
            "weighting_change_count",
            _normalize_nonnegative_decimal(
                "weighting_change_count",
                self.weighting_change_count,
            ),
        )
        _require_bool(
            "likely_voter_screen_change",
            self.likely_voter_screen_change,
        )
        object.__setattr__(
            self,
            "days_until_event",
            _normalize_nonnegative_decimal("days_until_event", self.days_until_event),
        )
        object.__setattr__(
            self,
            "evidence_confidence",
            _normalize_probability("evidence_confidence", self.evidence_confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self, "observation")


@dataclass(frozen=True)
class PolicyPollsterMethodologyShiftDigestRow:
    source_id: str
    market_slug: str
    pollster_id: str
    contest_key: str
    methodology_family: str
    sample_mode_shift_share: Decimal
    weighting_change_count: Decimal
    likely_voter_screen_change: bool
    days_until_event: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    watch_methodology_shift_risk_score: Decimal
    blocked_methodology_shift_risk_score: Decimal
    material_sample_mode_shift_share: Decimal
    high_sample_mode_shift_share: Decimal
    material_weighting_change_count: Decimal
    high_weighting_change_count: Decimal
    near_event_days: Decimal
    max_source_age_seconds: Decimal
    stale_confidence_cap: Decimal
    clear_confidence_cap: Decimal
    methodology_shift_risk_score: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    shift_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollsterMethodologyShiftDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "pollster_id",
            "contest_key",
            "methodology_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "sample_mode_shift_share",
            _normalize_probability(
                "sample_mode_shift_share",
                self.sample_mode_shift_share,
            ),
        )
        for field_name in (
            "weighting_change_count",
            "days_until_event",
            "source_age_seconds",
            "near_event_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool(
            "likely_voter_screen_change",
            self.likely_voter_screen_change,
        )
        for field_name in (
            "evidence_confidence",
            "watch_methodology_shift_risk_score",
            "blocked_methodology_shift_risk_score",
            "material_sample_mode_shift_share",
            "high_sample_mode_shift_share",
            "stale_confidence_cap",
            "clear_confidence_cap",
            "methodology_shift_risk_score",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_weighting_change_count",
            "high_weighting_change_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("shift_status", self.shift_status, SHIFT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self, "row")


@dataclass(frozen=True)
class PolicyPollsterMethodologyShiftReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            PolicyPollsterMethodologyShiftReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self, "reason_code_count")


@dataclass(frozen=True)
class PolicyPollsterMethodologyShiftDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    sample_mode_shift_row_count: Decimal
    weighting_change_row_count: Decimal
    likely_voter_screen_change_count: Decimal
    near_event_count: Decimal
    max_methodology_shift_risk_score: Decimal
    average_methodology_shift_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[PolicyPollsterMethodologyShiftDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PolicyPollsterMethodologyShiftReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollsterMethodologyShiftDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_POLLSTER_METHODOLOGY_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "sample_mode_shift_row_count",
            "weighting_change_row_count",
            "likely_voter_screen_change_count",
            "near_event_count",
            "max_methodology_shift_risk_score",
            "average_methodology_shift_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, SHIFT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self, "report")


def build_market_research_policy_pollster_methodology_shift_digest(
    observations: Iterable[PolicyPollsterMethodologyShiftObservation],
    *,
    config: PolicyPollsterMethodologyShiftDigestConfig,
    generated_at: datetime,
) -> PolicyPollsterMethodologyShiftDigestReport:
    if type(config) is not PolicyPollsterMethodologyShiftDigestConfig:
        raise ValueError("config must be exactly PolicyPollsterMethodologyShiftDigestConfig")
    _require_hard_flags(config, "config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    return PolicyPollsterMethodologyShiftDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON_CODE),
        sample_mode_shift_row_count=_reason_count(rows, SAMPLE_MODE_MATERIAL_REASON_CODE),
        weighting_change_row_count=_reason_count(rows, WEIGHTING_CHANGED_REASON_CODE),
        likely_voter_screen_change_count=_reason_count(
            rows,
            LIKELY_VOTER_SCREEN_CHANGED_REASON_CODE,
        ),
        near_event_count=_reason_count(rows, NEAR_EVENT_REASON_CODE),
        max_methodology_shift_risk_score=_max_row_decimal(
            rows,
            "methodology_shift_risk_score",
        ),
        average_methodology_shift_risk_score=_ratio(
            _sum_decimal(row.methodology_shift_risk_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_policy_pollster_methodology_shift_digest_payload(
    report: PolicyPollsterMethodologyShiftDigestReport,
) -> dict[str, Any]:
    if type(report) is not PolicyPollsterMethodologyShiftDigestReport:
        raise ValueError(
            "report must be exactly PolicyPollsterMethodologyShiftDigestReport",
        )
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: PolicyPollsterMethodologyShiftObservation,
    *,
    config: PolicyPollsterMethodologyShiftDigestConfig,
    generated_at: datetime,
) -> PolicyPollsterMethodologyShiftDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    risk_score = _methodology_shift_risk_score(
        sample_mode_shift_share=value.sample_mode_shift_share,
        weighting_change_count=value.weighting_change_count,
        likely_voter_screen_change=value.likely_voter_screen_change,
        days_until_event=value.days_until_event,
        high_sample_mode_shift_share=config.high_sample_mode_shift_share,
        high_weighting_change_count=config.high_weighting_change_count,
        near_event_days=config.near_event_days,
    )
    shift_status = _shift_status(risk_score, config=config)
    confidence_cap = _confidence_cap(
        shift_status=shift_status,
        source_fresh=source_fresh,
        config=config,
    )
    return PolicyPollsterMethodologyShiftDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        pollster_id=value.pollster_id,
        contest_key=value.contest_key,
        methodology_family=value.methodology_family,
        sample_mode_shift_share=value.sample_mode_shift_share,
        weighting_change_count=value.weighting_change_count,
        likely_voter_screen_change=value.likely_voter_screen_change,
        days_until_event=value.days_until_event,
        evidence_confidence=value.evidence_confidence,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        watch_methodology_shift_risk_score=config.watch_methodology_shift_risk_score,
        blocked_methodology_shift_risk_score=config.blocked_methodology_shift_risk_score,
        material_sample_mode_shift_share=config.material_sample_mode_shift_share,
        high_sample_mode_shift_share=config.high_sample_mode_shift_share,
        material_weighting_change_count=config.material_weighting_change_count,
        high_weighting_change_count=config.high_weighting_change_count,
        near_event_days=config.near_event_days,
        max_source_age_seconds=config.max_source_age_seconds,
        stale_confidence_cap=config.stale_confidence_cap,
        clear_confidence_cap=config.clear_confidence_cap,
        methodology_shift_risk_score=risk_score,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.evidence_confidence, confidence_cap),
        shift_status=shift_status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            shift_status=shift_status,
            sample_mode_shift_share=value.sample_mode_shift_share,
            weighting_change_count=value.weighting_change_count,
            likely_voter_screen_change=value.likely_voter_screen_change,
            days_until_event=value.days_until_event,
            source_fresh=source_fresh,
            config=config,
        ),
    )


def _methodology_shift_risk_score(
    *,
    sample_mode_shift_share: Decimal,
    weighting_change_count: Decimal,
    likely_voter_screen_change: bool,
    days_until_event: Decimal,
    high_sample_mode_shift_share: Decimal,
    high_weighting_change_count: Decimal,
    near_event_days: Decimal,
) -> Decimal:
    sample_component = (
        min(ONE, _ratio(sample_mode_shift_share, high_sample_mode_shift_share))
        * SAMPLE_MODE_SHIFT_RISK_WEIGHT
    )
    weighting_component = (
        min(ONE, _ratio(weighting_change_count, high_weighting_change_count))
        * WEIGHTING_CHANGE_RISK_WEIGHT
    )
    likely_voter_component = (
        LIKELY_VOTER_SCREEN_RISK_WEIGHT if likely_voter_screen_change else ZERO
    )
    near_event_component = (
        NEAR_EVENT_RISK_WEIGHT if days_until_event <= near_event_days else ZERO
    )
    return _quantize_decimal(
        min(
            ONE,
            sample_component
            + weighting_component
            + likely_voter_component
            + near_event_component,
        ),
    )


def _shift_status(
    risk_score: Decimal,
    *,
    config: PolicyPollsterMethodologyShiftDigestConfig,
) -> str:
    if risk_score >= config.blocked_methodology_shift_risk_score:
        return BLOCKED_STATUS
    if risk_score >= config.watch_methodology_shift_risk_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    shift_status: str,
    source_fresh: bool,
    config: PolicyPollsterMethodologyShiftDigestConfig,
) -> Decimal:
    caps = [ONE]
    if shift_status == PASS_STATUS:
        caps.append(config.clear_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    shift_status: str,
    sample_mode_shift_share: Decimal,
    weighting_change_count: Decimal,
    likely_voter_screen_change: bool,
    days_until_event: Decimal,
    source_fresh: bool,
    config: PolicyPollsterMethodologyShiftDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.extend(
        _generated_row_reason_codes(
            shift_status=shift_status,
            sample_mode_shift_share=sample_mode_shift_share,
            weighting_change_count=weighting_change_count,
            likely_voter_screen_change=likely_voter_screen_change,
            days_until_event=days_until_event,
            source_fresh=source_fresh,
            material_sample_mode_shift_share=config.material_sample_mode_shift_share,
            high_sample_mode_shift_share=config.high_sample_mode_shift_share,
            material_weighting_change_count=config.material_weighting_change_count,
            high_weighting_change_count=config.high_weighting_change_count,
            near_event_days=config.near_event_days,
        ),
    )
    return _normalize_reason_codes(tuple(reason_codes))


def _generated_row_reason_codes(
    *,
    shift_status: str,
    sample_mode_shift_share: Decimal,
    weighting_change_count: Decimal,
    likely_voter_screen_change: bool,
    days_until_event: Decimal,
    source_fresh: bool,
    material_sample_mode_shift_share: Decimal,
    high_sample_mode_shift_share: Decimal,
    material_weighting_change_count: Decimal,
    high_weighting_change_count: Decimal,
    near_event_days: Decimal,
) -> tuple[str, ...]:
    if shift_status == BLOCKED_STATUS:
        reason_codes = [BLOCKED_REASON_CODE]
    elif shift_status == WATCH_STATUS:
        reason_codes = [WATCH_REASON_CODE]
    else:
        reason_codes = [BELOW_THRESHOLD_REASON_CODE]
    reason_codes.append(SOURCE_FRESH_REASON_CODE if source_fresh else SOURCE_STALE_REASON_CODE)
    if sample_mode_shift_share >= material_sample_mode_shift_share:
        reason_codes.append(SAMPLE_MODE_MATERIAL_REASON_CODE)
    if sample_mode_shift_share >= high_sample_mode_shift_share:
        reason_codes.append(SAMPLE_MODE_HIGH_REASON_CODE)
    if weighting_change_count >= material_weighting_change_count:
        reason_codes.append(WEIGHTING_CHANGED_REASON_CODE)
    if weighting_change_count >= high_weighting_change_count:
        reason_codes.append(MANY_WEIGHTING_CHANGES_REASON_CODE)
    if likely_voter_screen_change:
        reason_codes.append(LIKELY_VOTER_SCREEN_CHANGED_REASON_CODE)
    if days_until_event <= near_event_days:
        reason_codes.append(NEAR_EVENT_REASON_CODE)
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[PolicyPollsterMethodologyShiftDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[PolicyPollsterMethodologyShiftDigestRow, ...],
) -> tuple[PolicyPollsterMethodologyShiftReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REASON_CODE,):
        return (
            PolicyPollsterMethodologyShiftReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        PolicyPollsterMethodologyShiftReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[PolicyPollsterMethodologyShiftObservation],
) -> tuple[PolicyPollsterMethodologyShiftObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain PolicyPollsterMethodologyShiftObservation")
    normalized = tuple(observations)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not PolicyPollsterMethodologyShiftObservation:
            raise ValueError(
                "observations must contain PolicyPollsterMethodologyShiftObservation",
            )
        _require_hard_flags(value, "observation")
        if value.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id values")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[PolicyPollsterMethodologyShiftDigestRow],
) -> tuple[PolicyPollsterMethodologyShiftDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain PolicyPollsterMethodologyShiftDigestRow")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not PolicyPollsterMethodologyShiftDigestRow:
            raise ValueError("rows must contain PolicyPollsterMethodologyShiftDigestRow")
        _require_hard_flags(row, "row")
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id values")
        seen.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[PolicyPollsterMethodologyShiftReasonCodeCount],
) -> tuple[PolicyPollsterMethodologyShiftReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not PolicyPollsterMethodologyShiftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PolicyPollsterMethodologyShiftReasonCodeCount",
            )
        _require_hard_flags(value, "reason_code_count")
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: PolicyPollsterMethodologyShiftDigestRow) -> None:
    _validate_row_config_thresholds(row)
    expected_risk_score = _methodology_shift_risk_score(
        sample_mode_shift_share=row.sample_mode_shift_share,
        weighting_change_count=row.weighting_change_count,
        likely_voter_screen_change=row.likely_voter_screen_change,
        days_until_event=row.days_until_event,
        high_sample_mode_shift_share=row.high_sample_mode_shift_share,
        high_weighting_change_count=row.high_weighting_change_count,
        near_event_days=row.near_event_days,
    )
    if row.methodology_shift_risk_score != expected_risk_score:
        raise ValueError("methodology_shift_risk_score must match row factors")
    expected_status = _row_shift_status(
        row.methodology_shift_risk_score,
        watch_methodology_shift_risk_score=row.watch_methodology_shift_risk_score,
        blocked_methodology_shift_risk_score=row.blocked_methodology_shift_risk_score,
    )
    if row.shift_status != expected_status:
        raise ValueError("shift_status must match methodology_shift_risk_score")
    expected_confidence_cap = _row_confidence_cap(
        shift_status=row.shift_status,
        source_fresh=row.source_age_seconds <= row.max_source_age_seconds,
        stale_confidence_cap=row.stale_confidence_cap,
        clear_confidence_cap=row.clear_confidence_cap,
    )
    if row.confidence_cap != expected_confidence_cap:
        raise ValueError("confidence_cap must match row factors")
    if row.capped_confidence != min(row.evidence_confidence, row.confidence_cap):
        raise ValueError("capped_confidence must match evidence_confidence")
    expected_generated_reason_codes = _generated_row_reason_codes(
        shift_status=row.shift_status,
        sample_mode_shift_share=row.sample_mode_shift_share,
        weighting_change_count=row.weighting_change_count,
        likely_voter_screen_change=row.likely_voter_screen_change,
        days_until_event=row.days_until_event,
        source_fresh=row.source_age_seconds <= row.max_source_age_seconds,
        material_sample_mode_shift_share=row.material_sample_mode_shift_share,
        high_sample_mode_shift_share=row.high_sample_mode_shift_share,
        material_weighting_change_count=row.material_weighting_change_count,
        high_weighting_change_count=row.high_weighting_change_count,
        near_event_days=row.near_event_days,
    )
    actual_generated_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code.startswith(GENERATED_REASON_CODE_PREFIX)
    )
    if actual_generated_reason_codes != expected_generated_reason_codes:
        raise ValueError("reason_codes must match row factors")


def _validate_row_config_thresholds(row: PolicyPollsterMethodologyShiftDigestRow) -> None:
    if (
        row.watch_methodology_shift_risk_score
        > row.blocked_methodology_shift_risk_score
    ):
        raise ValueError(
            "watch_methodology_shift_risk_score must not exceed "
            "blocked_methodology_shift_risk_score",
        )
    if row.material_sample_mode_shift_share > row.high_sample_mode_shift_share:
        raise ValueError(
            "material_sample_mode_shift_share must not exceed "
            "high_sample_mode_shift_share",
        )
    if row.material_weighting_change_count > row.high_weighting_change_count:
        raise ValueError(
            "material_weighting_change_count must not exceed high_weighting_change_count",
        )


def _validate_report(report: PolicyPollsterMethodologyShiftDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, SOURCE_STALE_REASON_CODE):
        raise ValueError("stale_source_count must match rows")
    if report.sample_mode_shift_row_count != _reason_count(
        report.rows,
        SAMPLE_MODE_MATERIAL_REASON_CODE,
    ):
        raise ValueError("sample_mode_shift_row_count must match rows")
    if report.weighting_change_row_count != _reason_count(
        report.rows,
        WEIGHTING_CHANGED_REASON_CODE,
    ):
        raise ValueError("weighting_change_row_count must match rows")
    if report.likely_voter_screen_change_count != _reason_count(
        report.rows,
        LIKELY_VOTER_SCREEN_CHANGED_REASON_CODE,
    ):
        raise ValueError("likely_voter_screen_change_count must match rows")
    if report.near_event_count != _reason_count(report.rows, NEAR_EVENT_REASON_CODE):
        raise ValueError("near_event_count must match rows")
    if report.max_methodology_shift_risk_score != _max_row_decimal(
        report.rows,
        "methodology_shift_risk_score",
    ):
        raise ValueError("max_methodology_shift_risk_score must match rows")
    if report.average_methodology_shift_risk_score != _ratio(
        _sum_decimal(row.methodology_shift_risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_methodology_shift_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _row_shift_status(
    risk_score: Decimal,
    *,
    watch_methodology_shift_risk_score: Decimal,
    blocked_methodology_shift_risk_score: Decimal,
) -> str:
    if risk_score >= blocked_methodology_shift_risk_score:
        return BLOCKED_STATUS
    if risk_score >= watch_methodology_shift_risk_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_confidence_cap(
    *,
    shift_status: str,
    source_fresh: bool,
    stale_confidence_cap: Decimal,
    clear_confidence_cap: Decimal,
) -> Decimal:
    caps = [ONE]
    if shift_status == PASS_STATUS:
        caps.append(clear_confidence_cap)
    if not source_fresh:
        caps.append(stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _digest_status(rows: tuple[PolicyPollsterMethodologyShiftDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.shift_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.shift_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[PolicyPollsterMethodologyShiftDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.shift_status == status))


def _reason_count(
    rows: tuple[PolicyPollsterMethodologyShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[PolicyPollsterMethodologyShiftDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object, label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: PolicyPollsterMethodologyShiftDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.shift_status],
        -row.methodology_shift_risk_score,
        row.market_slug,
        row.source_id,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
