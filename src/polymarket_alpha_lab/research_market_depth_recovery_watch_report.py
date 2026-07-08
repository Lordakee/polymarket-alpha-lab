from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_MARKET_DEPTH_RECOVERY_WATCH_CONFIG_VERSION = (
    "research-market-depth-recovery-watch-report-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1")
SIX_PLACES = Decimal("0.000001")
STATUS_VALUES = ("pass", "watch", "block")

_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw-",
    "raw_",
    "market_id",
    "condition-",
    "condition_",
    "condition_id",
    "source-",
    "source_",
    "source_id",
    "source_url",
    "source_text",
    "token-",
    "token_",
    "credential",
    "secret",
    "session",
    "cookie",
    "bearer",
)


@dataclass(frozen=True)
class ResearchMarketDepthRecoveryWatchConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_DEPTH_RECOVERY_WATCH_CONFIG_VERSION
    pass_recovery_score: Decimal = Decimal("0.700000")
    watch_recovery_score: Decimal = Decimal("0.400000")
    pass_aggregate_depth_recovery: Decimal = Decimal("0.700000")
    watch_aggregate_depth_recovery: Decimal = Decimal("0.400000")
    pass_spread_normalization: Decimal = Decimal("0.700000")
    watch_spread_normalization: Decimal = Decimal("0.400000")
    fresh_quote_age_seconds: Decimal = Decimal("60.000000")
    stale_quote_age_seconds: Decimal = Decimal("900.000000")
    watch_catalyst_pressure: Decimal = Decimal("0.350000")
    block_catalyst_pressure: Decimal = Decimal("0.700000")
    watch_fee_friction: Decimal = Decimal("0.300000")
    block_fee_friction: Decimal = Decimal("0.700000")
    aggregate_depth_recovery_weight: Decimal = Decimal("0.350000")
    spread_normalization_weight: Decimal = Decimal("0.250000")
    quote_freshness_weight: Decimal = Decimal("0.150000")
    catalyst_pressure_weight: Decimal = Decimal("0.150000")
    fee_friction_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthRecoveryWatchConfig:
            raise TypeError(
                "ResearchMarketDepthRecoveryWatchConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthRecoveryWatchConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_DEPTH_RECOVERY_WATCH_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "pass_recovery_score",
            "watch_recovery_score",
            "pass_aggregate_depth_recovery",
            "watch_aggregate_depth_recovery",
            "pass_spread_normalization",
            "watch_spread_normalization",
            "watch_catalyst_pressure",
            "block_catalyst_pressure",
            "watch_fee_friction",
            "block_fee_friction",
            "aggregate_depth_recovery_weight",
            "spread_normalization_weight",
            "quote_freshness_weight",
            "catalyst_pressure_weight",
            "fee_friction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_quote_age_seconds", "stale_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_recovery_score <= self.watch_recovery_score:
            raise ValueError("pass_recovery_score must exceed watch_recovery_score")
        if self.pass_aggregate_depth_recovery <= self.watch_aggregate_depth_recovery:
            raise ValueError(
                "pass_aggregate_depth_recovery must exceed "
                "watch_aggregate_depth_recovery",
            )
        if self.pass_spread_normalization <= self.watch_spread_normalization:
            raise ValueError(
                "pass_spread_normalization must exceed watch_spread_normalization",
            )
        if self.stale_quote_age_seconds <= self.fresh_quote_age_seconds:
            raise ValueError("stale_quote_age_seconds must exceed fresh_quote_age_seconds")
        if self.block_catalyst_pressure <= self.watch_catalyst_pressure:
            raise ValueError(
                "block_catalyst_pressure must exceed watch_catalyst_pressure",
            )
        if self.block_fee_friction <= self.watch_fee_friction:
            raise ValueError("block_fee_friction must exceed watch_fee_friction")
        if (
            self.aggregate_depth_recovery_weight
            + self.spread_normalization_weight
            + self.quote_freshness_weight
            + self.catalyst_pressure_weight
            + self.fee_friction_weight
        ) != ONE:
            raise ValueError(
                "aggregate_depth_recovery_weight, spread_normalization_weight, "
                "quote_freshness_weight, catalyst_pressure_weight, and "
                "fee_friction_weight must sum to 1.000000",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthRecoveryWatchObservation:
    public_recovery_id: str
    public_event_label: str
    observed_at: datetime
    aggregate_depth_recovery: Decimal
    spread_normalization: Decimal
    quote_age_seconds: Decimal
    catalyst_pressure: Decimal
    fee_friction: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthRecoveryWatchObservation:
            raise TypeError(
                "ResearchMarketDepthRecoveryWatchObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthRecoveryWatchObservation, "observation")
        for field_name in ("public_recovery_id", "public_event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_depth_recovery",
            "spread_normalization",
            "catalyst_pressure",
            "fee_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthRecoveryWatchRow:
    public_recovery_id: str
    public_event_label: str
    observed_at: datetime
    aggregate_depth_recovery: Decimal
    spread_normalization: Decimal
    quote_age_seconds: Decimal
    catalyst_pressure: Decimal
    fee_friction: Decimal
    aggregate_depth_recovery_score: Decimal
    spread_normalization_score: Decimal
    quote_freshness_score: Decimal
    catalyst_pressure_score: Decimal
    fee_friction_score: Decimal
    recovery_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthRecoveryWatchRow:
            raise TypeError("ResearchMarketDepthRecoveryWatchRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthRecoveryWatchRow, "row")
        for field_name in ("public_recovery_id", "public_event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        for field_name in (
            "aggregate_depth_recovery",
            "spread_normalization",
            "catalyst_pressure",
            "fee_friction",
            "aggregate_depth_recovery_score",
            "spread_normalization_score",
            "quote_freshness_score",
            "catalyst_pressure_score",
            "fee_friction_score",
            "recovery_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthRecoveryWatchReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthRecoveryWatchReasonCodeCount:
            raise TypeError(
                "ResearchMarketDepthRecoveryWatchReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthRecoveryWatchReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        if self.count == ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketDepthRecoveryWatchReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_recovery_score: Decimal | None
    min_aggregate_depth_recovery: Decimal
    max_quote_age_seconds: Decimal
    max_catalyst_pressure: Decimal
    max_fee_friction: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketDepthRecoveryWatchReasonCodeCount, ...]
    rows: tuple[ResearchMarketDepthRecoveryWatchRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthRecoveryWatchReport:
            raise TypeError(
                "ResearchMarketDepthRecoveryWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthRecoveryWatchReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_aggregate_depth_recovery",
            "max_catalyst_pressure",
            "max_fee_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_recovery_score",
            _require_optional_ratio_decimal(
                "average_recovery_score",
                self.average_recovery_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchMarketDepthRecoveryWatchReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchMarketDepthRecoveryWatchReasonCodeCount",
                )
            _require_hard_flags("reason_code_count", row)
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchMarketDepthRecoveryWatchRow:
                raise ValueError("rows must contain ResearchMarketDepthRecoveryWatchRow")
            _require_hard_flags("row", row)
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_market_depth_recovery_watch_report(
    rows: Iterable[object],
    *,
    config: ResearchMarketDepthRecoveryWatchConfig,
    generated_at: datetime,
) -> ResearchMarketDepthRecoveryWatchReport:
    if type(config) is not ResearchMarketDepthRecoveryWatchConfig:
        raise ValueError("config must be a ResearchMarketDepthRecoveryWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    recovery_rows = tuple(
        sorted(
            (
                _row_from_input_row(row, config=config)
                for row in _normalize_input_rows(rows)
            ),
            key=_row_sort_key,
        ),
    )
    for row in recovery_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")
    reason_codes = _report_reason_codes(recovery_rows)
    return ResearchMarketDepthRecoveryWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(recovery_rows)),
        pass_count=_count(_status_count(recovery_rows, "pass")),
        watch_count=_count(_status_count(recovery_rows, "watch")),
        block_count=_count(_status_count(recovery_rows, "block")),
        average_recovery_score=_average_recovery_score(recovery_rows),
        min_aggregate_depth_recovery=_min_ratio(
            tuple(row.aggregate_depth_recovery for row in recovery_rows),
        ),
        max_quote_age_seconds=_max_decimal(
            tuple(row.quote_age_seconds for row in recovery_rows),
        ),
        max_catalyst_pressure=_max_ratio(
            tuple(row.catalyst_pressure for row in recovery_rows),
        ),
        max_fee_friction=_max_ratio(tuple(row.fee_friction for row in recovery_rows)),
        status=_report_status(recovery_rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(recovery_rows, reason_codes),
        rows=recovery_rows,
    )


def research_market_depth_recovery_watch_report_payload(
    report: ResearchMarketDepthRecoveryWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthRecoveryWatchReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketDepthRecoveryWatchReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_market_depth_recovery_watch_report_digest(
    report: ResearchMarketDepthRecoveryWatchReport | dict[str, Any],
) -> str:
    payload = research_market_depth_recovery_watch_report_payload(report)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


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


def _normalize_input_rows(rows: Iterable[object]) -> tuple[object, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) not in (
            ResearchMarketDepthRecoveryWatchObservation,
            ResearchMarketDepthRecoveryWatchRow,
        ):
            raise ValueError(
                "rows must contain ResearchMarketDepthRecoveryWatchObservation or "
                "ResearchMarketDepthRecoveryWatchRow",
            )
        _require_hard_flags("row", row)
    return normalized


def _row_from_input_row(
    row: object,
    *,
    config: ResearchMarketDepthRecoveryWatchConfig,
) -> ResearchMarketDepthRecoveryWatchRow:
    if type(row) is ResearchMarketDepthRecoveryWatchRow:
        _validate_row_against_config(row, config=config)
        return row
    if type(row) is ResearchMarketDepthRecoveryWatchObservation:
        return _score_observation(row, config=config)
    raise ValueError("row must be a supported recovery row")


def _score_observation(
    row: ResearchMarketDepthRecoveryWatchObservation,
    *,
    config: ResearchMarketDepthRecoveryWatchConfig,
) -> ResearchMarketDepthRecoveryWatchRow:
    aggregate_depth_score = row.aggregate_depth_recovery
    spread_score = row.spread_normalization
    quote_score = _inverse_threshold_score(
        row.quote_age_seconds,
        pass_value=config.fresh_quote_age_seconds,
        block_value=config.stale_quote_age_seconds,
    )
    catalyst_score = _quantize_ratio(ONE - row.catalyst_pressure)
    fee_score = _quantize_ratio(ONE - row.fee_friction)
    recovery_score = _recovery_score(
        aggregate_depth_score=aggregate_depth_score,
        spread_score=spread_score,
        quote_score=quote_score,
        catalyst_score=catalyst_score,
        fee_score=fee_score,
        config=config,
    )
    status = _row_status(recovery_score, config=config)
    return ResearchMarketDepthRecoveryWatchRow(
        public_recovery_id=row.public_recovery_id,
        public_event_label=row.public_event_label,
        observed_at=row.observed_at,
        aggregate_depth_recovery=row.aggregate_depth_recovery,
        spread_normalization=row.spread_normalization,
        quote_age_seconds=row.quote_age_seconds,
        catalyst_pressure=row.catalyst_pressure,
        fee_friction=row.fee_friction,
        aggregate_depth_recovery_score=aggregate_depth_score,
        spread_normalization_score=spread_score,
        quote_freshness_score=quote_score,
        catalyst_pressure_score=catalyst_score,
        fee_friction_score=fee_score,
        recovery_score=recovery_score,
        status=status,
        reason_codes=_row_reason_codes(row, status=status, config=config),
    )


def _recovery_score(
    *,
    aggregate_depth_score: Decimal,
    spread_score: Decimal,
    quote_score: Decimal,
    catalyst_score: Decimal,
    fee_score: Decimal,
    config: ResearchMarketDepthRecoveryWatchConfig,
) -> Decimal:
    return _quantize_ratio(
        aggregate_depth_score * config.aggregate_depth_recovery_weight
        + spread_score * config.spread_normalization_weight
        + quote_score * config.quote_freshness_weight
        + catalyst_score * config.catalyst_pressure_weight
        + fee_score * config.fee_friction_weight,
    )


def _inverse_threshold_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    block_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ONE
    if value >= block_value:
        return ZERO
    return _quantize_ratio(ONE - ((value - pass_value) / (block_value - pass_value)))


def _row_status(
    recovery_score: Decimal,
    *,
    config: ResearchMarketDepthRecoveryWatchConfig,
) -> str:
    if recovery_score < config.watch_recovery_score:
        return "block"
    if recovery_score < config.pass_recovery_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    row: ResearchMarketDepthRecoveryWatchObservation,
    *,
    status: str,
    config: ResearchMarketDepthRecoveryWatchConfig,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if row.aggregate_depth_recovery < config.watch_aggregate_depth_recovery:
        reasons.add("aggregate_depth_recovery_block")
    elif row.aggregate_depth_recovery < config.pass_aggregate_depth_recovery:
        reasons.add("aggregate_depth_recovery_watch")
    if row.spread_normalization < config.watch_spread_normalization:
        reasons.add("spread_normalization_block")
    elif row.spread_normalization < config.pass_spread_normalization:
        reasons.add("spread_normalization_watch")
    if row.quote_age_seconds >= config.stale_quote_age_seconds:
        reasons.add("stale_quote_risk")
    elif row.quote_age_seconds > config.fresh_quote_age_seconds:
        reasons.add("quote_freshness_watch")
    if row.catalyst_pressure >= config.block_catalyst_pressure:
        reasons.add("catalyst_pressure_high")
    if row.fee_friction >= config.block_fee_friction:
        reasons.add("fee_friction_high")
    elif row.fee_friction >= config.watch_fee_friction:
        reasons.add("fee_friction_elevated")
    if status == "block":
        reasons.add("depth_recovery_score_block")
    elif status == "watch":
        reasons.add("depth_recovery_score_watch")
    else:
        reasons.add("depth_recovery_pass")
    for reason_code in row.reason_codes:
        reasons.add(f"input_{reason_code}")
    return tuple(sorted(reasons))


def _report_status(rows: tuple[ResearchMarketDepthRecoveryWatchRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchMarketDepthRecoveryWatchRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_depth_recovery_observations",)
    reasons: set[str] = set()
    status = _report_status(rows)
    if status == "block":
        reasons.add("depth_recovery_block_present")
    elif status == "watch":
        reasons.add("depth_recovery_watch_present")
    else:
        reasons.add("depth_recovery_pass")
    for row in rows:
        if row.status != "pass":
            reasons.add(f"row_{row.status}_present")
    return tuple(sorted(reasons))


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthRecoveryWatchRow, ...],
    report_reasons: tuple[str, ...],
) -> tuple[ResearchMarketDepthRecoveryWatchReasonCodeCount, ...]:
    counts: dict[str, int] = {reason_code: 1 for reason_code in report_reasons}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchMarketDepthRecoveryWatchReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _status_count(rows: tuple[ResearchMarketDepthRecoveryWatchRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_recovery_score(
    rows: tuple[ResearchMarketDepthRecoveryWatchRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize_ratio(
        sum((row.recovery_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_ratio(min(values))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_ratio(max(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(max(values))


def _validate_row_against_config(
    row: ResearchMarketDepthRecoveryWatchRow,
    *,
    config: ResearchMarketDepthRecoveryWatchConfig,
) -> None:
    rebuilt = _score_observation(
        ResearchMarketDepthRecoveryWatchObservation(
            public_recovery_id=row.public_recovery_id,
            public_event_label=row.public_event_label,
            observed_at=row.observed_at,
            aggregate_depth_recovery=row.aggregate_depth_recovery,
            spread_normalization=row.spread_normalization,
            quote_age_seconds=row.quote_age_seconds,
            catalyst_pressure=row.catalyst_pressure,
            fee_friction=row.fee_friction,
        ),
        config=config,
    )
    if (
        row.aggregate_depth_recovery_score != rebuilt.aggregate_depth_recovery_score
        or row.spread_normalization_score != rebuilt.spread_normalization_score
        or row.quote_freshness_score != rebuilt.quote_freshness_score
        or row.catalyst_pressure_score != rebuilt.catalyst_pressure_score
        or row.fee_friction_score != rebuilt.fee_friction_score
        or row.recovery_score != rebuilt.recovery_score
        or row.status != rebuilt.status
    ):
        raise ValueError("row scores must match config")


def _validate_report(report: ResearchMarketDepthRecoveryWatchReport) -> None:
    row_count = _count(len(report.rows))
    if report.observation_count != row_count:
        raise ValueError("observation_count must equal rows length")
    if report.pass_count + report.watch_count + report.block_count != row_count:
        raise ValueError("status counts must equal rows length")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _row_sort_key(row: ResearchMarketDepthRecoveryWatchRow) -> tuple[str, str, str]:
    return (
        row.public_recovery_id,
        row.public_event_label,
        row.observed_at.isoformat(),
    )


def _json_ready(value: Any) -> Any:
    if dataclass_is_instance(value):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): _json_ready(nested)
            for key, nested in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_json_ready(nested) for nested in value]
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def dataclass_is_instance(value: object) -> bool:
    return hasattr(value, "__dataclass_fields__") and not isinstance(value, type)


def _reject_unsafe_public_payload(field_name: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            _require_public_string(f"{field_name} key", str(key))
            _reject_unsafe_public_payload(str(key), nested)
        return
    if isinstance(value, list):
        for nested in value:
            _reject_unsafe_public_payload(field_name, nested)
        return
    if type(value) is str:
        _reject_unsafe_text(field_name, value)


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if any(ord(char) > 127 for char in value):
        raise ValueError(f"{field_name} must be ASCII")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must be lowercase public text")
    _reject_unsafe_text(field_name, value)
    return value


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
    return tuple(sorted(frozenset(value)))


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if not value:
        raise ValueError(f"{field_name} must not contain empty values")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must contain lowercase reason codes")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1.000000")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_ratio_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    try:
        return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("decimal value must be quantizable") from exc


def _quantize_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize_decimal(value)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _decimal_string(value: Decimal) -> str:
    return format(_quantize_decimal(value), "f")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")
