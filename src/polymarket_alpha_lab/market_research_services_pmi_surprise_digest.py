"""Pure report reducer for services PMI surprise digests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-services-pmi-surprise-digest-v0"
)

SUMMARY_STATUSES = ("pass", "watch", "blocked")
SURPRISE_DIRECTIONS = ("upside", "downside", "inline")
ACTIVITY_STATUSES = ("expansion", "contraction")
REASON_CODES = (
    "services_pmi_surprise_digest_passed",
    "services_pmi_surprise_digest_empty",
    "services_pmi_downside_surprise_present",
    "services_pmi_upside_surprise_present",
)
NEXT_STEP = "review_services_pmi_surprises"
PMI_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
EXPANSION_LINE = Decimal("50")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchServicesPmiSurpriseDigestConfig",
    "MarketResearchServicesPmiSurpriseDigestReport",
    "PmiSurpriseDigestObservation",
    "PmiSurpriseDigestRow",
    "build_market_research_services_pmi_surprise_digest",
    "market_research_services_pmi_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchServicesPmiSurpriseDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchServicesPmiSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchServicesPmiSurpriseDigestConfig does not support subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags("MarketResearchServicesPmiSurpriseDigestConfig", self)


@dataclass(frozen=True)
class PmiSurpriseDigestObservation:
    region: str
    source_name: str
    period: str
    actual_pmi: Decimal
    consensus_pmi: Decimal
    prior_pmi: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PmiSurpriseDigestObservation:
            raise TypeError("PmiSurpriseDigestObservation does not support subclassing")
        _require_canonical_string("region", self.region)
        _require_canonical_string("source_name", self.source_name)
        _require_canonical_string("period", self.period)
        for field_name in ("actual_pmi", "consensus_pmi", "prior_pmi"):
            object.__setattr__(
                self,
                field_name,
                _quantize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("PmiSurpriseDigestObservation", self)


@dataclass(frozen=True)
class PmiSurpriseDigestRow:
    region: str
    source_name: str
    period: str
    actual_pmi: Decimal
    consensus_pmi: Decimal
    prior_pmi: Decimal
    surprise_pmi: Decimal
    abs_surprise_pmi: Decimal
    momentum_pmi: Decimal
    surprise_direction: str
    activity_status: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PmiSurpriseDigestRow:
            raise TypeError("PmiSurpriseDigestRow does not support subclassing")
        for value in (self.region, self.source_name, self.period):
            _require_row_string(value)
        for field_name in (
            "actual_pmi",
            "consensus_pmi",
            "prior_pmi",
            "surprise_pmi",
            "abs_surprise_pmi",
            "momentum_pmi",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_decimal(field_name, getattr(self, field_name)),
            )
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        _require_activity_status("activity_status", self.activity_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("PmiSurpriseDigestRow", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketResearchServicesPmiSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    summary_status: str
    summary_next_step: str
    observation_count: Decimal
    upside_surprise_count: Decimal
    downside_surprise_count: Decimal
    inline_surprise_count: Decimal
    expansion_count: Decimal
    contraction_count: Decimal
    average_surprise_pmi: Decimal
    average_abs_surprise_pmi: Decimal
    max_abs_surprise_pmi: Decimal
    upside_surprise_ratio: Decimal
    downside_surprise_ratio: Decimal
    expansion_ratio: Decimal
    rows: tuple[PmiSurpriseDigestRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchServicesPmiSurpriseDigestReport:
            raise TypeError(
                "MarketResearchServicesPmiSurpriseDigestReport does not support subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_summary_status("summary_status", self.summary_status)
        _require_canonical_string("summary_next_step", self.summary_next_step)
        for field_name in (
            "observation_count",
            "upside_surprise_count",
            "downside_surprise_count",
            "inline_surprise_count",
            "expansion_count",
            "contraction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_surprise_pmi",
            _quantize_decimal("average_surprise_pmi", self.average_surprise_pmi),
        )
        for field_name in (
            "average_abs_surprise_pmi",
            "max_abs_surprise_pmi",
            "upside_surprise_ratio",
            "downside_surprise_ratio",
            "expansion_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("MarketResearchServicesPmiSurpriseDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_services_pmi_surprise_digest(
    observations: list[PmiSurpriseDigestObservation]
    | tuple[PmiSurpriseDigestObservation, ...],
    *,
    config: MarketResearchServicesPmiSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchServicesPmiSurpriseDigestReport:
    if type(config) is not MarketResearchServicesPmiSurpriseDigestConfig:
        raise ValueError("config must be a MarketResearchServicesPmiSurpriseDigestConfig")
    _require_hard_flags("MarketResearchServicesPmiSurpriseDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _digest_rows(normalized_observations)
    reason_codes = _reason_codes(rows)

    return MarketResearchServicesPmiSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        summary_status=_summary_status(reason_codes),
        summary_next_step=NEXT_STEP,
        observation_count=_count_decimal(len(rows)),
        upside_surprise_count=_count_decimal(_direction_count(rows, "upside")),
        downside_surprise_count=_count_decimal(_direction_count(rows, "downside")),
        inline_surprise_count=_count_decimal(_direction_count(rows, "inline")),
        expansion_count=_count_decimal(_activity_count(rows, "expansion")),
        contraction_count=_count_decimal(_activity_count(rows, "contraction")),
        average_surprise_pmi=_average((row.surprise_pmi for row in rows), len(rows)),
        average_abs_surprise_pmi=_average(
            (row.abs_surprise_pmi for row in rows),
            len(rows),
        ),
        max_abs_surprise_pmi=_max_abs_surprise(rows),
        upside_surprise_ratio=_ratio(_direction_count(rows, "upside"), len(rows)),
        downside_surprise_ratio=_ratio(_direction_count(rows, "downside"), len(rows)),
        expansion_ratio=_ratio(_activity_count(rows, "expansion"), len(rows)),
        rows=rows,
        reason_codes=reason_codes,
    )


def market_research_services_pmi_surprise_digest_payload(
    report: MarketResearchServicesPmiSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchServicesPmiSurpriseDigestReport:
        raise ValueError("report must be a MarketResearchServicesPmiSurpriseDigestReport")
    _require_hard_flags("MarketResearchServicesPmiSurpriseDigestReport", report)
    return _payload_value(asdict(report))


def _normalize_observations(
    observations: list[PmiSurpriseDigestObservation]
    | tuple[PmiSurpriseDigestObservation, ...],
) -> tuple[PmiSurpriseDigestObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not PmiSurpriseDigestObservation:
            raise ValueError("observations must contain PmiSurpriseDigestObservation values")
        _require_hard_flags("PmiSurpriseDigestObservation", item)
    return normalized


def _digest_rows(
    observations: tuple[PmiSurpriseDigestObservation, ...],
) -> tuple[PmiSurpriseDigestRow, ...]:
    rows = tuple(_row_from_observation(item) for item in observations)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_observation(item: PmiSurpriseDigestObservation) -> PmiSurpriseDigestRow:
    surprise = item.actual_pmi - item.consensus_pmi
    return PmiSurpriseDigestRow(
        region=item.region,
        source_name=item.source_name,
        period=item.period,
        actual_pmi=item.actual_pmi,
        consensus_pmi=item.consensus_pmi,
        prior_pmi=item.prior_pmi,
        surprise_pmi=surprise,
        abs_surprise_pmi=abs(surprise),
        momentum_pmi=item.actual_pmi - item.prior_pmi,
        surprise_direction=_surprise_direction(surprise),
        activity_status=_activity_status(item.actual_pmi),
        observed_at=item.observed_at,
    )


def _row_sort_key(row: PmiSurpriseDigestRow) -> tuple[Decimal, str, str, str, str]:
    return (
        -row.abs_surprise_pmi,
        row.region,
        row.source_name,
        row.period,
        row.observed_at.isoformat(),
    )


def _reason_codes(rows: tuple[PmiSurpriseDigestRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("services_pmi_surprise_digest_empty",)
    reason_codes = []
    if any(row.surprise_direction == "downside" for row in rows):
        reason_codes.append("services_pmi_downside_surprise_present")
    if any(row.surprise_direction == "upside" for row in rows):
        reason_codes.append("services_pmi_upside_surprise_present")
    if reason_codes:
        return tuple(reason_codes)
    return ("services_pmi_surprise_digest_passed",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("services_pmi_surprise_digest_passed",):
        return "pass"
    if reason_codes == ("services_pmi_surprise_digest_empty",):
        return "blocked"
    return "watch"


def _surprise_direction(value: Decimal) -> str:
    if value > ZERO:
        return "upside"
    if value < ZERO:
        return "downside"
    return "inline"


def _activity_status(value: Decimal) -> str:
    if value >= EXPANSION_LINE:
        return "expansion"
    return "contraction"


def _direction_count(rows: tuple[PmiSurpriseDigestRow, ...], direction: str) -> int:
    return sum(1 for row in rows if row.surprise_direction == direction)


def _activity_count(rows: tuple[PmiSurpriseDigestRow, ...], activity_status: str) -> int:
    return sum(1 for row in rows if row.activity_status == activity_status)


def _average(values: object, count: int) -> Decimal:
    if count == 0:
        return _six(ZERO)
    return _six(sum(values, ZERO) / Decimal(count))


def _ratio(value: int, total: int) -> Decimal:
    if total == 0:
        return _six(ZERO)
    return _six(Decimal(value) / Decimal(total))


def _max_abs_surprise(rows: tuple[PmiSurpriseDigestRow, ...]) -> Decimal:
    if not rows:
        return _six(ZERO)
    return _six(max(row.abs_surprise_pmi for row in rows))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _six(Decimal(value))


def _validate_row_consistency(row: PmiSurpriseDigestRow) -> None:
    expected_surprise = (row.actual_pmi - row.consensus_pmi).quantize(PMI_QUANT)
    if row.surprise_pmi != expected_surprise:
        raise ValueError("surprise_pmi must match actual less consensus")
    if row.abs_surprise_pmi != abs(row.surprise_pmi).quantize(PMI_QUANT):
        raise ValueError("abs_surprise_pmi must match surprise_pmi")
    if row.momentum_pmi != (row.actual_pmi - row.prior_pmi).quantize(PMI_QUANT):
        raise ValueError("momentum_pmi must match actual less prior")
    if row.surprise_direction != _surprise_direction(row.surprise_pmi):
        raise ValueError("surprise_direction must match surprise_pmi")
    if row.activity_status != _activity_status(row.actual_pmi):
        raise ValueError("activity_status must match actual_pmi")


def _validate_report_consistency(
    report: MarketResearchServicesPmiSurpriseDigestReport,
) -> None:
    row_count = len(report.rows)
    if report.observation_count != _count_decimal(row_count):
        raise ValueError("observation_count must match rows")
    if report.upside_surprise_count != _count_decimal(_direction_count(report.rows, "upside")):
        raise ValueError("upside_surprise_count must match rows")
    if report.downside_surprise_count != _count_decimal(
        _direction_count(report.rows, "downside"),
    ):
        raise ValueError("downside_surprise_count must match rows")
    if report.inline_surprise_count != _count_decimal(_direction_count(report.rows, "inline")):
        raise ValueError("inline_surprise_count must match rows")
    if report.expansion_count != _count_decimal(_activity_count(report.rows, "expansion")):
        raise ValueError("expansion_count must match rows")
    if report.contraction_count != _count_decimal(_activity_count(report.rows, "contraction")):
        raise ValueError("contraction_count must match rows")
    if (
        report.upside_surprise_count
        + report.downside_surprise_count
        + report.inline_surprise_count
        != report.observation_count
    ):
        raise ValueError("surprise counts must reconcile")
    if report.expansion_count + report.contraction_count != report.observation_count:
        raise ValueError("activity counts must reconcile")
    if report.average_surprise_pmi != _average(
        (row.surprise_pmi for row in report.rows),
        row_count,
    ):
        raise ValueError("average_surprise_pmi must match rows")
    if report.average_abs_surprise_pmi != _average(
        (row.abs_surprise_pmi for row in report.rows),
        row_count,
    ):
        raise ValueError("average_abs_surprise_pmi must match rows")
    if report.max_abs_surprise_pmi != _max_abs_surprise(report.rows):
        raise ValueError("max_abs_surprise_pmi must match rows")
    if report.upside_surprise_ratio != _ratio(_direction_count(report.rows, "upside"), row_count):
        raise ValueError("upside_surprise_ratio must match rows")
    if report.downside_surprise_ratio != _ratio(
        _direction_count(report.rows, "downside"),
        row_count,
    ):
        raise ValueError("downside_surprise_ratio must match rows")
    if report.expansion_ratio != _ratio(_activity_count(report.rows, "expansion"), row_count):
        raise ValueError("expansion_ratio must match rows")
    if report.reason_codes != _reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.summary_status != _summary_status(report.reason_codes):
        raise ValueError("summary_status must match reason_codes")
    if report.summary_next_step != NEXT_STEP:
        raise ValueError("summary_next_step must match digest reducer")


def _normalize_rows(
    rows: tuple[PmiSurpriseDigestRow, ...],
) -> tuple[PmiSurpriseDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not PmiSurpriseDigestRow:
            raise ValueError("rows must contain PmiSurpriseDigestRow values")
        for value in (row.region, row.source_name, row.period):
            _require_row_string(value)
        _require_hard_flags("PmiSurpriseDigestRow", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_row_string(value: object) -> None:
    if type(value) is not str:
        raise ValueError("rows must contain string identifiers")
    if not value or value.strip() != value:
        raise ValueError("rows must contain canonical strings")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _six(value)


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _six(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_summary_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SUMMARY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_surprise_direction(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SURPRISE_DIRECTIONS:
        raise ValueError(f"{field_name} must be upside, downside, or inline")


def _require_activity_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ACTIVITY_STATUSES:
        raise ValueError(f"{field_name} must be expansion or contraction")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _six(value: Decimal) -> Decimal:
    return value.quantize(PMI_QUANT, rounding=ROUND_HALF_EVEN)


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(_six(value), "f")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value
