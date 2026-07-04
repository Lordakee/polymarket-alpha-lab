"""Pure Phase 1 soccer transfer news digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_SOCCER_TRANSFER_NEWS_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-transfer-news-digest-v0"
)

INPUT_REASON_CODES = (
    "transfer_news_probability_high",
    "transfer_news_probability_watch",
    "transfer_news_probability_inline",
)
ROW_REASON_CODES = (
    "soccer_transfer_news_high_signal",
    "soccer_transfer_news_watch_signal",
    "soccer_transfer_news_inline_signal",
    "soccer_transfer_news_source_fresh",
    "soccer_transfer_news_source_stale",
)
REPORT_REASON_CODES = (
    "soccer_transfer_news_high_signal_present",
    "soccer_transfer_news_watch_signal_present",
    "soccer_transfer_news_stale_source_present",
    "soccer_transfer_news_digest_clear",
    "soccer_transfer_news_digest_empty",
)
REASON_COUNT_CODES = REPORT_REASON_CODES
SIGNAL_BUCKETS = ("high_signal", "watch_signal", "inline_signal")
SIGNAL_STATUSES = ("blocked", "watch", "pass")

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_TRANSFER_PROBABILITY = Decimal("0.500000")
HIGH_TRANSFER_PROBABILITY = Decimal("0.700000")
MAX_FRESH_SOURCE_AGE_SECONDS = Decimal("1200.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_SOCCER_TRANSFER_NEWS_DIGEST_CONFIG_VERSION",
    "SoccerTransferNewsDigestConfig",
    "SoccerTransferNewsItem",
    "SoccerTransferNewsDigestRow",
    "SoccerTransferNewsReasonCodeCount",
    "SoccerTransferNewsDigestReport",
    "build_market_research_soccer_transfer_news_digest",
    "market_research_soccer_transfer_news_digest_payload",
)


@dataclass(frozen=True)
class SoccerTransferNewsDigestConfig:
    config_version: str = DEFAULT_SOCCER_TRANSFER_NEWS_DIGEST_CONFIG_VERSION
    watch_transfer_probability: Decimal = WATCH_TRANSFER_PROBABILITY
    high_transfer_probability: Decimal = HIGH_TRANSFER_PROBABILITY
    max_fresh_source_age_seconds: Decimal = MAX_FRESH_SOURCE_AGE_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerTransferNewsDigestConfig:
            raise TypeError("SoccerTransferNewsDigestConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SoccerTransferNewsDigestConfig:
            raise ValueError("config must be exactly SoccerTransferNewsDigestConfig")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_SOCCER_TRANSFER_NEWS_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_transfer_probability",
            _require_probability("watch_transfer_probability", self.watch_transfer_probability),
        )
        object.__setattr__(
            self,
            "high_transfer_probability",
            _require_probability("high_transfer_probability", self.high_transfer_probability),
        )
        object.__setattr__(
            self,
            "max_fresh_source_age_seconds",
            _require_nonnegative_decimal(
                "max_fresh_source_age_seconds",
                self.max_fresh_source_age_seconds,
            ),
        )
        if self.high_transfer_probability < self.watch_transfer_probability:
            raise ValueError("high_transfer_probability must be at least watch threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SoccerTransferNewsItem:
    source_id: str
    player_ref: str
    club_ref: str
    market_slug: str
    headline_ref: str
    transfer_probability: Decimal
    confidence_score: Decimal
    source_age_seconds: Decimal
    mention_count: Decimal
    published_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerTransferNewsItem:
            raise TypeError("SoccerTransferNewsItem does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SoccerTransferNewsItem:
            raise ValueError("item must be exactly SoccerTransferNewsItem")
        for field_name in (
            "source_id",
            "player_ref",
            "club_ref",
            "market_slug",
            "headline_ref",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "transfer_probability",
            _require_probability("transfer_probability", self.transfer_probability),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_probability("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "mention_count",
            _require_nonnegative_decimal("mention_count", self.mention_count),
        )
        object.__setattr__(self, "published_at", _as_utc("published_at", self.published_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_item(self)
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class SoccerTransferNewsDigestRow:
    source_id: str
    player_ref: str
    club_ref: str
    market_slug: str
    headline_ref: str
    transfer_probability: Decimal
    confidence_score: Decimal
    source_age_seconds: Decimal
    mention_count: Decimal
    published_at: datetime
    signal_bucket: str
    signal_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerTransferNewsDigestRow:
            raise TypeError("SoccerTransferNewsDigestRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SoccerTransferNewsDigestRow:
            raise ValueError("row must be exactly SoccerTransferNewsDigestRow")
        for field_name in (
            "source_id",
            "player_ref",
            "club_ref",
            "market_slug",
            "headline_ref",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "transfer_probability",
            _require_probability("transfer_probability", self.transfer_probability),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_probability("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "mention_count",
            _require_nonnegative_decimal("mention_count", self.mention_count),
        )
        object.__setattr__(self, "published_at", _as_utc("published_at", self.published_at))
        _require_member("signal_bucket", self.signal_bucket, SIGNAL_BUCKETS)
        _require_member("signal_status", self.signal_status, SIGNAL_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SoccerTransferNewsReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerTransferNewsReasonCodeCount:
            raise TypeError("SoccerTransferNewsReasonCodeCount does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SoccerTransferNewsReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly SoccerTransferNewsReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_COUNT_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class SoccerTransferNewsDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    high_signal_count: Decimal
    watch_signal_count: Decimal
    inline_signal_count: Decimal
    stale_source_count: Decimal
    max_transfer_probability: Decimal
    average_confidence_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[SoccerTransferNewsDigestRow, ...]
    reason_code_counts: tuple[SoccerTransferNewsReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerTransferNewsDigestReport:
            raise TypeError("SoccerTransferNewsDigestReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SoccerTransferNewsDigestReport:
            raise ValueError("report must be exactly SoccerTransferNewsDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_SOCCER_TRANSFER_NEWS_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "high_signal_count",
            "watch_signal_count",
            "inline_signal_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_transfer_probability",
            _require_probability("max_transfer_probability", self.max_transfer_probability),
        )
        object.__setattr__(
            self,
            "average_confidence_score",
            _require_probability("average_confidence_score", self.average_confidence_score),
        )
        _require_member("digest_status", self.digest_status, SIGNAL_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_soccer_transfer_news_digest(
    inputs: Iterable[SoccerTransferNewsItem],
    *,
    config: SoccerTransferNewsDigestConfig,
    generated_at: datetime,
) -> SoccerTransferNewsDigestReport:
    if type(config) is not SoccerTransferNewsDigestConfig:
        raise ValueError("config must be exactly SoccerTransferNewsDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_for_item(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    return SoccerTransferNewsDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=row_count,
        high_signal_count=_bucket_count(rows, "high_signal"),
        watch_signal_count=_bucket_count(rows, "watch_signal"),
        inline_signal_count=_bucket_count(rows, "inline_signal"),
        stale_source_count=_reason_count(rows, "soccer_transfer_news_source_stale"),
        max_transfer_probability=max(
            (row.transfer_probability for row in rows),
            default=ZERO,
        ),
        average_confidence_score=_ratio(
            _sum_decimal(row.confidence_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, row_count),
        reason_codes=reason_codes,
    )


def market_research_soccer_transfer_news_digest_payload(
    report: SoccerTransferNewsDigestReport,
) -> dict[str, Any]:
    if type(report) is not SoccerTransferNewsDigestReport:
        raise ValueError("report must be exactly SoccerTransferNewsDigestReport")
    return _json_ready(asdict(report))


def _row_for_item(
    item: SoccerTransferNewsItem,
    *,
    config: SoccerTransferNewsDigestConfig,
) -> SoccerTransferNewsDigestRow:
    bucket = _signal_bucket(item.transfer_probability, config=config)
    status = _signal_status(bucket)
    source_fresh = item.source_age_seconds <= config.max_fresh_source_age_seconds
    return SoccerTransferNewsDigestRow(
        source_id=item.source_id,
        player_ref=item.player_ref,
        club_ref=item.club_ref,
        market_slug=item.market_slug,
        headline_ref=item.headline_ref,
        transfer_probability=item.transfer_probability,
        confidence_score=item.confidence_score,
        source_age_seconds=item.source_age_seconds,
        mention_count=item.mention_count,
        published_at=item.published_at,
        signal_bucket=bucket,
        signal_status=status,
        reason_codes=_row_reason_codes(bucket=bucket, source_fresh=source_fresh),
    )


def _signal_bucket(
    transfer_probability: Decimal,
    *,
    config: SoccerTransferNewsDigestConfig,
) -> str:
    if transfer_probability >= config.high_transfer_probability:
        return "high_signal"
    if transfer_probability >= config.watch_transfer_probability:
        return "watch_signal"
    return "inline_signal"


def _signal_status(signal_bucket: str) -> str:
    if signal_bucket == "high_signal":
        return "blocked"
    if signal_bucket == "watch_signal":
        return "watch"
    return "pass"


def _input_reason_codes(transfer_probability: Decimal) -> tuple[str, ...]:
    if transfer_probability >= HIGH_TRANSFER_PROBABILITY:
        return ("transfer_news_probability_high",)
    if transfer_probability >= WATCH_TRANSFER_PROBABILITY:
        return ("transfer_news_probability_watch",)
    return ("transfer_news_probability_inline",)


def _row_reason_codes(*, bucket: str, source_fresh: bool) -> tuple[str, ...]:
    primary = {
        "high_signal": "soccer_transfer_news_high_signal",
        "watch_signal": "soccer_transfer_news_watch_signal",
        "inline_signal": "soccer_transfer_news_inline_signal",
    }[bucket]
    source_reason = (
        "soccer_transfer_news_source_fresh"
        if source_fresh
        else "soccer_transfer_news_source_stale"
    )
    return _normalize_reason_codes(
        "reason_codes",
        (primary, source_reason),
        ROW_REASON_CODES,
    )


def _report_reason_codes(
    rows: tuple[SoccerTransferNewsDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("soccer_transfer_news_digest_empty",)
    reasons: list[str] = []
    if any(row.signal_bucket == "high_signal" for row in rows):
        reasons.append("soccer_transfer_news_high_signal_present")
    if any(row.signal_bucket == "watch_signal" for row in rows):
        reasons.append("soccer_transfer_news_watch_signal_present")
    if any("soccer_transfer_news_source_stale" in row.reason_codes for row in rows):
        reasons.append("soccer_transfer_news_stale_source_present")
    if not reasons:
        reasons.append("soccer_transfer_news_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    row_count: Decimal,
) -> tuple[SoccerTransferNewsReasonCodeCount, ...]:
    if reason_codes == ("soccer_transfer_news_digest_empty",):
        return (
            SoccerTransferNewsReasonCodeCount(
                reason_code="soccer_transfer_news_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        SoccerTransferNewsReasonCodeCount(
            reason_code=reason_code,
            count=ONE,
            row_ratio=_ratio(ONE, row_count),
        )
        for reason_code in reason_codes
    )


def _digest_status(rows: tuple[SoccerTransferNewsDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.signal_status == "blocked" for row in rows):
        return "blocked"
    if any(row.signal_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_soccer_transfer_news_digest"
    if status == "watch":
        return "monitor_report_only_market_research_soccer_transfer_news_digest"
    return "block_report_only_market_research_soccer_transfer_news_digest"


def _validate_item(item: SoccerTransferNewsItem) -> None:
    if item.reason_codes != _input_reason_codes(item.transfer_probability):
        raise ValueError("reason_codes must match transfer_probability")


def _validate_row(row: SoccerTransferNewsDigestRow) -> None:
    if row.signal_bucket != _signal_bucket(
        row.transfer_probability,
        config=SoccerTransferNewsDigestConfig(),
    ):
        raise ValueError("signal_bucket must match transfer_probability")
    if row.signal_status != _signal_status(row.signal_bucket):
        raise ValueError("signal_status must match signal_bucket")
    source_fresh = row.source_age_seconds <= MAX_FRESH_SOURCE_AGE_SECONDS
    if row.reason_codes != _row_reason_codes(
        bucket=row.signal_bucket,
        source_fresh=source_fresh,
    ):
        raise ValueError("reason_codes must match signal_bucket and source age")


def _validate_report(report: SoccerTransferNewsDigestReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.high_signal_count != _bucket_count(report.rows, "high_signal"):
        raise ValueError("high_signal_count must match rows")
    if report.watch_signal_count != _bucket_count(report.rows, "watch_signal"):
        raise ValueError("watch_signal_count must match rows")
    if report.inline_signal_count != _bucket_count(report.rows, "inline_signal"):
        raise ValueError("inline_signal_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "soccer_transfer_news_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.max_transfer_probability != max(
        (row.transfer_probability for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_transfer_probability must match rows")
    if report.average_confidence_score != _ratio(
        _sum_decimal(row.confidence_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_confidence_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.row_count,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: Iterable[SoccerTransferNewsItem],
) -> tuple[SoccerTransferNewsItem, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must contain soccer transfer news items")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must contain soccer transfer news items") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not SoccerTransferNewsItem:
            raise ValueError("inputs must contain SoccerTransferNewsItem")
        if item.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen.add(item.source_id)
    return normalized


def _normalize_rows(value: object) -> tuple[SoccerTransferNewsDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain soccer transfer news digest rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain soccer transfer news digest rows") from exc
    for row in rows:
        if type(row) is not SoccerTransferNewsDigestRow:
            raise ValueError("rows must contain SoccerTransferNewsDigestRow")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.source_id for row in rows}) != len(rows):
        raise ValueError("rows must not contain duplicate source_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[SoccerTransferNewsReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not SoccerTransferNewsReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain SoccerTransferNewsReasonCodeCount",
            )
    if counts != tuple(
        sorted(counts, key=lambda item: REASON_COUNT_CODES.index(item.reason_code))
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code))
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(row: SoccerTransferNewsDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.signal_status],
        -row.transfer_probability,
        row.market_slug,
        row.source_id,
    )


def _bucket_count(rows: tuple[SoccerTransferNewsDigestRow, ...], bucket: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.signal_bucket == bucket))


def _reason_count(rows: tuple[SoccerTransferNewsDigestRow, ...], reason_code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
