"""Pure report-only macro indicator event map reducer."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_MACRO_INDICATOR_EVENT_MAP_CONFIG_VERSION = (
    "research-macro-indicator-event-map-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

EVENT_FAMILY_MACRO = "macro"
EVENT_FAMILY_EQUITY_INDEX = "equity_index"
EVENT_FAMILY_GOLD = "gold"
EVENT_FAMILIES = (
    EVENT_FAMILY_MACRO,
    EVENT_FAMILY_EQUITY_INDEX,
    EVENT_FAMILY_GOLD,
)

REASON_PREFIX = "research_macro_indicator_event_map_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
HISTORICAL_SENSITIVITY_BLOCK_REASON = (
    f"{REASON_PREFIX}historical_sensitivity_block"
)
HISTORICAL_SENSITIVITY_WATCH_REASON = (
    f"{REASON_PREFIX}historical_sensitivity_watch"
)
LOW_ALIGNMENT_REASON = f"{REASON_PREFIX}low_indicator_alignment"
MISSING_REVIEW_REASON = f"{REASON_PREFIX}missing_review"
RELEASE_TIME_UNCERTAIN_REASON = f"{REASON_PREFIX}release_time_uncertain"
RELEASE_TIME_UNTRUSTED_REASON = f"{REASON_PREFIX}release_time_untrusted"
RELEASE_WINDOW_CLOSE_REASON = f"{REASON_PREFIX}release_window_close"
REVIEW_NEED_BLOCK_REASON = f"{REASON_PREFIX}review_need_block"
REVIEW_NEED_WATCH_REASON = f"{REASON_PREFIX}review_need_watch"
STALE_REVIEW_REASON = f"{REASON_PREFIX}stale_review"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    RELEASE_TIME_UNTRUSTED_REASON,
    HISTORICAL_SENSITIVITY_BLOCK_REASON,
    REVIEW_NEED_BLOCK_REASON,
    MISSING_REVIEW_REASON,
    RELEASE_TIME_UNCERTAIN_REASON,
    LOW_ALIGNMENT_REASON,
    HISTORICAL_SENSITIVITY_WATCH_REASON,
    REVIEW_NEED_WATCH_REASON,
    STALE_REVIEW_REASON,
    RELEASE_WINDOW_CLOSE_REASON,
    THIN_SOURCES_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    RELEASE_TIME_UNTRUSTED_REASON,
    HISTORICAL_SENSITIVITY_BLOCK_REASON,
    REVIEW_NEED_BLOCK_REASON,
    MISSING_REVIEW_REASON,
    RELEASE_TIME_UNCERTAIN_REASON,
    LOW_ALIGNMENT_REASON,
    HISTORICAL_SENSITIVITY_WATCH_REASON,
    REVIEW_NEED_WATCH_REASON,
    STALE_REVIEW_REASON,
    RELEASE_WINDOW_CLOSE_REASON,
    THIN_SOURCES_REASON,
    PASS_REASON,
)
BLOCK_REASONS = (
    RELEASE_TIME_UNTRUSTED_REASON,
    HISTORICAL_SENSITIVITY_BLOCK_REASON,
    REVIEW_NEED_BLOCK_REASON,
    MISSING_REVIEW_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_research_macro_indicator_event_map",
    STATUS_WATCH: "watch_report_only_research_macro_indicator_event_map",
    STATUS_BLOCK: "block_report_only_research_macro_indicator_event_map",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_PUBLIC_REFERENCE_FRAGMENTS = (
    "bea",
    "bls",
    "calendar",
    "census",
    "federal-reserve",
    "official",
    "public",
    "release",
    "treasury",
)
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "api" + "_" + "key",
    "au" + "th",
    "b" + "et",
    "bro" + "ker",
    "can" + "cel",
    "cli" + "ent",
    "confiden" + "tial",
    "credential",
    "execu" + "tion",
    "inter" + "nal",
    "ord" + "er",
    "password",
    "posi" + "tion",
    "pri" + "vate",
    "recommenda" + "tion",
    "sec" + "ret",
    "sig" + "ning",
    "sta" + "ke",
    "token",
    "wal" + "let",
)
_FLAG_NAMES = frozenset(("paper_only", "report_only", "readonly"))
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ResearchMacroIndicatorEventMapConfig:
    config_version: str = DEFAULT_RESEARCH_MACRO_INDICATOR_EVENT_MAP_CONFIG_VERSION
    min_public_source_count: Decimal = Decimal("2")
    min_release_time_confidence: Decimal = Decimal("0.650000")
    block_release_time_confidence: Decimal = Decimal("0.400000")
    min_event_indicator_alignment: Decimal = Decimal("0.600000")
    historical_sensitivity_watch_threshold: Decimal = Decimal("0.500000")
    historical_sensitivity_block_threshold: Decimal = Decimal("0.800000")
    review_need_watch_threshold: Decimal = Decimal("0.400000")
    review_need_block_threshold: Decimal = Decimal("0.750000")
    max_review_lag_seconds: Decimal = Decimal("86400.000000")
    release_proximity_watch_seconds: Decimal = Decimal("10800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMacroIndicatorEventMapConfig:
            raise TypeError(
                "ResearchMacroIndicatorEventMapConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMacroIndicatorEventMapConfig:
            raise ValueError(
                "config must be exactly ResearchMacroIndicatorEventMapConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MACRO_INDICATOR_EVENT_MAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_nonnegative_count_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        for field_name in (
            "min_release_time_confidence",
            "block_release_time_confidence",
            "min_event_indicator_alignment",
            "historical_sensitivity_watch_threshold",
            "historical_sensitivity_block_threshold",
            "review_need_watch_threshold",
            "review_need_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_release_time_confidence > self.min_release_time_confidence:
            raise ValueError(
                "block_release_time_confidence must be no greater than "
                "min_release_time_confidence",
            )
        if (
            self.historical_sensitivity_watch_threshold
            > self.historical_sensitivity_block_threshold
        ):
            raise ValueError(
                "historical_sensitivity_block_threshold must be at least "
                "historical_sensitivity_watch_threshold",
            )
        if self.review_need_watch_threshold > self.review_need_block_threshold:
            raise ValueError(
                "review_need_block_threshold must be at least "
                "review_need_watch_threshold",
            )
        for field_name in (
            "max_review_lag_seconds",
            "release_proximity_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMacroIndicatorEventMapInputRow:
    event_key: str
    condition_id: str
    event_family: str
    macro_indicator: str
    public_release_reference: str
    scheduled_release_at: datetime
    reviewed_at: datetime | None
    public_source_count: Decimal
    release_time_confidence: Decimal
    historical_sensitivity_score: Decimal
    event_indicator_alignment_score: Decimal
    review_need_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMacroIndicatorEventMapInputRow:
            raise TypeError(
                "ResearchMacroIndicatorEventMapInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMacroIndicatorEventMapInputRow:
            raise ValueError(
                "input row must be exactly ResearchMacroIndicatorEventMapInputRow",
            )
        for field_name in ("event_key", "condition_id", "macro_indicator"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_family",
            _require_event_family("event_family", self.event_family),
        )
        object.__setattr__(
            self,
            "public_release_reference",
            _require_reference(
                "public_release_reference",
                self.public_release_reference,
            ),
        )
        object.__setattr__(
            self,
            "scheduled_release_at",
            _as_utc("scheduled_release_at", self.scheduled_release_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "release_time_confidence",
            "historical_sensitivity_score",
            "event_indicator_alignment_score",
            "review_need_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchMacroIndicatorEventMapRow:
    event_key: str
    condition_id: str
    event_family: str
    macro_indicator: str
    scheduled_release_at: datetime
    reviewed_at: datetime | None
    release_proximity_seconds: Decimal
    review_lag_seconds: Decimal | None
    public_source_count: Decimal
    release_time_confidence: Decimal
    historical_sensitivity_score: Decimal
    event_indicator_alignment_score: Decimal
    review_need_score: Decimal
    event_status: str
    review_required: bool
    redacted_release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchMacroIndicatorEventMapConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMacroIndicatorEventMapRow:
            raise TypeError(
                "ResearchMacroIndicatorEventMapRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchMacroIndicatorEventMapConfig | None,
    ) -> None:
        if type(self) is not ResearchMacroIndicatorEventMapRow:
            raise ValueError("row must be exactly ResearchMacroIndicatorEventMapRow")
        for field_name in ("event_key", "condition_id", "macro_indicator"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_family",
            _require_event_family("event_family", self.event_family),
        )
        object.__setattr__(
            self,
            "scheduled_release_at",
            _as_utc("scheduled_release_at", self.scheduled_release_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "release_proximity_seconds",
            _require_nonnegative_decimal(
                "release_proximity_seconds",
                self.release_proximity_seconds,
            ),
        )
        object.__setattr__(
            self,
            "review_lag_seconds",
            _require_optional_nonnegative_decimal(
                "review_lag_seconds",
                self.review_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "release_time_confidence",
            "historical_sensitivity_score",
            "event_indicator_alignment_score",
            "review_need_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("event_status", self.event_status)
        _require_bool("review_required", self.review_required)
        object.__setattr__(
            self,
            "redacted_release_reference",
            _require_redacted_reference(
                "redacted_release_reference",
                self.redacted_release_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMacroIndicatorEventMapReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMacroIndicatorEventMapReasonCodeCount:
            raise TypeError(
                "ResearchMacroIndicatorEventMapReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMacroIndicatorEventMapReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMacroIndicatorEventMapReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMacroIndicatorEventMapReport:
    generated_at: datetime
    config_version: str
    report_status: str
    next_step: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    review_required_count: Decimal
    high_sensitivity_count: Decimal
    close_release_count: Decimal
    thin_source_count: Decimal
    average_historical_sensitivity_score: Decimal
    average_release_time_confidence: Decimal
    max_review_need_score: Decimal
    rows: tuple[ResearchMacroIndicatorEventMapRow, ...]
    reason_code_counts: tuple[ResearchMacroIndicatorEventMapReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMacroIndicatorEventMapReport:
            raise TypeError(
                "ResearchMacroIndicatorEventMapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMacroIndicatorEventMapReport:
            raise ValueError("report must be exactly ResearchMacroIndicatorEventMapReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MACRO_INDICATOR_EVENT_MAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "next_step",
            _require_public_string("next_step", self.next_step),
        )
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "review_required_count",
            "high_sensitivity_count",
            "close_release_count",
            "thin_source_count",
            "average_historical_sensitivity_score",
            "average_release_time_confidence",
            "max_review_need_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchMacroIndicatorEventMapRow:
                raise ValueError("rows must contain ResearchMacroIndicatorEventMapRow")
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchMacroIndicatorEventMapReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchMacroIndicatorEventMapReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_macro_indicator_event_map_report(
    input_rows: list[ResearchMacroIndicatorEventMapInputRow]
    | tuple[ResearchMacroIndicatorEventMapInputRow, ...],
    *,
    config: ResearchMacroIndicatorEventMapConfig | None = None,
    generated_at: datetime,
) -> ResearchMacroIndicatorEventMapReport:
    cfg = config or ResearchMacroIndicatorEventMapConfig()
    if type(cfg) is not ResearchMacroIndicatorEventMapConfig:
        raise ValueError("config must be a ResearchMacroIndicatorEventMapConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    event_count = _count(len(ranked_rows))
    pass_count = _count(sum(1 for row in ranked_rows if row.event_status == STATUS_PASS))
    watch_count = _count(sum(1 for row in ranked_rows if row.event_status == STATUS_WATCH))
    block_count = _count(sum(1 for row in ranked_rows if row.event_status == STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchMacroIndicatorEventMapReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    report_status = _report_status(
        has_inputs=bool(ranked_rows),
        block_count=block_count,
        watch_count=watch_count,
    )
    return ResearchMacroIndicatorEventMapReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        report_status=report_status,
        next_step=NEXT_STEPS[report_status],
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        review_required_count=_count(
            sum(1 for row in ranked_rows if row.review_required),
        ),
        high_sensitivity_count=_count(
            sum(
                1
                for row in ranked_rows
                if HISTORICAL_SENSITIVITY_BLOCK_REASON in row.reason_codes
                or HISTORICAL_SENSITIVITY_WATCH_REASON in row.reason_codes
            ),
        ),
        close_release_count=_count(
            sum(1 for row in ranked_rows if RELEASE_WINDOW_CLOSE_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        average_historical_sensitivity_score=_ratio(
            _sum_decimal(row.historical_sensitivity_score for row in ranked_rows),
            event_count,
        ),
        average_release_time_confidence=_ratio(
            _sum_decimal(row.release_time_confidence for row in ranked_rows),
            event_count,
        ),
        max_review_need_score=max(
            (row.review_need_score for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_macro_indicator_event_map_report_payload(
    report: ResearchMacroIndicatorEventMapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMacroIndicatorEventMapReport:
        raise ValueError("report must be a ResearchMacroIndicatorEventMapReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload(payload)
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


def _build_row(
    row: ResearchMacroIndicatorEventMapInputRow,
    *,
    config: ResearchMacroIndicatorEventMapConfig,
    generated_at: datetime,
) -> ResearchMacroIndicatorEventMapRow:
    release_proximity_seconds = _abs_decimal(
        _datetime_delta_seconds(row.scheduled_release_at, generated_at),
    )
    review_lag_seconds = (
        None
        if row.reviewed_at is None
        else _datetime_delta_seconds(generated_at, row.reviewed_at)
    )
    reason_codes = _row_reason_codes(
        release_proximity_seconds=release_proximity_seconds,
        review_lag_seconds=review_lag_seconds,
        public_source_count=row.public_source_count,
        release_time_confidence=row.release_time_confidence,
        historical_sensitivity_score=row.historical_sensitivity_score,
        event_indicator_alignment_score=row.event_indicator_alignment_score,
        review_need_score=row.review_need_score,
        config=config,
    )
    return ResearchMacroIndicatorEventMapRow(
        event_key=row.event_key,
        condition_id=row.condition_id,
        event_family=row.event_family,
        macro_indicator=row.macro_indicator,
        scheduled_release_at=row.scheduled_release_at,
        reviewed_at=row.reviewed_at,
        release_proximity_seconds=release_proximity_seconds,
        review_lag_seconds=review_lag_seconds,
        public_source_count=row.public_source_count,
        release_time_confidence=row.release_time_confidence,
        historical_sensitivity_score=row.historical_sensitivity_score,
        event_indicator_alignment_score=row.event_indicator_alignment_score,
        review_need_score=row.review_need_score,
        event_status=_row_status(reason_codes),
        review_required=_review_required(reason_codes),
        redacted_release_reference=_redacted_reference(row.public_release_reference),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchMacroIndicatorEventMapInputRow]
    | tuple[ResearchMacroIndicatorEventMapInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchMacroIndicatorEventMapInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchMacroIndicatorEventMapInputRow:
            raise ValueError(
                "input rows must contain ResearchMacroIndicatorEventMapInputRow",
            )
        _require_hard_flags("input row", row)
        if row.reviewed_at is not None and row.reviewed_at > generated_at:
            raise ValueError("reviewed_at must be on or before generated_at")
        key = (row.event_key, row.condition_id, row.macro_indicator)
        if key in seen:
            raise ValueError("input rows must not contain duplicate event maps")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    release_proximity_seconds: Decimal,
    review_lag_seconds: Decimal | None,
    public_source_count: Decimal,
    release_time_confidence: Decimal,
    historical_sensitivity_score: Decimal,
    event_indicator_alignment_score: Decimal,
    review_need_score: Decimal,
    config: ResearchMacroIndicatorEventMapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if release_time_confidence < config.block_release_time_confidence:
        reason_codes.append(RELEASE_TIME_UNTRUSTED_REASON)
    elif release_time_confidence < config.min_release_time_confidence:
        reason_codes.append(RELEASE_TIME_UNCERTAIN_REASON)
    if historical_sensitivity_score >= config.historical_sensitivity_block_threshold:
        reason_codes.append(HISTORICAL_SENSITIVITY_BLOCK_REASON)
    elif historical_sensitivity_score >= config.historical_sensitivity_watch_threshold:
        reason_codes.append(HISTORICAL_SENSITIVITY_WATCH_REASON)
    if review_need_score >= config.review_need_block_threshold:
        reason_codes.append(REVIEW_NEED_BLOCK_REASON)
    elif review_need_score >= config.review_need_watch_threshold:
        reason_codes.append(REVIEW_NEED_WATCH_REASON)
    if review_lag_seconds is None:
        reason_codes.append(MISSING_REVIEW_REASON)
    elif review_lag_seconds > config.max_review_lag_seconds:
        reason_codes.append(STALE_REVIEW_REASON)
    if event_indicator_alignment_score < config.min_event_indicator_alignment:
        reason_codes.append(LOW_ALIGNMENT_REASON)
    if release_proximity_seconds <= config.release_proximity_watch_seconds:
        reason_codes.append(RELEASE_WINDOW_CLOSE_REASON)
    if public_source_count < config.min_public_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in reason_codes for reason_code in BLOCK_REASONS):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _review_required(reason_codes: tuple[str, ...]) -> bool:
    return any(
        reason_code in reason_codes
        for reason_code in (
            MISSING_REVIEW_REASON,
            REVIEW_NEED_BLOCK_REASON,
            REVIEW_NEED_WATCH_REASON,
            STALE_REVIEW_REASON,
        )
    )


def _report_status(*, has_inputs: bool, block_count: Decimal, watch_count: Decimal) -> str:
    if not has_inputs or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchMacroIndicatorEventMapRow, ...],
) -> tuple[ResearchMacroIndicatorEventMapRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.event_status),
                -row.review_need_score,
                -row.historical_sensitivity_score,
                row.event_family,
                row.event_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchMacroIndicatorEventMapRow, ...],
) -> tuple[ResearchMacroIndicatorEventMapReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            event_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchMacroIndicatorEventMapRow,
    *,
    config: ResearchMacroIndicatorEventMapConfig | None,
) -> None:
    if config is None:
        config = ResearchMacroIndicatorEventMapConfig()
    if type(config) is not ResearchMacroIndicatorEventMapConfig:
        raise ValueError(
            "validation_config must be a ResearchMacroIndicatorEventMapConfig",
        )
    expected_reason_codes = _row_reason_codes(
        release_proximity_seconds=row.release_proximity_seconds,
        review_lag_seconds=row.review_lag_seconds,
        public_source_count=row.public_source_count,
        release_time_confidence=row.release_time_confidence,
        historical_sensitivity_score=row.historical_sensitivity_score,
        event_indicator_alignment_score=row.event_indicator_alignment_score,
        review_need_score=row.review_need_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.event_status != _row_status(row.reason_codes):
        raise ValueError("event_status must match reason_codes")
    if row.review_required is not _review_required(row.reason_codes):
        raise ValueError("review_required must match reason_codes")
    if not _is_redacted_reference(row.redacted_release_reference):
        raise ValueError("redacted_release_reference must be redacted or public")


def _validate_report(report: ResearchMacroIndicatorEventMapReport) -> None:
    if report.next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("next_step must match report_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in report.rows if row.event_status == STATUS_PASS),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.event_status == STATUS_WATCH),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in report.rows if row.event_status == STATUS_BLOCK),
    ):
        raise ValueError("block_count must match rows")
    if report.review_required_count != _count(
        sum(1 for row in report.rows if row.review_required),
    ):
        raise ValueError("review_required_count must match rows")
    if report.high_sensitivity_count != _count(
        sum(
            1
            for row in report.rows
            if HISTORICAL_SENSITIVITY_BLOCK_REASON in row.reason_codes
            or HISTORICAL_SENSITIVITY_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("high_sensitivity_count must match rows")
    if report.close_release_count != _count(
        sum(1 for row in report.rows if RELEASE_WINDOW_CLOSE_REASON in row.reason_codes),
    ):
        raise ValueError("close_release_count must match rows")
    if report.thin_source_count != _count(
        sum(1 for row in report.rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.average_historical_sensitivity_score != _ratio(
        _sum_decimal(row.historical_sensitivity_score for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_historical_sensitivity_score must match rows")
    if report.average_release_time_confidence != _ratio(
        _sum_decimal(row.release_time_confidence for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_release_time_confidence must match rows")
    if report.max_review_need_score != max(
        (row.review_need_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_review_need_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchMacroIndicatorEventMapReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        block_count=report.block_count,
        watch_count=report.watch_count,
    )
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with review reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a supported status")


def _require_event_family(field_name: str, value: object) -> str:
    if type(value) is not str or value not in EVENT_FAMILIES:
        raise ValueError(f"{field_name} must be a supported event family")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if any(character < " " for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    public_value = _require_public_string(field_name, value)
    if not _is_redacted_reference(public_value):
        raise ValueError(f"{field_name} must be redacted or public")
    return public_value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_NAMES:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    number = _require_decimal(field_name, value)
    if number < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return number


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    number = _require_nonnegative_decimal(field_name, value)
    if number != number.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return number


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    number = _require_decimal(field_name, value)
    if number < ZERO or number > ONE:
        raise ValueError(f"{field_name} must be in [0, 1]")
    return number


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    microseconds = (
        Decimal(delta.days) * Decimal("86400") * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize(value.copy_abs())


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _redacted_reference(value: str) -> str:
    if _is_safe_reference(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_safe_reference(value: str) -> bool:
    if type(value) is not str or not value.strip() or value != value.strip():
        return False
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        return False
    return any(fragment in lowered for fragment in _PUBLIC_REFERENCE_FRAGMENTS)


def _is_redacted_reference(value: str) -> bool:
    if _is_safe_reference(value):
        return True
    if len(value) != 19 or not value.startswith("sha256:"):
        return False
    return all(character in _HEX_CHARS for character in value.removeprefix("sha256:"))


def _reject_unsafe_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be text")
    if any(character < " " for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public and redacted")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text("payload value", value)
        return
    if isinstance(value, Decimal):
        raise ValueError("payload must serialize Decimal values")
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("payload must not contain integer values")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        raise ValueError("JSON numeric values must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
