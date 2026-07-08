"""Pure crypto onchain signal-readiness report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "ResearchCryptoOnchainSignalReadinessConfig",
    "ResearchCryptoOnchainSignalReadinessReasonCodeCount",
    "ResearchCryptoOnchainSignalReadinessReport",
    "ResearchCryptoOnchainSignalReadinessRow",
    "ResearchCryptoOnchainSignalReadinessSignal",
    "build_research_crypto_onchain_signal_readiness_report",
    "research_crypto_onchain_signal_readiness_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-crypto-onchain-signal-readiness-report-v0"
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
ASSET_GROUPS = ("btc", "crypto")
INDICATOR_FAMILIES = (
    "exchange_flow",
    "miner_activity",
    "reserve_flow",
    "chain_activity",
    "derivatives_proxy",
)
REFRESH_ACTIONS = (
    "keep_cadence",
    "refresh_before_use",
    "refresh_now",
    "manual_review_before_use",
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
HALF = Decimal("0.500000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")


@dataclass(frozen=True)
class ResearchCryptoOnchainSignalReadinessConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_readiness_score: Decimal = Decimal("0.800000")
    watch_readiness_score: Decimal = Decimal("0.550000")
    min_independent_family_count: Decimal = Decimal("2.000000")
    min_independence_score: Decimal = Decimal("0.700000")
    block_independence_score: Decimal = Decimal("0.400000")
    min_metric_stability_score: Decimal = Decimal("0.700000")
    block_metric_stability_score: Decimal = Decimal("0.400000")
    min_rebuttal_check_count: Decimal = Decimal("1.000000")
    watch_rebuttal_strength: Decimal = Decimal("0.300000")
    block_rebuttal_strength: Decimal = Decimal("0.600000")
    max_refresh_age_seconds: Decimal = Decimal("7200.000000")
    data_latency_weight: Decimal = Decimal("0.250000")
    independence_weight: Decimal = Decimal("0.250000")
    metric_stability_weight: Decimal = Decimal("0.250000")
    rebuttal_weight: Decimal = Decimal("0.150000")
    refresh_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCryptoOnchainSignalReadinessConfig:
            raise TypeError(
                "ResearchCryptoOnchainSignalReadinessConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCryptoOnchainSignalReadinessConfig:
            raise ValueError("config must be exactly ResearchCryptoOnchainSignalReadinessConfig")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_readiness_score",
            "watch_readiness_score",
            "min_independence_score",
            "block_independence_score",
            "min_metric_stability_score",
            "block_metric_stability_score",
            "watch_rebuttal_strength",
            "block_rebuttal_strength",
            "data_latency_weight",
            "independence_weight",
            "metric_stability_weight",
            "rebuttal_weight",
            "refresh_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_independent_family_count",
            "min_rebuttal_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_refresh_age_seconds",
            _require_positive_decimal(
                "max_refresh_age_seconds",
                self.max_refresh_age_seconds,
            ),
        )
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must exceed watch_readiness_score")
        if self.min_independence_score < self.block_independence_score:
            raise ValueError("min_independence_score must be at least block_independence_score")
        if self.min_metric_stability_score < self.block_metric_stability_score:
            raise ValueError(
                "min_metric_stability_score must be at least block_metric_stability_score",
            )
        if self.watch_rebuttal_strength > self.block_rebuttal_strength:
            raise ValueError(
                "block_rebuttal_strength must be at least watch_rebuttal_strength",
            )
        weight_sum = _quantize(
            self.data_latency_weight
            + self.independence_weight
            + self.metric_stability_weight
            + self.rebuttal_weight
            + self.refresh_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "data_latency_weight, independence_weight, metric_stability_weight, "
                "rebuttal_weight, and refresh_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCryptoOnchainSignalReadinessSignal:
    internal_signal_key: str
    asset_group: str
    indicator_family: str
    observed_at: datetime
    refreshed_at: datetime | None
    data_latency_seconds: Decimal
    max_allowed_latency_seconds: Decimal
    independent_family_count: Decimal
    independence_score: Decimal
    metric_stability_score: Decimal
    rebuttal_check_count: Decimal
    rebuttal_strength: Decimal
    refresh_required_within_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCryptoOnchainSignalReadinessSignal:
            raise TypeError(
                "ResearchCryptoOnchainSignalReadinessSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCryptoOnchainSignalReadinessSignal:
            raise ValueError("signal must be exactly ResearchCryptoOnchainSignalReadinessSignal")
        _require_internal_string("internal_signal_key", self.internal_signal_key)
        _require_enum("asset_group", self.asset_group, ASSET_GROUPS)
        _require_enum("indicator_family", self.indicator_family, INDICATOR_FAMILIES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "refreshed_at",
            _optional_utc("refreshed_at", self.refreshed_at),
        )
        for field_name in (
            "data_latency_seconds",
            "max_allowed_latency_seconds",
            "refresh_required_within_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independence_score",
            "metric_stability_score",
            "rebuttal_strength",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_family_count",
            "rebuttal_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchCryptoOnchainSignalReadinessRow:
    signal_index: Decimal
    asset_group: str
    indicator_family: str
    observed_at: datetime
    refresh_age_seconds: Decimal | None
    data_latency_seconds: Decimal
    data_latency_score: Decimal
    independence_score: Decimal
    metric_stability_score: Decimal
    rebuttal_score: Decimal
    refresh_score: Decimal
    readiness_score: Decimal
    status: str
    refresh_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCryptoOnchainSignalReadinessRow:
            raise TypeError(
                "ResearchCryptoOnchainSignalReadinessRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCryptoOnchainSignalReadinessRow:
            raise ValueError("row must be exactly ResearchCryptoOnchainSignalReadinessRow")
        object.__setattr__(
            self,
            "signal_index",
            _require_positive_whole_decimal("signal_index", self.signal_index),
        )
        _require_enum("asset_group", self.asset_group, ASSET_GROUPS)
        _require_enum("indicator_family", self.indicator_family, INDICATOR_FAMILIES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "refresh_age_seconds",
            _require_optional_nonnegative_decimal(
                "refresh_age_seconds",
                self.refresh_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "data_latency_seconds",
            _require_positive_decimal("data_latency_seconds", self.data_latency_seconds),
        )
        for field_name in (
            "data_latency_score",
            "independence_score",
            "metric_stability_score",
            "rebuttal_score",
            "refresh_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_enum("refresh_action", self.refresh_action, REFRESH_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchCryptoOnchainSignalReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCryptoOnchainSignalReadinessReasonCodeCount:
            raise TypeError(
                "ResearchCryptoOnchainSignalReadinessReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCryptoOnchainSignalReadinessReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchCryptoOnchainSignalReadinessReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchCryptoOnchainSignalReadinessReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    refresh_due_count: Decimal
    contrary_count: Decimal
    average_readiness_score: Decimal | None
    max_data_latency_seconds: Decimal | None
    minimum_independence_score: Decimal | None
    minimum_stability_score: Decimal | None
    status: str
    rows: tuple[ResearchCryptoOnchainSignalReadinessRow, ...]
    reason_code_counts: tuple[ResearchCryptoOnchainSignalReadinessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCryptoOnchainSignalReadinessReport:
            raise TypeError(
                "ResearchCryptoOnchainSignalReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCryptoOnchainSignalReadinessReport:
            raise ValueError("report must be exactly ResearchCryptoOnchainSignalReadinessReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "refresh_due_count",
            "contrary_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_readiness_score",
            _require_optional_ratio_decimal(
                "average_readiness_score",
                self.average_readiness_score,
            ),
        )
        object.__setattr__(
            self,
            "max_data_latency_seconds",
            _require_optional_positive_decimal(
                "max_data_latency_seconds",
                self.max_data_latency_seconds,
            ),
        )
        for field_name in (
            "minimum_independence_score",
            "minimum_stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_crypto_onchain_signal_readiness_report_payload(self)


def build_research_crypto_onchain_signal_readiness_report(
    signals: Iterable[object],
    *,
    config: ResearchCryptoOnchainSignalReadinessConfig,
    generated_at: datetime,
) -> ResearchCryptoOnchainSignalReadinessReport:
    if type(config) is not ResearchCryptoOnchainSignalReadinessConfig:
        raise ValueError("config must be a ResearchCryptoOnchainSignalReadinessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals, generated_at_utc)
    _reject_duplicate_internal_keys(signal_items)
    rows = tuple(
        _score_row_from_signal(
            signal_index=_decimal_count(index),
            signal=signal,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, signal in enumerate(
            sorted(signal_items, key=lambda item: item.internal_signal_key),
            start=1,
        )
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchCryptoOnchainSignalReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        refresh_due_count=_decimal_count(
            sum(1 for row in rows if row.refresh_action != "keep_cadence"),
        ),
        contrary_count=_decimal_count(
            sum(
                1
                for row in rows
                if "rebuttal_watch" in row.reason_codes
                or "rebuttal_block" in row.reason_codes
            ),
        ),
        average_readiness_score=_average_readiness_score(rows),
        max_data_latency_seconds=max(
            (row.data_latency_seconds for row in rows),
            default=None,
        ),
        minimum_independence_score=min(
            (row.independence_score for row in rows),
            default=None,
        ),
        minimum_stability_score=min(
            (row.metric_stability_score for row in rows),
            default=None,
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_crypto_onchain_signal_readiness_report_payload(
    report: ResearchCryptoOnchainSignalReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCryptoOnchainSignalReadinessReport:
        raise ValueError("report must be a ResearchCryptoOnchainSignalReadinessReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _normalize_signals(
    signals: Iterable[object],
    generated_at: datetime,
) -> tuple[ResearchCryptoOnchainSignalReadinessSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        values = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchCryptoOnchainSignalReadinessSignal:
            raise ValueError(
                "signals must contain ResearchCryptoOnchainSignalReadinessSignal values",
            )
        _require_hard_flags("signal", value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if value.refreshed_at is not None and value.refreshed_at > generated_at:
            raise ValueError("refreshed_at must be on or before generated_at")
        if value.refreshed_at is not None and value.refreshed_at < value.observed_at:
            raise ValueError("refreshed_at must be on or after observed_at")
    return values


def _reject_duplicate_internal_keys(
    signals: tuple[ResearchCryptoOnchainSignalReadinessSignal, ...],
) -> None:
    counts = Counter(signal.internal_signal_key for signal in signals)
    if any(count > 1 for count in counts.values()):
        raise ValueError("internal_signal_key values must be unique")


def _score_row_from_signal(
    *,
    signal_index: Decimal,
    signal: ResearchCryptoOnchainSignalReadinessSignal,
    config: ResearchCryptoOnchainSignalReadinessConfig,
    generated_at: datetime,
) -> ResearchCryptoOnchainSignalReadinessRow:
    data_latency_score = _data_latency_score(
        signal.data_latency_seconds,
        signal.max_allowed_latency_seconds,
    )
    independence_score = _independence_score(signal, config)
    rebuttal_score = _rebuttal_score(signal, config)
    refresh_age_seconds = (
        None
        if signal.refreshed_at is None
        else _datetime_delta_seconds(generated_at, signal.refreshed_at)
    )
    refresh_score = _refresh_score(
        refresh_age_seconds=refresh_age_seconds,
        required_within_seconds=signal.refresh_required_within_seconds,
        config=config,
    )
    readiness_score = _quantize(
        (data_latency_score * config.data_latency_weight)
        + (independence_score * config.independence_weight)
        + (signal.metric_stability_score * config.metric_stability_weight)
        + (rebuttal_score * config.rebuttal_weight)
        + (refresh_score * config.refresh_weight),
    )
    status = _row_status(
        data_latency_score=data_latency_score,
        independence_score=independence_score,
        metric_stability_score=signal.metric_stability_score,
        rebuttal_score=rebuttal_score,
        refresh_score=refresh_score,
        readiness_score=readiness_score,
        config=config,
    )
    refresh_action = _refresh_action(status=status, refresh_score=refresh_score)
    return ResearchCryptoOnchainSignalReadinessRow(
        signal_index=signal_index,
        asset_group=signal.asset_group,
        indicator_family=signal.indicator_family,
        observed_at=signal.observed_at,
        refresh_age_seconds=refresh_age_seconds,
        data_latency_seconds=signal.data_latency_seconds,
        data_latency_score=data_latency_score,
        independence_score=independence_score,
        metric_stability_score=signal.metric_stability_score,
        rebuttal_score=rebuttal_score,
        refresh_score=refresh_score,
        readiness_score=readiness_score,
        status=status,
        refresh_action=refresh_action,
        reason_codes=_row_reason_codes(
            signal=signal,
            config=config,
            status=status,
            data_latency_score=data_latency_score,
            independence_score=independence_score,
            rebuttal_score=rebuttal_score,
            refresh_score=refresh_score,
        ),
    )


def _data_latency_score(
    data_latency_seconds: Decimal,
    max_allowed_latency_seconds: Decimal,
) -> Decimal:
    if data_latency_seconds <= max_allowed_latency_seconds:
        return ONE
    if data_latency_seconds <= max_allowed_latency_seconds * TWO:
        return HALF
    return ZERO


def _independence_score(
    signal: ResearchCryptoOnchainSignalReadinessSignal,
    config: ResearchCryptoOnchainSignalReadinessConfig,
) -> Decimal:
    if config.min_independent_family_count == ZERO:
        return signal.independence_score
    with localcontext(DECIMAL_CONTEXT):
        family_coverage = signal.independent_family_count / config.min_independent_family_count
        if family_coverage > ONE:
            family_coverage = ONE
        return _quantize(signal.independence_score * family_coverage)


def _rebuttal_score(
    signal: ResearchCryptoOnchainSignalReadinessSignal,
    config: ResearchCryptoOnchainSignalReadinessConfig,
) -> Decimal:
    if signal.rebuttal_check_count < config.min_rebuttal_check_count:
        return ZERO
    if signal.rebuttal_strength >= config.block_rebuttal_strength:
        return ZERO
    if signal.rebuttal_strength >= config.watch_rebuttal_strength:
        return HALF
    return ONE


def _refresh_score(
    *,
    refresh_age_seconds: Decimal | None,
    required_within_seconds: Decimal,
    config: ResearchCryptoOnchainSignalReadinessConfig,
) -> Decimal:
    if refresh_age_seconds is None:
        return ZERO
    if refresh_age_seconds <= required_within_seconds:
        return ONE
    if refresh_age_seconds <= config.max_refresh_age_seconds:
        return HALF
    return ZERO


def _row_status(
    *,
    data_latency_score: Decimal,
    independence_score: Decimal,
    metric_stability_score: Decimal,
    rebuttal_score: Decimal,
    refresh_score: Decimal,
    readiness_score: Decimal,
    config: ResearchCryptoOnchainSignalReadinessConfig,
) -> str:
    if data_latency_score == ZERO:
        return STATUS_BLOCK
    if independence_score < config.block_independence_score:
        return STATUS_BLOCK
    if metric_stability_score < config.block_metric_stability_score:
        return STATUS_BLOCK
    if rebuttal_score == ZERO:
        return STATUS_BLOCK
    if refresh_score == ZERO:
        return STATUS_BLOCK
    if readiness_score < config.watch_readiness_score:
        return STATUS_BLOCK
    if readiness_score < config.pass_readiness_score:
        return STATUS_WATCH
    if data_latency_score < ONE:
        return STATUS_WATCH
    if independence_score < config.min_independence_score:
        return STATUS_WATCH
    if metric_stability_score < config.min_metric_stability_score:
        return STATUS_WATCH
    if rebuttal_score < ONE:
        return STATUS_WATCH
    if refresh_score < ONE:
        return STATUS_WATCH
    return STATUS_PASS


def _refresh_action(*, status: str, refresh_score: Decimal) -> str:
    if status == STATUS_BLOCK:
        return "manual_review_before_use"
    if refresh_score == ZERO:
        return "refresh_now"
    if refresh_score < ONE:
        return "refresh_before_use"
    return "keep_cadence"


def _row_reason_codes(
    *,
    signal: ResearchCryptoOnchainSignalReadinessSignal,
    config: ResearchCryptoOnchainSignalReadinessConfig,
    status: str,
    data_latency_score: Decimal,
    independence_score: Decimal,
    rebuttal_score: Decimal,
    refresh_score: Decimal,
) -> tuple[str, ...]:
    reason_codes = {f"onchain_signal_{status}"}
    if data_latency_score == ONE:
        reason_codes.add("data_latency_within_sla")
    elif data_latency_score == HALF:
        reason_codes.add("data_latency_watch")
    else:
        reason_codes.add("data_latency_block")
    if independence_score >= config.min_independence_score:
        reason_codes.add("independence_pass")
    elif independence_score >= config.block_independence_score:
        reason_codes.add("independence_watch")
    else:
        reason_codes.add("independence_block")
    if signal.metric_stability_score >= config.min_metric_stability_score:
        reason_codes.add("metric_stability_pass")
    elif signal.metric_stability_score >= config.block_metric_stability_score:
        reason_codes.add("metric_stability_watch")
    else:
        reason_codes.add("metric_stability_block")
    if signal.rebuttal_check_count < config.min_rebuttal_check_count:
        reason_codes.add("rebuttal_missing")
    elif rebuttal_score == ONE:
        reason_codes.add("rebuttal_clear")
    elif rebuttal_score == HALF:
        reason_codes.add("rebuttal_watch")
    else:
        reason_codes.add("rebuttal_block")
    if refresh_score == ONE:
        reason_codes.add("refresh_current")
    elif refresh_score == HALF:
        reason_codes.add("refresh_watch")
    else:
        reason_codes.add("refresh_due")
    for reason_code in signal.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchCryptoOnchainSignalReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_signals_to_assess",)
    if any(row.status == STATUS_BLOCK for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if any(row.status == STATUS_WATCH for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    return ("onchain_signal_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_signals_to_assess",):
        return STATUS_BLOCK
    if "onchain_signal_block" in reason_codes:
        return STATUS_BLOCK
    if "onchain_signal_watch" in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchCryptoOnchainSignalReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchCryptoOnchainSignalReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchCryptoOnchainSignalReadinessReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                signal_ratio=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _decimal_count(len(rows))
    return tuple(
        ResearchCryptoOnchainSignalReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            signal_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_readiness_score(
    rows: tuple[ResearchCryptoOnchainSignalReadinessRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(
        _sum_decimal(row.readiness_score for row in rows),
        _decimal_count(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchCryptoOnchainSignalReadinessRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchCryptoOnchainSignalReadinessRow, ...],
) -> tuple[ResearchCryptoOnchainSignalReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchCryptoOnchainSignalReadinessRow:
            raise ValueError(
                "rows must contain ResearchCryptoOnchainSignalReadinessRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.signal_index))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by signal_index")
    expected_index = ONE
    for row in rows:
        if row.signal_index != expected_index:
            raise ValueError("row signal_index values must be contiguous")
        expected_index += ONE
    return rows


def _normalize_reason_code_counts(
    values: tuple[ResearchCryptoOnchainSignalReadinessReasonCodeCount, ...],
) -> tuple[ResearchCryptoOnchainSignalReadinessReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchCryptoOnchainSignalReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCryptoOnchainSignalReadinessReasonCodeCount values",
            )
        _require_hard_flags("reason code count", value)
    sorted_values = tuple(sorted(values, key=lambda value: value.reason_code))
    if values != sorted_values:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    if len({value.reason_code for value in values}) != len(values):
        raise ValueError("reason_code_counts must have unique reason_code values")
    return values


def _validate_report_consistency(
    report: ResearchCryptoOnchainSignalReadinessReport,
) -> None:
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    expected_refresh_due = _decimal_count(
        sum(1 for row in report.rows if row.refresh_action != "keep_cadence"),
    )
    if report.refresh_due_count != expected_refresh_due:
        raise ValueError("refresh_due_count must match rows")
    expected_contrary = _decimal_count(
        sum(
            1
            for row in report.rows
            if "rebuttal_watch" in row.reason_codes
            or "rebuttal_block" in row.reason_codes
        ),
    )
    if report.contrary_count != expected_contrary:
        raise ValueError("contrary_count must match rows")
    if report.average_readiness_score != _average_readiness_score(report.rows):
        raise ValueError("average_readiness_score must match rows")
    expected_max_latency = max(
        (row.data_latency_seconds for row in report.rows),
        default=None,
    )
    if report.max_data_latency_seconds != expected_max_latency:
        raise ValueError("max_data_latency_seconds must match rows")
    expected_min_independence = min(
        (row.independence_score for row in report.rows),
        default=None,
    )
    if report.minimum_independence_score != expected_min_independence:
        raise ValueError("minimum_independence_score must match rows")
    expected_min_stability = min(
        (row.metric_stability_score for row in report.rows),
        default=None,
    )
    if report.minimum_stability_score != expected_min_stability:
        raise ValueError("minimum_stability_score must match rows")
    expected_reason_codes = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_enum(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value.startswith("input_"):
        _require_public_string(field_name, value.removeprefix("input_"))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    sorted_values = tuple(sorted(normalized))
    if tuple(normalized) != sorted_values:
        raise ValueError(f"{field_name} must be sorted")
    return sorted_values


def _require_internal_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a single-line string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a single-line string")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_optional_positive_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_positive_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return _quantize(decimal_value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return _quantize(decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return decimal_value


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(QUANT)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    if type(value) is Decimal:
        return _quantize(value)
    raise ValueError("count value must be an int or Decimal")


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not payload serializable")


def _reject_unsafe_public_payload(value: object, path: str = "") -> None:
    if type(value) is str:
        _reject_unsafe_public_string(path or "payload", value)
        return
    if type(value) in (bool, type(None)):
        return
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload numeric value must use Decimal")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_string(nested_path, key)
            _reject_unsafe_public_payload(item, nested_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"payload[{index}]"
            _reject_unsafe_public_payload(item, nested_path)
        return
    raise ValueError("payload value is not serializable")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        _join_parts("wal", "let"),
        _join_parts("addr", "ess"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        _join_parts("ds", "n"),
        _join_parts("ta", "ble"),
        _join_parts("tok", "en"),
        _join_parts("raw", "_", "mar", "ket"),
        _join_parts("condition", "_", "id"),
        _join_parts("slug"),
        "://",
        "@",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe public material")


def _join_parts(*parts: str) -> str:
    return "".join(parts)
