"""Pure Phase 1 crypto reserve digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-exchange-reserve-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_crypto_exchange_reserve_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_RESERVE_DROP_REASON = f"{REASON_PREFIX}material_reserve_drop"
STALE_SNAPSHOT_REASON = f"{REASON_PREFIX}stale_snapshot"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
HIGH_OUTFLOW_REASON = f"{REASON_PREFIX}high_outflow"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
THIN_ATTESTATION_REASON = f"{REASON_PREFIX}thin_attestation"

REASON_CODE_SEQUENCE = (
    MATERIAL_RESERVE_DROP_REASON,
    STALE_SNAPSHOT_REASON,
    PROBABILITY_REPRICING_REASON,
    HIGH_OUTFLOW_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_ATTESTATION_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_RESERVE_DROP_REASON,
    STALE_SNAPSHOT_REASON,
    PROBABILITY_REPRICING_REASON,
    HIGH_OUTFLOW_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_ATTESTATION_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_crypto_exchange_reserve_digest",
    STATUS_WATCH: "watch_report_only_market_research_crypto_exchange_reserve_digest",
    STATUS_BLOCKED: "block_report_only_market_research_crypto_exchange_reserve_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoExchangeReserveDigestConfig",
    "MarketResearchCryptoExchangeReserveDigestInputRow",
    "MarketResearchCryptoExchangeReserveDigestReasonCodeCount",
    "MarketResearchCryptoExchangeReserveDigestReport",
    "MarketResearchCryptoExchangeReserveDigestRow",
    "build_market_research_crypto_exchange_reserve_digest",
    "market_research_crypto_exchange_reserve_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DIGEST_CONFIG_VERSION
    )
    fresh_snapshot_max_age_seconds: Decimal = Decimal("7200.000000")
    material_reserve_drop_ratio: Decimal = Decimal("0.050000")
    min_attestation_count: Decimal = Decimal("2")
    high_outflow_ratio: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDigestConfig:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoExchangeReserveDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_snapshot_max_age_seconds",
            _require_positive_decimal(
                "fresh_snapshot_max_age_seconds",
                self.fresh_snapshot_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "material_reserve_drop_ratio",
            _require_ratio_decimal(
                "material_reserve_drop_ratio",
                self.material_reserve_drop_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_attestation_count",
            _require_positive_count_decimal(
                "min_attestation_count",
                self.min_attestation_count,
            ),
        )
        object.__setattr__(
            self,
            "high_outflow_ratio",
            _require_ratio_decimal("high_outflow_ratio", self.high_outflow_ratio),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDigestInputRow:
    research_key: str
    condition_id: str
    venue_key: str
    asset_key: str
    reserve_source_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    attestation_count: Decimal
    reserve_balance: Decimal
    prior_reserve_balance: Decimal
    net_flow_24h: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDigestInputRow:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchCryptoExchangeReserveDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("venue_key", self.venue_key)
        _require_public_string("asset_key", self.asset_key)
        _require_reference("reserve_source_reference", self.reserve_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "attestation_count",
            _require_nonnegative_count_decimal(
                "attestation_count",
                self.attestation_count,
            ),
        )
        for field_name in (
            "reserve_balance",
            "prior_reserve_balance",
            "net_flow_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.reserve_balance < ZERO:
            raise ValueError("reserve_balance must be nonnegative")
        if self.prior_reserve_balance < ZERO:
            raise ValueError("prior_reserve_balance must be nonnegative")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDigestRow:
    research_key: str
    condition_id: str
    venue_key: str
    asset_key: str
    reserve_status: str
    observed_at: datetime
    acknowledged_at: datetime | None
    snapshot_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    attestation_count: Decimal
    reserve_balance: Decimal
    prior_reserve_balance: Decimal
    reserve_delta: Decimal
    reserve_drop: Decimal
    reserve_drop_ratio: Decimal
    net_flow_24h: Decimal
    net_flow_24h_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    redacted_reserve_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDigestRow:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDigestRow:
            raise ValueError("row must be exactly MarketResearchCryptoExchangeReserveDigestRow")
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("venue_key", self.venue_key)
        _require_public_string("asset_key", self.asset_key)
        _require_digest_status("reserve_status", self.reserve_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal(
                "snapshot_age_seconds",
                self.snapshot_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "attestation_count",
            _require_nonnegative_count_decimal(
                "attestation_count",
                self.attestation_count,
            ),
        )
        for field_name in (
            "reserve_balance",
            "prior_reserve_balance",
            "reserve_delta",
            "reserve_drop",
            "net_flow_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("reserve_drop_ratio", "net_flow_24h_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _require_probability_delta("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "redacted_reserve_source_reference",
            _require_redacted_reference(
                "redacted_reserve_source_reference",
                self.redacted_reserve_source_reference,
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
class MarketResearchCryptoExchangeReserveDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchCryptoExchangeReserveDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "snapshot_ratio",
            _require_ratio_decimal("snapshot_ratio", self.snapshot_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reserve_snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    material_reserve_drop_count: Decimal
    stale_snapshot_count: Decimal
    high_outflow_count: Decimal
    thin_attestation_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    probability_repricing_count: Decimal
    average_reserve_drop_ratio: Decimal
    max_snapshot_age_seconds: Decimal
    average_attestation_count: Decimal
    rows: tuple[MarketResearchCryptoExchangeReserveDigestRow, ...]
    reason_code_counts: tuple[MarketResearchCryptoExchangeReserveDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDigestReport:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoExchangeReserveDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "reserve_snapshot_count",
            "ready_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "material_reserve_drop_count",
            "stale_snapshot_count",
            "high_outflow_count",
            "thin_attestation_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reserve_drop_ratio",
            "max_snapshot_age_seconds",
            "average_attestation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchCryptoExchangeReserveDigestConfig,
    MarketResearchCryptoExchangeReserveDigestInputRow,
    MarketResearchCryptoExchangeReserveDigestReasonCodeCount,
    MarketResearchCryptoExchangeReserveDigestReport,
    MarketResearchCryptoExchangeReserveDigestRow,
)


def build_market_research_crypto_exchange_reserve_digest(
    input_rows: list[MarketResearchCryptoExchangeReserveDigestInputRow]
    | tuple[MarketResearchCryptoExchangeReserveDigestInputRow, ...],
    *,
    config: MarketResearchCryptoExchangeReserveDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoExchangeReserveDigestReport:
    if type(config) is not MarketResearchCryptoExchangeReserveDigestConfig:
        raise ValueError("config must be a MarketResearchCryptoExchangeReserveDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _build_row(row, config=config, generated_at=generated_at_utc)
        for row in source_rows
    )
    ordered_rows = tuple(sorted(rows, key=_row_sort_key))
    reason_code_counts = _reason_code_counts(ordered_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ordered_rows:
        reason_code_counts = (
            MarketResearchCryptoExchangeReserveDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                snapshot_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    snapshot_count = _count(len(ordered_rows))
    ready_snapshot_count = _count(
        sum(1 for row in ordered_rows if row.reserve_status == STATUS_READY),
    )
    watch_snapshot_count = _count(
        sum(1 for row in ordered_rows if row.reserve_status == STATUS_WATCH),
    )
    blocked_snapshot_count = _count(
        sum(1 for row in ordered_rows if row.reserve_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ordered_rows),
        blocked_snapshot_count=blocked_snapshot_count,
        watch_snapshot_count=watch_snapshot_count,
    )

    return MarketResearchCryptoExchangeReserveDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        reserve_snapshot_count=snapshot_count,
        ready_snapshot_count=ready_snapshot_count,
        watch_snapshot_count=watch_snapshot_count,
        blocked_snapshot_count=blocked_snapshot_count,
        material_reserve_drop_count=_reason_count(
            ordered_rows,
            MATERIAL_RESERVE_DROP_REASON,
        ),
        stale_snapshot_count=_reason_count(ordered_rows, STALE_SNAPSHOT_REASON),
        high_outflow_count=_reason_count(ordered_rows, HIGH_OUTFLOW_REASON),
        thin_attestation_count=_reason_count(ordered_rows, THIN_ATTESTATION_REASON),
        missing_acknowledgement_count=_reason_count(
            ordered_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_count(
            ordered_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        probability_repricing_count=_reason_count(
            ordered_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        average_reserve_drop_ratio=_ratio(
            _sum_decimal(row.reserve_drop_ratio for row in ordered_rows),
            snapshot_count,
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in ordered_rows),
            default=ZERO,
        ),
        average_attestation_count=_ratio(
            _sum_decimal(row.attestation_count for row in ordered_rows),
            snapshot_count,
        ),
        rows=ordered_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_crypto_exchange_reserve_digest_payload(
    report: MarketResearchCryptoExchangeReserveDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResearchCryptoExchangeReserveDigestReport:
        _require_payload_safe_value("report", report)
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        ready = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        ready = _json_ready(report)
    else:
        raise ValueError("report must be a MarketResearchCryptoExchangeReserveDigestReport")
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(ready))
    _reject_unsafe_public_payload("payload", ready)
    return ready


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchCryptoExchangeReserveDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[tuple[str, str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchCryptoExchangeReserveDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchCryptoExchangeReserveDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        key = (
            input_row.research_key,
            input_row.condition_id,
            input_row.venue_key,
            input_row.asset_key,
        )
        if key in seen:
            raise ValueError(
                "input rows must use unique research condition venue asset keys",
            )
        seen.add(key)
        if input_row.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        if input_row.acknowledged_at is not None:
            if input_row.acknowledged_at > generated_at:
                raise ValueError("acknowledged_at cannot be after generated_at")
            if input_row.acknowledged_at < input_row.observed_at:
                raise ValueError("acknowledged_at cannot be before observed_at")
    return normalized


def _build_row(
    input_row: MarketResearchCryptoExchangeReserveDigestInputRow,
    *,
    config: MarketResearchCryptoExchangeReserveDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoExchangeReserveDigestRow:
    snapshot_age_seconds = _seconds_between(input_row.observed_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if input_row.acknowledged_at is None
        else _seconds_between(input_row.observed_at, input_row.acknowledged_at)
    )
    reserve_delta = _finite_decimal(
        input_row.reserve_balance - input_row.prior_reserve_balance,
    )
    reserve_drop = max(_finite_decimal(-reserve_delta), ZERO)
    reserve_drop_ratio = _ratio(reserve_drop, input_row.prior_reserve_balance)
    net_flow_24h_ratio = _ratio(abs(input_row.net_flow_24h), input_row.prior_reserve_balance)
    probability_delta = _probability_delta(
        input_row.market_probability_after - input_row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        attestation_count=input_row.attestation_count,
        reserve_drop_ratio=reserve_drop_ratio,
        net_flow_24h_ratio=net_flow_24h_ratio,
        probability_delta=probability_delta,
        snapshot_age_seconds=snapshot_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
    )
    return MarketResearchCryptoExchangeReserveDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        venue_key=input_row.venue_key,
        asset_key=input_row.asset_key,
        reserve_status=_row_status(reason_codes),
        observed_at=input_row.observed_at,
        acknowledged_at=input_row.acknowledged_at,
        snapshot_age_seconds=snapshot_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        attestation_count=input_row.attestation_count,
        reserve_balance=input_row.reserve_balance,
        prior_reserve_balance=input_row.prior_reserve_balance,
        reserve_delta=reserve_delta,
        reserve_drop=reserve_drop,
        reserve_drop_ratio=reserve_drop_ratio,
        net_flow_24h=input_row.net_flow_24h,
        net_flow_24h_ratio=net_flow_24h_ratio,
        market_probability_before=input_row.market_probability_before,
        market_probability_after=input_row.market_probability_after,
        probability_delta=probability_delta,
        redacted_reserve_source_reference=_redacted_reference(
            input_row.reserve_source_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    attestation_count: Decimal,
    reserve_drop_ratio: Decimal,
    net_flow_24h_ratio: Decimal,
    probability_delta: Decimal,
    snapshot_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    config: MarketResearchCryptoExchangeReserveDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if reserve_drop_ratio >= config.material_reserve_drop_ratio:
        reasons.append(MATERIAL_RESERVE_DROP_REASON)
    if snapshot_age_seconds > config.fresh_snapshot_max_age_seconds:
        reasons.append(STALE_SNAPSHOT_REASON)
    if abs(probability_delta) >= config.material_reserve_drop_ratio:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if net_flow_24h_ratio >= config.high_outflow_ratio:
        reasons.append(HIGH_OUTFLOW_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.fresh_snapshot_max_age_seconds / Decimal("4"):
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if attestation_count < config.min_attestation_count:
        reasons.append(THIN_ATTESTATION_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_snapshot_count: Decimal,
    watch_snapshot_count: Decimal,
) -> str:
    if not has_inputs:
        return STATUS_BLOCKED
    if blocked_snapshot_count > ZERO:
        return STATUS_BLOCKED
    if watch_snapshot_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_key(
    row: MarketResearchCryptoExchangeReserveDigestRow,
) -> tuple[int, str, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.reserve_status],
        row.venue_key,
        row.asset_key,
        row.condition_id,
        row.research_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoExchangeReserveDigestRow, ...],
) -> tuple[MarketResearchCryptoExchangeReserveDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    snapshot_count = _count(len(rows))
    return tuple(
        MarketResearchCryptoExchangeReserveDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            snapshot_ratio=_ratio(_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchCryptoExchangeReserveDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, str, str, str, str] | None = None
    seen: set[tuple[str, str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchCryptoExchangeReserveDigestRow:
            raise ValueError("rows must contain MarketResearchCryptoExchangeReserveDigestRow")
        _require_hard_flags("row", row)
        identity = (row.research_key, row.condition_id, row.venue_key, row.asset_key)
        if identity in seen:
            raise ValueError("rows must use unique research condition venue asset keys")
        seen.add(identity)
        key = _row_sort_key(row)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be sorted by unique status and venue asset keys")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchCryptoExchangeReserveDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_order = -1
    for count in counts:
        if type(count) is not MarketResearchCryptoExchangeReserveDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        rank = _reason_code_rank(count.reason_code)
        if rank <= previous_order:
            raise ValueError("reason_code_counts must be sorted by unique reason_code")
        previous_order = rank
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_order = -1
    for reason_code in reason_codes:
        rank = _row_reason_code_rank(reason_code)
        if rank <= previous_order:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_order = rank
    if READY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes ready cannot be combined")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_order = -1
    for reason_code in reason_codes:
        rank = _reason_code_rank(reason_code)
        if rank <= previous_order:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_order = rank
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _validate_row(row: MarketResearchCryptoExchangeReserveDigestRow) -> None:
    if row.acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError(
                "acknowledgement_lag_seconds must be None when acknowledgement is missing",
            )
    elif row.acknowledgement_lag_seconds is None:
        raise ValueError(
            "acknowledgement_lag_seconds must be present when acknowledgement is present",
        )
    if row.reserve_balance < ZERO:
        raise ValueError("reserve_balance must be nonnegative")
    if row.prior_reserve_balance < ZERO:
        raise ValueError("prior_reserve_balance must be nonnegative")
    expected_reserve_delta = _finite_decimal(row.reserve_balance - row.prior_reserve_balance)
    if row.reserve_delta != expected_reserve_delta:
        raise ValueError("reserve_delta must match reserve fields")
    if row.reserve_drop != max(_finite_decimal(-row.reserve_delta), ZERO):
        raise ValueError("reserve_drop must match reserve_delta")
    if row.reserve_drop_ratio != _ratio(row.reserve_drop, row.prior_reserve_balance):
        raise ValueError("reserve_drop_ratio must match reserve fields")
    if row.net_flow_24h_ratio != _ratio(abs(row.net_flow_24h), row.prior_reserve_balance):
        raise ValueError("net_flow_24h_ratio must match flow fields")
    expected_probability_delta = _probability_delta(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match probability fields")
    if row.reserve_status != _row_status(row.reason_codes):
        raise ValueError("reserve_status must match reason_codes")


def _validate_report(report: MarketResearchCryptoExchangeReserveDigestReport) -> None:
    if report.reserve_snapshot_count != _count(len(report.rows)):
        raise ValueError("reserve_snapshot_count must match rows")
    if report.ready_snapshot_count != _count(
        sum(1 for row in report.rows if row.reserve_status == STATUS_READY),
    ):
        raise ValueError("ready_snapshot_count must match rows")
    if report.watch_snapshot_count != _count(
        sum(1 for row in report.rows if row.reserve_status == STATUS_WATCH),
    ):
        raise ValueError("watch_snapshot_count must match rows")
    if report.blocked_snapshot_count != _count(
        sum(1 for row in report.rows if row.reserve_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_snapshot_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            MarketResearchCryptoExchangeReserveDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                snapshot_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_snapshot_count=report.blocked_snapshot_count,
        watch_snapshot_count=report.watch_snapshot_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    _validate_report_metric(
        report,
        "material_reserve_drop_count",
        MATERIAL_RESERVE_DROP_REASON,
    )
    _validate_report_metric(report, "stale_snapshot_count", STALE_SNAPSHOT_REASON)
    _validate_report_metric(report, "high_outflow_count", HIGH_OUTFLOW_REASON)
    _validate_report_metric(report, "thin_attestation_count", THIN_ATTESTATION_REASON)
    _validate_report_metric(
        report,
        "missing_acknowledgement_count",
        MISSING_ACKNOWLEDGEMENT_REASON,
    )
    _validate_report_metric(
        report,
        "slow_acknowledgement_count",
        SLOW_ACKNOWLEDGEMENT_REASON,
    )
    _validate_report_metric(
        report,
        "probability_repricing_count",
        PROBABILITY_REPRICING_REASON,
    )
    if report.average_reserve_drop_ratio != _ratio(
        _sum_decimal(row.reserve_drop_ratio for row in report.rows),
        report.reserve_snapshot_count,
    ):
        raise ValueError("average_reserve_drop_ratio must match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds must match rows")
    if report.average_attestation_count != _ratio(
        _sum_decimal(row.attestation_count for row in report.rows),
        report.reserve_snapshot_count,
    ):
        raise ValueError("average_attestation_count must match rows")


def _validate_report_metric(
    report: MarketResearchCryptoExchangeReserveDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _reason_count(report.rows, reason_code)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _reason_count(
    rows: tuple[MarketResearchCryptoExchangeReserveDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if any(fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be redacted")
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_digest_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be one of {DIGEST_STATUSES}")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _finite_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _finite_decimal(numerator / denominator)


def _probability_delta(value: Decimal) -> Decimal:
    if value < -ONE or value > ONE:
        raise ValueError("probability_delta must be between -1 and 1")
    return _finite_decimal(value)


def _finite_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be finite and quantizable") from exc


def _redacted_reference(reference: str) -> str:
    if not _is_sensitive_reference(reference):
        return reference
    digest = sha256(reference.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _is_sensitive_reference(reference: str) -> bool:
    lowered = reference.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS) or "://" in lowered


def _reason_code_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code must be a known reason code") from exc


def _row_reason_code_rank(reason_code: str) -> int:
    try:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_codes must contain row reason codes") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any, path: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or 'value'} must be a supported public dataclass")
        return {
            field.name: _json_ready(
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        normalized = _require_finite_decimal(field_name, value)
        if normalized != value or not value.same_quantum(QUANT):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} must be a supported public dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        if _require_finite_decimal(path or label, value) != value or not value.same_quantum(
            QUANT,
        ):
            raise ValueError(f"{path or label} must be quantized to six decimals")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        lowered = value.lower()
        if "://" in lowered or "?" in lowered:
            raise ValueError(f"{path or label} has unsafe value")
        if _has_unsafe_public_text_fragment(lowered):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            if _has_unsafe_public_text_fragment(key.lower()):
                raise ValueError(f"{item_path} has unsafe field")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_text_fragment(value: str) -> bool:
    return any(fragment in value for fragment in UNSAFE_TEXT_FRAGMENTS)
