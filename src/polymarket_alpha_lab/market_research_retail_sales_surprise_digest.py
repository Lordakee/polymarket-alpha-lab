"""Read-only retail sales surprise digest for Phase 1 research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    require_paper_only_flags,
)


DEFAULT_RETAIL_SALES_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-retail-sales-surprise-digest-v0"
)
SURPRISE_DIRECTIONS = ("positive", "negative", "inline")
SURPRISE_STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = (
    "retail_sales_positive_surprise",
    "retail_sales_negative_surprise",
    "retail_sales_inline",
)
ROW_REASON_CODES = (
    "retail_sales_segment_large_positive_surprise",
    "retail_sales_segment_large_negative_surprise",
    "retail_sales_segment_positive_surprise",
    "retail_sales_segment_negative_surprise",
    "retail_sales_segment_inline",
)
REPORT_REASON_CODES = (
    "retail_sales_surprise_digest_no_inputs",
    "retail_sales_surprise_digest_clear",
    "retail_sales_large_surprise_present",
    "retail_sales_positive_surprises_present",
    "retail_sales_negative_surprises_present",
    "retail_sales_mixed_surprises_present",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_COUNT = Decimal("1")
ONE_RATIO = Decimal("1.000000")
WATCH_ABS_SURPRISE_RATIO = Decimal("0.020000")
BLOCKED_ABS_SURPRISE_RATIO = Decimal("0.050000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("ex", "change", "_", "mutation"),
        _join_parts("tra", "de"),
        _join_parts("sig", "ning"),
        _join_parts("bro", "ker"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
    ),
)


@dataclass(frozen=True)
class RetailSalesSurpriseDigestConfig:
    config_version: str = DEFAULT_RETAIL_SALES_SURPRISE_DIGEST_CONFIG_VERSION
    watch_abs_surprise_ratio: Decimal = WATCH_ABS_SURPRISE_RATIO
    blocked_abs_surprise_ratio: Decimal = BLOCKED_ABS_SURPRISE_RATIO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RetailSalesSurpriseDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RETAIL_SALES_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_abs_surprise_ratio",
            _normalize_ratio(
                "watch_abs_surprise_ratio",
                self.watch_abs_surprise_ratio,
            ),
        )
        object.__setattr__(
            self,
            "blocked_abs_surprise_ratio",
            _normalize_ratio(
                "blocked_abs_surprise_ratio",
                self.blocked_abs_surprise_ratio,
            ),
        )
        if self.blocked_abs_surprise_ratio < self.watch_abs_surprise_ratio:
            raise ValueError("blocked_abs_surprise_ratio must be at least watch threshold")
        require_paper_only_flags("RetailSalesSurpriseDigestConfig", self)


@dataclass(frozen=True)
class RetailSalesSurpriseObservation:
    source_id: str
    region_id: str
    segment_id: str
    observed_sales: Decimal
    expected_sales: Decimal
    surprise_ratio: Decimal
    source_row_count: Decimal
    data_timestamp: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RetailSalesSurpriseObservation, "observation")
        for field_name in ("source_id", "region_id", "segment_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_sales",
            _normalize_nonnegative_value("observed_sales", self.observed_sales),
        )
        object.__setattr__(
            self,
            "expected_sales",
            _normalize_positive_value("expected_sales", self.expected_sales),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _normalize_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _validate_observation(self)
        require_paper_only_flags("RetailSalesSurpriseObservation", self)


@dataclass(frozen=True)
class RetailSalesSurpriseDigestRow:
    source_id: str
    region_id: str
    segment_id: str
    observed_sales: Decimal
    expected_sales: Decimal
    surprise_ratio: Decimal
    abs_surprise_ratio: Decimal
    source_row_count: Decimal
    data_timestamp: datetime
    surprise_direction: str
    surprise_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RetailSalesSurpriseDigestRow, "row")
        for field_name in ("source_id", "region_id", "segment_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_sales",
            _normalize_nonnegative_value("observed_sales", self.observed_sales),
        )
        object.__setattr__(
            self,
            "expected_sales",
            _normalize_positive_value("expected_sales", self.expected_sales),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _normalize_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        object.__setattr__(
            self,
            "abs_surprise_ratio",
            _normalize_ratio("abs_surprise_ratio", self.abs_surprise_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("surprise_direction", self.surprise_direction, SURPRISE_DIRECTIONS)
        _require_member("surprise_status", self.surprise_status, SURPRISE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("RetailSalesSurpriseDigestRow", self)


@dataclass(frozen=True)
class RetailSalesSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RetailSalesSurpriseReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_row_ratio("row_ratio", self.row_ratio),
        )
        require_paper_only_flags("RetailSalesSurpriseReasonCodeCount", self)


@dataclass(frozen=True)
class RetailSalesSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    inline_count: Decimal
    max_abs_surprise_ratio: Decimal
    average_surprise_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[RetailSalesSurpriseReasonCodeCount, ...]
    surprise_rows: tuple[RetailSalesSurpriseDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RetailSalesSurpriseDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RETAIL_SALES_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "observation_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "inline_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_abs_surprise_ratio",
            _normalize_ratio("max_abs_surprise_ratio", self.max_abs_surprise_ratio),
        )
        object.__setattr__(
            self,
            "average_surprise_ratio",
            _normalize_signed_ratio("average_surprise_ratio", self.average_surprise_ratio),
        )
        _require_member("digest_status", self.digest_status, SURPRISE_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "surprise_rows", _normalize_rows(self.surprise_rows))
        _validate_report(self)
        _reject_unsafe_public_payload("retail sales surprise digest report", self)
        require_paper_only_flags("RetailSalesSurpriseDigestReport", self)


def build_market_research_retail_sales_surprise_digest(
    inputs: list[RetailSalesSurpriseObservation]
    | tuple[RetailSalesSurpriseObservation, ...],
    *,
    config: RetailSalesSurpriseDigestConfig,
    generated_at: datetime,
) -> RetailSalesSurpriseDigestReport:
    if type(config) is not RetailSalesSurpriseDigestConfig:
        raise ValueError("config must be exactly RetailSalesSurpriseDigestConfig")
    require_paper_only_flags("config", config)
    rows = _normalize_inputs(inputs)
    digest_rows = tuple(
        sorted(
            (_digest_row(row, config) for row in rows),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(digest_rows)
    digest_status = _status_rollup(tuple(row.surprise_status for row in digest_rows))
    return RetailSalesSurpriseDigestReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        source_row_count=_sum_rows(digest_rows, "source_row_count"),
        observation_count=_count(len(digest_rows)),
        positive_surprise_count=_direction_count(digest_rows, "positive"),
        negative_surprise_count=_direction_count(digest_rows, "negative"),
        inline_count=_direction_count(digest_rows, "inline"),
        max_abs_surprise_ratio=_max_abs_surprise_ratio(digest_rows),
        average_surprise_ratio=_average_surprise_ratio(digest_rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, digest_rows),
        surprise_rows=digest_rows,
    )


def market_research_retail_sales_surprise_digest_payload(
    report: RetailSalesSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not RetailSalesSurpriseDigestReport:
        raise ValueError("report must be exactly RetailSalesSurpriseDigestReport")
    require_paper_only_flags("report", report)
    _reject_unsafe_public_payload("retail sales surprise digest report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("retail sales surprise digest payload", payload)
    return payload


def _json_ready(value: Any, path: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), path)
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return _decimal_payload(value)
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


def _decimal_payload(value: Decimal) -> str:
    with localcontext(DECIMAL_CONTEXT):
        return format(value.quantize(VALUE_QUANTUM), "f")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
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
            raise ValueError(f"{path or label} has unsafe public value")
        if _has_unsafe_public_text_fragment(lowered):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            if _has_unsafe_public_text_fragment(key.lower()):
                raise ValueError(f"{item_path} has unsafe public field")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_text_fragment(value: str) -> bool:
    return any(fragment in value for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _normalize_inputs(
    inputs: list[RetailSalesSurpriseObservation]
    | tuple[RetailSalesSurpriseObservation, ...],
) -> tuple[RetailSalesSurpriseObservation, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not RetailSalesSurpriseObservation:
            raise ValueError("inputs must contain RetailSalesSurpriseObservation values")
        require_paper_only_flags("input", row)
        if row.source_id in seen_source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return rows


def _digest_row(
    row: RetailSalesSurpriseObservation,
    config: RetailSalesSurpriseDigestConfig,
) -> RetailSalesSurpriseDigestRow:
    abs_surprise_ratio = abs(row.surprise_ratio)
    direction = _surprise_direction(row.surprise_ratio)
    status = _surprise_status(abs_surprise_ratio, config)
    return RetailSalesSurpriseDigestRow(
        source_id=row.source_id,
        region_id=row.region_id,
        segment_id=row.segment_id,
        observed_sales=row.observed_sales,
        expected_sales=row.expected_sales,
        surprise_ratio=row.surprise_ratio,
        abs_surprise_ratio=abs_surprise_ratio,
        source_row_count=row.source_row_count,
        data_timestamp=row.data_timestamp,
        surprise_direction=direction,
        surprise_status=status,
        reason_codes=_row_reason_codes(direction, status),
    )


def _row_reason_codes(direction: str, status: str) -> tuple[str, ...]:
    if direction == "positive" and status == "blocked":
        return ("retail_sales_segment_large_positive_surprise",)
    if direction == "negative" and status == "blocked":
        return ("retail_sales_segment_large_negative_surprise",)
    if direction == "positive":
        return ("retail_sales_segment_positive_surprise",)
    if direction == "negative":
        return ("retail_sales_segment_negative_surprise",)
    return ("retail_sales_segment_inline",)


def _report_reason_codes(
    rows: tuple[RetailSalesSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("retail_sales_surprise_digest_no_inputs",)
    codes: list[str] = []
    if any(row.surprise_status == "blocked" for row in rows):
        codes.append("retail_sales_large_surprise_present")
    has_positive = any(row.surprise_direction == "positive" for row in rows)
    has_negative = any(row.surprise_direction == "negative" for row in rows)
    if has_positive and has_negative:
        codes.append("retail_sales_mixed_surprises_present")
    else:
        if has_positive:
            codes.append("retail_sales_positive_surprises_present")
        if has_negative:
            codes.append("retail_sales_negative_surprises_present")
    if not codes:
        codes.append("retail_sales_surprise_digest_clear")
    return tuple(codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RetailSalesSurpriseDigestRow, ...],
) -> tuple[RetailSalesSurpriseReasonCodeCount, ...]:
    row_count = _count(len(rows))
    return tuple(
        RetailSalesSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_safe_row_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[RetailSalesSurpriseDigestRow, ...],
) -> Decimal:
    if reason_code == "retail_sales_surprise_digest_no_inputs":
        return ONE_COUNT if not rows else ZERO_COUNT
    if reason_code == "retail_sales_surprise_digest_clear":
        return _count(
            sum(1 for row in rows if row.surprise_direction == "inline"),
        )
    if reason_code == "retail_sales_large_surprise_present":
        return _count(sum(1 for row in rows if row.surprise_status == "blocked"))
    if reason_code == "retail_sales_positive_surprises_present":
        return _count(sum(1 for row in rows if row.surprise_direction == "positive"))
    if reason_code == "retail_sales_negative_surprises_present":
        return _count(sum(1 for row in rows if row.surprise_direction == "negative"))
    if reason_code == "retail_sales_mixed_surprises_present":
        return _count(sum(1 for row in rows if row.surprise_direction != "inline"))
    raise ValueError("reason_code must be supported")


def _recommended_next_step(digest_status: str) -> str:
    if digest_status == "pass":
        return "allow_report_only_retail_sales_surprise_screening"
    if digest_status == "watch":
        return "monitor_report_only_retail_sales_surprise_screening"
    return "block_report_only_retail_sales_surprise_screening"


def _row_sort_key(
    row: RetailSalesSurpriseDigestRow,
) -> tuple[Decimal, Decimal, datetime, str, str, str]:
    return (
        -STATUS_WEIGHT[row.surprise_status],
        -row.abs_surprise_ratio,
        row.data_timestamp,
        row.region_id,
        row.segment_id,
        row.source_id,
    )


def _surprise_direction(value: Decimal) -> str:
    if value > ZERO_RATIO:
        return "positive"
    if value < ZERO_RATIO:
        return "negative"
    return "inline"


def _surprise_status(
    abs_surprise_ratio: Decimal,
    config: RetailSalesSurpriseDigestConfig,
) -> str:
    if abs_surprise_ratio >= config.blocked_abs_surprise_ratio:
        return "blocked"
    if abs_surprise_ratio >= config.watch_abs_surprise_ratio:
        return "watch"
    return "pass"


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "blocked"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _direction_count(
    rows: tuple[RetailSalesSurpriseDigestRow, ...],
    direction: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.surprise_direction == direction))


def _sum_rows(
    rows: tuple[RetailSalesSurpriseDigestRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _max_abs_surprise_ratio(
    rows: tuple[RetailSalesSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _normalize_ratio(
        "max_abs_surprise_ratio",
        max(row.abs_surprise_ratio for row in rows),
    )


def _average_surprise_ratio(
    rows: tuple[RetailSalesSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_signed_ratio(
            "average_surprise_ratio",
            sum((row.surprise_ratio for row in rows), ZERO_RATIO) / Decimal(len(rows)),
        )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_observation(row: RetailSalesSurpriseObservation) -> None:
    expected_ratio = _computed_surprise_ratio(row.observed_sales, row.expected_sales)
    if row.surprise_ratio != expected_ratio:
        raise ValueError("surprise_ratio must match observed and expected")
    direction = _surprise_direction(row.surprise_ratio)
    expected_reason_code = f"retail_sales_{direction}_surprise"
    if direction == "inline":
        expected_reason_code = "retail_sales_inline"
    if row.reason_codes != (expected_reason_code,):
        raise ValueError("reason_codes must match surprise direction")


def _validate_row(row: RetailSalesSurpriseDigestRow) -> None:
    if row.surprise_ratio != _computed_surprise_ratio(
        row.observed_sales,
        row.expected_sales,
    ):
        raise ValueError("surprise_ratio must match observed and expected")
    if row.abs_surprise_ratio != abs(row.surprise_ratio):
        raise ValueError("abs_surprise_ratio must match surprise_ratio")
    if row.surprise_direction != _surprise_direction(row.surprise_ratio):
        raise ValueError("surprise_direction must match surprise_ratio")
    if row.reason_codes != _row_reason_codes(
        row.surprise_direction,
        row.surprise_status,
    ):
        raise ValueError("reason_codes must match row status")


def _validate_report(report: RetailSalesSurpriseDigestReport) -> None:
    if report.observation_count != _count(len(report.surprise_rows)):
        raise ValueError("observation_count must match surprise_rows")
    if report.source_row_count != _sum_rows(report.surprise_rows, "source_row_count"):
        raise ValueError("source_row_count must match surprise_rows")
    if report.positive_surprise_count != _direction_count(
        report.surprise_rows,
        "positive",
    ):
        raise ValueError("positive_surprise_count must match surprise_rows")
    if report.negative_surprise_count != _direction_count(
        report.surprise_rows,
        "negative",
    ):
        raise ValueError("negative_surprise_count must match surprise_rows")
    if report.inline_count != _direction_count(report.surprise_rows, "inline"):
        raise ValueError("inline_count must match surprise_rows")
    if report.max_abs_surprise_ratio != _max_abs_surprise_ratio(report.surprise_rows):
        raise ValueError("max_abs_surprise_ratio must match surprise_rows")
    if report.average_surprise_ratio != _average_surprise_ratio(report.surprise_rows):
        raise ValueError("average_surprise_ratio must match surprise_rows")
    if report.digest_status != _status_rollup(
        tuple(row.surprise_status for row in report.surprise_rows),
    ):
        raise ValueError("digest_status must match surprise_rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.surprise_rows):
        raise ValueError("reason_codes must match surprise_rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.surprise_rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.surprise_rows != tuple(sorted(report.surprise_rows, key=_row_sort_key)):
        raise ValueError("surprise_rows must be deterministic")


def _normalize_rows(value: object) -> tuple[RetailSalesSurpriseDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("surprise_rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("surprise_rows must be a tuple") from exc
    for row in rows:
        if type(row) is not RetailSalesSurpriseDigestRow:
            raise ValueError("surprise_rows must contain RetailSalesSurpriseDigestRow values")
        require_paper_only_flags("surprise row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[RetailSalesSurpriseReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a list or tuple")
    try:
        reason_code_counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a list or tuple") from exc
    seen_reason_codes: set[str] = set()
    for item in reason_code_counts:
        if type(item) is not RetailSalesSurpriseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain RetailSalesSurpriseReasonCodeCount values",
            )
        require_paper_only_flags("reason code count", item)
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique")
        seen_reason_codes.add(item.reason_code)
    expected = tuple(
        sorted(
            reason_code_counts,
            key=lambda item: REPORT_REASON_CODES.index(item.reason_code),
        ),
    )
    if reason_code_counts != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return reason_code_counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _computed_surprise_ratio(observed_sales: Decimal, expected_sales: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_signed_ratio(
            "surprise_ratio",
            (observed_sales - expected_sales) / expected_sales,
        )


def _safe_row_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_row_ratio("row_ratio", numerator / denominator)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_row_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or _has_unsafe_public_text_fragment(lowered):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_RETAIL_SALES_SURPRISE_DIGEST_CONFIG_VERSION",
    "INPUT_REASON_CODES",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "RetailSalesSurpriseDigestConfig",
    "RetailSalesSurpriseDigestReport",
    "RetailSalesSurpriseDigestRow",
    "RetailSalesSurpriseReasonCodeCount",
    "RetailSalesSurpriseObservation",
    "build_market_research_retail_sales_surprise_digest",
    "market_research_retail_sales_surprise_digest_payload",
)
