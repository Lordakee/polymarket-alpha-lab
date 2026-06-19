"""Paper-only correlation grouping reducer for recommendation rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "PaperCorrelationGroupingConfig",
    "PaperCorrelationInputRow",
    "PaperCorrelationGroupRow",
    "PaperCorrelationGroupingReport",
    "build_paper_correlation_grouping_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
GROUP_TYPES = ("event", "correlation", "theme")
SIDES = ("yes", "no", "none")
ACTIONS = ("recommend", "watch", "reject")
STATUSES = ("pass", "watch", "blocked")
GROUP_TYPE_RANK = {"event": 0, "correlation": 1, "theme": 2}
WATCH_THRESHOLD = Decimal("0.95")
PASS_REASON_CODE = "correlation_group_passed"
BLOCKING_REASON_CODES = (
    "group_notional_cap_exceeded",
    "group_count_cap_exceeded",
)
WATCH_REASON_CODES = (
    "near_group_notional_cap",
    "near_group_count_cap",
)


@dataclass(frozen=True)
class PaperCorrelationGroupingConfig:
    config_version: str
    max_group_notional: Decimal
    max_group_count: int
    event_max_group_notional: Decimal | None = None
    event_max_group_count: int | None = None
    theme_max_group_notional: Decimal | None = None
    theme_max_group_count: int | None = None
    correlation_max_group_notional: Decimal | None = None
    correlation_max_group_count: int | None = None

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_notional("max_group_notional", self.max_group_notional)
        _require_positive_int("max_group_count", self.max_group_count)
        _require_optional_positive_notional(
            "event_max_group_notional",
            self.event_max_group_notional,
        )
        _require_optional_positive_int(
            "event_max_group_count",
            self.event_max_group_count,
        )
        _require_optional_positive_notional(
            "theme_max_group_notional",
            self.theme_max_group_notional,
        )
        _require_optional_positive_int(
            "theme_max_group_count",
            self.theme_max_group_count,
        )
        _require_optional_positive_notional(
            "correlation_max_group_notional",
            self.correlation_max_group_notional,
        )
        _require_optional_positive_int(
            "correlation_max_group_count",
            self.correlation_max_group_count,
        )


@dataclass(frozen=True)
class PaperCorrelationInputRow:
    market_slug: str
    side: str
    action: str
    recommendation_score: Decimal
    requested_paper_notional: Decimal
    event_id: str
    theme_id: str
    correlation_group: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        _require_action("action", self.action)
        _require_ratio("recommendation_score", self.recommendation_score)
        _require_notional("requested_paper_notional", self.requested_paper_notional)
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("theme_id", self.theme_id)
        _require_canonical_string("correlation_group", self.correlation_group)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_input_row_consistency(self)
        _validate_hard_flags("input row", self)


@dataclass(frozen=True)
class PaperCorrelationGroupRow:
    group_key: str
    group_type: str
    row_count: int
    recommended_count: int
    requested_notional: Decimal
    group_status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("group_key", self.group_key)
        _require_group_type("group_type", self.group_type)
        _require_nonnegative_int("row_count", self.row_count)
        _require_nonnegative_int("recommended_count", self.recommended_count)
        _require_notional("requested_notional", self.requested_notional)
        _require_status("group_status", self.group_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_group_reason_codes(self.reason_codes),
        )
        _validate_group_row_consistency(self)


@dataclass(frozen=True)
class PaperCorrelationGroupingReport:
    generated_at: datetime
    config_version: str
    input_row_count: int
    group_count: int
    blocked_group_count: int
    watch_group_count: int
    group_rows: tuple[PaperCorrelationGroupRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("input_row_count", self.input_row_count)
        _require_nonnegative_int("group_count", self.group_count)
        _require_nonnegative_int("blocked_group_count", self.blocked_group_count)
        _require_nonnegative_int("watch_group_count", self.watch_group_count)
        object.__setattr__(
            self,
            "group_rows",
            _normalize_group_rows(self.group_rows),
        )
        _validate_report_consistency(self)
        _validate_hard_flags("report", self)

    def group_row(self, group_type: str, group_key: str) -> PaperCorrelationGroupRow:
        _require_group_type("group_type", group_type)
        _require_canonical_string("group_key", group_key)
        matches = tuple(
            row
            for row in self.group_rows
            if row.group_type == group_type and row.group_key == group_key
        )
        if len(matches) != 1:
            raise ValueError("group row must exist exactly once")
        return matches[0]


def build_paper_correlation_grouping_report(
    recommendation_rows: object,
    *,
    config: PaperCorrelationGroupingConfig,
    generated_at: datetime,
) -> PaperCorrelationGroupingReport:
    """Summarize supplied event/theme/correlation groups before allocation."""

    if type(config) is not PaperCorrelationGroupingConfig:
        raise ValueError("config must be a PaperCorrelationGroupingConfig")
    generated_at = _as_utc(generated_at)
    rows = _source_rows(recommendation_rows)
    group_rows = _group_rows(rows, config)
    return PaperCorrelationGroupingReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_row_count=len(rows),
        group_count=len(group_rows),
        blocked_group_count=_status_count(group_rows, "blocked"),
        watch_group_count=_status_count(group_rows, "watch"),
        group_rows=group_rows,
    )


def _source_rows(source: object) -> tuple[PaperCorrelationInputRow, ...]:
    if hasattr(source, "recommendation_rows"):
        _validate_hard_flags("recommendation source", source)
        rows_value = getattr(source, "recommendation_rows")
    else:
        rows_value = source
    if isinstance(rows_value, (str, bytes)):
        raise ValueError("recommendation_rows must be an iterable")
    try:
        rows = tuple(rows_value)
    except TypeError as exc:
        raise ValueError("recommendation_rows must be an iterable") from exc
    return tuple(_coerce_input_row(row) for row in rows)


def _coerce_input_row(row: object) -> PaperCorrelationInputRow:
    if type(row) is PaperCorrelationInputRow:
        return row
    return PaperCorrelationInputRow(
        market_slug=_source_string(row, "market_slug"),
        side=_source_string(row, "side"),
        action=_source_string(row, "action"),
        recommendation_score=_source_decimal(row, "recommendation_score"),
        requested_paper_notional=_source_decimal(row, "requested_paper_notional"),
        event_id=_source_string(row, "event_id"),
        theme_id=_source_string(row, "theme_id"),
        correlation_group=_source_string(row, "correlation_group"),
        reason_codes=_source_reason_codes(row),
        paper_only=_source_flag(row, "paper_only"),
        report_only=_source_flag(row, "report_only"),
        readonly=_source_flag(row, "readonly"),
    )


def _group_rows(
    rows: tuple[PaperCorrelationInputRow, ...],
    config: PaperCorrelationGroupingConfig,
) -> tuple[PaperCorrelationGroupRow, ...]:
    groups: dict[tuple[str, str], list[PaperCorrelationInputRow]] = {}
    for row in rows:
        for group_type, group_key in (
            ("event", row.event_id),
            ("correlation", row.correlation_group),
            ("theme", row.theme_id),
        ):
            groups.setdefault((group_type, group_key), []).append(row)

    return tuple(
        PaperCorrelationGroupRow(
            group_key=group_key,
            group_type=group_type,
            row_count=len(group_members),
            recommended_count=_recommended_count(group_members),
            requested_notional=_requested_notional(group_members),
            group_status=_group_status(
                group_members=tuple(group_members),
                group_type=group_type,
                config=config,
            ),
            reason_codes=_group_reason_codes(
                group_members=tuple(group_members),
                group_type=group_type,
                config=config,
            ),
        )
        for (group_type, group_key), group_members in sorted(
            groups.items(),
            key=lambda item: (GROUP_TYPE_RANK[item[0][0]], item[0][1]),
        )
    )


def _group_status(
    *,
    group_members: tuple[PaperCorrelationInputRow, ...],
    group_type: str,
    config: PaperCorrelationGroupingConfig,
) -> str:
    reason_codes = _cap_reason_codes(group_members, group_type, config)
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _group_reason_codes(
    *,
    group_members: tuple[PaperCorrelationInputRow, ...],
    group_type: str,
    config: PaperCorrelationGroupingConfig,
) -> tuple[str, ...]:
    reason_codes = list(_cap_reason_codes(group_members, group_type, config))
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    for source_reason_code in sorted(
        {
            reason_code
            for row in group_members
            for reason_code in row.reason_codes
        },
    ):
        if source_reason_code not in reason_codes:
            reason_codes.append(source_reason_code)
    return tuple(reason_codes)


def _cap_reason_codes(
    group_members: tuple[PaperCorrelationInputRow, ...],
    group_type: str,
    config: PaperCorrelationGroupingConfig,
) -> tuple[str, ...]:
    requested_notional = _requested_notional(group_members)
    recommended_count = _recommended_count(group_members)
    max_group_notional = _max_group_notional(group_type, config)
    max_group_count = _max_group_count(group_type, config)
    reason_codes: list[str] = []

    if requested_notional > max_group_notional:
        reason_codes.append("group_notional_cap_exceeded")
    elif requested_notional >= _quantize_decimal(max_group_notional * WATCH_THRESHOLD):
        reason_codes.append("near_group_notional_cap")

    if recommended_count > max_group_count:
        reason_codes.append("group_count_cap_exceeded")
    elif recommended_count == max_group_count:
        reason_codes.append("near_group_count_cap")

    return tuple(reason_codes)


def _max_group_notional(
    group_type: str,
    config: PaperCorrelationGroupingConfig,
) -> Decimal:
    if group_type == "event" and config.event_max_group_notional is not None:
        return config.event_max_group_notional
    if group_type == "theme" and config.theme_max_group_notional is not None:
        return config.theme_max_group_notional
    if (
        group_type == "correlation"
        and config.correlation_max_group_notional is not None
    ):
        return config.correlation_max_group_notional
    return config.max_group_notional


def _max_group_count(
    group_type: str,
    config: PaperCorrelationGroupingConfig,
) -> int:
    if group_type == "event" and config.event_max_group_count is not None:
        return config.event_max_group_count
    if group_type == "theme" and config.theme_max_group_count is not None:
        return config.theme_max_group_count
    if group_type == "correlation" and config.correlation_max_group_count is not None:
        return config.correlation_max_group_count
    return config.max_group_count


def _recommended_count(group_members: list[PaperCorrelationInputRow]) -> int:
    return sum(1 for row in group_members if row.action == "recommend")


def _requested_notional(group_members: list[PaperCorrelationInputRow]) -> Decimal:
    return _quantize_decimal(
        sum(
            (
                row.requested_paper_notional
                for row in group_members
                if row.action == "recommend"
            ),
            ZERO,
        ),
    )


def _status_count(rows: tuple[PaperCorrelationGroupRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.group_status == status)


def _source_string(row: object, field_name: str) -> str:
    value = _required_attr(row, field_name)
    _require_canonical_string(field_name, value)
    return value


def _source_decimal(row: object, field_name: str) -> Decimal:
    value = _required_attr(row, field_name)
    _require_decimal(field_name, value)
    return value


def _source_reason_codes(row: object) -> tuple[str, ...]:
    return _normalize_reason_codes(_required_attr(row, "reason_codes"))


def _source_flag(row: object, field_name: str) -> bool:
    if not hasattr(row, field_name):
        return True
    value = getattr(row, field_name)
    if value is not True:
        raise ValueError(f"input row must be {field_name}")
    return value


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _validate_input_row_consistency(row: PaperCorrelationInputRow) -> None:
    if row.action == "recommend":
        if row.side == "none":
            raise ValueError("recommended rows must have a side")
        if row.recommendation_score <= ZERO:
            raise ValueError("recommended rows must have positive recommendation_score")
        if row.requested_paper_notional <= ZERO:
            raise ValueError(
                "recommended rows must have positive requested_paper_notional",
            )
        return
    if row.requested_paper_notional != _quantize_decimal(ZERO):
        raise ValueError("unrecommended rows must have zero requested_paper_notional")


def _validate_group_row_consistency(row: PaperCorrelationGroupRow) -> None:
    if row.recommended_count > row.row_count:
        raise ValueError("recommended_count must be at most row_count")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.group_status != expected_status:
        raise ValueError("group_status must match reason_codes")


def _validate_report_consistency(report: PaperCorrelationGroupingReport) -> None:
    if report.group_count != len(report.group_rows):
        raise ValueError("group_count must match group_rows")
    total_grouped_rows = sum((row.row_count for row in report.group_rows), 0)
    if total_grouped_rows != report.input_row_count * len(GROUP_TYPES):
        raise ValueError("input_row_count must match group_rows")
    if report.blocked_group_count != _status_count(report.group_rows, "blocked"):
        raise ValueError("blocked_group_count must match group_rows")
    if report.watch_group_count != _status_count(report.group_rows, "watch"):
        raise ValueError("watch_group_count must match group_rows")
    if report.group_rows != _sorted_group_rows(report.group_rows):
        raise ValueError("group_rows must use deterministic sorting")
    group_keys = tuple((row.group_type, row.group_key) for row in report.group_rows)
    if len(set(group_keys)) != len(group_keys):
        raise ValueError("group_rows must contain unique group keys")


def _sorted_group_rows(
    rows: tuple[PaperCorrelationGroupRow, ...],
) -> tuple[PaperCorrelationGroupRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (GROUP_TYPE_RANK[row.group_type], row.group_key),
        ),
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_group_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GROUP_TYPES:
        raise ValueError(f"{field_name} must be event, theme, or correlation")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_notional(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_positive_notional(field_name: str, value: object) -> None:
    _require_notional(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_positive_notional(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_positive_notional(field_name, value)


def _require_ratio(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_positive_int(field_name: str, value: int | None) -> None:
    if value is not None:
        _require_positive_int(field_name, value)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return items


def _normalize_group_reason_codes(value: object) -> tuple[str, ...]:
    items = _normalize_reason_codes(value)
    allowed_system_codes = (
        PASS_REASON_CODE,
        *BLOCKING_REASON_CODES,
        *WATCH_REASON_CODES,
    )
    if not any(item in allowed_system_codes for item in items):
        raise ValueError("reason_codes must include group status semantics")
    return items


def _normalize_group_rows(value: object) -> tuple[PaperCorrelationGroupRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("group_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("group_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperCorrelationGroupRow:
            raise ValueError("group_rows must contain PaperCorrelationGroupRow values")
    return rows


def _quantize_decimal(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("decimal", value)
    return value.quantize(QUANTUM)
