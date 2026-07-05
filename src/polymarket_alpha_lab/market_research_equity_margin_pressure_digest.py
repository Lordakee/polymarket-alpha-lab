"""Pure equity margin pressure digest reducer for market research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_MARGIN_PRESSURE_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityMarginPressureDigestConfig",
    "MarketResearchEquityMarginPressureDigestInput",
    "MarketResearchEquityMarginPressureDigestReasonCodeCount",
    "MarketResearchEquityMarginPressureDigestReport",
    "MarketResearchEquityMarginPressureDigestRow",
    "build_market_research_equity_margin_pressure_digest_report",
    "market_research_equity_margin_pressure_digest_payload",
)


DEFAULT_MARKET_RESEARCH_EQUITY_MARGIN_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-equity-margin-pressure-digest-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "market_research_equity_margin_pressure_digest_no_inputs"


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class MarketResearchEquityMarginPressureDigestConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_MARGIN_PRESSURE_DIGEST_CONFIG_VERSION
    )
    gross_margin_pressure_watch: Decimal = Decimal("0.020000")
    gross_margin_pressure_blocked: Decimal = Decimal("0.050000")
    operating_margin_pressure_watch: Decimal = Decimal("0.020000")
    operating_margin_pressure_blocked: Decimal = Decimal("0.040000")
    cost_inflation_watch: Decimal = Decimal("0.030000")
    pricing_power_floor: Decimal = Decimal("0.000000")
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityMarginPressureDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "gross_margin_pressure_watch",
            "gross_margin_pressure_blocked",
            "operating_margin_pressure_watch",
            "operating_margin_pressure_blocked",
            "cost_inflation_watch",
            "stale_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pricing_power_floor",
            _normalize_decimal("pricing_power_floor", self.pricing_power_floor),
        )
        _require_at_most(
            "gross_margin_pressure_watch",
            self.gross_margin_pressure_watch,
            self.gross_margin_pressure_blocked,
        )
        _require_at_most(
            "operating_margin_pressure_watch",
            self.operating_margin_pressure_watch,
            self.operating_margin_pressure_blocked,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityMarginPressureDigestInput(_FinalPublicDataclass):
    company_id: str
    sector: str
    gross_margin_change: Decimal
    operating_margin_change: Decimal
    input_cost_inflation: Decimal
    pricing_power_change: Decimal
    source_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityMarginPressureDigestInput,
            "input",
        )
        _require_canonical_string("company_id", self.company_id)
        _require_canonical_string("sector", self.sector)
        for field_name in (
            "gross_margin_change",
            "operating_margin_change",
            "pricing_power_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "input_cost_inflation",
            _normalize_nonnegative_decimal(
                "input_cost_inflation",
                self.input_cost_inflation,
            ),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResearchEquityMarginPressureDigestRow(_FinalPublicDataclass):
    company_id: str
    sector: str
    pressure_status: str
    gross_margin_change: Decimal
    operating_margin_change: Decimal
    input_cost_inflation: Decimal
    pricing_power_change: Decimal
    margin_pressure_score: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityMarginPressureDigestRow,
            "row",
        )
        _require_canonical_string("company_id", self.company_id)
        _require_canonical_string("sector", self.sector)
        _require_status("pressure_status", self.pressure_status)
        for field_name in (
            "gross_margin_change",
            "operating_margin_change",
            "pricing_power_change",
            "margin_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("input_cost_inflation", "source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.pressure_status != _row_status(self.reason_codes):
            raise ValueError("pressure_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEquityMarginPressureDigestReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityMarginPressureDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchEquityMarginPressureDigestReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    company_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    gross_margin_pressure_count: Decimal
    operating_margin_pressure_count: Decimal
    cost_inflation_watch_count: Decimal
    stale_source_count: Decimal
    mean_margin_pressure_score: Decimal
    max_margin_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketResearchEquityMarginPressureDigestReasonCodeCount, ...]
    company_rows: tuple[MarketResearchEquityMarginPressureDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityMarginPressureDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "company_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "gross_margin_pressure_count",
            "operating_margin_pressure_count",
            "cost_inflation_watch_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_margin_pressure_score",
            "max_margin_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "company_rows", _normalize_rows(self.company_rows))
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchEquityMarginPressureDigestConfig,
    MarketResearchEquityMarginPressureDigestInput,
    MarketResearchEquityMarginPressureDigestReasonCodeCount,
    MarketResearchEquityMarginPressureDigestReport,
    MarketResearchEquityMarginPressureDigestRow,
)


def build_market_research_equity_margin_pressure_digest_report(
    observations: Iterable[MarketResearchEquityMarginPressureDigestInput],
    *,
    config: MarketResearchEquityMarginPressureDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityMarginPressureDigestReport:
    if type(config) is not MarketResearchEquityMarginPressureDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEquityMarginPressureDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations)
    rows = tuple(
        sorted(
            (
                _digest_row(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return MarketResearchEquityMarginPressureDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        company_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        gross_margin_pressure_count=_count(
            sum(
                1
                for row in rows
                if any(
                    code.startswith("gross_margin_pressure_")
                    for code in row.reason_codes
                )
            ),
        ),
        operating_margin_pressure_count=_count(
            sum(
                1
                for row in rows
                if any(
                    code.startswith("operating_margin_pressure_")
                    for code in row.reason_codes
                )
            ),
        ),
        cost_inflation_watch_count=_count(
            sum(1 for row in rows if "cost_inflation_watch" in row.reason_codes),
        ),
        stale_source_count=_count(
            sum(1 for row in rows if "source_stale_watch" in row.reason_codes),
        ),
        mean_margin_pressure_score=_mean(
            tuple(row.margin_pressure_score for row in rows),
        ),
        max_margin_pressure_score=_max_decimal(
            tuple(row.margin_pressure_score for row in rows),
        ),
        status=_rollup_status(tuple(row.pressure_status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        company_rows=rows,
    )


def market_research_equity_margin_pressure_digest_payload(
    report: MarketResearchEquityMarginPressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityMarginPressureDigestReport:
        raise ValueError(
            "report must be a MarketResearchEquityMarginPressureDigestReport",
        )
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _revalidate_public_dataclass_for_payload(label: str, value: object) -> None:
    if type(value) is MarketResearchEquityMarginPressureDigestConfig:
        _revalidate_config_for_payload(value)
        return
    if type(value) is MarketResearchEquityMarginPressureDigestInput:
        _revalidate_input_for_payload(value)
        return
    if type(value) is MarketResearchEquityMarginPressureDigestRow:
        _revalidate_row_for_payload(value)
        return
    if type(value) is MarketResearchEquityMarginPressureDigestReasonCodeCount:
        _revalidate_reason_code_count_for_payload(value)
        return
    if type(value) is MarketResearchEquityMarginPressureDigestReport:
        _revalidate_report_for_payload(value)
        return
        raise ValueError(f"{label} contains unsupported dataclass")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        _revalidate_public_dataclass_for_payload(label, value)
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _revalidate_config_for_payload(
    config: MarketResearchEquityMarginPressureDigestConfig,
) -> None:
    _require_exact_type(
        config,
        MarketResearchEquityMarginPressureDigestConfig,
        "config",
    )
    _require_canonical_string("config_version", config.config_version)
    for field_name in (
        "gross_margin_pressure_watch",
        "gross_margin_pressure_blocked",
        "operating_margin_pressure_watch",
        "operating_margin_pressure_blocked",
        "cost_inflation_watch",
        "stale_source_age_seconds",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(config, field_name))
    _require_six_decimal_decimal("pricing_power_floor", config.pricing_power_floor)
    _require_at_most(
        "gross_margin_pressure_watch",
        config.gross_margin_pressure_watch,
        config.gross_margin_pressure_blocked,
    )
    _require_at_most(
        "operating_margin_pressure_watch",
        config.operating_margin_pressure_watch,
        config.operating_margin_pressure_blocked,
    )
    _require_hard_flags("config", config)


def _revalidate_input_for_payload(
    row: MarketResearchEquityMarginPressureDigestInput,
) -> None:
    _require_exact_type(
        row,
        MarketResearchEquityMarginPressureDigestInput,
        "input",
    )
    _require_canonical_string("company_id", row.company_id)
    _require_canonical_string("sector", row.sector)
    for field_name in (
        "gross_margin_change",
        "operating_margin_change",
        "pricing_power_change",
    ):
        _require_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_nonnegative_six_decimal_decimal(
        "input_cost_inflation",
        row.input_cost_inflation,
    )
    _require_utc_datetime("source_observed_at", row.source_observed_at)
    _require_reason_codes_tuple(row.reason_codes)
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    _require_hard_flags("input", row)


def _revalidate_row_for_payload(
    row: MarketResearchEquityMarginPressureDigestRow,
) -> None:
    _require_exact_type(
        row,
        MarketResearchEquityMarginPressureDigestRow,
        "row",
    )
    _require_canonical_string("company_id", row.company_id)
    _require_canonical_string("sector", row.sector)
    _require_status("pressure_status", row.pressure_status)
    for field_name in (
        "gross_margin_change",
        "operating_margin_change",
        "pricing_power_change",
        "margin_pressure_score",
    ):
        _require_six_decimal_decimal(field_name, getattr(row, field_name))
    for field_name in ("input_cost_inflation", "source_age_seconds"):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_utc_datetime("source_observed_at", row.source_observed_at)
    _require_reason_codes_tuple(row.reason_codes)
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.pressure_status != _row_status(row.reason_codes):
        raise ValueError("pressure_status must match reason_codes")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(
    row: MarketResearchEquityMarginPressureDigestReasonCodeCount,
) -> None:
    _require_exact_type(
        row,
        MarketResearchEquityMarginPressureDigestReasonCodeCount,
        "reason_code_count",
    )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _revalidate_report_for_payload(
    report: MarketResearchEquityMarginPressureDigestReport,
) -> None:
    _require_exact_type(
        report,
        MarketResearchEquityMarginPressureDigestReport,
        "report",
    )
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "company_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "gross_margin_pressure_count",
        "operating_margin_pressure_count",
        "cost_inflation_watch_count",
        "stale_source_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_margin_pressure_score",
        "max_margin_pressure_score",
    ):
        _require_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _require_reason_codes_tuple(report.reason_codes)
    _normalize_report_reason_codes(report.reason_codes)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in report.reason_code_counts:
        if type(row) is not MarketResearchEquityMarginPressureDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchEquityMarginPressureDigestReasonCodeCount values",
            )
        _revalidate_reason_code_count_for_payload(row)
    if type(report.company_rows) is not tuple:
        raise ValueError("company_rows must be a tuple")
    for row in report.company_rows:
        if type(row) is not MarketResearchEquityMarginPressureDigestRow:
            raise ValueError(
                "company_rows must contain MarketResearchEquityMarginPressureDigestRow values",
            )
        _revalidate_row_for_payload(row)
    _validate_report(report)
    _require_hard_flags("report", report)


def _digest_row(
    row: MarketResearchEquityMarginPressureDigestInput,
    *,
    config: MarketResearchEquityMarginPressureDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityMarginPressureDigestRow:
    source_age_seconds = _source_age_seconds(row.source_observed_at, generated_at)
    margin_pressure_score = _margin_pressure_score(row)
    reason_codes = _row_reason_codes(
        row,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    return MarketResearchEquityMarginPressureDigestRow(
        company_id=row.company_id,
        sector=row.sector,
        pressure_status=_row_status(reason_codes),
        gross_margin_change=row.gross_margin_change,
        operating_margin_change=row.operating_margin_change,
        input_cost_inflation=row.input_cost_inflation,
        pricing_power_change=row.pricing_power_change,
        margin_pressure_score=margin_pressure_score,
        source_observed_at=row.source_observed_at,
        source_age_seconds=source_age_seconds,
        reason_codes=reason_codes,
    )


def _margin_pressure_score(row: MarketResearchEquityMarginPressureDigestInput) -> Decimal:
    gross_pressure = (
        _quantize(-row.gross_margin_change)
        if _quantize(-row.gross_margin_change) >= Decimal("0.020000")
        else ZERO
    )
    operating_pressure = (
        _quantize(-row.operating_margin_change)
        if _quantize(-row.operating_margin_change) >= Decimal("0.020000")
        else ZERO
    )
    return _quantize(gross_pressure + operating_pressure)


def _row_reason_codes(
    row: MarketResearchEquityMarginPressureDigestInput,
    *,
    source_age_seconds: Decimal,
    config: MarketResearchEquityMarginPressureDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    gross_pressure = _quantize(-row.gross_margin_change)
    operating_pressure = _quantize(-row.operating_margin_change)
    if gross_pressure >= config.gross_margin_pressure_blocked:
        reason_codes.append("gross_margin_pressure_blocked")
    elif gross_pressure >= config.gross_margin_pressure_watch:
        reason_codes.append("gross_margin_pressure_watch")
    if operating_pressure >= config.operating_margin_pressure_blocked:
        reason_codes.append("operating_margin_pressure_blocked")
    elif operating_pressure >= config.operating_margin_pressure_watch:
        reason_codes.append("operating_margin_pressure_watch")
    if row.input_cost_inflation >= config.cost_inflation_watch:
        reason_codes.append("cost_inflation_watch")
    if row.pricing_power_change < config.pricing_power_floor:
        reason_codes.append("pricing_power_negative_blocked")
    if source_age_seconds > config.stale_source_age_seconds:
        reason_codes.append("source_stale_watch")
    if not _has_pressure_reason(reason_codes):
        reason_codes.append("margin_pressure_clear")
    return tuple(sorted(reason_codes))


def _has_pressure_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code.endswith("_watch") or reason_code.endswith("_blocked")
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "blocked"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[MarketResearchEquityMarginPressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.pressure_status for row in rows))
    reason_codes = [f"equity_margin_pressure_digest_{'clear' if status == 'pass' else status}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "cost_inflation_watch",
        "gross_margin_pressure_blocked",
        "gross_margin_pressure_watch",
        "operating_margin_pressure_blocked",
        "operating_margin_pressure_watch",
        "pricing_power_negative_blocked",
        "source_stale_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[MarketResearchEquityMarginPressureDigestRow, ...],
) -> tuple[MarketResearchEquityMarginPressureDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchEquityMarginPressureDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _source_age_seconds(
    source_observed_at: datetime,
    generated_at: datetime,
) -> Decimal:
    seconds = Decimal(
        str(
            (
                generated_at - _as_utc("source_observed_at", source_observed_at)
            ).total_seconds(),
        ),
    )
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("source_observed_at must not be after generated_at")
    return age_seconds


def _normalize_inputs(
    observations: Iterable[MarketResearchEquityMarginPressureDigestInput],
) -> tuple[MarketResearchEquityMarginPressureDigestInput, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchEquityMarginPressureDigestInput:
            raise ValueError(
                "observations must contain MarketResearchEquityMarginPressureDigestInput values",
            )
        _require_hard_flags("input", row)
        if row.company_id in seen_ids:
            raise ValueError("observations must not contain duplicate company_id values")
        seen_ids.add(row.company_id)
    return rows


def _normalize_rows(
    rows: Iterable[MarketResearchEquityMarginPressureDigestRow],
) -> tuple[MarketResearchEquityMarginPressureDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("company_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("company_rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in values:
        if type(row) is not MarketResearchEquityMarginPressureDigestRow:
            raise ValueError(
                "company_rows must contain MarketResearchEquityMarginPressureDigestRow values",
            )
        _require_hard_flags("row", row)
        if row.company_id in seen_ids:
            raise ValueError("company_rows must not contain duplicate company_id values")
        seen_ids.add(row.company_id)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("company_rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[MarketResearchEquityMarginPressureDigestReasonCodeCount],
) -> tuple[MarketResearchEquityMarginPressureDigestReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not MarketResearchEquityMarginPressureDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchEquityMarginPressureDigestReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(
    row: MarketResearchEquityMarginPressureDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.pressure_status],
        -row.margin_pressure_score,
        row.company_id,
        row.sector,
    )


def _status_count(
    rows: tuple[MarketResearchEquityMarginPressureDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.pressure_status == status))


def _validate_report(report: MarketResearchEquityMarginPressureDigestReport) -> None:
    rows = report.company_rows
    if report.company_count != _count(len(rows)):
        raise ValueError("company_count must match company_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match company_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match company_rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match company_rows")
    if report.gross_margin_pressure_count != _count(
        sum(
            1
            for row in rows
            if any(
                code.startswith("gross_margin_pressure_")
                for code in row.reason_codes
            )
        ),
    ):
        raise ValueError("gross_margin_pressure_count must match company_rows")
    if report.operating_margin_pressure_count != _count(
        sum(
            1
            for row in rows
            if any(
                code.startswith("operating_margin_pressure_")
                for code in row.reason_codes
            )
        ),
    ):
        raise ValueError("operating_margin_pressure_count must match company_rows")
    if report.cost_inflation_watch_count != _count(
        sum(1 for row in rows if "cost_inflation_watch" in row.reason_codes),
    ):
        raise ValueError("cost_inflation_watch_count must match company_rows")
    if report.stale_source_count != _count(
        sum(1 for row in rows if "source_stale_watch" in row.reason_codes),
    ):
        raise ValueError("stale_source_count must match company_rows")
    if report.mean_margin_pressure_score != _mean(
        tuple(row.margin_pressure_score for row in rows),
    ):
        raise ValueError("mean_margin_pressure_score must match company_rows")
    if report.max_margin_pressure_score != _max_decimal(
        tuple(row.margin_pressure_score for row in rows),
    ):
        raise ValueError("max_margin_pressure_score must match company_rows")
    if report.status != _rollup_status(tuple(row.pressure_status for row in rows)):
        raise ValueError("status must match company_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match company_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match company_rows")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        _require_six_decimal_decimal(path or label, value)
        return
    if isinstance(value, datetime):
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_nonnegative_six_decimal_decimal(
    field_name: str,
    value: Decimal,
) -> None:
    _require_six_decimal_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_six_decimal_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_reason_codes_tuple(reason_codes: object) -> None:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
