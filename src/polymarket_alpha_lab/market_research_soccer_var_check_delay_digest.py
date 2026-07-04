"""Pure report-only reducer for soccer VAR check delay research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_VAR_CHECK_DELAY_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-var-check-delay-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
RISK_COMPONENT_COUNT = Decimal("6.000000")
UPSTREAM_RISK_FLOOR = Decimal("0.166667")

PASS_STATUS = "pass"
CLEAR_STATUS = "clear"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = (CLEAR_STATUS, WATCH_STATUS, BLOCKED_STATUS)

SOURCE_DISAGREEMENT_BLOCKED_REASON = (
    "soccer_var_check_delay_source_disagreement_blocked"
)
SOURCE_DELAY_AGE_BLOCKED_REASON = "soccer_var_check_delay_source_delay_age_blocked"
REVIEW_RATE_DELTA_BLOCKED_REASON = (
    "soccer_var_check_delay_review_rate_delta_blocked"
)
AVERAGE_CHECK_DURATION_BLOCKED_REASON = (
    "soccer_var_check_delay_average_check_duration_blocked"
)
REFEREE_PROPENSITY_BLOCKED_REASON = (
    "soccer_var_check_delay_referee_propensity_blocked"
)
INCIDENT_DENSITY_BLOCKED_REASON = "soccer_var_check_delay_incident_density_blocked"
SOURCE_DISAGREEMENT_WATCH_REASON = "soccer_var_check_delay_source_disagreement_watch"
SOURCE_DELAY_AGE_WATCH_REASON = "soccer_var_check_delay_source_delay_age_watch"
REVIEW_RATE_DELTA_WATCH_REASON = "soccer_var_check_delay_review_rate_delta_watch"
AVERAGE_CHECK_DURATION_WATCH_REASON = (
    "soccer_var_check_delay_average_check_duration_watch"
)
REFEREE_PROPENSITY_WATCH_REASON = "soccer_var_check_delay_referee_propensity_watch"
INCIDENT_DENSITY_WATCH_REASON = "soccer_var_check_delay_incident_density_watch"
UPSTREAM_REASON_PRESENT_REASON = "soccer_var_check_delay_upstream_reason_present"
CLEAR_REASON = "soccer_var_check_delay_clear"
PASSED_REASON = "soccer_var_check_delay_passed"
EMPTY_REASON = "soccer_var_check_delay_empty"

ROW_REASON_CODES = (
    SOURCE_DISAGREEMENT_BLOCKED_REASON,
    SOURCE_DELAY_AGE_BLOCKED_REASON,
    REVIEW_RATE_DELTA_BLOCKED_REASON,
    AVERAGE_CHECK_DURATION_BLOCKED_REASON,
    REFEREE_PROPENSITY_BLOCKED_REASON,
    INCIDENT_DENSITY_BLOCKED_REASON,
    SOURCE_DISAGREEMENT_WATCH_REASON,
    SOURCE_DELAY_AGE_WATCH_REASON,
    REVIEW_RATE_DELTA_WATCH_REASON,
    AVERAGE_CHECK_DURATION_WATCH_REASON,
    REFEREE_PROPENSITY_WATCH_REASON,
    INCIDENT_DENSITY_WATCH_REASON,
    UPSTREAM_REASON_PRESENT_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    SOURCE_DISAGREEMENT_BLOCKED_REASON,
    SOURCE_DELAY_AGE_BLOCKED_REASON,
    REVIEW_RATE_DELTA_BLOCKED_REASON,
    AVERAGE_CHECK_DURATION_BLOCKED_REASON,
    REFEREE_PROPENSITY_BLOCKED_REASON,
    INCIDENT_DENSITY_BLOCKED_REASON,
    SOURCE_DISAGREEMENT_WATCH_REASON,
    SOURCE_DELAY_AGE_WATCH_REASON,
    REVIEW_RATE_DELTA_WATCH_REASON,
    AVERAGE_CHECK_DURATION_WATCH_REASON,
    REFEREE_PROPENSITY_WATCH_REASON,
    INCIDENT_DENSITY_WATCH_REASON,
    UPSTREAM_REASON_PRESENT_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
BLOCKED_REASON_CODES = (
    SOURCE_DISAGREEMENT_BLOCKED_REASON,
    SOURCE_DELAY_AGE_BLOCKED_REASON,
    REVIEW_RATE_DELTA_BLOCKED_REASON,
    AVERAGE_CHECK_DURATION_BLOCKED_REASON,
    REFEREE_PROPENSITY_BLOCKED_REASON,
    INCIDENT_DENSITY_BLOCKED_REASON,
)

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_soccer_var_check_delay_monitoring",
    WATCH_STATUS: "review_report_only_soccer_var_check_delay_review",
    BLOCKED_STATUS: "block_report_only_soccer_var_check_delay_review",
}

_SENSITIVE_FRAGMENTS = (
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "can" "cel",
    "rep" "lace",
    "acc" "ount",
    "ad" "vice",
    "au" "th",
    "sign" "ing",
    "invest" "ment",
    "recom" "mend",
    "tra" "de",
    "b" "uy",
    "se" "ll",
    "se" "cret",
    "private" "_" "key",
    "api" "_" "key",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_VAR_CHECK_DELAY_DIGEST_CONFIG_VERSION",
    "MarketResearchSoccerVarCheckDelayDigestConfig",
    "MarketResearchSoccerVarCheckDelayDigestSignal",
    "MarketResearchSoccerVarCheckDelayDigestReasonCodeCount",
    "MarketResearchSoccerVarCheckDelayDigestRow",
    "MarketResearchSoccerVarCheckDelayDigestReport",
    "build_market_research_soccer_var_check_delay_digest",
    "market_research_soccer_var_check_delay_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchSoccerVarCheckDelayDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_VAR_CHECK_DELAY_DIGEST_CONFIG_VERSION
    )
    var_review_rate_delta_watch: Decimal = Decimal("0.120000")
    var_review_rate_delta_blocked: Decimal = Decimal("0.250000")
    average_check_duration_seconds_watch: Decimal = Decimal("60.000000")
    average_check_duration_seconds_blocked: Decimal = Decimal("120.000000")
    referee_var_propensity_watch: Decimal = Decimal("0.650000")
    referee_var_propensity_blocked: Decimal = Decimal("0.850000")
    source_delay_age_seconds_watch: Decimal = Decimal("20.000000")
    source_delay_age_seconds_blocked: Decimal = Decimal("45.000000")
    incident_density_watch: Decimal = Decimal("0.500000")
    incident_density_blocked: Decimal = Decimal("0.800000")
    source_disagreement_count_watch: Decimal = Decimal("1.000000")
    source_disagreement_count_blocked: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerVarCheckDelayDigestConfig:
            raise TypeError(
                "MarketResearchSoccerVarCheckDelayDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerVarCheckDelayDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchSoccerVarCheckDelayDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "var_review_rate_delta_watch",
            "average_check_duration_seconds_watch",
            "source_delay_age_seconds_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "var_review_rate_delta_blocked",
            "average_check_duration_seconds_blocked",
            "source_delay_age_seconds_blocked",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "referee_var_propensity_watch",
            "referee_var_propensity_blocked",
            "incident_density_watch",
            "incident_density_blocked",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "referee_var_propensity_blocked",
            "incident_density_blocked",
        ):
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        object.__setattr__(
            self,
            "source_disagreement_count_watch",
            _normalize_nonnegative_whole_decimal(
                "source_disagreement_count_watch",
                self.source_disagreement_count_watch,
            ),
        )
        object.__setattr__(
            self,
            "source_disagreement_count_blocked",
            _normalize_positive_whole_decimal(
                "source_disagreement_count_blocked",
                self.source_disagreement_count_blocked,
            ),
        )
        _require_watch_not_above_blocked(
            "var_review_rate_delta",
            self.var_review_rate_delta_watch,
            self.var_review_rate_delta_blocked,
        )
        _require_watch_not_above_blocked(
            "average_check_duration_seconds",
            self.average_check_duration_seconds_watch,
            self.average_check_duration_seconds_blocked,
        )
        _require_watch_not_above_blocked(
            "referee_var_propensity",
            self.referee_var_propensity_watch,
            self.referee_var_propensity_blocked,
        )
        _require_watch_not_above_blocked(
            "source_delay_age_seconds",
            self.source_delay_age_seconds_watch,
            self.source_delay_age_seconds_blocked,
        )
        _require_watch_not_above_blocked(
            "incident_density",
            self.incident_density_watch,
            self.incident_density_blocked,
        )
        _require_watch_not_above_blocked(
            "source_disagreement_count",
            self.source_disagreement_count_watch,
            self.source_disagreement_count_blocked,
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerVarCheckDelayDigestSignal:
    match_ref: str
    league_key: str
    market_slug: str
    source_ref: str
    kickoff_at: datetime
    source_timestamp: datetime
    var_review_rate_delta: Decimal
    average_check_duration_seconds: Decimal
    referee_var_propensity: Decimal
    source_delay_age_seconds: Decimal
    incident_density: Decimal
    source_disagreement_count: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_VAR_CHECK_DELAY_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerVarCheckDelayDigestSignal:
            raise TypeError(
                "MarketResearchSoccerVarCheckDelayDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerVarCheckDelayDigestSignal:
            raise ValueError(
                "signal must be exactly MarketResearchSoccerVarCheckDelayDigestSignal",
            )
        for field_name in (
            "match_ref",
            "league_key",
            "market_slug",
            "source_ref",
            "signal_config_version",
        ):
            value = getattr(self, field_name)
            _require_canonical_string(field_name, value)
            _reject_sensitive_text(field_name, value)
        object.__setattr__(self, "kickoff_at", _as_utc("kickoff_at", self.kickoff_at))
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        for field_name in (
            "var_review_rate_delta",
            "average_check_duration_seconds",
            "source_delay_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("referee_var_propensity", "incident_density"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_disagreement_count",
            _normalize_nonnegative_whole_decimal(
                "source_disagreement_count",
                self.source_disagreement_count,
            ),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchSoccerVarCheckDelayDigestReasonCodeCount:
    reason_code: str
    match_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerVarCheckDelayDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchSoccerVarCheckDelayDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerVarCheckDelayDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchSoccerVarCheckDelayDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "match_count",
            _normalize_nonnegative_whole_decimal("match_count", self.match_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSoccerVarCheckDelayDigestRow:
    match_ref: str
    league_key: str
    market_slug: str
    kickoff_at: datetime
    latest_source_timestamp: datetime
    signal_count: Decimal
    update_age_seconds: Decimal
    var_review_rate_delta_max: Decimal
    average_check_duration_seconds_max: Decimal
    referee_var_propensity_max: Decimal
    source_delay_age_seconds_max: Decimal
    incident_density_max: Decimal
    source_disagreement_count_max: Decimal
    upstream_reason_codes: tuple[str, ...]
    risk_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerVarCheckDelayDigestRow:
            raise TypeError(
                "MarketResearchSoccerVarCheckDelayDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerVarCheckDelayDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchSoccerVarCheckDelayDigestRow",
            )
        for field_name in ("match_ref", "league_key", "market_slug"):
            value = getattr(self, field_name)
            _require_canonical_string(field_name, value)
            _reject_sensitive_text(field_name, value)
        object.__setattr__(self, "kickoff_at", _as_utc("kickoff_at", self.kickoff_at))
        object.__setattr__(
            self,
            "latest_source_timestamp",
            _as_utc("latest_source_timestamp", self.latest_source_timestamp),
        )
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_whole_decimal("signal_count", self.signal_count),
        )
        object.__setattr__(
            self,
            "source_disagreement_count_max",
            _normalize_nonnegative_whole_decimal(
                "source_disagreement_count_max",
                self.source_disagreement_count_max,
            ),
        )
        for field_name in (
            "update_age_seconds",
            "var_review_rate_delta_max",
            "average_check_duration_seconds_max",
            "source_delay_age_seconds_max",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("referee_var_propensity_max", "incident_density_max"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "risk_score",
            _normalize_probability("risk_score", self.risk_score),
        )
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSoccerVarCheckDelayDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    match_count: Decimal
    clear_match_count: Decimal
    watch_match_count: Decimal
    blocked_match_count: Decimal
    signal_count: Decimal
    var_review_rate_delta_match_count: Decimal
    average_check_duration_match_count: Decimal
    referee_var_propensity_match_count: Decimal
    source_delay_age_match_count: Decimal
    incident_density_match_count: Decimal
    source_disagreement_match_count: Decimal
    upstream_reason_match_count: Decimal
    risk_score: Decimal
    var_review_rate_delta_watch: Decimal
    var_review_rate_delta_blocked: Decimal
    average_check_duration_seconds_watch: Decimal
    average_check_duration_seconds_blocked: Decimal
    referee_var_propensity_watch: Decimal
    referee_var_propensity_blocked: Decimal
    source_delay_age_seconds_watch: Decimal
    source_delay_age_seconds_blocked: Decimal
    incident_density_watch: Decimal
    incident_density_blocked: Decimal
    source_disagreement_count_watch: Decimal
    source_disagreement_count_blocked: Decimal
    max_var_review_rate_delta_observed: Decimal | None
    max_average_check_duration_seconds: Decimal | None
    max_referee_var_propensity_observed: Decimal | None
    max_source_delay_age_seconds: Decimal | None
    max_incident_density_observed: Decimal | None
    max_source_disagreement_count: Decimal | None
    rows: tuple[MarketResearchSoccerVarCheckDelayDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerVarCheckDelayDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerVarCheckDelayDigestReport:
            raise TypeError(
                "MarketResearchSoccerVarCheckDelayDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerVarCheckDelayDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchSoccerVarCheckDelayDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "match_count",
            "clear_match_count",
            "watch_match_count",
            "blocked_match_count",
            "signal_count",
            "var_review_rate_delta_match_count",
            "average_check_duration_match_count",
            "referee_var_propensity_match_count",
            "source_delay_age_match_count",
            "incident_density_match_count",
            "source_disagreement_match_count",
            "upstream_reason_match_count",
            "source_disagreement_count_watch",
            "source_disagreement_count_blocked",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "risk_score",
            _normalize_probability("risk_score", self.risk_score),
        )
        for field_name in (
            "var_review_rate_delta_watch",
            "var_review_rate_delta_blocked",
            "average_check_duration_seconds_watch",
            "average_check_duration_seconds_blocked",
            "source_delay_age_seconds_watch",
            "source_delay_age_seconds_blocked",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "referee_var_propensity_watch",
            "referee_var_propensity_blocked",
            "incident_density_watch",
            "incident_density_blocked",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_var_review_rate_delta_observed",
            "max_average_check_duration_seconds",
            "max_source_delay_age_seconds",
            "max_source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_referee_var_propensity_observed",
            "max_incident_density_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_soccer_var_check_delay_digest(
    signals: Iterable[MarketResearchSoccerVarCheckDelayDigestSignal],
    *,
    config: MarketResearchSoccerVarCheckDelayDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerVarCheckDelayDigestReport:
    if type(config) is not MarketResearchSoccerVarCheckDelayDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchSoccerVarCheckDelayDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals)
    rows = _build_rows(signal_items, config=config, generated_at=generated_at_utc)
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        digest_status = BLOCKED_STATUS
    elif row_reason_codes:
        digest_status = WATCH_STATUS
    else:
        digest_status = PASS_STATUS
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchSoccerVarCheckDelayDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        match_count=_whole(len(rows)),
        clear_match_count=_whole(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_match_count=_whole(
            sum(1 for row in rows if row.digest_status == WATCH_STATUS),
        ),
        blocked_match_count=_whole(
            sum(1 for row in rows if row.digest_status == BLOCKED_STATUS),
        ),
        signal_count=_whole(len(signal_items)),
        var_review_rate_delta_match_count=_whole(
            sum(
                1
                for row in rows
                if REVIEW_RATE_DELTA_BLOCKED_REASON in row.reason_codes
                or REVIEW_RATE_DELTA_WATCH_REASON in row.reason_codes
            ),
        ),
        average_check_duration_match_count=_whole(
            sum(
                1
                for row in rows
                if AVERAGE_CHECK_DURATION_BLOCKED_REASON in row.reason_codes
                or AVERAGE_CHECK_DURATION_WATCH_REASON in row.reason_codes
            ),
        ),
        referee_var_propensity_match_count=_whole(
            sum(
                1
                for row in rows
                if REFEREE_PROPENSITY_BLOCKED_REASON in row.reason_codes
                or REFEREE_PROPENSITY_WATCH_REASON in row.reason_codes
            ),
        ),
        source_delay_age_match_count=_whole(
            sum(
                1
                for row in rows
                if SOURCE_DELAY_AGE_BLOCKED_REASON in row.reason_codes
                or SOURCE_DELAY_AGE_WATCH_REASON in row.reason_codes
            ),
        ),
        incident_density_match_count=_whole(
            sum(
                1
                for row in rows
                if INCIDENT_DENSITY_BLOCKED_REASON in row.reason_codes
                or INCIDENT_DENSITY_WATCH_REASON in row.reason_codes
            ),
        ),
        source_disagreement_match_count=_whole(
            sum(
                1
                for row in rows
                if SOURCE_DISAGREEMENT_BLOCKED_REASON in row.reason_codes
                or SOURCE_DISAGREEMENT_WATCH_REASON in row.reason_codes
            ),
        ),
        upstream_reason_match_count=_whole(
            sum(1 for row in rows if UPSTREAM_REASON_PRESENT_REASON in row.reason_codes),
        ),
        risk_score=_max_or_zero(row.risk_score for row in rows),
        var_review_rate_delta_watch=config.var_review_rate_delta_watch,
        var_review_rate_delta_blocked=config.var_review_rate_delta_blocked,
        average_check_duration_seconds_watch=(
            config.average_check_duration_seconds_watch
        ),
        average_check_duration_seconds_blocked=(
            config.average_check_duration_seconds_blocked
        ),
        referee_var_propensity_watch=config.referee_var_propensity_watch,
        referee_var_propensity_blocked=config.referee_var_propensity_blocked,
        source_delay_age_seconds_watch=config.source_delay_age_seconds_watch,
        source_delay_age_seconds_blocked=config.source_delay_age_seconds_blocked,
        incident_density_watch=config.incident_density_watch,
        incident_density_blocked=config.incident_density_blocked,
        source_disagreement_count_watch=config.source_disagreement_count_watch,
        source_disagreement_count_blocked=config.source_disagreement_count_blocked,
        max_var_review_rate_delta_observed=_max_or_none(
            row.var_review_rate_delta_max for row in rows
        ),
        max_average_check_duration_seconds=_max_or_none(
            row.average_check_duration_seconds_max for row in rows
        ),
        max_referee_var_propensity_observed=_max_or_none(
            row.referee_var_propensity_max for row in rows
        ),
        max_source_delay_age_seconds=_max_or_none(
            row.source_delay_age_seconds_max for row in rows
        ),
        max_incident_density_observed=_max_or_none(
            row.incident_density_max for row in rows
        ),
        max_source_disagreement_count=_max_or_none(
            row.source_disagreement_count_max for row in rows
        ),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                {
                    (signal.source_ref, signal.signal_config_version)
                    for signal in signal_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_soccer_var_check_delay_digest_payload(
    report: MarketResearchSoccerVarCheckDelayDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSoccerVarCheckDelayDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchSoccerVarCheckDelayDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _build_rows(
    signals: tuple[MarketResearchSoccerVarCheckDelayDigestSignal, ...],
    *,
    config: MarketResearchSoccerVarCheckDelayDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchSoccerVarCheckDelayDigestRow, ...]:
    grouped: dict[tuple[str, str], list[MarketResearchSoccerVarCheckDelayDigestSignal]] = {}
    for signal in signals:
        grouped.setdefault((signal.match_ref, signal.league_key), []).append(signal)

    rows: list[MarketResearchSoccerVarCheckDelayDigestRow] = []
    for (match_ref, league_key), match_signals in grouped.items():
        market_slugs = {signal.market_slug for signal in match_signals}
        kickoff_values = {signal.kickoff_at for signal in match_signals}
        if len(market_slugs) != 1 or len(kickoff_values) != 1:
            raise ValueError("match group must use one market slug and kickoff")
        sorted_signals = sorted(
            match_signals,
            key=lambda item: (item.source_timestamp, item.source_ref),
        )
        latest = sorted_signals[-1]
        update_age_seconds = _seconds_between(generated_at, latest.source_timestamp)
        if update_age_seconds < ZERO:
            raise ValueError("source_timestamp values must not be in the future")

        var_review_rate_delta_max = max(
            item.var_review_rate_delta for item in sorted_signals
        )
        average_check_duration_seconds_max = max(
            item.average_check_duration_seconds for item in sorted_signals
        )
        referee_var_propensity_max = max(
            item.referee_var_propensity for item in sorted_signals
        )
        source_delay_age_seconds_max = max(
            item.source_delay_age_seconds for item in sorted_signals
        )
        incident_density_max = max(item.incident_density for item in sorted_signals)
        source_disagreement_count_max = max(
            item.source_disagreement_count for item in sorted_signals
        )
        upstream_reason_codes = _normalize_upstream_reason_codes(
            "upstream_reason_codes",
            tuple(
                reason_code
                for signal in sorted_signals
                for reason_code in signal.upstream_reason_codes
            ),
        )

        reason_codes: list[str] = []
        _append_threshold_reason(
            reason_codes,
            source_disagreement_count_max,
            config.source_disagreement_count_watch,
            config.source_disagreement_count_blocked,
            SOURCE_DISAGREEMENT_WATCH_REASON,
            SOURCE_DISAGREEMENT_BLOCKED_REASON,
        )
        _append_threshold_reason(
            reason_codes,
            source_delay_age_seconds_max,
            config.source_delay_age_seconds_watch,
            config.source_delay_age_seconds_blocked,
            SOURCE_DELAY_AGE_WATCH_REASON,
            SOURCE_DELAY_AGE_BLOCKED_REASON,
        )
        _append_threshold_reason(
            reason_codes,
            var_review_rate_delta_max,
            config.var_review_rate_delta_watch,
            config.var_review_rate_delta_blocked,
            REVIEW_RATE_DELTA_WATCH_REASON,
            REVIEW_RATE_DELTA_BLOCKED_REASON,
        )
        _append_threshold_reason(
            reason_codes,
            average_check_duration_seconds_max,
            config.average_check_duration_seconds_watch,
            config.average_check_duration_seconds_blocked,
            AVERAGE_CHECK_DURATION_WATCH_REASON,
            AVERAGE_CHECK_DURATION_BLOCKED_REASON,
        )
        _append_threshold_reason(
            reason_codes,
            referee_var_propensity_max,
            config.referee_var_propensity_watch,
            config.referee_var_propensity_blocked,
            REFEREE_PROPENSITY_WATCH_REASON,
            REFEREE_PROPENSITY_BLOCKED_REASON,
        )
        _append_threshold_reason(
            reason_codes,
            incident_density_max,
            config.incident_density_watch,
            config.incident_density_blocked,
            INCIDENT_DENSITY_WATCH_REASON,
            INCIDENT_DENSITY_BLOCKED_REASON,
        )
        if upstream_reason_codes:
            reason_codes.append(UPSTREAM_REASON_PRESENT_REASON)
        if not reason_codes:
            reason_codes.append(CLEAR_REASON)
        row_reason_codes = _sort_reason_codes(reason_codes, ROW_REASON_CODES)

        rows.append(
            MarketResearchSoccerVarCheckDelayDigestRow(
                match_ref=match_ref,
                league_key=league_key,
                market_slug=latest.market_slug,
                kickoff_at=latest.kickoff_at,
                latest_source_timestamp=latest.source_timestamp,
                signal_count=_whole(len(sorted_signals)),
                update_age_seconds=update_age_seconds,
                var_review_rate_delta_max=var_review_rate_delta_max,
                average_check_duration_seconds_max=(
                    average_check_duration_seconds_max
                ),
                referee_var_propensity_max=referee_var_propensity_max,
                source_delay_age_seconds_max=source_delay_age_seconds_max,
                incident_density_max=incident_density_max,
                source_disagreement_count_max=source_disagreement_count_max,
                upstream_reason_codes=upstream_reason_codes,
                risk_score=_apply_upstream_risk_floor(
                    _row_risk_score(
                        var_review_rate_delta_max,
                        average_check_duration_seconds_max,
                        referee_var_propensity_max,
                        source_delay_age_seconds_max,
                        incident_density_max,
                        source_disagreement_count_max,
                        config=config,
                    ),
                    upstream_reason_codes,
                ),
                digest_status=_row_status(row_reason_codes),
                reason_codes=row_reason_codes,
            ),
        )

    return tuple(sorted(rows, key=_row_sort_key))


def _append_threshold_reason(
    reason_codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    blocked_threshold: Decimal,
    watch_reason: str,
    blocked_reason: str,
) -> None:
    if value >= blocked_threshold:
        reason_codes.append(blocked_reason)
    elif value >= watch_threshold:
        reason_codes.append(watch_reason)


def _row_risk_score(
    var_review_rate_delta: Decimal,
    average_check_duration_seconds: Decimal,
    referee_var_propensity: Decimal,
    source_delay_age_seconds: Decimal,
    incident_density: Decimal,
    source_disagreement_count: Decimal,
    *,
    config: MarketResearchSoccerVarCheckDelayDigestConfig,
) -> Decimal:
    components = (
        _threshold_component(
            var_review_rate_delta,
            config.var_review_rate_delta_watch,
            config.var_review_rate_delta_blocked,
        ),
        _threshold_component(
            average_check_duration_seconds,
            config.average_check_duration_seconds_watch,
            config.average_check_duration_seconds_blocked,
        ),
        _threshold_component(
            referee_var_propensity,
            config.referee_var_propensity_watch,
            config.referee_var_propensity_blocked,
        ),
        _threshold_component(
            source_delay_age_seconds,
            config.source_delay_age_seconds_watch,
            config.source_delay_age_seconds_blocked,
        ),
        _threshold_component(
            incident_density,
            config.incident_density_watch,
            config.incident_density_blocked,
        ),
        _threshold_component(
            source_disagreement_count,
            config.source_disagreement_count_watch,
            config.source_disagreement_count_blocked,
        ),
    )
    return _quantize(_sum_decimals(components) / RISK_COMPONENT_COUNT)


def _threshold_component(
    value: Decimal,
    watch_threshold: Decimal,
    blocked_threshold: Decimal,
) -> Decimal:
    if value < watch_threshold:
        return ZERO.quantize(QUANTUM)
    if value >= blocked_threshold:
        return ONE
    return _quantize(value / blocked_threshold)


def _apply_upstream_risk_floor(
    risk_score: Decimal,
    upstream_reason_codes: tuple[str, ...],
) -> Decimal:
    if upstream_reason_codes and risk_score < UPSTREAM_RISK_FLOOR:
        return UPSTREAM_RISK_FLOOR
    return risk_score


def _row_sort_key(row: MarketResearchSoccerVarCheckDelayDigestRow) -> tuple[object, ...]:
    status_rank = {
        BLOCKED_STATUS: 0,
        WATCH_STATUS: 1,
        CLEAR_STATUS: 2,
    }[row.digest_status]
    return (
        status_rank,
        -row.risk_score,
        -row.source_disagreement_count_max,
        -row.source_delay_age_seconds_max,
        -row.var_review_rate_delta_max,
        -row.average_check_duration_seconds_max,
        -row.referee_var_propensity_max,
        -row.incident_density_max,
        row.match_ref,
        row.league_key,
        row.market_slug,
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSoccerVarCheckDelayDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code=reason_code,
            match_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchSoccerVarCheckDelayDigestSignal],
) -> tuple[MarketResearchSoccerVarCheckDelayDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchSoccerVarCheckDelayDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchSoccerVarCheckDelayDigestSignal records",
            )
        _require_flags("signal", signal)
        key = (signal.match_ref, signal.league_key, signal.source_ref)
        if key in seen:
            raise ValueError("signals must not contain duplicate match/source pairs")
        seen.add(key)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSoccerVarCheckDelayDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchSoccerVarCheckDelayDigestRow:
            raise ValueError(
                "rows must contain MarketResearchSoccerVarCheckDelayDigestRow records",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    keys = tuple((row.match_ref, row.league_key) for row in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate match keys")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    normalized = tuple(value)
    pairs: list[tuple[str, str]] = []
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError("signal_config_versions entries must be source/version pairs")
        source_ref, config_version = item
        _require_canonical_string("signal_config_versions source_ref", source_ref)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("signal_config_versions source_ref", source_ref)
        _reject_sensitive_text("signal_config_versions config_version", config_version)
        pairs.append((source_ref, config_version))
    normalized_pairs = tuple(pairs)
    if normalized_pairs != tuple(sorted(normalized_pairs)):
        raise ValueError("signal_config_versions must be sorted")
    if len(set(normalized_pairs)) != len(normalized_pairs):
        raise ValueError("signal_config_versions entries must be unique")
    return normalized_pairs


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerVarCheckDelayDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchSoccerVarCheckDelayDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerVarCheckDelayDigestReasonCodeCount records",
            )
        _require_flags("reason_code_count", item)
    if normalized != tuple(
        sorted(normalized, key=lambda item: DIGEST_REASON_CODES.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must be unique by reason_code")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason_codes")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason_codes") from exc
    if not items:
        raise ValueError(f"{field_name} must contain reason_codes")
    for item in items:
        _require_reason_code("reason_codes", item)
        if item not in allowed:
            raise ValueError(f"{field_name} contains unknown reason_codes")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} reason_codes must be unique")
    if items != _sort_reason_codes(items, allowed):
        raise ValueError(f"{field_name} reason_codes must be sorted deterministically")
    return items


def _normalize_upstream_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain upstream reason codes")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain upstream reason codes") from exc
    for item in items:
        _require_canonical_string(field_name, item)
        _reject_sensitive_text(field_name, item)
    return tuple(sorted(set(items)))


def _sort_reason_codes(items: Iterable[str], allowed: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(items, key=lambda item: allowed.index(item)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return BLOCKED_STATUS
    if reason_codes == (CLEAR_REASON,):
        return CLEAR_STATUS
    return WATCH_STATUS


def _validate_row(row: MarketResearchSoccerVarCheckDelayDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.digest_status != expected_status:
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status == CLEAR_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear rows must use the clear reason code")
    if row.digest_status != CLEAR_STATUS and CLEAR_REASON in row.reason_codes:
        raise ValueError("non-clear rows cannot use the clear reason code")
    if row.digest_status == CLEAR_STATUS and row.risk_score != ZERO:
        raise ValueError("clear rows must use zero risk_score")
    if row.digest_status != CLEAR_STATUS and row.risk_score <= ZERO:
        raise ValueError("non-clear rows must use positive risk_score")


def _validate_report(report: MarketResearchSoccerVarCheckDelayDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.match_count != _whole(len(report.rows)):
        raise ValueError("match_count must match rows")
    if report.signal_count != _sum_decimals(row.signal_count for row in report.rows):
        raise ValueError("signal_count must match rows")
    if report.clear_match_count != _whole(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_match_count must match rows")
    if report.watch_match_count != _whole(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_match_count must match rows")
    if report.blocked_match_count != _whole(
        sum(1 for row in report.rows if row.digest_status == BLOCKED_STATUS),
    ):
        raise ValueError("blocked_match_count must match rows")
    if (
        report.match_count
        != report.clear_match_count + report.watch_match_count + report.blocked_match_count
    ):
        raise ValueError("match counts must reconcile")
    for field_name, reason_pair in (
        (
            "var_review_rate_delta_match_count",
            (REVIEW_RATE_DELTA_BLOCKED_REASON, REVIEW_RATE_DELTA_WATCH_REASON),
        ),
        (
            "average_check_duration_match_count",
            (
                AVERAGE_CHECK_DURATION_BLOCKED_REASON,
                AVERAGE_CHECK_DURATION_WATCH_REASON,
            ),
        ),
        (
            "referee_var_propensity_match_count",
            (REFEREE_PROPENSITY_BLOCKED_REASON, REFEREE_PROPENSITY_WATCH_REASON),
        ),
        (
            "source_delay_age_match_count",
            (SOURCE_DELAY_AGE_BLOCKED_REASON, SOURCE_DELAY_AGE_WATCH_REASON),
        ),
        (
            "incident_density_match_count",
            (INCIDENT_DENSITY_BLOCKED_REASON, INCIDENT_DENSITY_WATCH_REASON),
        ),
        (
            "source_disagreement_match_count",
            (SOURCE_DISAGREEMENT_BLOCKED_REASON, SOURCE_DISAGREEMENT_WATCH_REASON),
        ),
    ):
        expected = _whole(
            sum(
                1
                for row in report.rows
                if reason_pair[0] in row.reason_codes
                or reason_pair[1] in row.reason_codes
            ),
        )
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.upstream_reason_match_count != _whole(
        sum(1 for row in report.rows if UPSTREAM_REASON_PRESENT_REASON in row.reason_codes),
    ):
        raise ValueError("upstream_reason_match_count must match rows")
    if report.risk_score != _max_or_zero(row.risk_score for row in report.rows):
        raise ValueError("risk_score must match rows")
    if report.max_var_review_rate_delta_observed != _max_or_none(
        row.var_review_rate_delta_max for row in report.rows
    ):
        raise ValueError("max_var_review_rate_delta_observed must match rows")
    if report.max_average_check_duration_seconds != _max_or_none(
        row.average_check_duration_seconds_max for row in report.rows
    ):
        raise ValueError("max_average_check_duration_seconds must match rows")
    if report.max_referee_var_propensity_observed != _max_or_none(
        row.referee_var_propensity_max for row in report.rows
    ):
        raise ValueError("max_referee_var_propensity_observed must match rows")
    if report.max_source_delay_age_seconds != _max_or_none(
        row.source_delay_age_seconds_max for row in report.rows
    ):
        raise ValueError("max_source_delay_age_seconds must match rows")
    if report.max_incident_density_observed != _max_or_none(
        row.incident_density_max for row in report.rows
    ):
        raise ValueError("max_incident_density_observed must match rows")
    if report.max_source_disagreement_count != _max_or_none(
        row.source_disagreement_count_max for row in report.rows
    ):
        raise ValueError("max_source_disagreement_count must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = (
        BLOCKED_STATUS
        if any(row.digest_status == BLOCKED_STATUS for row in report.rows)
        else WATCH_STATUS
        if row_reason_codes
        else PASS_STATUS
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_plain(item) for key, item in value.items()}
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _reject_sensitive_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS):
        raise ValueError(f"{field_name} contains sensitive text")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_watch_not_above_blocked(
    metric_name: str,
    watch_threshold: Decimal,
    blocked_threshold: Decimal,
) -> None:
    if watch_threshold > blocked_threshold:
        raise ValueError(f"{metric_name} watch threshold must not exceed blocked threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    try:
        normalized = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite Decimal") from exc
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + fractional)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _whole(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(max(items))


def _max_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    return _quantize(max(items))
