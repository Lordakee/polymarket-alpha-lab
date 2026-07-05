"""Pure Phase 1 market research calendar catalyst reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION = (
    "market-research-calendar-catalyst-digest-v0"
)
DIGEST_STATUSES = ("ready", "watch", "blocked")
NO_INPUTS_REASON = "market_research_calendar_catalyst_digest_no_inputs"
READY_REASON = "market_research_calendar_catalyst_digest_ready"
WATCH_REASON = "market_research_calendar_catalyst_digest_watch_window"
STALE_RESEARCH_REASON = "market_research_calendar_catalyst_digest_stale_research"
THIN_REFERENCES_REASON = "market_research_calendar_catalyst_digest_thin_references"
ELAPSED_REASON = "market_research_calendar_catalyst_digest_elapsed"
REPORT_REASON_CODE_SEQUENCE = (
    ELAPSED_REASON,
    NO_INPUTS_REASON,
    READY_REASON,
    STALE_RESEARCH_REASON,
    THIN_REFERENCES_REASON,
    WATCH_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    ELAPSED_REASON,
    READY_REASON,
    STALE_RESEARCH_REASON,
    THIN_REFERENCES_REASON,
    WATCH_REASON,
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION",
    "MarketResearchCalendarCatalystDigestConfig",
    "MarketResearchCalendarCatalystDigestInputRow",
    "MarketResearchCalendarCatalystDigestReasonCodeCount",
    "MarketResearchCalendarCatalystDigestReport",
    "MarketResearchCalendarCatalystDigestRow",
    "build_market_research_calendar_catalyst_digest",
    "market_research_calendar_catalyst_digest_json",
)


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


@dataclass(frozen=True)
class MarketResearchCalendarCatalystDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION
    watch_within_seconds: Decimal = Decimal("86400.000000")
    stale_research_after_seconds: Decimal = Decimal("7200.000000")
    min_reference_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCalendarCatalystDigestConfig:
            raise TypeError(
                "MarketResearchCalendarCatalystDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCalendarCatalystDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCalendarCatalystDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config_version")
        object.__setattr__(
            self,
            "watch_within_seconds",
            _require_positive_decimal("watch_within_seconds", self.watch_within_seconds),
        )
        object.__setattr__(
            self,
            "stale_research_after_seconds",
            _require_positive_decimal(
                "stale_research_after_seconds",
                self.stale_research_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_reference_count",
            _require_positive_count_decimal("min_reference_count", self.min_reference_count),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCalendarCatalystDigestInputRow:
    market_research_key: str
    catalyst_key: str
    catalyst_family: str
    catalyst_reference: str
    catalyst_at: datetime
    research_observed_at: datetime
    reference_count: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCalendarCatalystDigestInputRow:
            raise TypeError(
                "MarketResearchCalendarCatalystDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCalendarCatalystDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchCalendarCatalystDigestInputRow",
            )
        _require_public_string("market_research_key", self.market_research_key)
        _require_public_string("catalyst_key", self.catalyst_key)
        _require_public_string("catalyst_family", self.catalyst_family)
        _require_reference("catalyst_reference", self.catalyst_reference)
        object.__setattr__(self, "catalyst_at", _as_utc("catalyst_at", self.catalyst_at))
        object.__setattr__(
            self,
            "research_observed_at",
            _as_utc("research_observed_at", self.research_observed_at),
        )
        object.__setattr__(
            self,
            "reference_count",
            _require_nonnegative_count_decimal("reference_count", self.reference_count),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchCalendarCatalystDigestRow:
    market_research_key: str
    catalyst_key: str
    catalyst_family: str
    catalyst_status: str
    seconds_until_catalyst: Decimal
    research_age_seconds: Decimal
    watch_within_seconds: Decimal
    stale_research_after_seconds: Decimal
    reference_count: Decimal
    reference_gap_count: Decimal
    confidence_score: Decimal
    redacted_catalyst_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCalendarCatalystDigestRow:
            raise TypeError(
                "MarketResearchCalendarCatalystDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCalendarCatalystDigestRow:
            raise ValueError(
                "digest row must be exactly MarketResearchCalendarCatalystDigestRow",
            )
        _require_public_string("market_research_key", self.market_research_key)
        _require_public_string("catalyst_key", self.catalyst_key)
        _require_public_string("catalyst_family", self.catalyst_family)
        _require_digest_status("catalyst_status", self.catalyst_status)
        for field_name in (
            "seconds_until_catalyst",
            "research_age_seconds",
            "watch_within_seconds",
            "stale_research_after_seconds",
            "reference_count",
            "reference_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        if self.research_age_seconds < ZERO:
            raise ValueError("research_age_seconds must be nonnegative")
        if self.watch_within_seconds <= ZERO:
            raise ValueError("watch_within_seconds must be positive")
        if self.stale_research_after_seconds <= ZERO:
            raise ValueError("stale_research_after_seconds must be positive")
        object.__setattr__(
            self,
            "reference_count",
            _require_nonnegative_count_decimal("reference_count", self.reference_count),
        )
        object.__setattr__(
            self,
            "reference_gap_count",
            _require_nonnegative_count_decimal(
                "reference_gap_count",
                self.reference_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "redacted_catalyst_reference",
            _require_redacted_reference(
                "redacted_catalyst_reference",
                self.redacted_catalyst_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_digest_row(self)
        require_paper_only_flags("digest row", self)


@dataclass(frozen=True)
class MarketResearchCalendarCatalystDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    catalyst_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCalendarCatalystDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCalendarCatalystDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCalendarCatalystDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCalendarCatalystDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "catalyst_ratio",
            _require_ratio_decimal("catalyst_ratio", self.catalyst_ratio),
        )
        require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCalendarCatalystDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    catalyst_count: Decimal
    ready_catalyst_count: Decimal
    watch_catalyst_count: Decimal
    blocked_catalyst_count: Decimal
    upcoming_catalyst_count: Decimal
    elapsed_catalyst_count: Decimal
    stale_research_count: Decimal
    thin_reference_count: Decimal
    average_confidence_score: Decimal
    ready_catalyst_ratio: Decimal
    rows: tuple[MarketResearchCalendarCatalystDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchCalendarCatalystDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCalendarCatalystDigestReport:
            raise TypeError(
                "MarketResearchCalendarCatalystDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCalendarCatalystDigestReport:
            raise ValueError(
                "digest report must be exactly MarketResearchCalendarCatalystDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        for field_name in (
            "catalyst_count",
            "ready_catalyst_count",
            "watch_catalyst_count",
            "blocked_catalyst_count",
            "upcoming_catalyst_count",
            "elapsed_catalyst_count",
            "stale_research_count",
            "thin_reference_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_confidence_score",
            _require_ratio_decimal(
                "average_confidence_score",
                self.average_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "ready_catalyst_ratio",
            _require_ratio_decimal("ready_catalyst_ratio", self.ready_catalyst_ratio),
        )
        object.__setattr__(self, "rows", _normalize_digest_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_digest_report(self)
        require_paper_only_flags("digest report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchCalendarCatalystDigestConfig,
    MarketResearchCalendarCatalystDigestInputRow,
    MarketResearchCalendarCatalystDigestReasonCodeCount,
    MarketResearchCalendarCatalystDigestReport,
    MarketResearchCalendarCatalystDigestRow,
)


def build_market_research_calendar_catalyst_digest(
    input_rows: list[MarketResearchCalendarCatalystDigestInputRow]
    | tuple[MarketResearchCalendarCatalystDigestInputRow, ...],
    *,
    config: MarketResearchCalendarCatalystDigestConfig,
    generated_at: datetime,
) -> MarketResearchCalendarCatalystDigestReport:
    if type(config) is not MarketResearchCalendarCatalystDigestConfig:
        raise ValueError(
            "config must be a MarketResearchCalendarCatalystDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    digest_rows = _digest_rows(rows, config=config, generated_at=generated_at_utc)
    reason_codes = _report_reason_codes(digest_rows)
    digest_status = _report_status(digest_rows)
    catalyst_count = _decimal_count(len(digest_rows))
    ready_catalyst_count = _status_count(digest_rows, "ready")

    return MarketResearchCalendarCatalystDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        catalyst_count=catalyst_count,
        ready_catalyst_count=ready_catalyst_count,
        watch_catalyst_count=_status_count(digest_rows, "watch"),
        blocked_catalyst_count=_status_count(digest_rows, "blocked"),
        upcoming_catalyst_count=_decimal_count(
            sum(1 for row in digest_rows if row.seconds_until_catalyst > ZERO),
        ),
        elapsed_catalyst_count=_decimal_count(
            sum(1 for row in digest_rows if row.seconds_until_catalyst <= ZERO),
        ),
        stale_research_count=_decimal_count(
            sum(1 for row in digest_rows if STALE_RESEARCH_REASON in row.reason_codes),
        ),
        thin_reference_count=_decimal_count(
            sum(1 for row in digest_rows if THIN_REFERENCES_REASON in row.reason_codes),
        ),
        average_confidence_score=_average_confidence_score(digest_rows),
        ready_catalyst_ratio=_ratio(ready_catalyst_count, catalyst_count),
        rows=digest_rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, digest_rows),
    )


def market_research_calendar_catalyst_digest_json(
    report: MarketResearchCalendarCatalystDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchCalendarCatalystDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCalendarCatalystDigestReport",
        )
    _require_public_json_safe_value("report", report)
    json_report = _json_ready(report)
    if type(json_report) is not dict:
        raise ValueError("report JSON must be an object")
    require_paper_only_flags("report JSON", _DictFlags(json_report))
    _reject_unsafe_json_strings("report JSON", json_report)
    return json_report


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _digest_rows(
    rows: tuple[MarketResearchCalendarCatalystDigestInputRow, ...],
    *,
    config: MarketResearchCalendarCatalystDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchCalendarCatalystDigestRow, ...]:
    digest_rows = tuple(
        _digest_row(row, config=config, generated_at=generated_at)
        for row in sorted(
            rows,
            key=lambda item: (
                item.catalyst_key,
                item.market_research_key,
                item.catalyst_family,
                _redacted_reference(item.catalyst_reference),
            ),
        )
    )
    seen_keys: set[str] = set()
    for row in digest_rows:
        if row.catalyst_key in seen_keys:
            raise ValueError("catalyst_key values must be unique")
        seen_keys.add(row.catalyst_key)
    return digest_rows


def _digest_row(
    row: MarketResearchCalendarCatalystDigestInputRow,
    *,
    config: MarketResearchCalendarCatalystDigestConfig,
    generated_at: datetime,
) -> MarketResearchCalendarCatalystDigestRow:
    seconds_until_catalyst = _seconds_between(generated_at, row.catalyst_at)
    research_age_seconds = _seconds_between(row.research_observed_at, generated_at)
    reference_gap_count = _count_gap(config.min_reference_count, row.reference_count)
    reason_codes = _row_reason_codes(
        seconds_until_catalyst=seconds_until_catalyst,
        research_age_seconds=research_age_seconds,
        reference_gap_count=reference_gap_count,
        config=config,
    )
    return MarketResearchCalendarCatalystDigestRow(
        market_research_key=row.market_research_key,
        catalyst_key=row.catalyst_key,
        catalyst_family=row.catalyst_family,
        catalyst_status=_row_status(reason_codes),
        seconds_until_catalyst=seconds_until_catalyst,
        research_age_seconds=research_age_seconds,
        watch_within_seconds=config.watch_within_seconds,
        stale_research_after_seconds=config.stale_research_after_seconds,
        reference_count=row.reference_count,
        reference_gap_count=reference_gap_count,
        confidence_score=row.confidence_score,
        redacted_catalyst_reference=_redacted_reference(row.catalyst_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    seconds_until_catalyst: Decimal,
    research_age_seconds: Decimal,
    reference_gap_count: Decimal,
    config: MarketResearchCalendarCatalystDigestConfig,
) -> tuple[str, ...]:
    if seconds_until_catalyst <= ZERO:
        return (ELAPSED_REASON,)
    reason_codes: list[str] = []
    is_in_watch_window = seconds_until_catalyst <= config.watch_within_seconds
    if is_in_watch_window:
        reason_codes.append(WATCH_REASON)
    if is_in_watch_window and research_age_seconds > config.stale_research_after_seconds:
        reason_codes.append(STALE_RESEARCH_REASON)
    if is_in_watch_window and reference_gap_count > ZERO:
        reason_codes.append(THIN_REFERENCES_REASON)
    canonical_reasons = tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in set(reason_codes or [READY_REASON])
    )
    return _normalize_reason_codes(
        canonical_reasons,
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (ELAPSED_REASON,):
        return "blocked"
    if reason_codes == (READY_REASON,):
        return "ready"
    return "watch"


def _report_reason_codes(
    rows: tuple[MarketResearchCalendarCatalystDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in seen
    )


def _report_status(rows: tuple[MarketResearchCalendarCatalystDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.catalyst_status == "blocked" for row in rows):
        return "blocked"
    if any(row.catalyst_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketResearchCalendarCatalystDigestInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchCalendarCatalystDigestInputRow:
            raise ValueError("input rows must contain exact input rows")
        require_paper_only_flags("input row", row)
        if row.research_observed_at > generated_at:
            raise ValueError("research_observed_at cannot be in the future")
    return rows


def _normalize_digest_rows(
    value: object,
) -> tuple[MarketResearchCalendarCatalystDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[str, str, str] | None = None
    for row in rows:
        if type(row) is not MarketResearchCalendarCatalystDigestRow:
            raise ValueError("rows must contain exact digest rows")
        key = (row.catalyst_key, row.market_research_key, row.catalyst_family)
        if row.catalyst_key in seen:
            raise ValueError("rows must be unique")
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must be sorted")
        previous_key = key
        seen.add(row.catalyst_key)
    return rows


def _normalize_reason_codes(
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code, allowed)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if (
            previous is not None
            and allowed.index(previous) > allowed.index(reason_code)
        ):
            raise ValueError("reason_codes must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchCalendarCatalystDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    reason_code_counts = tuple(value)
    seen: set[str] = set()
    previous: str | None = None
    for count in reason_code_counts:
        if type(count) is not MarketResearchCalendarCatalystDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        require_paper_only_flags("reason code count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        if (
            previous is not None
            and REPORT_REASON_CODE_SEQUENCE.index(previous)
            > REPORT_REASON_CODE_SEQUENCE.index(count.reason_code)
        ):
            raise ValueError("reason_code_counts must be sorted")
        previous = count.reason_code
        seen.add(count.reason_code)
    return reason_code_counts


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("JSON value must be a supported public dataclass")
        ready: dict[str, object] = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{field.name} must be True")
            ready[field.name] = _json_ready(item)
        return ready
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        _require_six_decimal_json_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError("JSON value must not be a raw collection")
    raise ValueError("value is not JSON serializable")


def _require_public_json_safe_value(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        require_paper_only_flags(field_name, value)
        for field in fields(value):
            try:
                item = getattr(value, field.name)
            except AttributeError as exc:
                raise ValueError(
                    f"{field_name}.{field.name} must remain constructor-valid",
                ) from exc
            _require_public_json_safe_value(f"{field_name}.{field.name}", item)
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_json_decimal(field_name, value)
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_public_json_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) is str:
        _reject_unsafe_json_strings(field_name, value)
        return
    if type(value) is bool or value is None:
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError(f"{field_name} must not be a raw collection")
    raise ValueError(f"{field_name} must remain constructor-normalized")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid: {exc}") from exc


def _require_six_decimal_json_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must use six decimal places") from exc
    if normalized != value or not value.same_quantum(QUANT):
        raise ValueError(f"{field_name} must use six decimal places")


def _reject_unsafe_json_strings(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_json_strings(label, getattr(value, field.name))
        return
    if type(value) is str:
        if any(fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains disallowed text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"{label} contains disallowed text")
            _reject_unsafe_json_strings(label, item)
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            _reject_unsafe_json_strings(label, item)


def _validate_digest_row(row: MarketResearchCalendarCatalystDigestRow) -> None:
    if row.catalyst_status != _row_status(row.reason_codes):
        raise ValueError("catalyst_status must match reason_codes")
    if READY_REASON in row.reason_codes and row.reason_codes != (READY_REASON,):
        raise ValueError("ready reason requires ready status")
    if row.catalyst_status == "ready" and row.reason_codes != (READY_REASON,):
        raise ValueError("ready status requires ready reason")
    if row.catalyst_status == "blocked" and row.reason_codes != (ELAPSED_REASON,):
        raise ValueError("blocked status requires elapsed reason")
    if row.catalyst_status == "watch" and row.reason_codes in (
        (READY_REASON,),
        (ELAPSED_REASON,),
    ):
        raise ValueError("watch status requires watch reasons")
    if row.reference_gap_count > row.watch_within_seconds:
        raise ValueError("reference_gap_count is inconsistent")


def _validate_digest_report(
    report: MarketResearchCalendarCatalystDigestReport,
) -> None:
    if (
        report.ready_catalyst_count
        + report.watch_catalyst_count
        + report.blocked_catalyst_count
        != report.catalyst_count
    ):
        raise ValueError("catalyst status counts must tie to catalyst_count")
    if report.catalyst_count != _decimal_count(len(report.rows)):
        raise ValueError("catalyst_count must match rows")
    if report.ready_catalyst_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_catalyst_count must match rows")
    if report.watch_catalyst_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_catalyst_count must match rows")
    if report.blocked_catalyst_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_catalyst_count must match rows")
    if report.upcoming_catalyst_count != _decimal_count(
        sum(1 for row in report.rows if row.seconds_until_catalyst > ZERO),
    ):
        raise ValueError("upcoming_catalyst_count must match rows")
    if report.elapsed_catalyst_count != _decimal_count(
        sum(1 for row in report.rows if row.seconds_until_catalyst <= ZERO),
    ):
        raise ValueError("elapsed_catalyst_count must match rows")
    if report.stale_research_count != _decimal_count(
        sum(1 for row in report.rows if STALE_RESEARCH_REASON in row.reason_codes),
    ):
        raise ValueError("stale_research_count must match rows")
    if report.thin_reference_count != _decimal_count(
        sum(1 for row in report.rows if THIN_REFERENCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_reference_count must match rows")
    if report.average_confidence_score != _average_confidence_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.ready_catalyst_ratio != _ratio(
        report.ready_catalyst_count,
        report.catalyst_count,
    ):
        raise ValueError("ready_catalyst_ratio must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains disallowed text")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.startswith("sha256:") or len(value) != 19:
        raise ValueError(f"{field_name} must be a short sha256 value")
    return value


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
        raise ValueError(f"{field_name} must be a finite Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _status_count(
    rows: tuple[MarketResearchCalendarCatalystDigestRow, ...],
    catalyst_status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.catalyst_status == catalyst_status))


def _reason_count(
    rows: tuple[MarketResearchCalendarCatalystDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchCalendarCatalystDigestRow, ...],
) -> tuple[MarketResearchCalendarCatalystDigestReasonCodeCount, ...]:
    catalyst_count = _decimal_count(len(rows))
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchCalendarCatalystDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                catalyst_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchCalendarCatalystDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            catalyst_ratio=_ratio(_reason_count(rows, reason_code), catalyst_count),
        )
        for reason_code in reason_codes
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _count_gap(required_count: Decimal, observed_count: Decimal) -> Decimal:
    gap_count = required_count - observed_count
    if gap_count <= ZERO:
        return ZERO
    return gap_count.quantize(QUANT)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    elapsed = end - start
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(elapsed.days * 86400 + elapsed.seconds)
            + (Decimal(elapsed.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANT)


def _average_confidence_score(
    rows: tuple[MarketResearchCalendarCatalystDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    total = ZERO
    for row in rows:
        total += row.confidence_score
    with localcontext(DECIMAL_CONTEXT):
        return (total / _decimal_count(len(rows))).quantize(QUANT)


def _redacted_reference(catalyst_reference: str) -> str:
    return "sha256:" + sha256(catalyst_reference.encode("utf-8")).hexdigest()[:12]
