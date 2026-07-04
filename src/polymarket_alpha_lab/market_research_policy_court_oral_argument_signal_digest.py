"""Pure Phase 1 report-only reducer for policy court oral argument signals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_COURT_ORAL_ARGUMENT_SIGNAL_DIGEST_CONFIG_VERSION = (
    "market-research-policy-court-oral-argument-signal-digest-v0"
)
POLICY_COURT_ORAL_ARGUMENT_SIGNAL_RESEARCH_SCOPE = (
    "policy court oral argument signal research digest only"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS)
ROW_STATUSES = (CLEAR_STATUS, WATCH_STATUS)

SCORE_REASON = "policy_court_oral_argument_signal_score_high"
SKEPTICISM_REASON = "policy_court_oral_argument_skepticism_high"
UNCERTAINTY_REASON = "policy_court_oral_argument_uncertainty_high"
PRECEDENT_REASON = "policy_court_oral_argument_precedent_pressure_high"
CONFIDENCE_REASON = "policy_court_oral_argument_confidence_high"
ACTIVE_REASON = "policy_court_oral_argument_signal_active"
STALE_REASON = "policy_court_oral_argument_signal_stale"
CLEAR_REASON = "policy_court_oral_argument_signal_clear"
PASSED_REASON = "policy_court_oral_argument_signal_passed"
EMPTY_REASON = "policy_court_oral_argument_signal_empty"

ROW_REASON_CODES = (
    SCORE_REASON,
    SKEPTICISM_REASON,
    UNCERTAINTY_REASON,
    PRECEDENT_REASON,
    CONFIDENCE_REASON,
    ACTIVE_REASON,
    STALE_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    SCORE_REASON,
    SKEPTICISM_REASON,
    UNCERTAINTY_REASON,
    PRECEDENT_REASON,
    CONFIDENCE_REASON,
    ACTIVE_REASON,
    STALE_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_policy_court_oral_argument_signal_monitoring",
    WATCH_STATUS: "review_report_only_policy_court_oral_argument_signals",
}
WATCH_RANK = Decimal("0.000000")
CLEAR_RANK = Decimal("1.000000")

_BLOCKED_TEXT_PARTS = (
    "mar" "ket_" "slug",
    "ques" "tion",
    "pay" "load_" "json",
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "acc" "ount",
    "ad" "vice",
    "au" "th",
    "sign" "ing",
    "private_" "key",
    "api_" "key",
    "sec" "ret",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_COURT_ORAL_ARGUMENT_SIGNAL_DIGEST_CONFIG_VERSION",
    "POLICY_COURT_ORAL_ARGUMENT_SIGNAL_RESEARCH_SCOPE",
    "MarketResearchPolicyCourtOralArgumentSignalDigestConfig",
    "MarketResearchPolicyCourtOralArgumentSignalDigestSignal",
    "MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount",
    "MarketResearchPolicyCourtOralArgumentSignalDigestRow",
    "MarketResearchPolicyCourtOralArgumentSignalDigestReport",
    "build_market_research_policy_court_oral_argument_signal_digest",
    "market_research_policy_court_oral_argument_signal_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyCourtOralArgumentSignalDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_COURT_ORAL_ARGUMENT_SIGNAL_DIGEST_CONFIG_VERSION
    )
    oral_argument_signal_score_threshold: Decimal = Decimal("0.650000")
    skeptical_prompt_count_threshold: Decimal = Decimal("4.000000")
    uncertainty_prompt_count_threshold: Decimal = Decimal("2.000000")
    cited_precedent_count_threshold: Decimal = Decimal("3.000000")
    confidence_threshold: Decimal = Decimal("0.700000")
    signal_age_seconds_threshold: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCourtOralArgumentSignalDigestConfig:
            raise TypeError(
                "MarketResearchPolicyCourtOralArgumentSignalDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCourtOralArgumentSignalDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_COURT_ORAL_ARGUMENT_SIGNAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "oral_argument_signal_score_threshold",
            "skeptical_prompt_count_threshold",
            "uncertainty_prompt_count_threshold",
            "cited_precedent_count_threshold",
            "signal_age_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_threshold",
            _normalize_ratio_decimal("confidence_threshold", self.confidence_threshold),
        )
        _require_maximum_one_decimal(
            "oral_argument_signal_score_threshold",
            self.oral_argument_signal_score_threshold,
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyCourtOralArgumentSignalDigestSignal:
    case_key: str
    court_key: str
    docket_key: str
    source_ref: str
    observed_at: datetime
    skeptical_prompt_count: Decimal
    supportive_prompt_count: Decimal
    uncertainty_prompt_count: Decimal
    cited_precedent_count: Decimal
    outcome_alignment_confidence: Decimal
    oral_argument_signal_active: bool
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_COURT_ORAL_ARGUMENT_SIGNAL_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCourtOralArgumentSignalDigestSignal:
            raise TypeError(
                "MarketResearchPolicyCourtOralArgumentSignalDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCourtOralArgumentSignalDigestSignal,
            "signal",
        )
        for field_name in (
            "case_key",
            "court_key",
            "docket_key",
            "source_ref",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "skeptical_prompt_count",
            "supportive_prompt_count",
            "uncertainty_prompt_count",
            "cited_precedent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_alignment_confidence",
            _normalize_ratio_decimal(
                "outcome_alignment_confidence",
                self.outcome_alignment_confidence,
            ),
        )
        if type(self.oral_argument_signal_active) is not bool:
            raise ValueError("oral_argument_signal_active must be a bool")
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount:
    reason_code: str
    case_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "case_count",
            _normalize_nonnegative_decimal("case_count", self.case_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchPolicyCourtOralArgumentSignalDigestRow:
    case_key: str
    court_key: str
    docket_key: str
    signal_count: Decimal
    observed_at_latest: datetime
    skeptical_prompt_count_max: Decimal
    supportive_prompt_count_max: Decimal
    uncertainty_prompt_count_max: Decimal
    cited_precedent_count_max: Decimal
    outcome_alignment_confidence_max: Decimal
    oral_argument_signal_score: Decimal
    signal_age_seconds: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCourtOralArgumentSignalDigestRow:
            raise TypeError(
                "MarketResearchPolicyCourtOralArgumentSignalDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCourtOralArgumentSignalDigestRow,
            "row",
        )
        for field_name in ("case_key", "court_key", "docket_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_decimal("signal_count", self.signal_count),
        )
        object.__setattr__(
            self,
            "observed_at_latest",
            _as_utc("observed_at_latest", self.observed_at_latest),
        )
        for field_name in (
            "skeptical_prompt_count_max",
            "supportive_prompt_count_max",
            "uncertainty_prompt_count_max",
            "cited_precedent_count_max",
            "outcome_alignment_confidence_max",
            "oral_argument_signal_score",
            "signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_alignment_confidence_max",
            "oral_argument_signal_score",
        ):
            _require_maximum_one_decimal(field_name, getattr(self, field_name))
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyCourtOralArgumentSignalDigestReport:
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    case_count: Decimal
    signal_count: Decimal
    clear_case_count: Decimal
    watch_case_count: Decimal
    high_score_case_count: Decimal
    high_skepticism_case_count: Decimal
    high_uncertainty_case_count: Decimal
    high_precedent_pressure_case_count: Decimal
    high_confidence_case_count: Decimal
    active_signal_case_count: Decimal
    stale_signal_case_count: Decimal
    oral_argument_signal_score_threshold: Decimal
    skeptical_prompt_count_threshold: Decimal
    uncertainty_prompt_count_threshold: Decimal
    cited_precedent_count_threshold: Decimal
    confidence_threshold: Decimal
    signal_age_seconds_threshold: Decimal
    max_oral_argument_signal_score: Decimal
    max_signal_age_seconds: Decimal
    average_outcome_alignment_confidence: Decimal
    rows: tuple[MarketResearchPolicyCourtOralArgumentSignalDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCourtOralArgumentSignalDigestReport:
            raise TypeError(
                "MarketResearchPolicyCourtOralArgumentSignalDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCourtOralArgumentSignalDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != POLICY_COURT_ORAL_ARGUMENT_SIGNAL_RESEARCH_SCOPE:
            raise ValueError("research_scope must match policy court oral argument scope")
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "case_count",
            "signal_count",
            "clear_case_count",
            "watch_case_count",
            "high_score_case_count",
            "high_skepticism_case_count",
            "high_uncertainty_case_count",
            "high_precedent_pressure_case_count",
            "high_confidence_case_count",
            "active_signal_case_count",
            "stale_signal_case_count",
            "oral_argument_signal_score_threshold",
            "skeptical_prompt_count_threshold",
            "uncertainty_prompt_count_threshold",
            "cited_precedent_count_threshold",
            "confidence_threshold",
            "signal_age_seconds_threshold",
            "max_oral_argument_signal_score",
            "max_signal_age_seconds",
            "average_outcome_alignment_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "oral_argument_signal_score_threshold",
            "confidence_threshold",
            "max_oral_argument_signal_score",
            "average_outcome_alignment_confidence",
        ):
            _require_maximum_one_decimal(field_name, getattr(self, field_name))
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


def build_market_research_policy_court_oral_argument_signal_digest(
    signals: Iterable[MarketResearchPolicyCourtOralArgumentSignalDigestSignal],
    *,
    config: MarketResearchPolicyCourtOralArgumentSignalDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyCourtOralArgumentSignalDigestReport:
    _require_exact_type(
        config,
        MarketResearchPolicyCourtOralArgumentSignalDigestConfig,
        "config",
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals)
    rows = _build_rows(signal_items, config=config, generated_at=generated_at_utc)
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    digest_status = WATCH_STATUS if row_reason_codes else PASS_STATUS
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchPolicyCourtOralArgumentSignalDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=POLICY_COURT_ORAL_ARGUMENT_SIGNAL_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        case_count=_count_decimal(len(rows)),
        signal_count=_count_decimal(len(signal_items)),
        clear_case_count=_count_decimal(
            sum(ONE for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_case_count=_count_decimal(
            sum(ONE for row in rows if row.digest_status == WATCH_STATUS),
        ),
        high_score_case_count=_reason_count(rows, SCORE_REASON),
        high_skepticism_case_count=_reason_count(rows, SKEPTICISM_REASON),
        high_uncertainty_case_count=_reason_count(rows, UNCERTAINTY_REASON),
        high_precedent_pressure_case_count=_reason_count(rows, PRECEDENT_REASON),
        high_confidence_case_count=_reason_count(rows, CONFIDENCE_REASON),
        active_signal_case_count=_reason_count(rows, ACTIVE_REASON),
        stale_signal_case_count=_reason_count(rows, STALE_REASON),
        oral_argument_signal_score_threshold=config.oral_argument_signal_score_threshold,
        skeptical_prompt_count_threshold=config.skeptical_prompt_count_threshold,
        uncertainty_prompt_count_threshold=config.uncertainty_prompt_count_threshold,
        cited_precedent_count_threshold=config.cited_precedent_count_threshold,
        confidence_threshold=config.confidence_threshold,
        signal_age_seconds_threshold=config.signal_age_seconds_threshold,
        max_oral_argument_signal_score=_max_decimal(
            row.oral_argument_signal_score for row in rows
        ),
        max_signal_age_seconds=_max_decimal(row.signal_age_seconds for row in rows),
        average_outcome_alignment_confidence=_average_or_zero(
            row.outcome_alignment_confidence_max for row in rows
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


def market_research_policy_court_oral_argument_signal_digest_payload(
    report: MarketResearchPolicyCourtOralArgumentSignalDigestReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        MarketResearchPolicyCourtOralArgumentSignalDigestReport,
        "report",
    )
    _require_flags("report", report)
    payload = _to_plain(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _build_rows(
    signals: tuple[MarketResearchPolicyCourtOralArgumentSignalDigestSignal, ...],
    *,
    config: MarketResearchPolicyCourtOralArgumentSignalDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchPolicyCourtOralArgumentSignalDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str],
        list[MarketResearchPolicyCourtOralArgumentSignalDigestSignal],
    ] = {}
    for signal in signals:
        grouped.setdefault(
            (
                signal.case_key,
                signal.court_key,
                signal.docket_key,
            ),
            [],
        ).append(signal)

    rows: list[MarketResearchPolicyCourtOralArgumentSignalDigestRow] = []
    for (case_key, court_key, docket_key), case_signals in grouped.items():
        sorted_signals = sorted(
            case_signals,
            key=lambda item: (item.observed_at, item.source_ref),
        )
        observed_at_latest = max(item.observed_at for item in sorted_signals)
        signal_age_seconds = _datetime_delta_seconds(generated_at, observed_at_latest)
        if signal_age_seconds < ZERO:
            raise ValueError("observed_at values must be at or before generated_at")
        skeptical_prompt_count_max = max(
            item.skeptical_prompt_count for item in sorted_signals
        )
        supportive_prompt_count_max = max(
            item.supportive_prompt_count for item in sorted_signals
        )
        uncertainty_prompt_count_max = max(
            item.uncertainty_prompt_count for item in sorted_signals
        )
        cited_precedent_count_max = max(
            item.cited_precedent_count for item in sorted_signals
        )
        outcome_alignment_confidence_max = max(
            item.outcome_alignment_confidence for item in sorted_signals
        )
        active_signal_seen = any(
            item.oral_argument_signal_active for item in sorted_signals
        )
        oral_argument_signal_score = _oral_argument_signal_score(
            skeptical_prompt_count=skeptical_prompt_count_max,
            uncertainty_prompt_count=uncertainty_prompt_count_max,
            cited_precedent_count=cited_precedent_count_max,
            outcome_alignment_confidence=outcome_alignment_confidence_max,
            active_signal_seen=active_signal_seen,
            config=config,
        )
        reason_codes = _row_reason_codes(
            oral_argument_signal_score=oral_argument_signal_score,
            skeptical_prompt_count=skeptical_prompt_count_max,
            uncertainty_prompt_count=uncertainty_prompt_count_max,
            cited_precedent_count=cited_precedent_count_max,
            outcome_alignment_confidence=outcome_alignment_confidence_max,
            active_signal_seen=active_signal_seen,
            signal_age_seconds=signal_age_seconds,
            config=config,
        )
        rows.append(
            MarketResearchPolicyCourtOralArgumentSignalDigestRow(
                case_key=case_key,
                court_key=court_key,
                docket_key=docket_key,
                signal_count=_count_decimal(len(sorted_signals)),
                observed_at_latest=observed_at_latest,
                skeptical_prompt_count_max=skeptical_prompt_count_max,
                supportive_prompt_count_max=supportive_prompt_count_max,
                uncertainty_prompt_count_max=uncertainty_prompt_count_max,
                cited_precedent_count_max=cited_precedent_count_max,
                outcome_alignment_confidence_max=outcome_alignment_confidence_max,
                oral_argument_signal_score=oral_argument_signal_score,
                signal_age_seconds=signal_age_seconds,
                digest_status=WATCH_STATUS
                if reason_codes != (CLEAR_REASON,)
                else CLEAR_STATUS,
                reason_codes=reason_codes,
            ),
        )

    return tuple(sorted(rows, key=_row_sort_key))


def _row_reason_codes(
    *,
    oral_argument_signal_score: Decimal,
    skeptical_prompt_count: Decimal,
    uncertainty_prompt_count: Decimal,
    cited_precedent_count: Decimal,
    outcome_alignment_confidence: Decimal,
    active_signal_seen: bool,
    signal_age_seconds: Decimal,
    config: MarketResearchPolicyCourtOralArgumentSignalDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if oral_argument_signal_score >= config.oral_argument_signal_score_threshold:
        reason_codes.append(SCORE_REASON)
    if skeptical_prompt_count >= config.skeptical_prompt_count_threshold:
        reason_codes.append(SKEPTICISM_REASON)
    if uncertainty_prompt_count >= config.uncertainty_prompt_count_threshold:
        reason_codes.append(UNCERTAINTY_REASON)
    if cited_precedent_count >= config.cited_precedent_count_threshold:
        reason_codes.append(PRECEDENT_REASON)
    if outcome_alignment_confidence >= config.confidence_threshold:
        reason_codes.append(CONFIDENCE_REASON)
    if active_signal_seen:
        reason_codes.append(ACTIVE_REASON)
    if active_signal_seen and signal_age_seconds >= config.signal_age_seconds_threshold:
        reason_codes.append(STALE_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _oral_argument_signal_score(
    *,
    skeptical_prompt_count: Decimal,
    uncertainty_prompt_count: Decimal,
    cited_precedent_count: Decimal,
    outcome_alignment_confidence: Decimal,
    active_signal_seen: bool,
    config: MarketResearchPolicyCourtOralArgumentSignalDigestConfig,
) -> Decimal:
    return _quantize(
        max(
            ONE if active_signal_seen else ZERO,
            _bounded_ratio(
                skeptical_prompt_count,
                config.skeptical_prompt_count_threshold,
            ),
            _bounded_ratio(
                uncertainty_prompt_count,
                config.uncertainty_prompt_count_threshold,
            ),
            _bounded_ratio(
                cited_precedent_count,
                config.cited_precedent_count_threshold,
            ),
            outcome_alignment_confidence,
        ),
    )


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize(numerator / denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount(
            reason_code=reason_code,
            case_count=_count_decimal(sum(ONE for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchPolicyCourtOralArgumentSignalDigestSignal],
) -> tuple[MarketResearchPolicyCourtOralArgumentSignalDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        _require_exact_type(
            signal,
            MarketResearchPolicyCourtOralArgumentSignalDigestSignal,
            "signal",
        )
        _require_flags("signal", signal)
        key = (signal.case_key, signal.docket_key, signal.source_ref)
        if key in seen:
            raise ValueError("signals must not contain duplicate case/source pairs")
        seen.add(key)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchPolicyCourtOralArgumentSignalDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        _require_exact_type(
            row,
            MarketResearchPolicyCourtOralArgumentSignalDigestRow,
            "row",
        )
        _require_flags("row", row)
        key = (row.case_key, row.docket_key)
        if key in seen:
            raise ValueError("rows must not contain duplicate case/docket pairs")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) not in (tuple, list):
            raise ValueError("signal_config_versions entries must be source/version pairs")
        if Decimal(len(item)) != Decimal("2"):
            raise ValueError("signal_config_versions entries must be source/version pairs")
        source_ref, config_version = item
        _require_canonical_string("signal_config_versions source_ref", source_ref)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("signal_config_versions source_ref", source_ref)
        _reject_sensitive_text("signal_config_versions config_version", config_version)
        if source_ref in seen_refs:
            raise ValueError("signal_config_versions source_ref values must be unique")
        seen_refs.add(source_ref)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        _require_exact_type(
            item,
            MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount,
            "reason_code_count",
        )
    return normalized


def _validate_row(row: MarketResearchPolicyCourtOralArgumentSignalDigestRow) -> None:
    if row.digest_status == CLEAR_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear rows must use the clear reason")
    expected_status = (
        WATCH_STATUS
        if any(reason_code != CLEAR_REASON for reason_code in row.reason_codes)
        else CLEAR_STATUS
    )
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == WATCH_STATUS and row.reason_codes == (CLEAR_REASON,):
        raise ValueError("watch rows must include a watch reason")
    if row.oral_argument_signal_score == ZERO and row.digest_status == WATCH_STATUS:
        raise ValueError("watch rows must have positive oral_argument_signal_score")


def _validate_report(
    report: MarketResearchPolicyCourtOralArgumentSignalDigestReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.case_count != _count_decimal(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.signal_count != _quantize(sum((row.signal_count for row in report.rows), ZERO)):
        raise ValueError("signal_count must match rows")
    if report.clear_case_count != _count_decimal(
        sum(ONE for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_case_count must match rows")
    if report.watch_case_count != _count_decimal(
        sum(ONE for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_case_count must match rows")
    if report.case_count != report.clear_case_count + report.watch_case_count:
        raise ValueError("case counts must reconcile")
    if report.high_score_case_count != _reason_count(report.rows, SCORE_REASON):
        raise ValueError("high_score_case_count must match rows")
    if report.high_skepticism_case_count != _reason_count(report.rows, SKEPTICISM_REASON):
        raise ValueError("high_skepticism_case_count must match rows")
    if report.high_uncertainty_case_count != _reason_count(
        report.rows,
        UNCERTAINTY_REASON,
    ):
        raise ValueError("high_uncertainty_case_count must match rows")
    if report.high_precedent_pressure_case_count != _reason_count(
        report.rows,
        PRECEDENT_REASON,
    ):
        raise ValueError("high_precedent_pressure_case_count must match rows")
    if report.high_confidence_case_count != _reason_count(report.rows, CONFIDENCE_REASON):
        raise ValueError("high_confidence_case_count must match rows")
    if report.active_signal_case_count != _reason_count(report.rows, ACTIVE_REASON):
        raise ValueError("active_signal_case_count must match rows")
    if report.stale_signal_case_count != _reason_count(report.rows, STALE_REASON):
        raise ValueError("stale_signal_case_count must match rows")
    if report.max_oral_argument_signal_score != _max_decimal(
        row.oral_argument_signal_score for row in report.rows
    ):
        raise ValueError("max_oral_argument_signal_score must match rows")
    if report.max_signal_age_seconds != _max_decimal(
        row.signal_age_seconds for row in report.rows
    ):
        raise ValueError("max_signal_age_seconds must match rows")
    if report.average_outcome_alignment_confidence != _average_or_zero(
        row.outcome_alignment_confidence_max for row in report.rows
    ):
        raise ValueError("average_outcome_alignment_confidence must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_status = WATCH_STATUS if row_reason_codes else PASS_STATUS
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _reason_count(
    rows: tuple[MarketResearchPolicyCourtOralArgumentSignalDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(ONE for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketResearchPolicyCourtOralArgumentSignalDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.digest_status),
        -row.oral_argument_signal_score,
        -row.outcome_alignment_confidence_max,
        -row.skeptical_prompt_count_max,
        -row.uncertainty_prompt_count_max,
        -row.signal_age_seconds,
        row.case_key,
        row.docket_key,
    )


def _status_rank(status: str) -> Decimal:
    if status == WATCH_STATUS:
        return WATCH_RANK
    return CLEAR_RANK


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return text.removesuffix("+00:00") + "Z"
        return text
    if is_dataclass(value):
        return {field.name: _to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value


def _sort_reason_codes(
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{name} contains invalid reason code for this field")
    if Decimal(len(reason_codes)) != Decimal(len(set(reason_codes))):
        raise ValueError(f"{name} must be unique")
    if reason_codes != _sort_reason_codes(reason_codes, allowed):
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} is not recognized")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")
    if value != value.strip():
        raise ValueError(f"{name} must not contain leading or trailing whitespace")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(blocked in lowered for blocked in _BLOCKED_TEXT_PARTS):
        raise ValueError(f"{name} contains unsafe text")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized == ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    try:
        normalized = value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not normalized.is_finite():
        raise ValueError(f"{name} must be finite")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    _require_maximum_one_decimal(name, normalized)
    return normalized


def _require_maximum_one_decimal(name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{name} must be at most 1")


def _require_flags(name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{name} {flag} must be True")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _count_decimal(value: object) -> Decimal:
    return _quantize(Decimal(value))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(max(normalized))


def _average_or_zero(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / _count_decimal(len(normalized)))


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _quantize(value: Decimal) -> Decimal:
    try:
        normalized = value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("decimal value must be finite") from exc
    if not normalized.is_finite():
        raise ValueError("decimal value must be finite")
    return normalized
