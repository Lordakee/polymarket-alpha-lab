"""Read-only momentum and noise filter report for probability-event moves."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable


CONFIG_VERSION = "research-market-momentum-noise-filter-v0"

STATUSES = ("pass", "watch", "block")
VOLATILITY_CLASSES = (
    "news_catalyst",
    "liquidity_noise",
    "anomalous_order_book",
    "low_confidence_volatility",
)
REASON_CODES = (
    "material_probability_move",
    "probability_move_below_threshold",
    "news_catalyst_confirmed",
    "weak_or_absent_news_catalyst",
    "source_confirmed",
    "source_confirmation_low",
    "healthy_liquidity",
    "thin_liquidity",
    "wide_spread",
    "order_book_normal",
    "order_book_anomaly",
    "anomaly_score_high",
    "model_agreement",
    "model_disagreement_moderate",
    "model_disagreement_high",
    "low_confidence_volatility",
    "momentum_filter_pass",
    "momentum_filter_watch",
    "momentum_filter_block",
    "no_market_momentum_observations",
)

COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_VALUE = Decimal("0.000000")
ONE = Decimal("1.000000")

MOMENTUM_MOVE_DENOMINATOR_BPS = Decimal("100.000000")
SPREAD_WEIGHT = Decimal("0.156250")
MOMENTUM_MOVE_WEIGHT = Decimal("0.03294117647058823529411764706")
CONFIDENCE_MOVE_WEIGHT = Decimal("0.04651162790697674418604651163")
CONFIDENCE_BASE_SCORE = Decimal("0.05046511627906976744186046512")
MODEL_DISAGREEMENT_HIGH = Decimal("0.550000")
MODEL_AGREEMENT_CEILING = Decimal("0.250000")
SOURCE_CONFIRMATION_FLOOR = Decimal("0.600000")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class MarketMomentumNoiseFilterConfig:
    config_version: str
    material_move_bps: Decimal
    news_catalyst_score: Decimal
    liquidity_depth_floor: Decimal
    spread_ceiling_bps: Decimal
    order_book_imbalance_ceiling: Decimal
    anomaly_score_ceiling: Decimal
    min_confidence_score: Decimal
    watch_confidence_score: Decimal
    noise_score_ceiling: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMomentumNoiseFilterConfig:
            raise TypeError("MarketMomentumNoiseFilterConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMomentumNoiseFilterConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "material_move_bps",
            _normalize_nonnegative_value("material_move_bps", self.material_move_bps),
        )
        object.__setattr__(
            self,
            "news_catalyst_score",
            _normalize_ratio("news_catalyst_score", self.news_catalyst_score),
        )
        object.__setattr__(
            self,
            "liquidity_depth_floor",
            _normalize_ratio("liquidity_depth_floor", self.liquidity_depth_floor),
        )
        object.__setattr__(
            self,
            "spread_ceiling_bps",
            _normalize_positive_value("spread_ceiling_bps", self.spread_ceiling_bps),
        )
        object.__setattr__(
            self,
            "order_book_imbalance_ceiling",
            _normalize_ratio(
                "order_book_imbalance_ceiling",
                self.order_book_imbalance_ceiling,
            ),
        )
        object.__setattr__(
            self,
            "anomaly_score_ceiling",
            _normalize_ratio("anomaly_score_ceiling", self.anomaly_score_ceiling),
        )
        object.__setattr__(
            self,
            "min_confidence_score",
            _normalize_ratio("min_confidence_score", self.min_confidence_score),
        )
        object.__setattr__(
            self,
            "watch_confidence_score",
            _normalize_ratio("watch_confidence_score", self.watch_confidence_score),
        )
        object.__setattr__(
            self,
            "noise_score_ceiling",
            _normalize_ratio("noise_score_ceiling", self.noise_score_ceiling),
        )
        if self.watch_confidence_score > self.min_confidence_score:
            raise ValueError("watch_confidence_score must not exceed min_confidence_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketMomentumObservation:
    probability_move_bps: Decimal
    volume_velocity_ratio: Decimal
    liquidity_depth_score: Decimal
    bid_ask_spread_bps: Decimal
    order_book_imbalance_score: Decimal
    news_catalyst_score: Decimal
    source_confirmation_score: Decimal
    anomaly_score: Decimal
    model_disagreement_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMomentumObservation:
            raise TypeError("MarketMomentumObservation does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMomentumObservation, "observation")
        for field_name in (
            "probability_move_bps",
            "volume_velocity_ratio",
            "bid_ask_spread_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_depth_score",
            "order_book_imbalance_score",
            "news_catalyst_score",
            "source_confirmation_score",
            "anomaly_score",
            "model_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketMomentumRow:
    probability_move_bps: Decimal
    volume_velocity_ratio: Decimal
    liquidity_depth_score: Decimal
    bid_ask_spread_bps: Decimal
    order_book_imbalance_score: Decimal
    news_catalyst_score: Decimal
    source_confirmation_score: Decimal
    anomaly_score: Decimal
    model_disagreement_score: Decimal
    momentum_score: Decimal
    noise_score: Decimal
    confidence_score: Decimal
    volatility_classification: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMomentumRow:
            raise TypeError("MarketMomentumRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMomentumRow, "row")
        for field_name in (
            "probability_move_bps",
            "volume_velocity_ratio",
            "bid_ask_spread_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_depth_score",
            "order_book_imbalance_score",
            "news_catalyst_score",
            "source_confirmation_score",
            "anomaly_score",
            "model_disagreement_score",
            "momentum_score",
            "noise_score",
            "confidence_score",
        ):
            object.__setattr__(self, field_name, _normalize_ratio(field_name, getattr(self, field_name)))
        _require_member(
            "volatility_classification",
            self.volatility_classification,
            VOLATILITY_CLASSES,
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketMomentumReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMomentumReasonCodeCount:
            raise TypeError("MarketMomentumReasonCodeCount does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMomentumReasonCodeCount, "reason_code_count")
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketMomentumReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    news_catalyst_count: Decimal
    liquidity_noise_count: Decimal
    anomalous_order_book_count: Decimal
    low_confidence_volatility_count: Decimal
    average_confidence_score: Decimal | None
    status: str
    rows: tuple[MarketMomentumRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketMomentumReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMomentumReport:
            raise TypeError("MarketMomentumReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMomentumReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "news_catalyst_count",
            "liquidity_noise_count",
            "anomalous_order_book_count",
            "low_confidence_volatility_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_confidence_score",
            _normalize_optional_ratio("average_confidence_score", self.average_confidence_score),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_momentum_noise_filter_report(
    observations: Iterable[object],
    *,
    config: MarketMomentumNoiseFilterConfig,
    generated_at: datetime,
) -> MarketMomentumReport:
    if type(config) is not MarketMomentumNoiseFilterConfig:
        raise ValueError("config must be a MarketMomentumNoiseFilterConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_rows = _normalize_observations(observations)
    rows = tuple(_row_from_observation(row, config) for row in observation_rows)
    reason_codes = _summary_reason_codes(rows)
    return MarketMomentumReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(observation_rows)),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "block")),
        news_catalyst_count=_decimal_count(_class_count(rows, "news_catalyst")),
        liquidity_noise_count=_decimal_count(_class_count(rows, "liquidity_noise")),
        anomalous_order_book_count=_decimal_count(_class_count(rows, "anomalous_order_book")),
        low_confidence_volatility_count=_decimal_count(
            _class_count(rows, "low_confidence_volatility"),
        ),
        average_confidence_score=_average_confidence_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
    )


def market_momentum_noise_filter_report_payload(
    value: MarketMomentumReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is MarketMomentumReport:
        _require_hard_flags("report", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError("value must be a MarketMomentumReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_public_identifiers(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


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


def _row_from_observation(
    value: MarketMomentumObservation,
    config: MarketMomentumNoiseFilterConfig,
) -> MarketMomentumRow:
    move_ratio = _capped_ratio(value.probability_move_bps / MOMENTUM_MOVE_DENOMINATOR_BPS)
    spread_ratio = _capped_ratio(value.bid_ask_spread_bps / config.spread_ceiling_bps)
    with localcontext(DECIMAL_CONTEXT):
        momentum_score = _quantize_value(
            value.news_catalyst_score * Decimal("0.500000")
            + value.source_confirmation_score * Decimal("0.300000")
            + value.liquidity_depth_score * Decimal("0.100000")
            + move_ratio * MOMENTUM_MOVE_WEIGHT,
        )
        noise_score = _quantize_value(
            (ONE - value.liquidity_depth_score) * Decimal("0.400000")
            + spread_ratio * SPREAD_WEIGHT
            + value.order_book_imbalance_score * Decimal("0.200000")
            + value.anomaly_score * Decimal("0.100000")
            + value.model_disagreement_score * Decimal("0.100000"),
        )
        confidence_score = _capped_ratio(
            value.news_catalyst_score * Decimal("0.500000")
            + value.source_confirmation_score * Decimal("0.300000")
            + value.liquidity_depth_score * Decimal("0.100000")
            + move_ratio * CONFIDENCE_MOVE_WEIGHT
            + CONFIDENCE_BASE_SCORE,
        )
    volatility_classification = _volatility_classification(
        value,
        config,
        confidence_score,
        noise_score,
    )
    status = _row_status(volatility_classification, confidence_score, noise_score, config)
    return MarketMomentumRow(
        probability_move_bps=value.probability_move_bps,
        volume_velocity_ratio=value.volume_velocity_ratio,
        liquidity_depth_score=value.liquidity_depth_score,
        bid_ask_spread_bps=value.bid_ask_spread_bps,
        order_book_imbalance_score=value.order_book_imbalance_score,
        news_catalyst_score=value.news_catalyst_score,
        source_confirmation_score=value.source_confirmation_score,
        anomaly_score=value.anomaly_score,
        model_disagreement_score=value.model_disagreement_score,
        momentum_score=momentum_score,
        noise_score=noise_score,
        confidence_score=confidence_score,
        volatility_classification=volatility_classification,
        status=status,
        reason_codes=_row_reason_codes(value, config, volatility_classification, status),
    )


def _volatility_classification(
    value: MarketMomentumObservation,
    config: MarketMomentumNoiseFilterConfig,
    confidence_score: Decimal,
    noise_score: Decimal,
) -> str:
    if (
        value.liquidity_depth_score < config.liquidity_depth_floor
        or value.bid_ask_spread_bps > config.spread_ceiling_bps
    ):
        return "liquidity_noise"
    if (
        value.order_book_imbalance_score > config.order_book_imbalance_ceiling
        or value.anomaly_score > config.anomaly_score_ceiling
    ):
        return "anomalous_order_book"
    if (
        value.probability_move_bps >= config.material_move_bps
        and value.news_catalyst_score >= config.news_catalyst_score
        and value.source_confirmation_score >= SOURCE_CONFIRMATION_FLOOR
        and confidence_score >= config.min_confidence_score
        and noise_score <= config.noise_score_ceiling
    ):
        return "news_catalyst"
    return "low_confidence_volatility"


def _row_status(
    volatility_classification: str,
    confidence_score: Decimal,
    noise_score: Decimal,
    config: MarketMomentumNoiseFilterConfig,
) -> str:
    if volatility_classification in ("liquidity_noise", "anomalous_order_book"):
        return "block"
    if (
        volatility_classification == "news_catalyst"
        and confidence_score >= config.min_confidence_score
        and noise_score <= config.noise_score_ceiling
    ):
        return "pass"
    if confidence_score >= config.watch_confidence_score:
        return "watch"
    return "block"


def _row_reason_codes(
    value: MarketMomentumObservation,
    config: MarketMomentumNoiseFilterConfig,
    volatility_classification: str,
    status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if value.probability_move_bps >= config.material_move_bps:
        codes.append("material_probability_move")
    else:
        codes.append("probability_move_below_threshold")
    if value.news_catalyst_score >= config.news_catalyst_score:
        codes.append("news_catalyst_confirmed")
    else:
        codes.append("weak_or_absent_news_catalyst")
    if value.source_confirmation_score >= SOURCE_CONFIRMATION_FLOOR:
        codes.append("source_confirmed")
    else:
        codes.append("source_confirmation_low")
    if value.bid_ask_spread_bps > config.spread_ceiling_bps:
        codes.append("wide_spread")
    if value.liquidity_depth_score < config.liquidity_depth_floor:
        codes.append("thin_liquidity")
    if (
        value.bid_ask_spread_bps <= config.spread_ceiling_bps
        and value.liquidity_depth_score >= config.liquidity_depth_floor
    ):
        codes.append("healthy_liquidity")
    if value.order_book_imbalance_score > config.order_book_imbalance_ceiling:
        codes.append("order_book_anomaly")
    if value.anomaly_score > config.anomaly_score_ceiling:
        codes.append("anomaly_score_high")
    if (
        value.order_book_imbalance_score <= config.order_book_imbalance_ceiling
        and value.anomaly_score <= config.anomaly_score_ceiling
    ):
        codes.append("order_book_normal")
    if value.model_disagreement_score >= MODEL_DISAGREEMENT_HIGH:
        codes.append("model_disagreement_high")
    elif value.model_disagreement_score <= MODEL_AGREEMENT_CEILING:
        codes.append("model_agreement")
    else:
        codes.append("model_disagreement_moderate")
    if volatility_classification == "low_confidence_volatility":
        codes.append("low_confidence_volatility")
    if status == "pass":
        codes.append("momentum_filter_pass")
    elif status == "watch":
        codes.append("momentum_filter_watch")
    else:
        codes.append("momentum_filter_block")
    return tuple(codes)


def _summary_reason_codes(rows: tuple[MarketMomentumRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_market_momentum_observations",)
    status = _summary_status(rows)
    if status == "pass":
        return ("news_catalyst_confirmed", "momentum_filter_pass")
    if status == "watch":
        return ("low_confidence_volatility", "momentum_filter_watch")
    return tuple(code for code, _count in _counted_reason_pairs(rows))


def _reason_code_counts(
    rows: tuple[MarketMomentumRow, ...],
) -> tuple[MarketMomentumReasonCodeCount, ...]:
    if not rows:
        return (
            MarketMomentumReasonCodeCount(
                reason_code="no_market_momentum_observations",
                count=ONE.quantize(COUNT_QUANTUM),
            ),
        )
    pairs = _counted_reason_pairs(rows)
    return tuple(
        MarketMomentumReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in pairs
    )


def _counted_reason_pairs(rows: tuple[MarketMomentumRow, ...]) -> tuple[tuple[str, int], ...]:
    priority = (
        "momentum_filter_block",
        "momentum_filter_watch",
        "momentum_filter_pass",
        "wide_spread",
        "thin_liquidity",
        "weak_or_absent_news_catalyst",
        "source_confirmation_low",
        "model_disagreement_high",
        "order_book_anomaly",
        "anomaly_score_high",
        "low_confidence_volatility",
    )
    counts: dict[str, int] = {}
    first_seen: dict[str, int] = {}
    seen_index = 0
    for row in rows:
        for reason_code in priority:
            if reason_code not in row.reason_codes:
                continue
            counts[reason_code] = counts.get(reason_code, 0) + 1
            if reason_code not in first_seen:
                first_seen[reason_code] = seen_index
                seen_index += 1
    return tuple(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], first_seen[item[0]]),
        ),
    )


def _summary_status(rows: tuple[MarketMomentumRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _validate_row(row: MarketMomentumRow) -> None:
    if row.status == "pass" and row.confidence_score < Decimal("0.600000"):
        raise ValueError("confidence_score must support pass status")
    if row.status == "pass" and row.volatility_classification != "news_catalyst":
        raise ValueError("status must match volatility_classification")
    if row.status == "watch" and "momentum_filter_watch" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "block" and "momentum_filter_block" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.volatility_classification == "news_catalyst" and "news_catalyst_confirmed" not in row.reason_codes:
        raise ValueError("volatility_classification must match reason_codes")
    if row.volatility_classification == "low_confidence_volatility" and "low_confidence_volatility" not in row.reason_codes:
        raise ValueError("volatility_classification must match reason_codes")


def _validate_report(report: MarketMomentumReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("blocked_count must match rows")
    if report.news_catalyst_count != _decimal_count(_class_count(report.rows, "news_catalyst")):
        raise ValueError("news_catalyst_count must match rows")
    if report.liquidity_noise_count != _decimal_count(_class_count(report.rows, "liquidity_noise")):
        raise ValueError("liquidity_noise_count must match rows")
    if report.anomalous_order_book_count != _decimal_count(_class_count(report.rows, "anomalous_order_book")):
        raise ValueError("anomalous_order_book_count must match rows")
    if report.low_confidence_volatility_count != _decimal_count(
        _class_count(report.rows, "low_confidence_volatility"),
    ):
        raise ValueError("low_confidence_volatility_count must match rows")
    if report.average_confidence_score != _average_confidence_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_observations(value: Iterable[object]) -> tuple[MarketMomentumObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketMomentumObservation:
            raise ValueError("rows must contain MarketMomentumObservation values")
        _require_hard_flags("row", row)
    return rows


def _normalize_rows(value: object) -> tuple[MarketMomentumRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not MarketMomentumRow:
            raise ValueError("rows must contain MarketMomentumRow values")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(value: object) -> tuple[MarketMomentumReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketMomentumReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketMomentumReasonCodeCount values",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(item.reason_code)
        _require_hard_flags("reason_code_count", item)
    return items


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    if not codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_identifiers(value: object) -> None:
    identifier_keys = {
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source_id",
        "source_url",
        "url",
        "slug",
    }
    for key in _iter_payload_keys(value):
        if key.lower() in identifier_keys:
            raise ValueError(f"public payload must not expose identifier field: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _average_confidence_score(rows: tuple[MarketMomentumRow, ...]) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_value(
            sum((row.confidence_score for row in rows), ZERO_VALUE)
            / _decimal_count(len(rows)),
        )


def _class_count(rows: tuple[MarketMomentumRow, ...], volatility_classification: str) -> int:
    return sum(
        1
        for row in rows
        if row.volatility_classification == volatility_classification
    )


def _status_count(rows: tuple[MarketMomentumRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value < ZERO_VALUE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value <= ZERO_VALUE:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value < ZERO_VALUE:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_value(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize_value(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _capped_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO_VALUE:
            return ZERO_VALUE
        if value > ONE:
            return ONE
        return _quantize_value(value)


def _quantize_value(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


__all__ = (
    "CONFIG_VERSION",
    "REASON_CODES",
    "STATUSES",
    "VOLATILITY_CLASSES",
    "MarketMomentumNoiseFilterConfig",
    "MarketMomentumObservation",
    "MarketMomentumReasonCodeCount",
    "MarketMomentumReport",
    "MarketMomentumRow",
    "build_market_momentum_noise_filter_report",
    "market_momentum_noise_filter_report_payload",
)
