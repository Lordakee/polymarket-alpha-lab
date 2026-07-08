from __future__ import annotations

from collections.abc import Iterable
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_RESEARCH_MARKET_MAKER_ACTIVITY_ANOMALY_SCORECARD_CONFIG_VERSION = (
    "research-market-maker-activity-anomaly-scorecard-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
STATUS_VALUES = ("pass", "watch", "block")
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class ResearchMarketMakerActivityAnomalyScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_MAKER_ACTIVITY_ANOMALY_SCORECARD_CONFIG_VERSION
    )
    watch_anomaly_score: Decimal = Decimal("0.350000")
    block_anomaly_score: Decimal = Decimal("0.700000")
    pass_quote_age_seconds: Decimal = Decimal("60.000000")
    block_quote_age_seconds: Decimal = Decimal("900.000000")
    pass_depth_imbalance_ratio: Decimal = Decimal("0.200000")
    block_depth_imbalance_ratio: Decimal = Decimal("0.800000")
    pass_spread_widening_ratio: Decimal = Decimal("0.250000")
    block_spread_widening_ratio: Decimal = Decimal("2.000000")
    pass_volume_burst_ratio: Decimal = Decimal("2.000000")
    block_volume_burst_ratio: Decimal = Decimal("8.000000")
    pass_top_liquidity_share: Decimal = Decimal("0.350000")
    block_top_liquidity_share: Decimal = Decimal("0.750000")
    quote_freshness_weight: Decimal = Decimal("0.200000")
    depth_imbalance_weight: Decimal = Decimal("0.200000")
    spread_widening_weight: Decimal = Decimal("0.200000")
    volume_burst_weight: Decimal = Decimal("0.200000")
    liquidity_concentration_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMakerActivityAnomalyScorecardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketMakerActivityAnomalyScorecardConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in ("watch_anomaly_score", "block_anomaly_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_quote_age_seconds",
            "block_quote_age_seconds",
            "pass_spread_widening_ratio",
            "block_spread_widening_ratio",
            "pass_volume_burst_ratio",
            "block_volume_burst_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_depth_imbalance_ratio",
            "block_depth_imbalance_ratio",
            "pass_top_liquidity_share",
            "block_top_liquidity_share",
            "quote_freshness_weight",
            "depth_imbalance_weight",
            "spread_widening_weight",
            "volume_burst_weight",
            "liquidity_concentration_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_anomaly_score <= self.watch_anomaly_score:
            raise ValueError("block_anomaly_score must exceed watch_anomaly_score")
        _require_increasing_threshold(
            "quote_age_seconds",
            self.pass_quote_age_seconds,
            self.block_quote_age_seconds,
        )
        _require_increasing_threshold(
            "depth_imbalance_ratio",
            self.pass_depth_imbalance_ratio,
            self.block_depth_imbalance_ratio,
        )
        _require_increasing_threshold(
            "spread_widening_ratio",
            self.pass_spread_widening_ratio,
            self.block_spread_widening_ratio,
        )
        _require_increasing_threshold(
            "volume_burst_ratio",
            self.pass_volume_burst_ratio,
            self.block_volume_burst_ratio,
        )
        _require_increasing_threshold(
            "top_liquidity_share",
            self.pass_top_liquidity_share,
            self.block_top_liquidity_share,
        )
        if (
            self.quote_freshness_weight
            + self.depth_imbalance_weight
            + self.spread_widening_weight
            + self.volume_burst_weight
            + self.liquidity_concentration_weight
        ) != ONE:
            raise ValueError(
                "quote_freshness_weight, depth_imbalance_weight, "
                "spread_widening_weight, volume_burst_weight, and "
                "liquidity_concentration_weight must sum to 1.000000",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketMakerActivityAnomalyObservation:
    research_bucket: str
    public_event_label: str
    observed_at: datetime
    quote_age_seconds: Decimal
    bid_depth_units: Decimal
    ask_depth_units: Decimal
    current_spread_bps: Decimal
    baseline_spread_bps: Decimal
    current_volume_units: Decimal
    baseline_volume_units: Decimal
    top_liquidity_share: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMakerActivityAnomalyObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketMakerActivityAnomalyObservation",
            )
        for field_name in ("research_bucket", "public_event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "quote_age_seconds",
            "bid_depth_units",
            "ask_depth_units",
            "current_spread_bps",
            "baseline_spread_bps",
            "current_volume_units",
            "baseline_volume_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "top_liquidity_share",
            _require_ratio_decimal("top_liquidity_share", self.top_liquidity_share),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketMakerActivityAnomalyScoreRow:
    research_bucket: str
    public_event_label: str
    observed_at: datetime
    quote_age_seconds: Decimal
    bid_depth_units: Decimal
    ask_depth_units: Decimal
    current_spread_bps: Decimal
    baseline_spread_bps: Decimal
    current_volume_units: Decimal
    baseline_volume_units: Decimal
    top_liquidity_share: Decimal
    quote_freshness_score: Decimal
    depth_imbalance_ratio: Decimal
    depth_imbalance_score: Decimal
    spread_widening_ratio: Decimal
    spread_widening_score: Decimal
    volume_burst_ratio: Decimal
    volume_burst_score: Decimal
    liquidity_concentration_score: Decimal
    anomaly_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchMarketMakerActivityAnomalyScorecardConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchMarketMakerActivityAnomalyScorecardConfig | None,
    ) -> None:
        if type(self) is not ResearchMarketMakerActivityAnomalyScoreRow:
            raise ValueError("row must be exactly ResearchMarketMakerActivityAnomalyScoreRow")
        for field_name in ("research_bucket", "public_event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "quote_age_seconds",
            "bid_depth_units",
            "ask_depth_units",
            "current_spread_bps",
            "baseline_spread_bps",
            "current_volume_units",
            "baseline_volume_units",
            "depth_imbalance_ratio",
            "spread_widening_ratio",
            "volume_burst_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "top_liquidity_share",
            "quote_freshness_score",
            "depth_imbalance_score",
            "spread_widening_score",
            "volume_burst_score",
            "liquidity_concentration_score",
            "anomaly_score",
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
            or ResearchMarketMakerActivityAnomalyScorecardConfig(),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketMakerActivityAnomalyReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMakerActivityAnomalyReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketMakerActivityAnomalyReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketMakerActivityAnomalyScorecardReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    quote_freshness_count: Decimal
    depth_imbalance_count: Decimal
    spread_widening_count: Decimal
    volume_burst_count: Decimal
    liquidity_concentration_count: Decimal
    average_anomaly_score: Decimal | None
    max_anomaly_score: Decimal
    status: str
    rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...]
    reason_code_counts: tuple[ResearchMarketMakerActivityAnomalyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMakerActivityAnomalyScorecardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchMarketMakerActivityAnomalyScorecardReport",
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
            "quote_freshness_count",
            "depth_imbalance_count",
            "spread_widening_count",
            "volume_burst_count",
            "liquidity_concentration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_anomaly_score",
            _require_optional_ratio_decimal(
                "average_anomaly_score",
                self.average_anomaly_score,
            ),
        )
        object.__setattr__(
            self,
            "max_anomaly_score",
            _require_ratio_decimal("max_anomaly_score", self.max_anomaly_score),
        )
        _require_status("status", self.status)
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchMarketMakerActivityAnomalyScoreRow:
                raise ValueError(
                    "rows must contain ResearchMarketMakerActivityAnomalyScoreRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchMarketMakerActivityAnomalyReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchMarketMakerActivityAnomalyReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_market_maker_activity_anomaly_scorecard_report(
    rows: Iterable[object],
    *,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
    generated_at: datetime,
) -> ResearchMarketMakerActivityAnomalyScorecardReport:
    if type(config) is not ResearchMarketMakerActivityAnomalyScorecardConfig:
        raise ValueError(
            "config must be a ResearchMarketMakerActivityAnomalyScorecardConfig",
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

    return ResearchMarketMakerActivityAnomalyScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(score_rows)),
        pass_count=_count(_status_count(score_rows, "pass")),
        watch_count=_count(_status_count(score_rows, "watch")),
        block_count=_count(_status_count(score_rows, "block")),
        quote_freshness_count=_count(
            _reason_count(score_rows, "quote_freshness_watch")
            + _reason_count(score_rows, "quote_freshness_block"),
        ),
        depth_imbalance_count=_count(
            _reason_count(score_rows, "depth_imbalance_watch")
            + _reason_count(score_rows, "depth_imbalance_high"),
        ),
        spread_widening_count=_count(
            _reason_count(score_rows, "spread_widening_watch")
            + _reason_count(score_rows, "spread_widening_high"),
        ),
        volume_burst_count=_count(
            _reason_count(score_rows, "volume_burst_watch")
            + _reason_count(score_rows, "volume_burst_high"),
        ),
        liquidity_concentration_count=_count(
            _reason_count(score_rows, "liquidity_concentration_watch")
            + _reason_count(score_rows, "liquidity_concentration_high"),
        ),
        average_anomaly_score=_average_anomaly_score(score_rows),
        max_anomaly_score=_max_anomaly_score(score_rows),
        status=_report_status(score_rows),
        rows=score_rows,
        reason_code_counts=_reason_code_counts(score_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_maker_activity_anomaly_scorecard_payload(
    report: ResearchMarketMakerActivityAnomalyScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketMakerActivityAnomalyScorecardReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketMakerActivityAnomalyScorecardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_market_maker_activity_anomaly_scorecard_digest(
    report: ResearchMarketMakerActivityAnomalyScorecardReport | dict[str, Any],
) -> str:
    payload = research_market_maker_activity_anomaly_scorecard_payload(report)
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
            ResearchMarketMakerActivityAnomalyObservation,
            ResearchMarketMakerActivityAnomalyScoreRow,
        ):
            raise ValueError(
                "rows must contain ResearchMarketMakerActivityAnomalyObservation "
                "or ResearchMarketMakerActivityAnomalyScoreRow",
            )
        _require_hard_flags("row", row)
    return normalized


def _row_from_input_row(
    row: object,
    *,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> ResearchMarketMakerActivityAnomalyScoreRow:
    if type(row) is ResearchMarketMakerActivityAnomalyScoreRow:
        _validate_row_consistency(row, config=config)
        return row
    if type(row) is ResearchMarketMakerActivityAnomalyObservation:
        return _score_observation(row, config=config)
    raise ValueError("row must be a supported activity anomaly scorecard row")


def _score_observation(
    row: ResearchMarketMakerActivityAnomalyObservation,
    *,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> ResearchMarketMakerActivityAnomalyScoreRow:
    depth_imbalance_ratio = _depth_imbalance_ratio(
        row.bid_depth_units,
        row.ask_depth_units,
    )
    spread_widening_ratio = _spread_widening_ratio(
        current_spread_bps=row.current_spread_bps,
        baseline_spread_bps=row.baseline_spread_bps,
        config=config,
    )
    volume_burst_ratio = _volume_burst_ratio(
        current_volume_units=row.current_volume_units,
        baseline_volume_units=row.baseline_volume_units,
        config=config,
    )
    quote_freshness_score = _threshold_score(
        row.quote_age_seconds,
        pass_value=config.pass_quote_age_seconds,
        block_value=config.block_quote_age_seconds,
    )
    depth_imbalance_score = _threshold_score(
        depth_imbalance_ratio,
        pass_value=config.pass_depth_imbalance_ratio,
        block_value=config.block_depth_imbalance_ratio,
    )
    spread_widening_score = _threshold_score(
        spread_widening_ratio,
        pass_value=config.pass_spread_widening_ratio,
        block_value=config.block_spread_widening_ratio,
    )
    volume_burst_score = _threshold_score(
        volume_burst_ratio,
        pass_value=config.pass_volume_burst_ratio,
        block_value=config.block_volume_burst_ratio,
    )
    liquidity_concentration_score = _threshold_score(
        row.top_liquidity_share,
        pass_value=config.pass_top_liquidity_share,
        block_value=config.block_top_liquidity_share,
    )
    anomaly_score = _anomaly_score(
        quote_freshness_score=quote_freshness_score,
        depth_imbalance_score=depth_imbalance_score,
        spread_widening_score=spread_widening_score,
        volume_burst_score=volume_burst_score,
        liquidity_concentration_score=liquidity_concentration_score,
        config=config,
    )
    status = _row_status(anomaly_score, config=config)
    return ResearchMarketMakerActivityAnomalyScoreRow(
        research_bucket=row.research_bucket,
        public_event_label=row.public_event_label,
        observed_at=row.observed_at,
        quote_age_seconds=row.quote_age_seconds,
        bid_depth_units=row.bid_depth_units,
        ask_depth_units=row.ask_depth_units,
        current_spread_bps=row.current_spread_bps,
        baseline_spread_bps=row.baseline_spread_bps,
        current_volume_units=row.current_volume_units,
        baseline_volume_units=row.baseline_volume_units,
        top_liquidity_share=row.top_liquidity_share,
        quote_freshness_score=quote_freshness_score,
        depth_imbalance_ratio=depth_imbalance_ratio,
        depth_imbalance_score=depth_imbalance_score,
        spread_widening_ratio=spread_widening_ratio,
        spread_widening_score=spread_widening_score,
        volume_burst_ratio=volume_burst_ratio,
        volume_burst_score=volume_burst_score,
        liquidity_concentration_score=liquidity_concentration_score,
        anomaly_score=anomaly_score,
        status=status,
        reason_codes=_row_reason_codes(
            row,
            depth_imbalance_ratio=depth_imbalance_ratio,
            spread_widening_ratio=spread_widening_ratio,
            volume_burst_ratio=volume_burst_ratio,
            status=status,
            config=config,
        ),
        validation_config=config,
    )


def _row_reason_codes(
    row: ResearchMarketMakerActivityAnomalyObservation,
    *,
    depth_imbalance_ratio: Decimal,
    spread_widening_ratio: Decimal,
    volume_burst_ratio: Decimal,
    status: str,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"activity_anomaly_score_{status}"]
    if row.quote_age_seconds >= config.block_quote_age_seconds:
        reason_codes.append("quote_freshness_block")
    elif row.quote_age_seconds > config.pass_quote_age_seconds:
        reason_codes.append("quote_freshness_watch")
    if depth_imbalance_ratio >= config.block_depth_imbalance_ratio:
        reason_codes.append("depth_imbalance_high")
    elif depth_imbalance_ratio > config.pass_depth_imbalance_ratio:
        reason_codes.append("depth_imbalance_watch")
    if spread_widening_ratio >= config.block_spread_widening_ratio:
        reason_codes.append("spread_widening_high")
    elif spread_widening_ratio > config.pass_spread_widening_ratio:
        reason_codes.append("spread_widening_watch")
    if volume_burst_ratio >= config.block_volume_burst_ratio:
        reason_codes.append("volume_burst_high")
    elif volume_burst_ratio > config.pass_volume_burst_ratio:
        reason_codes.append("volume_burst_watch")
    if row.top_liquidity_share >= config.block_top_liquidity_share:
        reason_codes.append("liquidity_concentration_high")
    elif row.top_liquidity_share > config.pass_top_liquidity_share:
        reason_codes.append("liquidity_concentration_watch")
    for reason_code in row.reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _depth_imbalance_ratio(bid_depth_units: Decimal, ask_depth_units: Decimal) -> Decimal:
    total_depth = bid_depth_units + ask_depth_units
    if total_depth == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(abs(bid_depth_units - ask_depth_units) / total_depth)


def _spread_widening_ratio(
    *,
    current_spread_bps: Decimal,
    baseline_spread_bps: Decimal,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> Decimal:
    if baseline_spread_bps == ZERO:
        if current_spread_bps == ZERO:
            return ZERO.quantize(RATIO_QUANTUM)
        return config.block_spread_widening_ratio
    return _quantize(max(ZERO, current_spread_bps / baseline_spread_bps - ONE))


def _volume_burst_ratio(
    *,
    current_volume_units: Decimal,
    baseline_volume_units: Decimal,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> Decimal:
    if baseline_volume_units == ZERO:
        if current_volume_units == ZERO:
            return ONE.quantize(RATIO_QUANTUM)
        return config.block_volume_burst_ratio
    return _quantize(current_volume_units / baseline_volume_units)


def _threshold_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    block_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ZERO.quantize(RATIO_QUANTUM)
    if value >= block_value:
        return ONE.quantize(RATIO_QUANTUM)
    return _quantize((value - pass_value) / (block_value - pass_value))


def _anomaly_score(
    *,
    quote_freshness_score: Decimal,
    depth_imbalance_score: Decimal,
    spread_widening_score: Decimal,
    volume_burst_score: Decimal,
    liquidity_concentration_score: Decimal,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> Decimal:
    return _quantize(
        quote_freshness_score * config.quote_freshness_weight
        + depth_imbalance_score * config.depth_imbalance_weight
        + spread_widening_score * config.spread_widening_weight
        + volume_burst_score * config.volume_burst_weight
        + liquidity_concentration_score * config.liquidity_concentration_weight,
    )


def _row_status(
    anomaly_score: Decimal,
    *,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> str:
    if anomaly_score >= config.block_anomaly_score:
        return "block"
    if anomaly_score >= config.watch_anomaly_score:
        return "watch"
    return "pass"


def _validate_row_consistency(
    row: ResearchMarketMakerActivityAnomalyScoreRow,
    *,
    config: ResearchMarketMakerActivityAnomalyScorecardConfig,
) -> None:
    expected_depth_imbalance_ratio = _depth_imbalance_ratio(
        row.bid_depth_units,
        row.ask_depth_units,
    )
    expected_spread_widening_ratio = _spread_widening_ratio(
        current_spread_bps=row.current_spread_bps,
        baseline_spread_bps=row.baseline_spread_bps,
        config=config,
    )
    expected_volume_burst_ratio = _volume_burst_ratio(
        current_volume_units=row.current_volume_units,
        baseline_volume_units=row.baseline_volume_units,
        config=config,
    )
    expected_quote_freshness_score = _threshold_score(
        row.quote_age_seconds,
        pass_value=config.pass_quote_age_seconds,
        block_value=config.block_quote_age_seconds,
    )
    expected_depth_imbalance_score = _threshold_score(
        expected_depth_imbalance_ratio,
        pass_value=config.pass_depth_imbalance_ratio,
        block_value=config.block_depth_imbalance_ratio,
    )
    expected_spread_widening_score = _threshold_score(
        expected_spread_widening_ratio,
        pass_value=config.pass_spread_widening_ratio,
        block_value=config.block_spread_widening_ratio,
    )
    expected_volume_burst_score = _threshold_score(
        expected_volume_burst_ratio,
        pass_value=config.pass_volume_burst_ratio,
        block_value=config.block_volume_burst_ratio,
    )
    expected_liquidity_concentration_score = _threshold_score(
        row.top_liquidity_share,
        pass_value=config.pass_top_liquidity_share,
        block_value=config.block_top_liquidity_share,
    )
    expected_anomaly_score = _anomaly_score(
        quote_freshness_score=expected_quote_freshness_score,
        depth_imbalance_score=expected_depth_imbalance_score,
        spread_widening_score=expected_spread_widening_score,
        volume_burst_score=expected_volume_burst_score,
        liquidity_concentration_score=expected_liquidity_concentration_score,
        config=config,
    )
    if row.depth_imbalance_ratio != expected_depth_imbalance_ratio:
        raise ValueError("depth_imbalance_ratio must match row inputs")
    if row.spread_widening_ratio != expected_spread_widening_ratio:
        raise ValueError("spread_widening_ratio must match row inputs")
    if row.volume_burst_ratio != expected_volume_burst_ratio:
        raise ValueError("volume_burst_ratio must match row inputs")
    if row.quote_freshness_score != expected_quote_freshness_score:
        raise ValueError("quote_freshness_score must match row inputs")
    if row.depth_imbalance_score != expected_depth_imbalance_score:
        raise ValueError("depth_imbalance_score must match row inputs")
    if row.spread_widening_score != expected_spread_widening_score:
        raise ValueError("spread_widening_score must match row inputs")
    if row.volume_burst_score != expected_volume_burst_score:
        raise ValueError("volume_burst_score must match row inputs")
    if row.liquidity_concentration_score != expected_liquidity_concentration_score:
        raise ValueError("liquidity_concentration_score must match row inputs")
    if row.anomaly_score != expected_anomaly_score:
        raise ValueError("anomaly_score must match row inputs")
    if row.status != _row_status(row.anomaly_score, config=config):
        raise ValueError("status must match anomaly_score")


def _validate_report(report: ResearchMarketMakerActivityAnomalyScorecardReport) -> None:
    rows = report.rows
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.quote_freshness_count != _count(
        _reason_count(rows, "quote_freshness_watch")
        + _reason_count(rows, "quote_freshness_block"),
    ):
        raise ValueError("quote_freshness_count must match rows")
    if report.depth_imbalance_count != _count(
        _reason_count(rows, "depth_imbalance_watch")
        + _reason_count(rows, "depth_imbalance_high"),
    ):
        raise ValueError("depth_imbalance_count must match rows")
    if report.spread_widening_count != _count(
        _reason_count(rows, "spread_widening_watch")
        + _reason_count(rows, "spread_widening_high"),
    ):
        raise ValueError("spread_widening_count must match rows")
    if report.volume_burst_count != _count(
        _reason_count(rows, "volume_burst_watch")
        + _reason_count(rows, "volume_burst_high"),
    ):
        raise ValueError("volume_burst_count must match rows")
    if report.liquidity_concentration_count != _count(
        _reason_count(rows, "liquidity_concentration_watch")
        + _reason_count(rows, "liquidity_concentration_high"),
    ):
        raise ValueError("liquidity_concentration_count must match rows")
    if report.average_anomaly_score != _average_anomaly_score(rows):
        raise ValueError("average_anomaly_score must match rows")
    if report.max_anomaly_score != _max_anomaly_score(rows):
        raise ValueError("max_anomaly_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")


def _row_sort_key(
    row: ResearchMarketMakerActivityAnomalyScoreRow,
) -> tuple[int, str, str]:
    return (
        STATUS_VALUES.index(row.status),
        row.research_bucket,
        row.public_event_label,
    )


def _status_count(
    rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _average_anomaly_score(
    rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.anomaly_score for row in rows), ZERO) / Decimal(len(rows)))


def _max_anomaly_score(
    rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(max(row.anomaly_score for row in rows))


def _report_status(rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_activity_observations",)
    reason_codes: set[str] = set()
    for row in rows:
        reason_codes.update(row.reason_codes)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchMarketMakerActivityAnomalyScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketMakerActivityAnomalyReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketMakerActivityAnomalyReasonCodeCount(
                reason_code="no_activity_observations",
                count=Decimal("1"),
            ),
        )
    return tuple(
        ResearchMarketMakerActivityAnomalyReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
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


def _require_increasing_threshold(
    label: str,
    pass_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value <= pass_value:
        raise ValueError(f"block_{label} must exceed pass_{label}")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if _has_unsafe_fragment(value):
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
    if _has_unsafe_fragment(value):
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
        _reject_unsafe_public_payload(label, _json_ready(value), path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
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
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {label}")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _unsafe_fragments())


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "raw_" + "market",
        "market" + "_id",
        "condition" + "_id",
        "source" + "_id",
        "raw_" + "source",
        "wal" + "let",
        "a" + "uth",
        "to" + "ken",
        "api" + "_" + "key",
        "sec" + "ret",
        "cre" + "dential",
        "private" + "_" + "key",
        "ses" + "sion",
        "coo" + "kie",
        "bear" + "er",
        "or" + "der",
        "tra" + "de",
        "tra" + "ding",
        "li" + "ve",
        "b" + "uy",
        "s" + "ell",
        "reco" + "mmend",
        "position" + "_" + "size",
        "position " + "sizing",
    )


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = (
    "ResearchMarketMakerActivityAnomalyObservation",
    "ResearchMarketMakerActivityAnomalyReasonCodeCount",
    "ResearchMarketMakerActivityAnomalyScoreRow",
    "ResearchMarketMakerActivityAnomalyScorecardConfig",
    "ResearchMarketMakerActivityAnomalyScorecardReport",
    "build_research_market_maker_activity_anomaly_scorecard_report",
    "research_market_maker_activity_anomaly_scorecard_digest",
    "research_market_maker_activity_anomaly_scorecard_payload",
)
