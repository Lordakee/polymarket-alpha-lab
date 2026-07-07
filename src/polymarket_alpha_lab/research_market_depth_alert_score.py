"""Paper-only market depth alert scoring for manual research screening."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
NEGATIVE_ONE = Decimal("-1")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_PRIORITY = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
REASON_ORDER = (
    "redacted_depth_block",
    "liquidity_change_block",
    "spread_block",
    "cost_share_block",
    "redacted_depth_watch",
    "liquidity_change_watch",
    "spread_watch",
    "cost_share_watch",
    "depth_alert_pass",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source",
    "ref",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchMarketDepthAlertScoreConfig:
    config_version: str
    min_pass_depth_score: Decimal
    min_watch_depth_score: Decimal
    min_pass_liquidity_change_score: Decimal
    min_watch_liquidity_change_score: Decimal
    max_pass_spread: Decimal
    max_watch_spread: Decimal
    max_pass_cost_share: Decimal
    max_watch_cost_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_depth_score",
            "min_watch_depth_score",
            "max_pass_spread",
            "max_watch_spread",
            "max_pass_cost_share",
            "max_watch_cost_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_liquidity_change_score",
            "min_watch_liquidity_change_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_depth_score < self.min_watch_depth_score:
            raise ValueError("min_pass_depth_score must be at least min_watch_depth_score")
        if self.min_pass_liquidity_change_score < self.min_watch_liquidity_change_score:
            raise ValueError(
                "min_pass_liquidity_change_score must be at least "
                "min_watch_liquidity_change_score",
            )
        if self.max_pass_spread > self.max_watch_spread:
            raise ValueError("max_pass_spread must be at most max_watch_spread")
        if self.max_pass_cost_share > self.max_watch_cost_share:
            raise ValueError("max_pass_cost_share must be at most max_watch_cost_share")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketDepthAlertScoreObservation:
    private_candidate_id: str
    private_market_id: str
    private_market_slug: str
    private_market_question: str
    source_reference: str
    source_url: str
    source_text: str
    observed_at: datetime
    redacted_depth_score: Decimal
    liquidity_change_score: Decimal
    spread: Decimal
    cost_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "private_candidate_id",
            "private_market_id",
            "private_market_slug",
            "private_market_question",
            "source_reference",
            "source_url",
            "source_text",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "redacted_depth_score",
            _normalize_ratio_decimal("redacted_depth_score", self.redacted_depth_score),
        )
        object.__setattr__(
            self,
            "liquidity_change_score",
            _normalize_signed_ratio_decimal(
                "liquidity_change_score",
                self.liquidity_change_score,
            ),
        )
        for field_name in ("spread", "cost_share"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketDepthAlertScoreRow:
    review_rank: Decimal
    status: str
    reason_codes: tuple[str, ...]
    depth_band: str
    liquidity_change_band: str
    spread_band: str
    cost_share_band: str
    redacted_depth_score: Decimal
    liquidity_change_score: Decimal
    spread: Decimal
    cost_share: Decimal
    alert_score: Decimal
    operator_note: str = "manual_screen_only"
    observed_age_seconds: Decimal = ZERO
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "review_rank", _normalize_count("review_rank", self.review_rank))
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_member("depth_band", self.depth_band, ("deep", "adequate", "thin"))
        _require_member(
            "liquidity_change_band",
            self.liquidity_change_band,
            ("improving", "softening", "deteriorating"),
        )
        _require_member("spread_band", self.spread_band, ("tight", "wide", "very_wide"))
        _require_member("cost_share_band", self.cost_share_band, ("low", "elevated", "high"))
        object.__setattr__(
            self,
            "redacted_depth_score",
            _normalize_ratio_decimal("redacted_depth_score", self.redacted_depth_score),
        )
        object.__setattr__(
            self,
            "liquidity_change_score",
            _normalize_signed_ratio_decimal(
                "liquidity_change_score",
                self.liquidity_change_score,
            ),
        )
        for field_name in ("spread", "cost_share", "alert_score", "observed_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_or_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.alert_score > ONE:
            raise ValueError("alert_score must be at most one")
        _require_public_string("operator_note", self.operator_note)
        _require_hard_flags(self)
        _validate_row_consistency(self)
        _apply_or_verify_digest(self)
        _reject_unsafe_public_payload(_json_ready(asdict(self)))


@dataclass(frozen=True)
class ResearchMarketDepthAlertScoreReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_redacted_depth_score: Decimal
    min_liquidity_change_score: Decimal
    max_spread: Decimal
    max_cost_share: Decimal
    average_alert_score: Decimal
    rows: tuple[ResearchMarketDepthAlertScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_redacted_depth_score",
            "max_spread",
            "max_cost_share",
            "average_alert_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_liquidity_change_score",
            _normalize_signed_ratio_decimal(
                "min_liquidity_change_score",
                self.min_liquidity_change_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        _validate_report_consistency(self)
        _apply_or_verify_digest(self)
        _reject_unsafe_public_payload(_json_ready(asdict(self)))


def build_research_market_depth_alert_score_report(
    observations: Iterable[ResearchMarketDepthAlertScoreObservation],
    *,
    config: ResearchMarketDepthAlertScoreConfig,
    generated_at: datetime,
) -> ResearchMarketDepthAlertScoreReport:
    if type(config) is not ResearchMarketDepthAlertScoreConfig:
        raise ValueError("config must be a ResearchMarketDepthAlertScoreConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    row_inputs = tuple(
        sorted(
            (
                _row_input_from_observation(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in items
            ),
            key=_row_input_sort_key,
        ),
    )
    rows = tuple(
        _row_from_input(row_input, review_rank=_count(index))
        for index, row_input in enumerate(row_inputs, start=1)
    )
    return ResearchMarketDepthAlertScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        item_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        min_redacted_depth_score=_min_ratio(tuple(row.redacted_depth_score for row in rows)),
        min_liquidity_change_score=_min_signed_ratio(
            tuple(row.liquidity_change_score for row in rows),
        ),
        max_spread=_max_ratio(tuple(row.spread for row in rows)),
        max_cost_share=_max_ratio(tuple(row.cost_share for row in rows)),
        average_alert_score=_average_ratio(tuple(row.alert_score for row in rows)),
        rows=rows,
    )


def research_market_depth_alert_score_payload(
    report: ResearchMarketDepthAlertScoreReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthAlertScoreReport:
        raise ValueError("report must be a ResearchMarketDepthAlertScoreReport")
    _require_hard_flags(report)
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


@dataclass(frozen=True)
class _RowInput:
    private_sort_key: tuple[str, str]
    observed_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    depth_band: str
    liquidity_change_band: str
    spread_band: str
    cost_share_band: str
    redacted_depth_score: Decimal
    liquidity_change_score: Decimal
    spread: Decimal
    cost_share: Decimal
    alert_score: Decimal


def _row_input_from_observation(
    observation: ResearchMarketDepthAlertScoreObservation,
    *,
    config: ResearchMarketDepthAlertScoreConfig,
    generated_at: datetime,
) -> _RowInput:
    reason_codes = _row_reason_codes(
        redacted_depth_score=observation.redacted_depth_score,
        liquidity_change_score=observation.liquidity_change_score,
        spread=observation.spread,
        cost_share=observation.cost_share,
        config=config,
    )
    status = _row_status(reason_codes)
    return _RowInput(
        private_sort_key=(observation.private_market_id, observation.private_candidate_id),
        observed_age_seconds=_seconds_between(generated_at, observation.observed_at),
        status=status,
        reason_codes=reason_codes,
        depth_band=_depth_band(observation.redacted_depth_score, config),
        liquidity_change_band=_liquidity_change_band(
            observation.liquidity_change_score,
            config,
        ),
        spread_band=_spread_band(observation.spread, config),
        cost_share_band=_cost_share_band(observation.cost_share, config),
        redacted_depth_score=observation.redacted_depth_score,
        liquidity_change_score=observation.liquidity_change_score,
        spread=observation.spread,
        cost_share=observation.cost_share,
        alert_score=_alert_score(
            redacted_depth_score=observation.redacted_depth_score,
            liquidity_change_score=observation.liquidity_change_score,
            spread=observation.spread,
            cost_share=observation.cost_share,
        ),
    )


def _row_from_input(row_input: _RowInput, *, review_rank: Decimal) -> ResearchMarketDepthAlertScoreRow:
    return ResearchMarketDepthAlertScoreRow(
        review_rank=review_rank,
        status=row_input.status,
        reason_codes=row_input.reason_codes,
        depth_band=row_input.depth_band,
        liquidity_change_band=row_input.liquidity_change_band,
        spread_band=row_input.spread_band,
        cost_share_band=row_input.cost_share_band,
        redacted_depth_score=row_input.redacted_depth_score,
        liquidity_change_score=row_input.liquidity_change_score,
        spread=row_input.spread,
        cost_share=row_input.cost_share,
        alert_score=row_input.alert_score,
        observed_age_seconds=row_input.observed_age_seconds,
    )


def _row_reason_codes(
    *,
    redacted_depth_score: Decimal,
    liquidity_change_score: Decimal,
    spread: Decimal,
    cost_share: Decimal,
    config: ResearchMarketDepthAlertScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if redacted_depth_score < config.min_watch_depth_score:
        reason_codes.append("redacted_depth_block")
    elif redacted_depth_score < config.min_pass_depth_score:
        reason_codes.append("redacted_depth_watch")
    if liquidity_change_score < config.min_watch_liquidity_change_score:
        reason_codes.append("liquidity_change_block")
    elif liquidity_change_score < config.min_pass_liquidity_change_score:
        reason_codes.append("liquidity_change_watch")
    if spread > config.max_watch_spread:
        reason_codes.append("spread_block")
    elif spread > config.max_pass_spread:
        reason_codes.append("spread_watch")
    if cost_share > config.max_watch_cost_share:
        reason_codes.append("cost_share_block")
    elif cost_share > config.max_pass_cost_share:
        reason_codes.append("cost_share_watch")
    if not reason_codes:
        reason_codes.append("depth_alert_pass")
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchMarketDepthAlertScoreRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchMarketDepthAlertScoreRow, ...]) -> tuple[str, ...]:
    status = _report_status(rows)
    reason_codes = [f"market_depth_alert_score_{status}"]
    for reason_code in REASON_ORDER:
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _depth_band(
    redacted_depth_score: Decimal,
    config: ResearchMarketDepthAlertScoreConfig,
) -> str:
    if redacted_depth_score >= config.min_pass_depth_score:
        return "deep"
    if redacted_depth_score >= config.min_watch_depth_score:
        return "adequate"
    return "thin"


def _liquidity_change_band(
    liquidity_change_score: Decimal,
    config: ResearchMarketDepthAlertScoreConfig,
) -> str:
    if liquidity_change_score >= config.min_pass_liquidity_change_score:
        return "improving"
    if liquidity_change_score >= config.min_watch_liquidity_change_score:
        return "softening"
    return "deteriorating"


def _spread_band(spread: Decimal, config: ResearchMarketDepthAlertScoreConfig) -> str:
    if spread <= config.max_pass_spread:
        return "tight"
    if spread <= config.max_watch_spread:
        return "wide"
    return "very_wide"


def _cost_share_band(cost_share: Decimal, config: ResearchMarketDepthAlertScoreConfig) -> str:
    if cost_share <= config.max_pass_cost_share:
        return "low"
    if cost_share <= config.max_watch_cost_share:
        return "elevated"
    return "high"


def _alert_score(
    *,
    redacted_depth_score: Decimal,
    liquidity_change_score: Decimal,
    spread: Decimal,
    cost_share: Decimal,
) -> Decimal:
    score = _subtract_decimal(
        _add_decimal(redacted_depth_score, liquidity_change_score),
        _add_decimal(spread, cost_share),
    )
    if score < ZERO:
        return _quantize(ZERO)
    if score > ONE:
        return _quantize(ONE)
    return score


def _row_input_sort_key(row_input: _RowInput) -> tuple[Decimal, Decimal, Decimal, tuple[str, str]]:
    return (
        STATUS_PRIORITY[row_input.status],
        -row_input.alert_score,
        row_input.spread,
        row_input.private_sort_key,
    )


def _row_sort_key(row: ResearchMarketDepthAlertScoreRow) -> tuple[Decimal, Decimal]:
    return STATUS_PRIORITY[row.status], row.review_rank


def _normalize_observations(
    observations: Iterable[ResearchMarketDepthAlertScoreObservation],
) -> tuple[ResearchMarketDepthAlertScoreObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchMarketDepthAlertScoreObservation:
            raise ValueError(
                "observations must contain ResearchMarketDepthAlertScoreObservation values",
            )
        _require_hard_flags(observation)
        if observation.private_candidate_id in seen:
            raise ValueError("observations must not contain duplicate private_candidate_id values")
        seen.add(observation.private_candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketDepthAlertScoreRow],
) -> tuple[ResearchMarketDepthAlertScoreRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMarketDepthAlertScoreRow:
            raise ValueError("rows must contain ResearchMarketDepthAlertScoreRow values")
        _require_hard_flags(row)
        _verify_digest(row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and review_rank")
    return normalized


def _validate_row_consistency(row: ResearchMarketDepthAlertScoreRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("depth_alert_pass",):
        raise ValueError("reason_codes must match pass status")
    if row.alert_score != _alert_score(
        redacted_depth_score=row.redacted_depth_score,
        liquidity_change_score=row.liquidity_change_score,
        spread=row.spread,
        cost_share=row.cost_share,
    ):
        raise ValueError("alert_score must match depth, liquidity, spread, and cost")


def _validate_report_consistency(report: ResearchMarketDepthAlertScoreReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for index, row in enumerate(report.rows, start=1):
        if row.review_rank != _count(index):
            raise ValueError("review_rank must be sequential")
        _verify_digest(row)
    if report.min_redacted_depth_score != _min_ratio(
        tuple(row.redacted_depth_score for row in report.rows),
    ):
        raise ValueError("min_redacted_depth_score must match rows")
    if report.min_liquidity_change_score != _min_signed_ratio(
        tuple(row.liquidity_change_score for row in report.rows),
    ):
        raise ValueError("min_liquidity_change_score must match rows")
    if report.max_spread != _max_ratio(tuple(row.spread for row in report.rows)):
        raise ValueError("max_spread must match rows")
    if report.max_cost_share != _max_ratio(tuple(row.cost_share for row in report.rows)):
        raise ValueError("max_cost_share must match rows")
    if report.average_alert_score != _average_ratio(tuple(row.alert_score for row in report.rows)):
        raise ValueError("average_alert_score must match rows")


def _status_count(rows: tuple[ResearchMarketDepthAlertScoreRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize(ZERO)
    return _normalize_ratio_decimal("min_ratio", min(values))


def _min_signed_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize(ZERO)
    return _normalize_signed_ratio_decimal("min_signed_ratio", min(values))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize(ZERO)
    return _normalize_ratio_decimal("max_ratio", max(values))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize(ZERO)
    return _divide_decimal(_sum_decimals(values), Decimal(len(values)))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    normalized = _quantize(seconds + microseconds)
    if normalized < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_ratio_or_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    return normalized


def _normalize_signed_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < NEGATIVE_ONE:
        raise ValueError(f"{field_name} must be at least negative one")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for item in normalized:
        _require_public_string(field_name, item)
    return normalized


def _require_private_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _apply_or_verify_digest(
    value: ResearchMarketDepthAlertScoreRow | ResearchMarketDepthAlertScoreReport,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: ResearchMarketDepthAlertScoreRow | ResearchMarketDepthAlertScoreReport,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: ResearchMarketDepthAlertScoreRow | ResearchMarketDepthAlertScoreReport,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if _has_unsafe_public_fragment(key):
                raise ValueError("public payload contains unsafe public content")
            _require_public_string("public_payload_key", key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError("public payload contains unsafe public content")


def _json_ready(value: Any) -> Any:
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "ResearchMarketDepthAlertScoreConfig",
    "ResearchMarketDepthAlertScoreObservation",
    "ResearchMarketDepthAlertScoreReport",
    "ResearchMarketDepthAlertScoreRow",
    "build_research_market_depth_alert_score_report",
    "research_market_depth_alert_score_payload",
)
