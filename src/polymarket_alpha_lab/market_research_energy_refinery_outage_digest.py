"""Pure Phase 1 energy refinery outage digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION = (
    "market-research-energy-refinery-outage-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_energy_refinery_outage_digest_"
PASS_REASON = f"{REASON_PREFIX}passed"
EMPTY_REASON = f"{REASON_PREFIX}empty"
MATERIAL_CAPACITY_REASON = f"{REASON_PREFIX}material_capacity_offline"
CRITICAL_CAPACITY_REASON = f"{REASON_PREFIX}critical_capacity_offline"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
LOW_CONFIDENCE_REASON = f"{REASON_PREFIX}low_confidence"
WATCH_REASON = f"{REASON_PREFIX}watch"

ROW_REASON_CODE_SEQUENCE = (
    CRITICAL_CAPACITY_REASON,
    MATERIAL_CAPACITY_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    LOW_CONFIDENCE_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    CRITICAL_CAPACITY_REASON,
    MATERIAL_CAPACITY_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    LOW_CONFIDENCE_REASON,
    WATCH_REASON,
    PASS_REASON,
    EMPTY_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "allow_report_only_energy_refinery_outage_digest",
    STATUS_WATCH: "watch_report_only_energy_refinery_outage_digest",
    STATUS_BLOCKED: "block_report_only_energy_refinery_outage_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyRefineryOutageDigestConfig",
    "MarketResearchEnergyRefineryOutageDigestInput",
    "MarketResearchEnergyRefineryOutageDigestReasonCodeCount",
    "MarketResearchEnergyRefineryOutageDigestRegionSummary",
    "MarketResearchEnergyRefineryOutageDigestReport",
    "MarketResearchEnergyRefineryOutageDigestSignal",
    "build_market_research_energy_refinery_outage_digest",
    "market_research_energy_refinery_outage_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION
    )
    material_capacity_bpd: Decimal = Decimal("150000.000000")
    critical_capacity_bpd: Decimal = Decimal("400000.000000")
    max_signal_age_seconds: Decimal = Decimal("21600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_confidence_ratio: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageDigestConfig:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyRefineryOutageDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEnergyRefineryOutageDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "material_capacity_bpd",
            "critical_capacity_bpd",
            "max_signal_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_capacity_bpd >= self.critical_capacity_bpd:
            raise ValueError("material_capacity_bpd must be below critical_capacity_bpd")
        object.__setattr__(
            self,
            "min_confidence_ratio",
            _require_ratio_decimal("min_confidence_ratio", self.min_confidence_ratio),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageDigestInput:
    refinery_key: str
    region: str
    signal_status: str
    observed_at: datetime
    offline_capacity_bpd: Decimal
    total_capacity_bpd: Decimal
    expected_restart_delay_days: Decimal
    source_count: Decimal
    confidence_ratio: Decimal
    source_ref: str
    source_config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageDigestInput:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageDigestInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyRefineryOutageDigestInput:
            raise ValueError(
                "input must be exactly MarketResearchEnergyRefineryOutageDigestInput",
            )
        for field_name in ("refinery_key", "region", "source_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("signal_status", self.signal_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "offline_capacity_bpd",
            _require_nonnegative_decimal(
                "offline_capacity_bpd",
                self.offline_capacity_bpd,
            ),
        )
        object.__setattr__(
            self,
            "total_capacity_bpd",
            _require_positive_decimal("total_capacity_bpd", self.total_capacity_bpd),
        )
        if self.offline_capacity_bpd > self.total_capacity_bpd:
            raise ValueError("offline_capacity_bpd must not exceed total_capacity_bpd")
        object.__setattr__(
            self,
            "expected_restart_delay_days",
            _require_nonnegative_decimal(
                "expected_restart_delay_days",
                self.expected_restart_delay_days,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "confidence_ratio",
            _require_ratio_decimal("confidence_ratio", self.confidence_ratio),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageDigestSignal:
    refinery_key: str
    region: str
    signal_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    offline_capacity_bpd: Decimal
    total_capacity_bpd: Decimal
    outage_capacity_ratio: Decimal
    expected_restart_delay_days: Decimal
    source_count: Decimal
    confidence_ratio: Decimal
    redacted_source_ref: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageDigestSignal:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageDigestSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyRefineryOutageDigestSignal:
            raise ValueError(
                "signal must be exactly MarketResearchEnergyRefineryOutageDigestSignal",
            )
        for field_name in ("refinery_key", "region", "redacted_source_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("signal_status", self.signal_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "offline_capacity_bpd",
            "total_capacity_bpd",
            "expected_restart_delay_days",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.total_capacity_bpd <= ZERO:
            raise ValueError("total_capacity_bpd must be positive")
        if self.offline_capacity_bpd > self.total_capacity_bpd:
            raise ValueError("offline_capacity_bpd must not exceed total_capacity_bpd")
        for field_name in ("outage_capacity_ratio", "confidence_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_signal_consistency(self)
        require_paper_only_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageDigestRegionSummary:
    region: str
    signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    offline_capacity_bpd: Decimal
    max_outage_capacity_ratio: Decimal
    max_expected_restart_delay_days: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageDigestRegionSummary:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageDigestRegionSummary does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyRefineryOutageDigestRegionSummary:
            raise ValueError(
                "region summary must be exactly "
                "MarketResearchEnergyRefineryOutageDigestRegionSummary",
            )
        _require_public_string("region", self.region)
        for field_name in (
            "signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_signal_count",
            "offline_capacity_bpd",
            "max_expected_restart_delay_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_outage_capacity_ratio",
            _require_ratio_decimal(
                "max_outage_capacity_ratio",
                self.max_outage_capacity_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        require_paper_only_flags("region summary", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyRefineryOutageDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchEnergyRefineryOutageDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    refinery_count: Decimal
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    material_outage_count: Decimal
    critical_outage_count: Decimal
    stale_signal_count: Decimal
    thin_source_count: Decimal
    low_confidence_count: Decimal
    total_offline_capacity_bpd: Decimal
    max_offline_capacity_bpd: Decimal
    max_outage_capacity_ratio: Decimal
    max_expected_restart_delay_days: Decimal
    average_confidence_ratio: Decimal
    signals: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...]
    region_summaries: tuple[MarketResearchEnergyRefineryOutageDigestRegionSummary, ...]
    source_config_versions: tuple[tuple[str, str, str], ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageDigestReport:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyRefineryOutageDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchEnergyRefineryOutageDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "refinery_count",
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "material_outage_count",
            "critical_outage_count",
            "stale_signal_count",
            "thin_source_count",
            "low_confidence_count",
            "total_offline_capacity_bpd",
            "max_offline_capacity_bpd",
            "max_expected_restart_delay_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_outage_capacity_ratio",
            "average_confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "signals", _normalize_signals(self.signals))
        object.__setattr__(
            self,
            "region_summaries",
            _normalize_region_summaries(self.region_summaries),
        )
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)


def build_market_research_energy_refinery_outage_digest(
    signals: tuple[object, ...],
    *,
    generated_at: datetime,
    config: MarketResearchEnergyRefineryOutageDigestConfig | None = None,
) -> MarketResearchEnergyRefineryOutageDigestReport:
    cfg = config or MarketResearchEnergyRefineryOutageDigestConfig()
    if type(cfg) is not MarketResearchEnergyRefineryOutageDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchEnergyRefineryOutageDigestConfig",
        )
    require_paper_only_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_signals = _normalize_inputs(signals)
    rows = tuple(
        sorted(
            (
                _build_signal(row, generated_at=generated_at_utc, config=cfg)
                for row in input_signals
            ),
            key=lambda row: (row.refinery_key, row.region, row.observed_at),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows)
    return MarketResearchEnergyRefineryOutageDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        refinery_count=_decimal_count(len({row.refinery_key for row in rows})),
        signal_count=_decimal_count(len(rows)),
        pass_signal_count=_status_count(rows, STATUS_PASS),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        material_outage_count=_reason_count(MATERIAL_CAPACITY_REASON, rows),
        critical_outage_count=_reason_count(CRITICAL_CAPACITY_REASON, rows),
        stale_signal_count=_reason_count(STALE_SIGNAL_REASON, rows),
        thin_source_count=_reason_count(THIN_SOURCES_REASON, rows),
        low_confidence_count=_reason_count(LOW_CONFIDENCE_REASON, rows),
        total_offline_capacity_bpd=_sum_decimal(
            row.offline_capacity_bpd for row in rows
        ),
        max_offline_capacity_bpd=_max_decimal(
            (row.offline_capacity_bpd for row in rows),
            default=ZERO,
        ),
        max_outage_capacity_ratio=_max_decimal(
            (row.outage_capacity_ratio for row in rows),
            default=ZERO,
        ),
        max_expected_restart_delay_days=_max_decimal(
            (row.expected_restart_delay_days for row in rows),
            default=ZERO,
        ),
        average_confidence_ratio=_average_decimal(
            row.confidence_ratio for row in rows
        ),
        signals=rows,
        region_summaries=_region_summaries(rows),
        source_config_versions=_source_config_versions(input_signals),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_energy_refinery_outage_digest_payload(
    report: MarketResearchEnergyRefineryOutageDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyRefineryOutageDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchEnergyRefineryOutageDigestReport",
        )
    _validate_report_consistency(report)
    return _serialize_payload(asdict(report))


def _build_signal(
    row: MarketResearchEnergyRefineryOutageDigestInput,
    *,
    generated_at: datetime,
    config: MarketResearchEnergyRefineryOutageDigestConfig,
) -> MarketResearchEnergyRefineryOutageDigestSignal:
    age_seconds = _seconds_between(generated_at, row.observed_at)
    if age_seconds < ZERO:
        raise ValueError("observed_at cannot be after generated_at")
    outage_ratio = _ratio(row.offline_capacity_bpd, row.total_capacity_bpd)
    reason_codes = _signal_reason_codes(
        row=row,
        signal_age_seconds=age_seconds,
        config=config,
    )
    return MarketResearchEnergyRefineryOutageDigestSignal(
        refinery_key=row.refinery_key,
        region=row.region,
        signal_status=_signal_status(reason_codes),
        observed_at=row.observed_at,
        signal_age_seconds=age_seconds,
        offline_capacity_bpd=_quantize(row.offline_capacity_bpd),
        total_capacity_bpd=_quantize(row.total_capacity_bpd),
        outage_capacity_ratio=outage_ratio,
        expected_restart_delay_days=_quantize(row.expected_restart_delay_days),
        source_count=_quantize(row.source_count),
        confidence_ratio=_quantize(row.confidence_ratio),
        redacted_source_ref=_redact_ref(row.source_ref),
        reason_codes=reason_codes,
    )


def _signal_reason_codes(
    *,
    row: MarketResearchEnergyRefineryOutageDigestInput,
    signal_age_seconds: Decimal,
    config: MarketResearchEnergyRefineryOutageDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.signal_status == STATUS_BLOCKED or (
        row.offline_capacity_bpd >= config.critical_capacity_bpd
    ):
        reasons.append(CRITICAL_CAPACITY_REASON)
    elif row.signal_status == STATUS_WATCH or (
        row.offline_capacity_bpd >= config.material_capacity_bpd
    ):
        reasons.append(MATERIAL_CAPACITY_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if row.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if row.confidence_ratio < config.min_confidence_ratio:
        reasons.append(LOW_CONFIDENCE_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons), sequence=ROW_REASON_CODE_SEQUENCE)


def _signal_status(reason_codes: tuple[str, ...]) -> str:
    if CRITICAL_CAPACITY_REASON in reason_codes or LOW_CONFIDENCE_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_reason_codes(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes}
    reasons = [
        reason
        for reason in REPORT_REASON_CODE_SEQUENCE
        if reason in present and reason != PASS_REASON
    ]
    if any(row.signal_status == STATUS_WATCH for row in rows):
        reasons.append(WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons), sequence=REPORT_REASON_CODE_SEQUENCE)


def _report_status(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...],
) -> str:
    if not rows or any(row.signal_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.signal_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _region_summaries(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...],
) -> tuple[MarketResearchEnergyRefineryOutageDigestRegionSummary, ...]:
    regions = tuple(sorted({row.region for row in rows}))
    summaries: list[MarketResearchEnergyRefineryOutageDigestRegionSummary] = []
    for region in regions:
        region_rows = tuple(row for row in rows if row.region == region)
        reason_codes = _report_reason_codes(region_rows)
        if reason_codes == (PASS_REASON,):
            continue
        summaries.append(
            MarketResearchEnergyRefineryOutageDigestRegionSummary(
                region=region,
                signal_count=_decimal_count(len(region_rows)),
                watch_signal_count=_status_count(region_rows, STATUS_WATCH),
                blocked_signal_count=_status_count(region_rows, STATUS_BLOCKED),
                stale_signal_count=_reason_count(STALE_SIGNAL_REASON, region_rows),
                offline_capacity_bpd=_sum_decimal(
                    row.offline_capacity_bpd for row in region_rows
                ),
                max_outage_capacity_ratio=_max_decimal(
                    (row.outage_capacity_ratio for row in region_rows),
                    default=ZERO,
                ),
                max_expected_restart_delay_days=_max_decimal(
                    (row.expected_restart_delay_days for row in region_rows),
                    default=ZERO,
                ),
                reason_codes=reason_codes,
            ),
        )
    return tuple(summaries)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...],
) -> tuple[MarketResearchEnergyRefineryOutageDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ZERO,
                signal_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(reason_code, rows),
            signal_ratio=_ratio(_reason_count(reason_code, rows), total),
        )
        for reason_code in reason_codes
    )


def _reason_count(
    reason_code: str,
    rows: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...],
) -> Decimal:
    if reason_code == WATCH_REASON:
        return _status_count(rows, STATUS_WATCH)
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.signal_status == status))


def _source_config_versions(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestInput, ...],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        sorted(
            {
                (
                    row.refinery_key,
                    row.region,
                    row.source_config_version,
                )
                for row in rows
            },
        ),
    )


def _normalize_inputs(
    rows: tuple[object, ...],
) -> tuple[MarketResearchEnergyRefineryOutageDigestInput, ...]:
    if type(rows) is not tuple:
        raise ValueError("signals must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyRefineryOutageDigestInput:
            raise ValueError(
                "signals must contain MarketResearchEnergyRefineryOutageDigestInput",
            )
    return rows


def _normalize_signals(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...],
) -> tuple[MarketResearchEnergyRefineryOutageDigestSignal, ...]:
    if type(rows) is not tuple:
        raise ValueError("signals must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyRefineryOutageDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchEnergyRefineryOutageDigestSignal",
            )
    return tuple(sorted(rows, key=lambda row: (row.refinery_key, row.region, row.observed_at)))


def _normalize_region_summaries(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestRegionSummary, ...],
) -> tuple[MarketResearchEnergyRefineryOutageDigestRegionSummary, ...]:
    if type(rows) is not tuple:
        raise ValueError("region_summaries must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyRefineryOutageDigestRegionSummary:
            raise ValueError(
                "region_summaries must contain "
                "MarketResearchEnergyRefineryOutageDigestRegionSummary",
            )
    return tuple(sorted(rows, key=lambda row: row.region))


def _normalize_source_config_versions(
    rows: tuple[tuple[str, str, str], ...],
) -> tuple[tuple[str, str, str], ...]:
    if type(rows) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str, str]] = []
    for row in rows:
        if type(row) is not tuple or len(row) != 3:
            raise ValueError("source_config_versions rows must be three-item tuples")
        refinery_key, region, version = row
        _require_public_string("source_config_versions refinery_key", refinery_key)
        _require_public_string("source_config_versions region", region)
        _require_canonical_string("source_config_versions version", version)
        normalized.append((refinery_key, region, version))
    return tuple(sorted(normalized))


def _normalize_reason_code_counts(
    rows: tuple[MarketResearchEnergyRefineryOutageDigestReasonCodeCount, ...],
) -> tuple[MarketResearchEnergyRefineryOutageDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyRefineryOutageDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyRefineryOutageDigestReasonCodeCount",
            )
    return tuple(
        sorted(
            rows,
            key=lambda row: REPORT_REASON_CODE_SEQUENCE.index(row.reason_code),
        ),
    )


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in sequence:
            raise ValueError("unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in sequence if reason_code in seen)


def _validate_signal_consistency(
    row: MarketResearchEnergyRefineryOutageDigestSignal,
) -> None:
    if row.signal_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass signals must only use passed reason")
    if row.signal_status == STATUS_BLOCKED and not any(
        reason in row.reason_codes
        for reason in (CRITICAL_CAPACITY_REASON, LOW_CONFIDENCE_REASON)
    ):
        raise ValueError("blocked signals must include blocked severity reason")
    if row.signal_status == STATUS_WATCH and not any(
        reason in row.reason_codes
        for reason in (MATERIAL_CAPACITY_REASON, STALE_SIGNAL_REASON, THIN_SOURCES_REASON)
    ):
        raise ValueError("watch signals must include watch reason")


def _validate_report_consistency(
    report: MarketResearchEnergyRefineryOutageDigestReport,
) -> None:
    if report.signal_count != _decimal_count(len(report.signals)):
        raise ValueError("signal_count must match signals")
    if report.refinery_count != _decimal_count(
        len({row.refinery_key for row in report.signals}),
    ):
        raise ValueError("refinery_count must match signals")
    if report.pass_signal_count != _status_count(report.signals, STATUS_PASS):
        raise ValueError("pass_signal_count must match signals")
    if report.watch_signal_count != _status_count(report.signals, STATUS_WATCH):
        raise ValueError("watch_signal_count must match signals")
    if report.blocked_signal_count != _status_count(report.signals, STATUS_BLOCKED):
        raise ValueError("blocked_signal_count must match signals")
    if report.digest_status != _report_status(report.signals):
        raise ValueError("digest_status must match signals")
    if report.reason_codes != _report_reason_codes(report.signals):
        raise ValueError("reason_codes must match signals")


def _serialize_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        return {key: _serialize_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_payload(item) for item in value]
    raise ValueError("payload value is not supported")


def _redact_ref(value: str) -> str:
    if _is_public_ref(value):
        return value
    return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"


def _is_public_ref(value: str) -> bool:
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    return value.startswith("public_") and all(character in allowed for character in value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(value / total)


def _average_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(_sum_decimal(items), _decimal_count(len(items)))


def _sum_decimal(values: object) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return _quantize(total)


def _max_decimal(values: object, *, default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return _quantize(max(items))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith(REASON_PREFIX):
        raise ValueError(f"{field_name} must use refinery outage digest prefix")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    return value


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value
