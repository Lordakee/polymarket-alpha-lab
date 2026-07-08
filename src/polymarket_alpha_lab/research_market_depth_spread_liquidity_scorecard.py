from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_LIQUIDITY_SCORECARD_CONFIG_VERSION = (
    "research-market-depth-spread-liquidity-scorecard-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
STATUS_VALUES = ("pass", "watch", "block")
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

_SURFACE_FRAGMENTS = (
    "raw_market",
    "market_id",
    "condition_id",
    "source_id",
    "raw_source",
    "auth",
    "token",
    "api_key",
    "secret",
    "credential",
    "wallet",
    "private_key",
    "session",
    "cookie",
    "bearer",
    "order",
    "trade",
    "trading",
    "position",
)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadLiquidityScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_LIQUIDITY_SCORECARD_CONFIG_VERSION
    )
    pass_liquidity_score: Decimal = Decimal("0.700000")
    watch_liquidity_score: Decimal = Decimal("0.400000")
    pass_depth_units: Decimal = Decimal("100.000000")
    pass_spread_bps: Decimal = Decimal("25.000000")
    block_spread_bps: Decimal = Decimal("250.000000")
    pass_top_participant_share: Decimal = Decimal("0.350000")
    block_top_participant_share: Decimal = Decimal("0.750000")
    pass_quote_age_seconds: Decimal = Decimal("60.000000")
    block_quote_age_seconds: Decimal = Decimal("900.000000")
    pass_cost_pressure_score: Decimal = Decimal("0.150000")
    block_cost_pressure_score: Decimal = Decimal("0.750000")
    depth_weight: Decimal = Decimal("0.300000")
    spread_weight: Decimal = Decimal("0.250000")
    concentration_weight: Decimal = Decimal("0.200000")
    stale_quote_weight: Decimal = Decimal("0.150000")
    cost_pressure_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthSpreadLiquidityScorecardConfig:
            raise TypeError(
                "ResearchMarketDepthSpreadLiquidityScorecardConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthSpreadLiquidityScorecardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketDepthSpreadLiquidityScorecardConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in ("pass_liquidity_score", "watch_liquidity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pass_depth_units",
            _require_positive_decimal("pass_depth_units", self.pass_depth_units),
        )
        for field_name in (
            "pass_spread_bps",
            "block_spread_bps",
            "pass_quote_age_seconds",
            "block_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_top_participant_share",
            "block_top_participant_share",
            "pass_cost_pressure_score",
            "block_cost_pressure_score",
            "depth_weight",
            "spread_weight",
            "concentration_weight",
            "stale_quote_weight",
            "cost_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_liquidity_score <= self.watch_liquidity_score:
            raise ValueError("pass_liquidity_score must exceed watch_liquidity_score")
        if self.block_spread_bps <= self.pass_spread_bps:
            raise ValueError("block_spread_bps must exceed pass_spread_bps")
        if self.block_top_participant_share <= self.pass_top_participant_share:
            raise ValueError(
                "block_top_participant_share must exceed pass_top_participant_share",
            )
        if self.block_quote_age_seconds <= self.pass_quote_age_seconds:
            raise ValueError(
                "block_quote_age_seconds must exceed pass_quote_age_seconds",
            )
        if self.block_cost_pressure_score <= self.pass_cost_pressure_score:
            raise ValueError(
                "block_cost_pressure_score must exceed pass_cost_pressure_score",
            )
        if (
            self.depth_weight
            + self.spread_weight
            + self.concentration_weight
            + self.stale_quote_weight
            + self.cost_pressure_weight
        ) != ONE:
            raise ValueError(
                "depth_weight, spread_weight, concentration_weight, "
                "stale_quote_weight, and cost_pressure_weight must sum to 1.000000",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadLiquidityObservation:
    research_key: str
    public_event_id: str
    public_outcome_label: str
    observed_at: datetime
    depth_units: Decimal
    spread_bps: Decimal
    top_participant_share: Decimal
    quote_age_seconds: Decimal
    cost_pressure_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthSpreadLiquidityObservation:
            raise TypeError(
                "ResearchMarketDepthSpreadLiquidityObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthSpreadLiquidityObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketDepthSpreadLiquidityObservation",
            )
        for field_name in ("research_key", "public_event_id", "public_outcome_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "depth_units",
            _require_nonnegative_decimal("depth_units", self.depth_units),
        )
        object.__setattr__(
            self,
            "spread_bps",
            _require_nonnegative_decimal("spread_bps", self.spread_bps),
        )
        object.__setattr__(
            self,
            "top_participant_share",
            _require_ratio_decimal("top_participant_share", self.top_participant_share),
        )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        object.__setattr__(
            self,
            "cost_pressure_score",
            _require_ratio_decimal("cost_pressure_score", self.cost_pressure_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadLiquidityScoreRow:
    research_key: str
    public_event_id: str
    public_outcome_label: str
    observed_at: datetime
    depth_units: Decimal
    spread_bps: Decimal
    top_participant_share: Decimal
    quote_age_seconds: Decimal
    cost_pressure_score: Decimal
    depth_score: Decimal
    spread_score: Decimal
    concentration_score: Decimal
    stale_quote_score: Decimal
    cost_pressure_score_component: Decimal
    liquidity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchMarketDepthSpreadLiquidityScorecardConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthSpreadLiquidityScoreRow:
            raise TypeError(
                "ResearchMarketDepthSpreadLiquidityScoreRow does not support "
                "subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchMarketDepthSpreadLiquidityScorecardConfig | None,
    ) -> None:
        if type(self) is not ResearchMarketDepthSpreadLiquidityScoreRow:
            raise ValueError(
                "row must be exactly ResearchMarketDepthSpreadLiquidityScoreRow",
            )
        for field_name in ("research_key", "public_event_id", "public_outcome_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("depth_units", "spread_bps", "quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "top_participant_share",
            "cost_pressure_score",
            "depth_score",
            "spread_score",
            "concentration_score",
            "stale_quote_score",
            "cost_pressure_score_component",
            "liquidity_score",
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
        _validate_row_consistency(
            self,
            config=validation_config
            or ResearchMarketDepthSpreadLiquidityScorecardConfig(),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadLiquidityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthSpreadLiquidityReasonCodeCount:
            raise TypeError(
                "ResearchMarketDepthSpreadLiquidityReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthSpreadLiquidityReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketDepthSpreadLiquidityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadLiquidityScorecardReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    thin_depth_count: Decimal
    elevated_spread_count: Decimal
    concentrated_liquidity_count: Decimal
    stale_quote_count: Decimal
    cost_pressure_count: Decimal
    average_liquidity_score: Decimal | None
    max_spread_bps: Decimal
    max_top_participant_share: Decimal
    max_quote_age_seconds: Decimal
    max_cost_pressure_score: Decimal
    status: str
    rows: tuple[ResearchMarketDepthSpreadLiquidityScoreRow, ...]
    reason_code_counts: tuple[ResearchMarketDepthSpreadLiquidityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthSpreadLiquidityScorecardReport:
            raise TypeError(
                "ResearchMarketDepthSpreadLiquidityScorecardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthSpreadLiquidityScorecardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchMarketDepthSpreadLiquidityScorecardReport",
            )
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
            "thin_depth_count",
            "elevated_spread_count",
            "concentrated_liquidity_count",
            "stale_quote_count",
            "cost_pressure_count",
            "max_spread_bps",
            "max_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_top_participant_share", "max_cost_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_liquidity_score",
            _require_optional_ratio_decimal(
                "average_liquidity_score",
                self.average_liquidity_score,
            ),
        )
        _require_status("status", self.status)
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchMarketDepthSpreadLiquidityScoreRow:
                raise ValueError(
                    "rows must contain ResearchMarketDepthSpreadLiquidityScoreRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchMarketDepthSpreadLiquidityReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchMarketDepthSpreadLiquidityReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_market_depth_spread_liquidity_scorecard_report(
    rows: Iterable[object],
    *,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
    generated_at: datetime,
) -> ResearchMarketDepthSpreadLiquidityScorecardReport:
    if type(config) is not ResearchMarketDepthSpreadLiquidityScorecardConfig:
        raise ValueError(
            "config must be a ResearchMarketDepthSpreadLiquidityScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    score_rows = tuple(
        sorted(
            (
                _row_from_input_row(row, config=config)
                for row in _normalize_input_rows(rows)
            ),
            key=_row_sort_key,
        ),
    )
    for row in score_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")
    reason_codes = _report_reason_codes(score_rows)

    return ResearchMarketDepthSpreadLiquidityScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(score_rows)),
        pass_count=_count(_status_count(score_rows, "pass")),
        watch_count=_count(_status_count(score_rows, "watch")),
        block_count=_count(_status_count(score_rows, "block")),
        thin_depth_count=_count(_reason_count(score_rows, "thin_depth")),
        elevated_spread_count=_count(
            _reason_count(score_rows, "elevated_spread")
            + _reason_count(score_rows, "wide_spread"),
        ),
        concentrated_liquidity_count=_count(
            _reason_count(score_rows, "liquidity_concentration_watch")
            + _reason_count(score_rows, "liquidity_concentration_high"),
        ),
        stale_quote_count=_count(
            _reason_count(score_rows, "quote_age_watch")
            + _reason_count(score_rows, "stale_quote_risk"),
        ),
        cost_pressure_count=_count(
            _reason_count(score_rows, "cost_pressure_elevated")
            + _reason_count(score_rows, "cost_pressure_high"),
        ),
        average_liquidity_score=_average_liquidity_score(score_rows),
        max_spread_bps=_max_decimal(tuple(row.spread_bps for row in score_rows)),
        max_top_participant_share=_max_ratio(
            tuple(row.top_participant_share for row in score_rows),
        ),
        max_quote_age_seconds=_max_decimal(
            tuple(row.quote_age_seconds for row in score_rows),
        ),
        max_cost_pressure_score=_max_ratio(
            tuple(row.cost_pressure_score for row in score_rows),
        ),
        status=_report_status(score_rows),
        rows=score_rows,
        reason_code_counts=_reason_code_counts(score_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_depth_spread_liquidity_scorecard_payload(
    report: ResearchMarketDepthSpreadLiquidityScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthSpreadLiquidityScorecardReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketDepthSpreadLiquidityScorecardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_market_depth_spread_liquidity_scorecard_digest(
    report: ResearchMarketDepthSpreadLiquidityScorecardReport | dict[str, Any],
) -> str:
    payload = research_market_depth_spread_liquidity_scorecard_payload(report)
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
            ResearchMarketDepthSpreadLiquidityObservation,
            ResearchMarketDepthSpreadLiquidityScoreRow,
        ):
            raise ValueError(
                "rows must contain "
                "ResearchMarketDepthSpreadLiquidityObservation or "
                "ResearchMarketDepthSpreadLiquidityScoreRow",
            )
        _require_hard_flags("row", row)
    return normalized


def _row_from_input_row(
    row: object,
    *,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
) -> ResearchMarketDepthSpreadLiquidityScoreRow:
    if type(row) is ResearchMarketDepthSpreadLiquidityScoreRow:
        _validate_row_consistency(row, config=config)
        return row
    if type(row) is ResearchMarketDepthSpreadLiquidityObservation:
        return _score_observation(row, config=config)
    raise ValueError("row must be a supported liquidity scorecard row")


def _score_observation(
    row: ResearchMarketDepthSpreadLiquidityObservation,
    *,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
) -> ResearchMarketDepthSpreadLiquidityScoreRow:
    depth_score = _depth_score(row.depth_units, config=config)
    spread_score = _inverse_threshold_score(
        row.spread_bps,
        pass_value=config.pass_spread_bps,
        block_value=config.block_spread_bps,
    )
    concentration_score = _inverse_threshold_score(
        row.top_participant_share,
        pass_value=config.pass_top_participant_share,
        block_value=config.block_top_participant_share,
    )
    stale_quote_score = _inverse_threshold_score(
        row.quote_age_seconds,
        pass_value=config.pass_quote_age_seconds,
        block_value=config.block_quote_age_seconds,
    )
    cost_score = _inverse_threshold_score(
        row.cost_pressure_score,
        pass_value=config.pass_cost_pressure_score,
        block_value=config.block_cost_pressure_score,
    )
    liquidity_score = _liquidity_score(
        depth_score=depth_score,
        spread_score=spread_score,
        concentration_score=concentration_score,
        stale_quote_score=stale_quote_score,
        cost_pressure_score_component=cost_score,
        config=config,
    )
    status = _row_status(liquidity_score, config=config)
    reason_codes = _row_reason_codes(row, status=status, config=config)
    return ResearchMarketDepthSpreadLiquidityScoreRow(
        research_key=row.research_key,
        public_event_id=row.public_event_id,
        public_outcome_label=row.public_outcome_label,
        observed_at=row.observed_at,
        depth_units=row.depth_units,
        spread_bps=row.spread_bps,
        top_participant_share=row.top_participant_share,
        quote_age_seconds=row.quote_age_seconds,
        cost_pressure_score=row.cost_pressure_score,
        depth_score=depth_score,
        spread_score=spread_score,
        concentration_score=concentration_score,
        stale_quote_score=stale_quote_score,
        cost_pressure_score_component=cost_score,
        liquidity_score=liquidity_score,
        status=status,
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    row: ResearchMarketDepthSpreadLiquidityObservation,
    *,
    status: str,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"liquidity_score_{status}"]
    if row.depth_units < config.pass_depth_units:
        reason_codes.append("thin_depth")
    if row.spread_bps >= config.block_spread_bps:
        reason_codes.append("wide_spread")
    elif row.spread_bps > config.pass_spread_bps:
        reason_codes.append("elevated_spread")
    if row.top_participant_share >= config.block_top_participant_share:
        reason_codes.append("liquidity_concentration_high")
    elif row.top_participant_share > config.pass_top_participant_share:
        reason_codes.append("liquidity_concentration_watch")
    if row.quote_age_seconds >= config.block_quote_age_seconds:
        reason_codes.append("stale_quote_risk")
    elif row.quote_age_seconds > config.pass_quote_age_seconds:
        reason_codes.append("quote_age_watch")
    if row.cost_pressure_score >= config.block_cost_pressure_score:
        reason_codes.append("cost_pressure_high")
    elif row.cost_pressure_score > config.pass_cost_pressure_score:
        reason_codes.append("cost_pressure_elevated")
    for reason_code in row.reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _depth_score(
    depth_units: Decimal,
    *,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
) -> Decimal:
    if depth_units >= config.pass_depth_units:
        return ONE.quantize(RATIO_QUANTUM)
    return _quantize(depth_units / config.pass_depth_units)


def _inverse_threshold_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    block_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ONE.quantize(RATIO_QUANTUM)
    if value >= block_value:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize((block_value - value) / (block_value - pass_value))


def _liquidity_score(
    *,
    depth_score: Decimal,
    spread_score: Decimal,
    concentration_score: Decimal,
    stale_quote_score: Decimal,
    cost_pressure_score_component: Decimal,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
) -> Decimal:
    return _quantize(
        depth_score * config.depth_weight
        + spread_score * config.spread_weight
        + concentration_score * config.concentration_weight
        + stale_quote_score * config.stale_quote_weight
        + cost_pressure_score_component * config.cost_pressure_weight,
    )


def _row_status(
    liquidity_score: Decimal,
    *,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
) -> str:
    if liquidity_score >= config.pass_liquidity_score:
        return "pass"
    if liquidity_score >= config.watch_liquidity_score:
        return "watch"
    return "block"


def _validate_row_consistency(
    row: ResearchMarketDepthSpreadLiquidityScoreRow,
    *,
    config: ResearchMarketDepthSpreadLiquidityScorecardConfig,
) -> None:
    expected_depth = _depth_score(row.depth_units, config=config)
    expected_spread = _inverse_threshold_score(
        row.spread_bps,
        pass_value=config.pass_spread_bps,
        block_value=config.block_spread_bps,
    )
    expected_concentration = _inverse_threshold_score(
        row.top_participant_share,
        pass_value=config.pass_top_participant_share,
        block_value=config.block_top_participant_share,
    )
    expected_stale = _inverse_threshold_score(
        row.quote_age_seconds,
        pass_value=config.pass_quote_age_seconds,
        block_value=config.block_quote_age_seconds,
    )
    expected_cost = _inverse_threshold_score(
        row.cost_pressure_score,
        pass_value=config.pass_cost_pressure_score,
        block_value=config.block_cost_pressure_score,
    )
    expected_liquidity = _liquidity_score(
        depth_score=expected_depth,
        spread_score=expected_spread,
        concentration_score=expected_concentration,
        stale_quote_score=expected_stale,
        cost_pressure_score_component=expected_cost,
        config=config,
    )
    if row.depth_score != expected_depth:
        raise ValueError("depth_score must match row inputs")
    if row.spread_score != expected_spread:
        raise ValueError("spread_score must match row inputs")
    if row.concentration_score != expected_concentration:
        raise ValueError("concentration_score must match row inputs")
    if row.stale_quote_score != expected_stale:
        raise ValueError("stale_quote_score must match row inputs")
    if row.cost_pressure_score_component != expected_cost:
        raise ValueError("cost_pressure_score_component must match row inputs")
    if row.liquidity_score != expected_liquidity:
        raise ValueError("liquidity_score must match row inputs")
    expected_status = _row_status(row.liquidity_score, config=config)
    if row.status != expected_status:
        raise ValueError("status must match liquidity_score")


def _validate_report(
    report: ResearchMarketDepthSpreadLiquidityScorecardReport,
) -> None:
    rows = report.rows
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.thin_depth_count != _count(_reason_count(rows, "thin_depth")):
        raise ValueError("thin_depth_count must match rows")
    if report.elevated_spread_count != _count(
        _reason_count(rows, "elevated_spread") + _reason_count(rows, "wide_spread"),
    ):
        raise ValueError("elevated_spread_count must match rows")
    if report.concentrated_liquidity_count != _count(
        _reason_count(rows, "liquidity_concentration_watch")
        + _reason_count(rows, "liquidity_concentration_high"),
    ):
        raise ValueError("concentrated_liquidity_count must match rows")
    if report.stale_quote_count != _count(
        _reason_count(rows, "quote_age_watch")
        + _reason_count(rows, "stale_quote_risk"),
    ):
        raise ValueError("stale_quote_count must match rows")
    if report.cost_pressure_count != _count(
        _reason_count(rows, "cost_pressure_elevated")
        + _reason_count(rows, "cost_pressure_high"),
    ):
        raise ValueError("cost_pressure_count must match rows")
    if report.average_liquidity_score != _average_liquidity_score(rows):
        raise ValueError("average_liquidity_score must match rows")
    if report.max_spread_bps != _max_decimal(tuple(row.spread_bps for row in rows)):
        raise ValueError("max_spread_bps must match rows")
    if report.max_top_participant_share != _max_ratio(
        tuple(row.top_participant_share for row in rows),
    ):
        raise ValueError("max_top_participant_share must match rows")
    if report.max_quote_age_seconds != _max_decimal(
        tuple(row.quote_age_seconds for row in rows),
    ):
        raise ValueError("max_quote_age_seconds must match rows")
    if report.max_cost_pressure_score != _max_ratio(
        tuple(row.cost_pressure_score for row in rows),
    ):
        raise ValueError("max_cost_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")


def _row_sort_key(
    row: ResearchMarketDepthSpreadLiquidityScoreRow,
) -> tuple[int, str, str, str]:
    return (
        STATUS_VALUES.index(row.status),
        row.research_key,
        row.public_event_id,
        row.public_outcome_label,
    )


def _status_count(
    rows: tuple[ResearchMarketDepthSpreadLiquidityScoreRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketDepthSpreadLiquidityScoreRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _average_liquidity_score(
    rows: tuple[ResearchMarketDepthSpreadLiquidityScoreRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.liquidity_score for row in rows), ZERO) / Decimal(len(rows)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(max(values))


def _report_status(
    rows: tuple[ResearchMarketDepthSpreadLiquidityScoreRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthSpreadLiquidityScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_observations",)
    reason_codes: set[str] = set()
    for row in rows:
        reason_codes.update(row.reason_codes)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthSpreadLiquidityScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketDepthSpreadLiquidityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthSpreadLiquidityReasonCodeCount(
                reason_code="no_liquidity_observations",
                count=Decimal("1"),
            ),
        )
    return tuple(
        ResearchMarketDepthSpreadLiquidityReasonCodeCount(
            reason_code=reason_code,
            count=_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if _has_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_" for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if _has_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of {STATUS_VALUES}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            item_path = key if not path else f"{path}.{key}"
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str and _has_surface_fragment(value):
        raise ValueError(f"{path or label} has unsafe value")
    if type(value) in (float, int):
        raise ValueError(f"{path or label} must use Decimal-derived string values")


def _has_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _SURFACE_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_LIQUIDITY_SCORECARD_CONFIG_VERSION",
    "ResearchMarketDepthSpreadLiquidityObservation",
    "ResearchMarketDepthSpreadLiquidityReasonCodeCount",
    "ResearchMarketDepthSpreadLiquidityScoreRow",
    "ResearchMarketDepthSpreadLiquidityScorecardConfig",
    "ResearchMarketDepthSpreadLiquidityScorecardReport",
    "build_research_market_depth_spread_liquidity_scorecard_report",
    "research_market_depth_spread_liquidity_scorecard_digest",
    "research_market_depth_spread_liquidity_scorecard_payload",
)
