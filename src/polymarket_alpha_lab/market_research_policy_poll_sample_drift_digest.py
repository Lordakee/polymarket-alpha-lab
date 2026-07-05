"""Pure Phase 1 policy poll sample-composition drift digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_POLL_SAMPLE_DRIFT_DIGEST_CONFIG_VERSION",
    "PolicyPollSampleDriftDigestConfig",
    "PolicyPollSampleDriftObservation",
    "PolicyPollSampleDriftDigestRow",
    "PolicyPollSampleDriftReasonCodeCount",
    "PolicyPollSampleDriftDigestReport",
    "build_market_research_policy_poll_sample_drift_digest",
    "market_research_policy_poll_sample_drift_digest_payload",
)


DEFAULT_MARKET_RESEARCH_POLICY_POLL_SAMPLE_DRIFT_DIGEST_CONFIG_VERSION = (
    "market-research-policy-poll-sample-drift-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
DRIFT_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_poll_sample_drift_screening",
    WATCH_STATUS: "monitor_report_only_poll_sample_drift_screening",
    PASS_STATUS: "allow_report_only_poll_sample_drift_screening",
}

PARTY_MIX_RISK_WEIGHT = Decimal("0.350000")
DEMOGRAPHIC_MIX_RISK_WEIGHT = Decimal("0.300000")
SAMPLE_SIZE_DROP_RISK_WEIGHT = Decimal("0.250000")
NEAR_EVENT_RISK_WEIGHT = Decimal("0.100000")

GENERATED_REASON_CODE_PREFIX = "poll_sample_drift_"
EMPTY_REASON_CODE = "poll_sample_drift_digest_empty"
BLOCKED_REASON_CODE = "poll_sample_drift_blocked"
WATCH_REASON_CODE = "poll_sample_drift_watch"
BELOW_THRESHOLD_REASON_CODE = "poll_sample_drift_below_threshold"
SOURCE_FRESH_REASON_CODE = "poll_sample_drift_source_fresh"
SOURCE_STALE_REASON_CODE = "poll_sample_drift_source_stale"
PARTY_MIX_MATERIAL_REASON_CODE = "poll_sample_drift_party_mix_material"
PARTY_MIX_HIGH_REASON_CODE = "poll_sample_drift_party_mix_high"
DEMOGRAPHIC_MIX_MATERIAL_REASON_CODE = (
    "poll_sample_drift_demographic_mix_material"
)
DEMOGRAPHIC_MIX_HIGH_REASON_CODE = "poll_sample_drift_demographic_mix_high"
SAMPLE_SIZE_DROP_MATERIAL_REASON_CODE = (
    "poll_sample_drift_sample_size_drop_material"
)
SAMPLE_SIZE_DROP_HIGH_REASON_CODE = "poll_sample_drift_sample_size_drop_high"
NEAR_EVENT_REASON_CODE = "poll_sample_drift_near_event"


@dataclass(frozen=True)
class PolicyPollSampleDriftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_POLL_SAMPLE_DRIFT_DIGEST_CONFIG_VERSION
    )
    watch_sample_drift_risk_score: Decimal = Decimal("0.350000")
    blocked_sample_drift_risk_score: Decimal = Decimal("0.700000")
    material_party_drift_share: Decimal = Decimal("0.050000")
    high_party_drift_share: Decimal = Decimal("0.120000")
    material_demographic_drift_share: Decimal = Decimal("0.070000")
    high_demographic_drift_share: Decimal = Decimal("0.150000")
    material_sample_size_drop_share: Decimal = Decimal("0.200000")
    high_sample_size_drop_share: Decimal = Decimal("0.400000")
    near_event_days: Decimal = Decimal("21.000000")
    max_source_age_seconds: Decimal = Decimal("172800.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    clear_confidence_cap: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyPollSampleDriftDigestConfig:
            raise TypeError(
                "PolicyPollSampleDriftDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollSampleDriftDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_POLL_SAMPLE_DRIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_sample_drift_risk_score",
            "blocked_sample_drift_risk_score",
            "material_party_drift_share",
            "material_demographic_drift_share",
            "material_sample_size_drop_share",
            "stale_confidence_cap",
            "clear_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_party_drift_share",
            "high_demographic_drift_share",
            "high_sample_size_drop_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "near_event_days",
            _normalize_nonnegative_decimal("near_event_days", self.near_event_days),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        _validate_config_thresholds(
            watch_sample_drift_risk_score=self.watch_sample_drift_risk_score,
            blocked_sample_drift_risk_score=self.blocked_sample_drift_risk_score,
            material_party_drift_share=self.material_party_drift_share,
            high_party_drift_share=self.high_party_drift_share,
            material_demographic_drift_share=self.material_demographic_drift_share,
            high_demographic_drift_share=self.high_demographic_drift_share,
            material_sample_size_drop_share=self.material_sample_size_drop_share,
            high_sample_size_drop_share=self.high_sample_size_drop_share,
        )
        _require_hard_flags(self, "config")


@dataclass(frozen=True)
class PolicyPollSampleDriftObservation:
    source_id: str
    market_slug: str
    pollster_id: str
    contest_key: str
    sample_frame_key: str
    party_sample_drift_share: Decimal
    demographic_sample_drift_share: Decimal
    sample_size_drop_share: Decimal
    days_until_event: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyPollSampleDriftObservation:
            raise TypeError(
                "PolicyPollSampleDriftObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollSampleDriftObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "pollster_id",
            "contest_key",
            "sample_frame_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "party_sample_drift_share",
            "demographic_sample_drift_share",
            "sample_size_drop_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_reason_codes("upstream_reason_codes", self.upstream_reason_codes)
        _require_hard_flags(self, "observation")


@dataclass(frozen=True)
class PolicyPollSampleDriftDigestRow:
    source_id: str
    market_slug: str
    pollster_id: str
    contest_key: str
    sample_frame_key: str
    party_sample_drift_share: Decimal
    demographic_sample_drift_share: Decimal
    sample_size_drop_share: Decimal
    days_until_event: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    watch_sample_drift_risk_score: Decimal
    blocked_sample_drift_risk_score: Decimal
    material_party_drift_share: Decimal
    high_party_drift_share: Decimal
    material_demographic_drift_share: Decimal
    high_demographic_drift_share: Decimal
    material_sample_size_drop_share: Decimal
    high_sample_size_drop_share: Decimal
    near_event_days: Decimal
    max_source_age_seconds: Decimal
    stale_confidence_cap: Decimal
    clear_confidence_cap: Decimal
    sample_drift_risk_score: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    drift_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyPollSampleDriftDigestRow:
            raise TypeError(
                "PolicyPollSampleDriftDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollSampleDriftDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "pollster_id",
            "contest_key",
            "sample_frame_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "party_sample_drift_share",
            "demographic_sample_drift_share",
            "sample_size_drop_share",
            "evidence_confidence",
            "watch_sample_drift_risk_score",
            "blocked_sample_drift_risk_score",
            "material_party_drift_share",
            "material_demographic_drift_share",
            "material_sample_size_drop_share",
            "stale_confidence_cap",
            "clear_confidence_cap",
            "sample_drift_risk_score",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_party_drift_share",
            "high_demographic_drift_share",
            "high_sample_size_drop_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "days_until_event",
            "source_age_seconds",
            "near_event_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_member("drift_status", self.drift_status, DRIFT_STATUSES)
        _require_reason_codes("reason_codes", self.reason_codes)
        _validate_row(self)
        _require_hard_flags(self, "row")


@dataclass(frozen=True)
class PolicyPollSampleDriftReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyPollSampleDriftReasonCodeCount:
            raise TypeError(
                "PolicyPollSampleDriftReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            PolicyPollSampleDriftReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self, "reason_code_count")


@dataclass(frozen=True)
class PolicyPollSampleDriftDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    party_drift_row_count: Decimal
    demographic_drift_row_count: Decimal
    sample_size_drop_row_count: Decimal
    near_event_count: Decimal
    max_sample_drift_risk_score: Decimal
    average_sample_drift_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[PolicyPollSampleDriftDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PolicyPollSampleDriftReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyPollSampleDriftDigestReport:
            raise TypeError(
                "PolicyPollSampleDriftDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPollSampleDriftDigestReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_POLL_SAMPLE_DRIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "party_drift_row_count",
            "demographic_drift_row_count",
            "sample_size_drop_row_count",
            "near_event_count",
            "max_sample_drift_risk_score",
            "average_sample_drift_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DRIFT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_rows(self.rows)
        _require_reason_codes("reason_codes", self.reason_codes)
        _require_reason_code_counts(self.reason_code_counts)
        _validate_report(self)
        _require_hard_flags(self, "report")


def build_market_research_policy_poll_sample_drift_digest(
    observations: Iterable[PolicyPollSampleDriftObservation],
    *,
    config: PolicyPollSampleDriftDigestConfig,
    generated_at: datetime,
) -> PolicyPollSampleDriftDigestReport:
    if type(config) is not PolicyPollSampleDriftDigestConfig:
        raise ValueError("config must be exactly PolicyPollSampleDriftDigestConfig")
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
    return PolicyPollSampleDriftDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON_CODE),
        party_drift_row_count=_reason_count(rows, PARTY_MIX_MATERIAL_REASON_CODE),
        demographic_drift_row_count=_reason_count(
            rows,
            DEMOGRAPHIC_MIX_MATERIAL_REASON_CODE,
        ),
        sample_size_drop_row_count=_reason_count(
            rows,
            SAMPLE_SIZE_DROP_MATERIAL_REASON_CODE,
        ),
        near_event_count=_reason_count(rows, NEAR_EVENT_REASON_CODE),
        max_sample_drift_risk_score=_max_row_decimal(
            rows,
            "sample_drift_risk_score",
        ),
        average_sample_drift_risk_score=_ratio(
            _sum_decimal(row.sample_drift_risk_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_policy_poll_sample_drift_digest_payload(
    report: PolicyPollSampleDriftDigestReport,
) -> dict[str, Any]:
    if type(report) is not PolicyPollSampleDriftDigestReport:
        raise ValueError("report must be exactly PolicyPollSampleDriftDigestReport")
    _require_payload_public_dataclass(report)
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _require_payload_public_dataclass(value: object) -> None:
    label = _payload_public_dataclass_label(value)
    _require_hard_flags(value, label)
    for field in fields(value):
        _require_payload_public_field(field.name, getattr(value, field.name))
    if type(value) is PolicyPollSampleDriftDigestRow:
        _require_payload_row(value)
        return
    if type(value) is PolicyPollSampleDriftReasonCodeCount:
        _require_payload_reason_code_count(value)
        return
    if type(value) is PolicyPollSampleDriftDigestReport:
        _require_payload_report(value)
        return
    if type(value) is PolicyPollSampleDriftDigestConfig:
        _require_payload_config(value)
        return
    if type(value) is PolicyPollSampleDriftObservation:
        _require_payload_observation(value)


def _payload_public_dataclass_label(value: object) -> str:
    if type(value) is PolicyPollSampleDriftDigestConfig:
        return "config"
    if type(value) is PolicyPollSampleDriftObservation:
        return "observation"
    if type(value) is PolicyPollSampleDriftDigestRow:
        return "row"
    if type(value) is PolicyPollSampleDriftReasonCodeCount:
        return "reason_code_count"
    if type(value) is PolicyPollSampleDriftDigestReport:
        return "report"
    raise ValueError("payload dataclasses must be exact public digest records")


def _require_payload_public_field(field_name: str, value: object) -> None:
    if field_name in ("generated_at", "observed_at"):
        _require_payload_utc_datetime(field_name, value)
        return
    if type(value) is Decimal:
        _require_payload_six_decimal(field_name, value)
        return
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_public_dataclass(value)
        return
    if type(value) is tuple:
        for item in value:
            if field_name == "rows" and type(item) is not PolicyPollSampleDriftDigestRow:
                raise ValueError("rows must contain PolicyPollSampleDriftDigestRow")
            if (
                field_name == "reason_code_counts"
                and type(item) is not PolicyPollSampleDriftReasonCodeCount
            ):
                raise ValueError(
                    "reason_code_counts must contain PolicyPollSampleDriftReasonCodeCount",
                )
            _require_payload_public_field(field_name, item)
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _require_payload_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be normalized to UTC")


def _require_payload_six_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must have exactly six decimal places")


def _require_payload_config(value: PolicyPollSampleDriftDigestConfig) -> None:
    _require_canonical_string("config_version", value.config_version)
    if (
        value.config_version
        != DEFAULT_MARKET_RESEARCH_POLICY_POLL_SAMPLE_DRIFT_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _validate_config_thresholds(
        watch_sample_drift_risk_score=_normalize_probability(
            "watch_sample_drift_risk_score",
            value.watch_sample_drift_risk_score,
        ),
        blocked_sample_drift_risk_score=_normalize_probability(
            "blocked_sample_drift_risk_score",
            value.blocked_sample_drift_risk_score,
        ),
        material_party_drift_share=_normalize_probability(
            "material_party_drift_share",
            value.material_party_drift_share,
        ),
        high_party_drift_share=_normalize_positive_probability(
            "high_party_drift_share",
            value.high_party_drift_share,
        ),
        material_demographic_drift_share=_normalize_probability(
            "material_demographic_drift_share",
            value.material_demographic_drift_share,
        ),
        high_demographic_drift_share=_normalize_positive_probability(
            "high_demographic_drift_share",
            value.high_demographic_drift_share,
        ),
        material_sample_size_drop_share=_normalize_probability(
            "material_sample_size_drop_share",
            value.material_sample_size_drop_share,
        ),
        high_sample_size_drop_share=_normalize_positive_probability(
            "high_sample_size_drop_share",
            value.high_sample_size_drop_share,
        ),
    )
    _normalize_nonnegative_decimal("near_event_days", value.near_event_days)
    _normalize_positive_decimal(
        "max_source_age_seconds",
        value.max_source_age_seconds,
    )
    _normalize_probability("stale_confidence_cap", value.stale_confidence_cap)
    _normalize_probability("clear_confidence_cap", value.clear_confidence_cap)


def _require_payload_observation(value: PolicyPollSampleDriftObservation) -> None:
    for field_name in (
        "source_id",
        "market_slug",
        "pollster_id",
        "contest_key",
        "sample_frame_key",
    ):
        _require_canonical_string(field_name, getattr(value, field_name))
    for field_name in (
        "party_sample_drift_share",
        "demographic_sample_drift_share",
        "sample_size_drop_share",
    ):
        _normalize_probability(field_name, getattr(value, field_name))
    _normalize_nonnegative_decimal("days_until_event", value.days_until_event)
    _normalize_probability("evidence_confidence", value.evidence_confidence)
    _require_reason_codes("upstream_reason_codes", value.upstream_reason_codes)


def _require_payload_row(value: PolicyPollSampleDriftDigestRow) -> None:
    for field_name in (
        "source_id",
        "market_slug",
        "pollster_id",
        "contest_key",
        "sample_frame_key",
    ):
        _require_canonical_string(field_name, getattr(value, field_name))
    for field_name in (
        "party_sample_drift_share",
        "demographic_sample_drift_share",
        "sample_size_drop_share",
        "evidence_confidence",
        "watch_sample_drift_risk_score",
        "blocked_sample_drift_risk_score",
        "material_party_drift_share",
        "material_demographic_drift_share",
        "material_sample_size_drop_share",
        "stale_confidence_cap",
        "clear_confidence_cap",
        "sample_drift_risk_score",
        "confidence_cap",
        "capped_confidence",
    ):
        _normalize_probability(field_name, getattr(value, field_name))
    for field_name in (
        "high_party_drift_share",
        "high_demographic_drift_share",
        "high_sample_size_drop_share",
    ):
        _normalize_positive_probability(field_name, getattr(value, field_name))
    for field_name in (
        "days_until_event",
        "source_age_seconds",
        "near_event_days",
    ):
        _normalize_nonnegative_decimal(field_name, getattr(value, field_name))
    _normalize_positive_decimal("max_source_age_seconds", value.max_source_age_seconds)
    _require_member("drift_status", value.drift_status, DRIFT_STATUSES)
    _require_reason_codes("reason_codes", value.reason_codes)
    _validate_row(value)


def _require_payload_reason_code_count(
    value: PolicyPollSampleDriftReasonCodeCount,
) -> None:
    _require_canonical_string("reason_code", value.reason_code)
    _normalize_positive_decimal("count", value.count)
    _normalize_probability("row_ratio", value.row_ratio)


def _require_payload_report(value: PolicyPollSampleDriftDigestReport) -> None:
    _require_canonical_string("config_version", value.config_version)
    if (
        value.config_version
        != DEFAULT_MARKET_RESEARCH_POLICY_POLL_SAMPLE_DRIFT_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "input_count",
        "row_count",
        "blocked_count",
        "watch_count",
        "pass_count",
        "stale_source_count",
        "party_drift_row_count",
        "demographic_drift_row_count",
        "sample_size_drop_row_count",
        "near_event_count",
        "max_sample_drift_risk_score",
        "average_sample_drift_risk_score",
    ):
        _normalize_nonnegative_decimal(field_name, getattr(value, field_name))
    _require_member("digest_status", value.digest_status, DRIFT_STATUSES)
    _require_canonical_string("recommended_next_step", value.recommended_next_step)
    _require_rows(value.rows)
    _require_reason_codes("reason_codes", value.reason_codes)
    _require_reason_code_counts(value.reason_code_counts)
    _validate_report(value)


def _row_from_observation(
    value: PolicyPollSampleDriftObservation,
    *,
    config: PolicyPollSampleDriftDigestConfig,
    generated_at: datetime,
) -> PolicyPollSampleDriftDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    risk_score = _sample_drift_risk_score(
        party_sample_drift_share=value.party_sample_drift_share,
        demographic_sample_drift_share=value.demographic_sample_drift_share,
        sample_size_drop_share=value.sample_size_drop_share,
        days_until_event=value.days_until_event,
        high_party_drift_share=config.high_party_drift_share,
        high_demographic_drift_share=config.high_demographic_drift_share,
        high_sample_size_drop_share=config.high_sample_size_drop_share,
        near_event_days=config.near_event_days,
    )
    drift_status = _sample_drift_status(risk_score, config=config)
    confidence_cap = _confidence_cap(
        drift_status=drift_status,
        source_fresh=source_fresh,
        config=config,
    )
    return PolicyPollSampleDriftDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        pollster_id=value.pollster_id,
        contest_key=value.contest_key,
        sample_frame_key=value.sample_frame_key,
        party_sample_drift_share=value.party_sample_drift_share,
        demographic_sample_drift_share=value.demographic_sample_drift_share,
        sample_size_drop_share=value.sample_size_drop_share,
        days_until_event=value.days_until_event,
        evidence_confidence=value.evidence_confidence,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        watch_sample_drift_risk_score=config.watch_sample_drift_risk_score,
        blocked_sample_drift_risk_score=config.blocked_sample_drift_risk_score,
        material_party_drift_share=config.material_party_drift_share,
        high_party_drift_share=config.high_party_drift_share,
        material_demographic_drift_share=config.material_demographic_drift_share,
        high_demographic_drift_share=config.high_demographic_drift_share,
        material_sample_size_drop_share=config.material_sample_size_drop_share,
        high_sample_size_drop_share=config.high_sample_size_drop_share,
        near_event_days=config.near_event_days,
        max_source_age_seconds=config.max_source_age_seconds,
        stale_confidence_cap=config.stale_confidence_cap,
        clear_confidence_cap=config.clear_confidence_cap,
        sample_drift_risk_score=risk_score,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.evidence_confidence, confidence_cap),
        drift_status=drift_status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            drift_status=drift_status,
            party_sample_drift_share=value.party_sample_drift_share,
            demographic_sample_drift_share=value.demographic_sample_drift_share,
            sample_size_drop_share=value.sample_size_drop_share,
            days_until_event=value.days_until_event,
            source_fresh=source_fresh,
            config=config,
        ),
    )


def _sample_drift_risk_score(
    *,
    party_sample_drift_share: Decimal,
    demographic_sample_drift_share: Decimal,
    sample_size_drop_share: Decimal,
    days_until_event: Decimal,
    high_party_drift_share: Decimal,
    high_demographic_drift_share: Decimal,
    high_sample_size_drop_share: Decimal,
    near_event_days: Decimal,
) -> Decimal:
    party_component = (
        _risk_fraction(party_sample_drift_share, high_party_drift_share)
        * PARTY_MIX_RISK_WEIGHT
    )
    demographic_component = (
        _risk_fraction(
            demographic_sample_drift_share,
            high_demographic_drift_share,
        )
        * DEMOGRAPHIC_MIX_RISK_WEIGHT
    )
    sample_size_component = (
        _risk_fraction(sample_size_drop_share, high_sample_size_drop_share)
        * SAMPLE_SIZE_DROP_RISK_WEIGHT
    )
    near_event_component = (
        NEAR_EVENT_RISK_WEIGHT if days_until_event <= near_event_days else ZERO
    )
    return _quantize_decimal(
        min(
            ONE,
            party_component
            + demographic_component
            + sample_size_component
            + near_event_component,
        ),
    )


def _sample_drift_status(
    risk_score: Decimal,
    *,
    config: PolicyPollSampleDriftDigestConfig,
) -> str:
    if risk_score >= config.blocked_sample_drift_risk_score:
        return BLOCKED_STATUS
    if risk_score >= config.watch_sample_drift_risk_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    drift_status: str,
    source_fresh: bool,
    config: PolicyPollSampleDriftDigestConfig,
) -> Decimal:
    caps = [ONE]
    if drift_status == PASS_STATUS:
        caps.append(config.clear_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    drift_status: str,
    party_sample_drift_share: Decimal,
    demographic_sample_drift_share: Decimal,
    sample_size_drop_share: Decimal,
    days_until_event: Decimal,
    source_fresh: bool,
    config: PolicyPollSampleDriftDigestConfig,
) -> tuple[str, ...]:
    return _canonical_reason_codes(
        upstream_reason_codes
        + _generated_row_reason_codes(
            drift_status=drift_status,
            party_sample_drift_share=party_sample_drift_share,
            demographic_sample_drift_share=demographic_sample_drift_share,
            sample_size_drop_share=sample_size_drop_share,
            days_until_event=days_until_event,
            source_fresh=source_fresh,
            material_party_drift_share=config.material_party_drift_share,
            high_party_drift_share=config.high_party_drift_share,
            material_demographic_drift_share=config.material_demographic_drift_share,
            high_demographic_drift_share=config.high_demographic_drift_share,
            material_sample_size_drop_share=config.material_sample_size_drop_share,
            high_sample_size_drop_share=config.high_sample_size_drop_share,
            near_event_days=config.near_event_days,
        ),
    )


def _generated_row_reason_codes(
    *,
    drift_status: str,
    party_sample_drift_share: Decimal,
    demographic_sample_drift_share: Decimal,
    sample_size_drop_share: Decimal,
    days_until_event: Decimal,
    source_fresh: bool,
    material_party_drift_share: Decimal,
    high_party_drift_share: Decimal,
    material_demographic_drift_share: Decimal,
    high_demographic_drift_share: Decimal,
    material_sample_size_drop_share: Decimal,
    high_sample_size_drop_share: Decimal,
    near_event_days: Decimal,
) -> tuple[str, ...]:
    if drift_status == BLOCKED_STATUS:
        reason_codes = [BLOCKED_REASON_CODE]
    elif drift_status == WATCH_STATUS:
        reason_codes = [WATCH_REASON_CODE]
    else:
        reason_codes = [BELOW_THRESHOLD_REASON_CODE]
    reason_codes.append(SOURCE_FRESH_REASON_CODE if source_fresh else SOURCE_STALE_REASON_CODE)
    if party_sample_drift_share >= material_party_drift_share:
        reason_codes.append(PARTY_MIX_MATERIAL_REASON_CODE)
    if party_sample_drift_share >= high_party_drift_share:
        reason_codes.append(PARTY_MIX_HIGH_REASON_CODE)
    if demographic_sample_drift_share >= material_demographic_drift_share:
        reason_codes.append(DEMOGRAPHIC_MIX_MATERIAL_REASON_CODE)
    if demographic_sample_drift_share >= high_demographic_drift_share:
        reason_codes.append(DEMOGRAPHIC_MIX_HIGH_REASON_CODE)
    if sample_size_drop_share >= material_sample_size_drop_share:
        reason_codes.append(SAMPLE_SIZE_DROP_MATERIAL_REASON_CODE)
    if sample_size_drop_share >= high_sample_size_drop_share:
        reason_codes.append(SAMPLE_SIZE_DROP_HIGH_REASON_CODE)
    if days_until_event <= near_event_days:
        reason_codes.append(NEAR_EVENT_REASON_CODE)
    return _canonical_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[PolicyPollSampleDriftDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _canonical_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[PolicyPollSampleDriftDigestRow, ...],
) -> tuple[PolicyPollSampleDriftReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REASON_CODE,):
        return (
            PolicyPollSampleDriftReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        PolicyPollSampleDriftReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[PolicyPollSampleDriftObservation],
) -> tuple[PolicyPollSampleDriftObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain PolicyPollSampleDriftObservation")
    normalized = tuple(observations)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not PolicyPollSampleDriftObservation:
            raise ValueError(
                "observations must contain PolicyPollSampleDriftObservation",
            )
        _require_hard_flags(value, "observation")
        if value.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id values")
        seen.add(value.source_id)
    return normalized


def _validate_row(row: PolicyPollSampleDriftDigestRow) -> None:
    _validate_config_thresholds(
        watch_sample_drift_risk_score=row.watch_sample_drift_risk_score,
        blocked_sample_drift_risk_score=row.blocked_sample_drift_risk_score,
        material_party_drift_share=row.material_party_drift_share,
        high_party_drift_share=row.high_party_drift_share,
        material_demographic_drift_share=row.material_demographic_drift_share,
        high_demographic_drift_share=row.high_demographic_drift_share,
        material_sample_size_drop_share=row.material_sample_size_drop_share,
        high_sample_size_drop_share=row.high_sample_size_drop_share,
    )
    expected_risk_score = _sample_drift_risk_score(
        party_sample_drift_share=row.party_sample_drift_share,
        demographic_sample_drift_share=row.demographic_sample_drift_share,
        sample_size_drop_share=row.sample_size_drop_share,
        days_until_event=row.days_until_event,
        high_party_drift_share=row.high_party_drift_share,
        high_demographic_drift_share=row.high_demographic_drift_share,
        high_sample_size_drop_share=row.high_sample_size_drop_share,
        near_event_days=row.near_event_days,
    )
    if row.sample_drift_risk_score != expected_risk_score:
        raise ValueError("sample_drift_risk_score must match row factors")
    expected_status = _row_sample_drift_status(
        row.sample_drift_risk_score,
        watch_sample_drift_risk_score=row.watch_sample_drift_risk_score,
        blocked_sample_drift_risk_score=row.blocked_sample_drift_risk_score,
    )
    if row.drift_status != expected_status:
        raise ValueError("drift_status must match sample_drift_risk_score")
    expected_confidence_cap = _row_confidence_cap(
        drift_status=row.drift_status,
        source_fresh=row.source_age_seconds <= row.max_source_age_seconds,
        stale_confidence_cap=row.stale_confidence_cap,
        clear_confidence_cap=row.clear_confidence_cap,
    )
    if row.confidence_cap != expected_confidence_cap:
        raise ValueError("confidence_cap must match row factors")
    if row.capped_confidence != min(row.evidence_confidence, row.confidence_cap):
        raise ValueError("capped_confidence must match evidence_confidence")
    expected_generated_reason_codes = _generated_row_reason_codes(
        drift_status=row.drift_status,
        party_sample_drift_share=row.party_sample_drift_share,
        demographic_sample_drift_share=row.demographic_sample_drift_share,
        sample_size_drop_share=row.sample_size_drop_share,
        days_until_event=row.days_until_event,
        source_fresh=row.source_age_seconds <= row.max_source_age_seconds,
        material_party_drift_share=row.material_party_drift_share,
        high_party_drift_share=row.high_party_drift_share,
        material_demographic_drift_share=row.material_demographic_drift_share,
        high_demographic_drift_share=row.high_demographic_drift_share,
        material_sample_size_drop_share=row.material_sample_size_drop_share,
        high_sample_size_drop_share=row.high_sample_size_drop_share,
        near_event_days=row.near_event_days,
    )
    actual_generated_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code.startswith(GENERATED_REASON_CODE_PREFIX)
    )
    if actual_generated_reason_codes != expected_generated_reason_codes:
        raise ValueError("reason_codes must match row factors")


def _validate_config_thresholds(
    *,
    watch_sample_drift_risk_score: Decimal,
    blocked_sample_drift_risk_score: Decimal,
    material_party_drift_share: Decimal,
    high_party_drift_share: Decimal,
    material_demographic_drift_share: Decimal,
    high_demographic_drift_share: Decimal,
    material_sample_size_drop_share: Decimal,
    high_sample_size_drop_share: Decimal,
) -> None:
    if watch_sample_drift_risk_score > blocked_sample_drift_risk_score:
        raise ValueError(
            "watch_sample_drift_risk_score must not exceed "
            "blocked_sample_drift_risk_score",
        )
    if material_party_drift_share > high_party_drift_share:
        raise ValueError(
            "material_party_drift_share must not exceed high_party_drift_share",
        )
    if material_demographic_drift_share > high_demographic_drift_share:
        raise ValueError(
            "material_demographic_drift_share must not exceed "
            "high_demographic_drift_share",
        )
    if material_sample_size_drop_share > high_sample_size_drop_share:
        raise ValueError(
            "material_sample_size_drop_share must not exceed "
            "high_sample_size_drop_share",
        )


def _validate_report(report: PolicyPollSampleDriftDigestReport) -> None:
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
    if report.party_drift_row_count != _reason_count(
        report.rows,
        PARTY_MIX_MATERIAL_REASON_CODE,
    ):
        raise ValueError("party_drift_row_count must match rows")
    if report.demographic_drift_row_count != _reason_count(
        report.rows,
        DEMOGRAPHIC_MIX_MATERIAL_REASON_CODE,
    ):
        raise ValueError("demographic_drift_row_count must match rows")
    if report.sample_size_drop_row_count != _reason_count(
        report.rows,
        SAMPLE_SIZE_DROP_MATERIAL_REASON_CODE,
    ):
        raise ValueError("sample_size_drop_row_count must match rows")
    if report.near_event_count != _reason_count(report.rows, NEAR_EVENT_REASON_CODE):
        raise ValueError("near_event_count must match rows")
    if report.max_sample_drift_risk_score != _max_row_decimal(
        report.rows,
        "sample_drift_risk_score",
    ):
        raise ValueError("max_sample_drift_risk_score must match rows")
    if report.average_sample_drift_risk_score != _ratio(
        _sum_decimal(row.sample_drift_risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_sample_drift_risk_score must match rows")
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


def _row_sample_drift_status(
    risk_score: Decimal,
    *,
    watch_sample_drift_risk_score: Decimal,
    blocked_sample_drift_risk_score: Decimal,
) -> str:
    if risk_score >= blocked_sample_drift_risk_score:
        return BLOCKED_STATUS
    if risk_score >= watch_sample_drift_risk_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_confidence_cap(
    *,
    drift_status: str,
    source_fresh: bool,
    stale_confidence_cap: Decimal,
    clear_confidence_cap: Decimal,
) -> Decimal:
    caps = [ONE]
    if drift_status == PASS_STATUS:
        caps.append(clear_confidence_cap)
    if not source_fresh:
        caps.append(stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _digest_status(rows: tuple[PolicyPollSampleDriftDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.drift_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.drift_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[PolicyPollSampleDriftDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.drift_status == status))


def _reason_count(
    rows: tuple[PolicyPollSampleDriftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[PolicyPollSampleDriftDigestRow, ...],
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


def _risk_fraction(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, numerator / denominator)


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
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _canonical_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_reason_codes(field_name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must contain unique reason codes")
    if value != tuple(sorted(value)):
        raise ValueError(f"{field_name} must be sorted")


def _require_rows(value: object) -> None:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in value:
        if type(row) is not PolicyPollSampleDriftDigestRow:
            raise ValueError("rows must contain PolicyPollSampleDriftDigestRow")
        _require_hard_flags(row, "row")
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id values")
        seen.add(row.source_id)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")


def _require_reason_code_counts(value: object) -> None:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    reason_codes: list[str] = []
    for item in value:
        if type(item) is not PolicyPollSampleDriftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PolicyPollSampleDriftReasonCodeCount",
            )
        _require_hard_flags(item, "reason_code_count")
        reason_codes.append(item.reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts must contain unique reason codes")
    if tuple(reason_codes) != tuple(sorted(reason_codes)):
        raise ValueError("reason_code_counts must be sorted")


def _require_hard_flags(value: object, label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: PolicyPollSampleDriftDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.drift_status],
        -row.sample_drift_risk_score,
        row.market_slug,
        row.source_id,
    )


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError("payload value must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload value must be safe for serialization")
