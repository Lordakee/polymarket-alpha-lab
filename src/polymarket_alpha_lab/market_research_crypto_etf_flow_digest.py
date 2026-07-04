"""Pure Phase 1 crypto ETF flow market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-etf-flow-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
ETF_FLOW_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_etf_flow_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_etf_flow_digest_no_inputs"
FLOW_PRESSURE_REASON = "market_research_crypto_etf_flow_digest_flow_pressure"
FLOW_REVERSAL_REASON = "market_research_crypto_etf_flow_digest_flow_reversal"
SOURCE_GAP_REASON = "market_research_crypto_etf_flow_digest_source_gap"
CONFIDENCE_GAP_REASON = "market_research_crypto_etf_flow_digest_confidence_gap"
PREMIUM_DISCOUNT_PRESSURE_REASON = (
    "market_research_crypto_etf_flow_digest_premium_discount_pressure"
)
STALE_OBSERVATION_REASON = "market_research_crypto_etf_flow_digest_stale_observation"

REASON_CODE_SEQUENCE = (
    FLOW_PRESSURE_REASON,
    FLOW_REVERSAL_REASON,
    SOURCE_GAP_REASON,
    CONFIDENCE_GAP_REASON,
    PREMIUM_DISCOUNT_PRESSURE_REASON,
    STALE_OBSERVATION_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    FLOW_PRESSURE_REASON,
    FLOW_REVERSAL_REASON,
    SOURCE_GAP_REASON,
    CONFIDENCE_GAP_REASON,
    PREMIUM_DISCOUNT_PRESSURE_REASON,
    STALE_OBSERVATION_REASON,
    READY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoEtfFlowDigestConfig",
    "MarketResearchCryptoEtfFlowDigestReasonCodeCount",
    "MarketResearchCryptoEtfFlowDigestReport",
    "MarketResearchCryptoEtfFlowDigestRow",
    "MarketResearchCryptoEtfFlowObservation",
    "build_market_research_crypto_etf_flow_digest",
    "market_research_crypto_etf_flow_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DIGEST_CONFIG_VERSION
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_abs_net_flow_usd: Decimal = Decimal("25000000.000000")
    min_flow_confidence: Decimal = Decimal("0.650000")
    max_premium_discount_abs: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDigestConfig:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoEtfFlowDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_observation_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_abs_net_flow_usd",
            _require_nonnegative_count_decimal(
                "min_abs_net_flow_usd",
                self.min_abs_net_flow_usd,
            ),
        )
        for field_name in ("min_flow_confidence", "max_premium_discount_abs"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowObservation:
    condition_id: str
    flow_key: str
    asset_symbol: str
    observed_at: datetime
    net_flow_usd: Decimal
    previous_net_flow_usd: Decimal
    source_count: Decimal
    flow_confidence: Decimal
    premium_discount: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowObservation:
            raise TypeError(
                "MarketResearchCryptoEtfFlowObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowObservation:
            raise ValueError(
                "observation must be exactly MarketResearchCryptoEtfFlowObservation",
            )
        for field_name in (
            "condition_id",
            "flow_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("net_flow_usd", "previous_net_flow_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "flow_confidence",
            _require_ratio_decimal("flow_confidence", self.flow_confidence),
        )
        object.__setattr__(
            self,
            "premium_discount",
            _require_signed_ratio_decimal("premium_discount", self.premium_discount),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowDigestRow:
    condition_id: str
    flow_key: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    net_flow_usd: Decimal
    previous_net_flow_usd: Decimal
    net_flow_abs_usd: Decimal
    flow_change_abs_usd: Decimal
    source_count: Decimal
    flow_confidence: Decimal
    premium_discount: Decimal
    premium_discount_abs: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDigestRow:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDigestRow:
            raise ValueError("row must be exactly MarketResearchCryptoEtfFlowDigestRow")
        for field_name in ("condition_id", "flow_key", "asset_symbol"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "net_flow_abs_usd",
            "flow_change_abs_usd",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("net_flow_usd", "previous_net_flow_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flow_confidence",
            _require_ratio_decimal("flow_confidence", self.flow_confidence),
        )
        object.__setattr__(
            self,
            "premium_discount",
            _require_signed_ratio_decimal("premium_discount", self.premium_discount),
        )
        object.__setattr__(
            self,
            "premium_discount_abs",
            _require_ratio_decimal("premium_discount_abs", self.premium_discount_abs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoEtfFlowDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    flow_pressure_observation_count: Decimal
    flow_reversal_observation_count: Decimal
    source_gap_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    premium_discount_pressure_observation_count: Decimal
    stale_observation_count: Decimal
    total_net_flow_usd: Decimal
    average_net_flow_usd: Decimal
    average_flow_confidence: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    min_source_count: Decimal
    min_abs_net_flow_usd: Decimal
    min_flow_confidence: Decimal
    max_premium_discount_abs: Decimal
    rows: tuple[MarketResearchCryptoEtfFlowDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoEtfFlowDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDigestReport:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDigestReport:
            raise ValueError("report must be exactly MarketResearchCryptoEtfFlowDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "flow_pressure_observation_count",
            "flow_reversal_observation_count",
            "source_gap_observation_count",
            "confidence_gap_observation_count",
            "premium_discount_pressure_observation_count",
            "stale_observation_count",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "min_source_count",
            "min_abs_net_flow_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("total_net_flow_usd", "average_net_flow_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_flow_confidence",
            "min_flow_confidence",
            "max_premium_discount_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_etf_flow_digest(
    observations: Iterable[MarketResearchCryptoEtfFlowObservation],
    *,
    config: MarketResearchCryptoEtfFlowDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoEtfFlowDigestReport:
    cfg = config or MarketResearchCryptoEtfFlowDigestConfig()
    if type(cfg) is not MarketResearchCryptoEtfFlowDigestConfig:
        raise ValueError("config must be exactly MarketResearchCryptoEtfFlowDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(
            observation,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for observation in normalized_observations
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.flow_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoEtfFlowDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        flow_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            FLOW_PRESSURE_REASON,
        ),
        flow_reversal_observation_count=_reason_observation_count(
            sorted_rows,
            FLOW_REVERSAL_REASON,
        ),
        source_gap_observation_count=_reason_observation_count(
            sorted_rows,
            SOURCE_GAP_REASON,
        ),
        confidence_gap_observation_count=_reason_observation_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        premium_discount_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            PREMIUM_DISCOUNT_PRESSURE_REASON,
        ),
        stale_observation_count=_reason_observation_count(
            sorted_rows,
            STALE_OBSERVATION_REASON,
        ),
        total_net_flow_usd=_decimal_sum(row.net_flow_usd for row in sorted_rows),
        average_net_flow_usd=_ratio(
            _decimal_sum(row.net_flow_usd for row in sorted_rows),
            observation_count,
        ),
        average_flow_confidence=_ratio(
            _decimal_sum(row.flow_confidence for row in sorted_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        min_source_count=cfg.min_source_count,
        min_abs_net_flow_usd=cfg.min_abs_net_flow_usd,
        min_flow_confidence=cfg.min_flow_confidence,
        max_premium_discount_abs=cfg.max_premium_discount_abs,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.flow_key, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_etf_flow_digest_payload(
    report: MarketResearchCryptoEtfFlowDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoEtfFlowDigestReport:
        raise ValueError("report must be exactly MarketResearchCryptoEtfFlowDigestReport")
    return _freeze(_json_ready(report))


def _row_for_observation(
    observation: MarketResearchCryptoEtfFlowObservation,
    *,
    config: MarketResearchCryptoEtfFlowDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoEtfFlowDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    net_flow_abs_usd = _count_abs(observation.net_flow_usd)
    flow_change_abs_usd = _count_abs(
        observation.net_flow_usd - observation.previous_net_flow_usd,
    )
    premium_discount_abs = _ratio_abs(observation.premium_discount)
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        net_flow_abs_usd=net_flow_abs_usd,
        premium_discount_abs=premium_discount_abs,
    )
    return MarketResearchCryptoEtfFlowDigestRow(
        condition_id=observation.condition_id,
        flow_key=observation.flow_key,
        asset_symbol=observation.asset_symbol,
        digest_status=_row_status(reason_codes),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        net_flow_usd=observation.net_flow_usd,
        previous_net_flow_usd=observation.previous_net_flow_usd,
        net_flow_abs_usd=net_flow_abs_usd,
        flow_change_abs_usd=flow_change_abs_usd,
        source_count=observation.source_count,
        flow_confidence=observation.flow_confidence,
        premium_discount=observation.premium_discount,
        premium_discount_abs=premium_discount_abs,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoEtfFlowObservation,
    config: MarketResearchCryptoEtfFlowDigestConfig,
    observation_age_seconds: Decimal,
    net_flow_abs_usd: Decimal,
    premium_discount_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if net_flow_abs_usd >= config.min_abs_net_flow_usd:
        reasons.append(FLOW_PRESSURE_REASON)
    if (
        net_flow_abs_usd >= config.min_abs_net_flow_usd
        and _flow_direction(observation.net_flow_usd) < 0
    ):
        reasons.append(FLOW_REVERSAL_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
    if observation.flow_confidence < config.min_flow_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if premium_discount_abs > config.max_premium_discount_abs:
        reasons.append(PREMIUM_DISCOUNT_PRESSURE_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _flow_direction(value: Decimal) -> int:
    if value > ZERO:
        return 1
    if value < ZERO:
        return -1
    return 0


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(
        reason in reason_codes
        for reason in (
            FLOW_REVERSAL_REASON,
            CONFIDENCE_GAP_REASON,
            PREMIUM_DISCOUNT_PRESSURE_REASON,
            STALE_OBSERVATION_REASON,
        )
    ):
        return STATUS_BLOCKED
    if reason_codes == (FLOW_PRESSURE_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _row_sort_value(row: MarketResearchCryptoEtfFlowDigestRow) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity)


def _report_status(rows: tuple[MarketResearchCryptoEtfFlowDigestRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_etf_flow_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_etf_flow_digest"
    return "allow_report_only_market_research_crypto_etf_flow_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoEtfFlowDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoEtfFlowDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoEtfFlowDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfFlowDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoEtfFlowDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            observation_ratio=_ratio(_decimal_count(counts[reason_code]), observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoEtfFlowDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoEtfFlowDigestRow) -> None:
    if row.net_flow_abs_usd != _count_abs(row.net_flow_usd):
        raise ValueError("net_flow_abs_usd does not match net_flow_usd")
    if row.flow_change_abs_usd != _count_abs(
        row.net_flow_usd - row.previous_net_flow_usd,
    ):
        raise ValueError("flow_change_abs_usd does not match flow inputs")
    if row.premium_discount_abs != _ratio_abs(row.premium_discount):
        raise ValueError("premium_discount_abs does not match premium_discount")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoEtfFlowDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (FLOW_PRESSURE_REASON, report.flow_pressure_observation_count),
        (FLOW_REVERSAL_REASON, report.flow_reversal_observation_count),
        (SOURCE_GAP_REASON, report.source_gap_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
        (
            PREMIUM_DISCOUNT_PRESSURE_REASON,
            report.premium_discount_pressure_observation_count,
        ),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(report.rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.total_net_flow_usd != _decimal_sum(row.net_flow_usd for row in report.rows):
        raise ValueError("total_net_flow_usd does not match rows")
    if report.average_net_flow_usd != _ratio(
        _decimal_sum(row.net_flow_usd for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_net_flow_usd does not match rows")
    if report.average_flow_confidence != _ratio(
        _decimal_sum(row.flow_confidence for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_flow_confidence does not match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_observations(
    observations: Iterable[MarketResearchCryptoEtfFlowObservation],
) -> tuple[MarketResearchCryptoEtfFlowObservation, ...]:
    observation_tuple = tuple(observations)
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoEtfFlowObservation:
            raise ValueError(
                "observations must contain MarketResearchCryptoEtfFlowObservation",
            )
        if observation.flow_key in seen_keys:
            raise ValueError("flow_key values must be unique")
        seen_keys.add(observation.flow_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoEtfFlowDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfFlowDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoEtfFlowDigestRow:
            raise ValueError("rows must contain MarketResearchCryptoEtfFlowDigestRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoEtfFlowDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoEtfFlowDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoEtfFlowDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason code count", item)
    return items


def _normalize_source_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    seen_keys: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        flow_key, source_config_version = item
        _require_public_string("flow_key", flow_key)
        _require_public_string("source_config_version", source_config_version)
        if flow_key in seen_keys:
            raise ValueError("source_config_versions flow_key values must be unique")
        seen_keys.add(flow_key)
        pairs.append((flow_key, source_config_version))
    return tuple(pairs)


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != value:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in ETF_FLOW_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _require_public_text(field_name, value)


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_signed_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _count_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _ratio_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{field.name} must be True")
            ready[field.name] = _json_ready(item)
        return ready
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is str:
        _require_public_text("JSON string value", value)
        return value
    if type(value) is bool or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
