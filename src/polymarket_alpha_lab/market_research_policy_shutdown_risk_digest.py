"""Pure policy shutdown risk digest for market research."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_SHUTDOWN_RISK_DIGEST_CONFIG_VERSION = (
    "market-research-policy-shutdown-risk-digest-v0"
)

CLEAR_REASON = "market_research_policy_shutdown_risk_digest_clear"
EMPTY_REASON = "market_research_policy_shutdown_risk_digest_empty"
ELEVATED_PROBABILITY_REASON = (
    "market_research_policy_shutdown_risk_digest_elevated_probability"
)
MATERIAL_IMPACT_REASON = "market_research_policy_shutdown_risk_digest_material_impact"
STALE_SIGNAL_REASON = "market_research_policy_shutdown_risk_digest_stale_signal"
THIN_SOURCE_REASON = (
    "market_research_policy_shutdown_risk_digest_thin_source_coverage"
)

REASON_CODES = (
    ELEVATED_PROBABILITY_REASON,
    MATERIAL_IMPACT_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCE_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
RISK_STATUSES = ("blocked", "watch", "clear")
NEXT_STEPS = {
    "clear": "allow_report_only_market_research_policy_shutdown_risk_digest",
    "watch": "refresh_report_only_market_research_policy_shutdown_risk_digest",
    "blocked": "block_report_only_market_research_policy_shutdown_risk_digest",
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}
REASON_RANK = {
    ELEVATED_PROBABILITY_REASON: 0,
    MATERIAL_IMPACT_REASON: 1,
    STALE_SIGNAL_REASON: 2,
    THIN_SOURCE_REASON: 3,
    CLEAR_REASON: 4,
    EMPTY_REASON: 5,
}

__all__ = (
    "MarketResearchPolicyShutdownRiskDigestConfig",
    "MarketResearchPolicyShutdownRiskDigestReasonCodeCount",
    "MarketResearchPolicyShutdownRiskDigestReport",
    "MarketResearchPolicyShutdownRiskDigestRow",
    "MarketResearchPolicyShutdownRiskDigestSignal",
    "build_market_research_policy_shutdown_risk_digest",
    "market_research_policy_shutdown_risk_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyShutdownRiskDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_SHUTDOWN_RISK_DIGEST_CONFIG_VERSION
    )
    elevated_shutdown_probability_threshold: Decimal = Decimal("0.500000")
    material_impact_threshold: Decimal = Decimal("0.400000")
    fresh_signal_max_age_seconds: Decimal = Decimal("7200.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyShutdownRiskDigestConfig:
            raise TypeError(
                "MarketResearchPolicyShutdownRiskDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            MarketResearchPolicyShutdownRiskDigestConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "elevated_shutdown_probability_threshold",
            _require_ratio_decimal(
                "elevated_shutdown_probability_threshold",
                self.elevated_shutdown_probability_threshold,
            ),
        )
        object.__setattr__(
            self,
            "material_impact_threshold",
            _require_ratio_decimal("material_impact_threshold", self.material_impact_threshold),
        )
        object.__setattr__(
            self,
            "fresh_signal_max_age_seconds",
            _require_positive_decimal(
                "fresh_signal_max_age_seconds",
                self.fresh_signal_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_independent_source_count",
            _require_positive_count_decimal(
                "min_independent_source_count",
                self.min_independent_source_count,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyShutdownRiskDigestSignal:
    market_research_key: str
    policy_jurisdiction: str
    policy_surface: str
    source_ref: str
    source_family: str
    observed_at: datetime
    shutdown_probability: Decimal
    impact_score: Decimal
    source_confidence: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_SHUTDOWN_RISK_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyShutdownRiskDigestSignal:
            raise TypeError(
                "MarketResearchPolicyShutdownRiskDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "signal",
            self,
            MarketResearchPolicyShutdownRiskDigestSignal,
        )
        for field_name in (
            "market_research_key",
            "policy_jurisdiction",
            "policy_surface",
            "source_ref",
            "source_family",
            "signal_config_version",
        ):
            value = getattr(self, field_name)
            _require_canonical_string(field_name, value)
            _require_redacted_reference(field_name, value)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "shutdown_probability",
            "impact_score",
            "source_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchPolicyShutdownRiskDigestRow:
    market_research_key: str
    policy_jurisdiction: str
    policy_surface: str
    risk_status: str
    signal_count: Decimal
    independent_source_count: Decimal
    stale_signal_count: Decimal
    max_shutdown_probability: Decimal
    average_shutdown_probability: Decimal
    max_impact_score: Decimal
    average_source_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyShutdownRiskDigestRow:
            raise TypeError(
                "MarketResearchPolicyShutdownRiskDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            MarketResearchPolicyShutdownRiskDigestRow,
        )
        for field_name in (
            "market_research_key",
            "policy_jurisdiction",
            "policy_surface",
        ):
            value = getattr(self, field_name)
            _require_canonical_string(field_name, value)
            _require_redacted_reference(field_name, value)
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        for field_name in (
            "signal_count",
            "independent_source_count",
            "stale_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_shutdown_probability",
            "average_shutdown_probability",
            "max_impact_score",
            "average_source_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyShutdownRiskDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    surface_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyShutdownRiskDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyShutdownRiskDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            MarketResearchPolicyShutdownRiskDigestReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "surface_ratio",
            _require_ratio_decimal("surface_ratio", self.surface_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchPolicyShutdownRiskDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    policy_surface_count: Decimal
    clear_surface_count: Decimal
    watch_surface_count: Decimal
    blocked_surface_count: Decimal
    signal_count: Decimal
    elevated_surface_count: Decimal
    stale_signal_surface_count: Decimal
    thin_source_surface_count: Decimal
    shutdown_risk_surface_ratio: Decimal | None
    max_signal_age_seconds: Decimal | None
    elevated_shutdown_probability_threshold: Decimal
    material_impact_threshold: Decimal
    fresh_signal_max_age_seconds: Decimal
    min_independent_source_count: Decimal
    rows: tuple[MarketResearchPolicyShutdownRiskDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchPolicyShutdownRiskDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyShutdownRiskDigestReport:
            raise TypeError(
                "MarketResearchPolicyShutdownRiskDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            MarketResearchPolicyShutdownRiskDigestReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, RISK_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "policy_surface_count",
            "clear_surface_count",
            "watch_surface_count",
            "blocked_surface_count",
            "signal_count",
            "elevated_surface_count",
            "stale_signal_surface_count",
            "thin_source_surface_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.shutdown_risk_surface_ratio is not None:
            object.__setattr__(
                self,
                "shutdown_risk_surface_ratio",
                _require_ratio_decimal(
                    "shutdown_risk_surface_ratio",
                    self.shutdown_risk_surface_ratio,
                ),
            )
        if self.max_signal_age_seconds is not None:
            object.__setattr__(
                self,
                "max_signal_age_seconds",
                _require_nonnegative_decimal(
                    "max_signal_age_seconds",
                    self.max_signal_age_seconds,
                ),
            )
        object.__setattr__(
            self,
            "elevated_shutdown_probability_threshold",
            _require_ratio_decimal(
                "elevated_shutdown_probability_threshold",
                self.elevated_shutdown_probability_threshold,
            ),
        )
        object.__setattr__(
            self,
            "material_impact_threshold",
            _require_ratio_decimal("material_impact_threshold", self.material_impact_threshold),
        )
        object.__setattr__(
            self,
            "fresh_signal_max_age_seconds",
            _require_positive_decimal(
                "fresh_signal_max_age_seconds",
                self.fresh_signal_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_independent_source_count",
            _require_positive_count_decimal(
                "min_independent_source_count",
                self.min_independent_source_count,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_policy_shutdown_risk_digest(
    signals: object,
    *,
    config: MarketResearchPolicyShutdownRiskDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyShutdownRiskDigestReport:
    if type(config) is not MarketResearchPolicyShutdownRiskDigestConfig:
        raise ValueError("config must be a MarketResearchPolicyShutdownRiskDigestConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
    rows = _build_rows(normalized_signals, config=config, generated_at=generated_at)
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    surface_count = _decimal_count(len(rows))
    elevated_count = _decimal_count(
        sum(1 for row in rows if ELEVATED_PROBABILITY_REASON in row.reason_codes),
    )
    return MarketResearchPolicyShutdownRiskDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        policy_surface_count=surface_count,
        clear_surface_count=_decimal_count(_row_status_count(rows, "clear")),
        watch_surface_count=_decimal_count(_row_status_count(rows, "watch")),
        blocked_surface_count=_decimal_count(_row_status_count(rows, "blocked")),
        signal_count=_decimal_count(len(normalized_signals)),
        elevated_surface_count=elevated_count,
        stale_signal_surface_count=_decimal_count(
            sum(1 for row in rows if STALE_SIGNAL_REASON in row.reason_codes),
        ),
        thin_source_surface_count=_decimal_count(
            sum(1 for row in rows if THIN_SOURCE_REASON in row.reason_codes),
        ),
        shutdown_risk_surface_ratio=_ratio(elevated_count, surface_count),
        max_signal_age_seconds=_max_signal_age_seconds(
            normalized_signals,
            generated_at=generated_at,
        ),
        elevated_shutdown_probability_threshold=(
            config.elevated_shutdown_probability_threshold
        ),
        material_impact_threshold=config.material_impact_threshold,
        fresh_signal_max_age_seconds=config.fresh_signal_max_age_seconds,
        min_independent_source_count=config.min_independent_source_count,
        rows=rows,
        source_config_versions=_source_config_versions(normalized_signals),
        reason_code_counts=_reason_code_counts(rows, surface_count),
        reason_codes=reason_codes,
    )


def market_research_policy_shutdown_risk_digest_payload(
    report: MarketResearchPolicyShutdownRiskDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyShutdownRiskDigestReport:
        raise ValueError("report must be a MarketResearchPolicyShutdownRiskDigestReport")
    _validate_payload_public_value("report", report)
    return _to_payload(report)


def _build_rows(
    signals: tuple[MarketResearchPolicyShutdownRiskDigestSignal, ...],
    *,
    config: MarketResearchPolicyShutdownRiskDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchPolicyShutdownRiskDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str],
        list[MarketResearchPolicyShutdownRiskDigestSignal],
    ] = {}
    for signal in signals:
        grouped.setdefault(
            (
                signal.market_research_key,
                signal.policy_jurisdiction,
                signal.policy_surface,
            ),
            [],
        ).append(signal)
    return tuple(
        sorted(
            (
                _build_row(
                    market_research_key=market_research_key,
                    policy_jurisdiction=policy_jurisdiction,
                    policy_surface=policy_surface,
                    signals=tuple(group_signals),
                    config=config,
                    generated_at=generated_at,
                )
                for (
                    market_research_key,
                    policy_jurisdiction,
                    policy_surface,
                ), group_signals in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )


def _build_row(
    *,
    market_research_key: str,
    policy_jurisdiction: str,
    policy_surface: str,
    signals: tuple[MarketResearchPolicyShutdownRiskDigestSignal, ...],
    config: MarketResearchPolicyShutdownRiskDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyShutdownRiskDigestRow:
    signal_count = _decimal_count(len(signals))
    source_count = _decimal_count(len({signal.source_family for signal in signals}))
    ages = tuple(
        _decimal_count(int((generated_at - signal.observed_at).total_seconds()))
        for signal in signals
    )
    stale_count = _decimal_count(
        sum(age > config.fresh_signal_max_age_seconds for age in ages),
    )
    max_probability = max(signal.shutdown_probability for signal in signals)
    max_impact = max(signal.impact_score for signal in signals)
    average_probability = _ratio(
        _sum_decimal(signal.shutdown_probability for signal in signals),
        signal_count,
    )
    average_confidence = _ratio(
        _sum_decimal(signal.source_confidence for signal in signals),
        signal_count,
    )
    reason_codes = _row_reason_codes(
        max_shutdown_probability=max_probability,
        max_impact_score=max_impact,
        stale_signal_count=stale_count,
        independent_source_count=source_count,
        config=config,
    )
    return MarketResearchPolicyShutdownRiskDigestRow(
        market_research_key=market_research_key,
        policy_jurisdiction=policy_jurisdiction,
        policy_surface=policy_surface,
        risk_status=_row_status(reason_codes),
        signal_count=signal_count,
        independent_source_count=source_count,
        stale_signal_count=stale_count,
        max_shutdown_probability=max_probability,
        average_shutdown_probability=average_probability,
        max_impact_score=max_impact,
        average_source_confidence=average_confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    max_shutdown_probability: Decimal,
    max_impact_score: Decimal,
    stale_signal_count: Decimal,
    independent_source_count: Decimal,
    config: MarketResearchPolicyShutdownRiskDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if max_shutdown_probability >= config.elevated_shutdown_probability_threshold:
        reasons.append(ELEVATED_PROBABILITY_REASON)
    if max_impact_score >= config.material_impact_threshold:
        reasons.append(MATERIAL_IMPACT_REASON)
    if stale_signal_count > ZERO:
        reasons.append(STALE_SIGNAL_REASON)
    if independent_source_count < config.min_independent_source_count:
        reasons.append(THIN_SOURCE_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(sorted(reasons, key=_reason_sort_key))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        ELEVATED_PROBABILITY_REASON in reason_codes
        and MATERIAL_IMPACT_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "clear"
    return "watch"


def _digest_status(rows: tuple[MarketResearchPolicyShutdownRiskDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.risk_status == "blocked" for row in rows):
        return "blocked"
    if any(row.risk_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketResearchPolicyShutdownRiskDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = sorted(
        {reason for row in rows for reason in row.reason_codes},
        key=_reason_sort_key,
    )
    if reasons == [CLEAR_REASON]:
        return (CLEAR_REASON,)
    return tuple(reason for reason in reasons if reason != CLEAR_REASON)


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyShutdownRiskDigestRow, ...],
    surface_count: Decimal,
) -> tuple[MarketResearchPolicyShutdownRiskDigestReasonCodeCount, ...]:
    if surface_count == ZERO:
        return (
            MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                surface_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            surface_ratio=_ratio(_decimal_count(count), surface_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], _reason_sort_key(item[0])),
        )
    )


def _source_config_versions(
    signals: tuple[MarketResearchPolicyShutdownRiskDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (signal.source_ref, signal.signal_config_version)
                for signal in signals
            },
        )
    )


def _max_signal_age_seconds(
    signals: tuple[MarketResearchPolicyShutdownRiskDigestSignal, ...],
    *,
    generated_at: datetime,
) -> Decimal | None:
    if not signals:
        return None
    return _decimal_count(
        max(int((generated_at - signal.observed_at).total_seconds()) for signal in signals),
    )


def _normalize_signals(
    value: object,
) -> tuple[MarketResearchPolicyShutdownRiskDigestSignal, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        signals = tuple(value)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen_refs: set[str] = set()
    for signal in signals:
        if type(signal) is not MarketResearchPolicyShutdownRiskDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchPolicyShutdownRiskDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.source_ref in seen_refs:
            raise ValueError("source_ref values must be unique")
        seen_refs.add(signal.source_ref)
    return signals


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchPolicyShutdownRiskDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    if not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    rows = value
    for row in rows:
        if type(row) is not MarketResearchPolicyShutdownRiskDigestRow:
            raise ValueError("rows must contain MarketResearchPolicyShutdownRiskDigestRow")
        _require_hard_flags("row", row)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must be deterministic")
    keys = [
        (row.market_research_key, row.policy_jurisdiction, row.policy_surface)
        for row in rows
    ]
    if len(set(keys)) != len(keys):
        raise ValueError("rows must be unique")
    return rows


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_config_versions must be a tuple")
    if not isinstance(value, tuple):
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        source_ref, config_version = item
        _require_canonical_string("source_config_versions source_ref", source_ref)
        _require_canonical_string("source_config_versions config_version", config_version)
        _require_redacted_reference("source_config_versions source_ref", source_ref)
        _require_redacted_reference(
            "source_config_versions config_version",
            config_version,
        )
        pairs.append((source_ref, config_version))
    normalized = tuple(pairs)
    expected = tuple(sorted(set(normalized)))
    if normalized != expected:
        raise ValueError("source_config_versions must be unique and deterministic")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchPolicyShutdownRiskDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    counts = value
    for count in counts:
        if type(count) is not MarketResearchPolicyShutdownRiskDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyShutdownRiskDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    expected = tuple(
        sorted(
            counts,
            key=lambda count: (-count.count, _reason_sort_key(count.reason_code)),
        )
    )
    if counts != expected:
        raise ValueError("reason_code_counts must be deterministic")
    reason_codes = [count.reason_code for count in counts]
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts must be unique")
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason in reasons:
        _require_reason_code(field_name, reason)
    expected = tuple(sorted(set(reasons), key=_reason_sort_key))
    if reasons != expected:
        raise ValueError(f"{field_name} must be unique and deterministic")
    return reasons


def _validate_row_consistency(row: MarketResearchPolicyShutdownRiskDigestRow) -> None:
    if row.signal_count <= ZERO:
        raise ValueError("signal_count must be positive for rows")
    if row.independent_source_count > row.signal_count:
        raise ValueError("independent_source_count must not exceed signal_count")
    if row.stale_signal_count > row.signal_count:
        raise ValueError("stale_signal_count must not exceed signal_count")
    expected_status = _row_status(row.reason_codes)
    if row.risk_status != expected_status:
        raise ValueError("risk_status must match reason_codes")


def _validate_report_consistency(
    report: MarketResearchPolicyShutdownRiskDigestReport,
) -> None:
    row_count = _decimal_count(len(report.rows))
    if report.policy_surface_count != row_count:
        raise ValueError("policy_surface_count must match rows")
    if report.policy_surface_count != (
        report.clear_surface_count
        + report.watch_surface_count
        + report.blocked_surface_count
    ):
        raise ValueError("policy_surface_count must match status counts")
    expected_status = _digest_status(report.rows)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.rows, report.policy_surface_count)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    elevated_count = _decimal_count(
        sum(1 for row in report.rows if ELEVATED_PROBABILITY_REASON in row.reason_codes),
    )
    stale_count = _decimal_count(
        sum(1 for row in report.rows if STALE_SIGNAL_REASON in row.reason_codes),
    )
    thin_count = _decimal_count(
        sum(1 for row in report.rows if THIN_SOURCE_REASON in row.reason_codes),
    )
    if report.elevated_surface_count != elevated_count:
        raise ValueError("elevated_surface_count must match rows")
    if report.stale_signal_surface_count != stale_count:
        raise ValueError("stale_signal_surface_count must match rows")
    if report.thin_source_surface_count != thin_count:
        raise ValueError("thin_source_surface_count must match rows")
    expected_ratio = _ratio(
        report.elevated_surface_count,
        report.policy_surface_count,
    )
    if report.shutdown_risk_surface_ratio != expected_ratio:
        raise ValueError("shutdown_risk_surface_ratio must match rows")


def _row_status_count(
    rows: tuple[MarketResearchPolicyShutdownRiskDigestRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.risk_status == status)


def _row_sort_key(row: MarketResearchPolicyShutdownRiskDigestRow) -> tuple[int, str, str, str]:
    return (
        STATUS_RANK[row.risk_status],
        row.policy_jurisdiction,
        row.policy_surface,
        row.market_research_key,
    )


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    return (REASON_RANK.get(reason_code, len(REASON_RANK)), reason_code)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} is unknown")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} is invalid")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty trimmed string")


def _require_exact_type(
    label: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_redacted_reference(field_name: str, value: str) -> None:
    lowered = value.lower()
    fragments = (
        "wal" + "let",
        "acc" + "ount",
        "tok" + "en",
        "sec" + "ret",
        "private" + "_" + "key",
        "0x",
    )
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"{field_name} must be redacted")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_payload_decimal(field_name: str, value: object) -> None:
    if (
        type(value) is not Decimal
        or not value.is_finite()
        or not value.same_quantum(QUANT)
    ):
        raise ValueError(f"{field_name} must be a six-decimal Decimal")


def _require_payload_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a UTC-aware datetime")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{label} {flag} must be True")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_UP)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANT, rounding=ROUND_HALF_UP)


def _validate_payload_public_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        _require_payload_decimal(field_name, value)
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    if type(value) is datetime:
        _require_payload_datetime(field_name, value)
        return
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if is_dataclass(value) and not isinstance(value, type):
        _validate_payload_public_dataclass(value)
        for field in fields(value):
            _validate_payload_public_value(field.name, getattr(value, field.name))
        return
    if type(value) is tuple:
        for item in value:
            _validate_payload_public_value(field_name, item)
        return
    if value is None or type(value) in {str, bool}:
        return
    raise ValueError("payload contains unsupported public value")


def _validate_payload_public_dataclass(value: object) -> None:
    if type(value) is MarketResearchPolicyShutdownRiskDigestConfig:
        _validate_payload_config(value)
        return
    if type(value) is MarketResearchPolicyShutdownRiskDigestSignal:
        _validate_payload_signal(value)
        return
    if type(value) is MarketResearchPolicyShutdownRiskDigestRow:
        _validate_payload_row(value)
        return
    if type(value) is MarketResearchPolicyShutdownRiskDigestReasonCodeCount:
        _validate_payload_reason_code_count(value)
        return
    if type(value) is MarketResearchPolicyShutdownRiskDigestReport:
        _validate_payload_report(value)
        return
    raise ValueError("payload contains unsupported public dataclass")


def _validate_payload_config(
    value: MarketResearchPolicyShutdownRiskDigestConfig,
) -> None:
    _require_canonical_string("config_version", value.config_version)
    _require_ratio_decimal(
        "elevated_shutdown_probability_threshold",
        value.elevated_shutdown_probability_threshold,
    )
    _require_ratio_decimal("material_impact_threshold", value.material_impact_threshold)
    _require_positive_decimal(
        "fresh_signal_max_age_seconds",
        value.fresh_signal_max_age_seconds,
    )
    _require_positive_count_decimal(
        "min_independent_source_count",
        value.min_independent_source_count,
    )
    _require_hard_flags("config", value)


def _validate_payload_signal(
    value: MarketResearchPolicyShutdownRiskDigestSignal,
) -> None:
    for field_name in (
        "market_research_key",
        "policy_jurisdiction",
        "policy_surface",
        "source_ref",
        "source_family",
        "signal_config_version",
    ):
        field_value = getattr(value, field_name)
        _require_canonical_string(field_name, field_value)
        _require_redacted_reference(field_name, field_value)
    _require_payload_datetime("observed_at", value.observed_at)
    for field_name in (
        "shutdown_probability",
        "impact_score",
        "source_confidence",
    ):
        _require_ratio_decimal(field_name, getattr(value, field_name))
    _require_hard_flags("signal", value)


def _validate_payload_row(
    value: MarketResearchPolicyShutdownRiskDigestRow,
) -> None:
    for field_name in (
        "market_research_key",
        "policy_jurisdiction",
        "policy_surface",
    ):
        field_value = getattr(value, field_name)
        _require_canonical_string(field_name, field_value)
        _require_redacted_reference(field_name, field_value)
    _require_member("risk_status", value.risk_status, RISK_STATUSES)
    _normalize_reason_codes("reason_codes", value.reason_codes)
    _validate_row_consistency(value)
    _require_hard_flags("row", value)


def _validate_payload_reason_code_count(
    value: MarketResearchPolicyShutdownRiskDigestReasonCodeCount,
) -> None:
    _require_reason_code("reason_code", value.reason_code)
    _require_positive_decimal("count", value.count)
    _require_ratio_decimal("surface_ratio", value.surface_ratio)
    _require_hard_flags("reason_code_count", value)


def _validate_payload_report(
    value: MarketResearchPolicyShutdownRiskDigestReport,
) -> None:
    _require_payload_datetime("generated_at", value.generated_at)
    _require_canonical_string("config_version", value.config_version)
    _require_member("digest_status", value.digest_status, RISK_STATUSES)
    _require_canonical_string("recommended_next_step", value.recommended_next_step)
    _normalize_rows(value.rows)
    _normalize_source_config_versions(value.source_config_versions)
    _normalize_reason_code_counts(value.reason_code_counts)
    _normalize_reason_codes("reason_codes", value.reason_codes)
    _validate_report_consistency(value)
    _require_hard_flags("report", value)


def _to_payload(value: object, field_name: str = "payload") -> Any:
    if type(value) is Decimal:
        _require_payload_decimal(field_name, value)
        return f"{value:.6f}"
    if type(value) is datetime:
        _require_payload_datetime(field_name, value)
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _validate_payload_public_dataclass(value)
        return {
            field.name: _to_payload(getattr(value, field.name), field.name)
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return tuple(_to_payload(item, field_name) for item in value)
    if value is None or type(value) in {str, bool}:
        return value
    raise ValueError("payload contains unsupported public value")
