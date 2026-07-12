"""Report-only source family redundancy snapshot for probability events."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Any


__all__ = (
    "ProbabilityEventSourceFamilyRedundancyConfig",
    "ProbabilityEventSourceFamilyRedundancyReport",
    "build_probability_event_source_family_redundancy_report",
    "probability_event_source_family_redundancy_report_payload",
)


DEFAULT_CONFIG_VERSION = "probability-event-source-family-redundancy-v0"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")

REDUNDANCY_STATUSES = ("pass", "watch", "block")
REASON_CODE_SEQUENCE = (
    "source_family_contradiction_present",
    "source_family_count_below_minimum",
    "independent_family_under_minimum",
    "official_family_concentration",
    "single_source_dependency_present",
    "source_family_redundancy_pass",
)
MANUAL_NEXT_STEPS = (
    "continue_paper_review_with_current_source_mix",
    "manually_add_independent_source_family",
    "pause_paper_event_and_resolve_source_contradictions",
    "pause_paper_event_and_collect_more_source_families",
)


@dataclass(frozen=True)
class ProbabilityEventSourceFamilyRedundancyConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_source_family_count: Decimal = Decimal("3.000000")
    min_independent_family_count: Decimal = Decimal("2.000000")
    min_independent_family_ratio: Decimal = Decimal("0.500000")
    official_family_concentration_threshold: Decimal = Decimal("0.666667")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSourceFamilyRedundancyConfig:
            raise TypeError(
                "ProbabilityEventSourceFamilyRedundancyConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSourceFamilyRedundancyConfig:
            raise ValueError(
                "config must be exactly ProbabilityEventSourceFamilyRedundancyConfig",
            )
        _require_config_version(self.config_version)
        for field_name in ("min_source_family_count", "min_independent_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_independent_family_ratio",
            "official_family_concentration_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventSourceFamilyRedundancyReport:
    generated_at: datetime
    config_version: str
    source_family_count: Decimal
    official_family_count: Decimal
    independent_family_count: Decimal
    single_source_dependency_count: Decimal
    contradiction_count: Decimal
    independent_family_ratio: Decimal
    official_family_ratio: Decimal
    redundancy_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSourceFamilyRedundancyReport:
            raise TypeError(
                "ProbabilityEventSourceFamilyRedundancyReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSourceFamilyRedundancyReport:
            raise ValueError(
                "report must be exactly ProbabilityEventSourceFamilyRedundancyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "source_family_count",
            "official_family_count",
            "independent_family_count",
            "single_source_dependency_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("independent_family_ratio", "official_family_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_family_counts(self)
        _require_enum("redundancy_status", self.redundancy_status, REDUNDANCY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def status(self) -> str:
        return self.redundancy_status

    @property
    def payload(self) -> dict[str, Any]:
        return probability_event_source_family_redundancy_report_payload(self)


def build_probability_event_source_family_redundancy_report(
    *,
    source_family_count: Decimal,
    official_family_count: Decimal,
    independent_family_count: Decimal,
    single_source_dependency_count: Decimal,
    contradiction_count: Decimal,
    config: ProbabilityEventSourceFamilyRedundancyConfig,
    generated_at: datetime,
) -> ProbabilityEventSourceFamilyRedundancyReport:
    if type(config) is not ProbabilityEventSourceFamilyRedundancyConfig:
        raise ValueError("config must be a ProbabilityEventSourceFamilyRedundancyConfig")
    _require_hard_flags("config", config)
    source_count = _require_nonnegative_count_decimal(
        "source_family_count",
        source_family_count,
    )
    official_count = _require_nonnegative_count_decimal(
        "official_family_count",
        official_family_count,
    )
    independent_count = _require_nonnegative_count_decimal(
        "independent_family_count",
        independent_family_count,
    )
    single_dependency_count = _require_nonnegative_count_decimal(
        "single_source_dependency_count",
        single_source_dependency_count,
    )
    contradiction_total = _require_nonnegative_count_decimal(
        "contradiction_count",
        contradiction_count,
    )
    _validate_raw_family_counts(
        source_family_count=source_count,
        official_family_count=official_count,
        independent_family_count=independent_count,
        single_source_dependency_count=single_dependency_count,
    )
    independent_ratio = _ratio(independent_count, source_count)
    official_ratio = _ratio(official_count, source_count)
    reason_codes = _reason_codes(
        source_family_count=source_count,
        official_family_count=official_count,
        independent_family_count=independent_count,
        single_source_dependency_count=single_dependency_count,
        contradiction_count=contradiction_total,
        independent_family_ratio=independent_ratio,
        official_family_ratio=official_ratio,
        config=config,
    )
    redundancy_status = _redundancy_status(reason_codes)
    return ProbabilityEventSourceFamilyRedundancyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_family_count=source_count,
        official_family_count=official_count,
        independent_family_count=independent_count,
        single_source_dependency_count=single_dependency_count,
        contradiction_count=contradiction_total,
        independent_family_ratio=independent_ratio,
        official_family_ratio=official_ratio,
        redundancy_status=redundancy_status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(redundancy_status, reason_codes),
    )


def probability_event_source_family_redundancy_report_payload(
    report: ProbabilityEventSourceFamilyRedundancyReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventSourceFamilyRedundancyReport:
        raise ValueError(
            "report must be a ProbabilityEventSourceFamilyRedundancyReport",
        )
    _require_hard_flags("report", report)
    return {field.name: _payload_value(getattr(report, field.name)) for field in fields(report)}


def _reason_codes(
    *,
    source_family_count: Decimal,
    official_family_count: Decimal,
    independent_family_count: Decimal,
    single_source_dependency_count: Decimal,
    contradiction_count: Decimal,
    independent_family_ratio: Decimal,
    official_family_ratio: Decimal,
    config: ProbabilityEventSourceFamilyRedundancyConfig,
) -> tuple[str, ...]:
    if contradiction_count > ZERO:
        return ("source_family_contradiction_present",)

    reason_codes: list[str] = []
    if source_family_count < config.min_source_family_count:
        reason_codes.append("source_family_count_below_minimum")
    if (
        independent_family_count < config.min_independent_family_count
        or independent_family_ratio < config.min_independent_family_ratio
    ):
        reason_codes.append("independent_family_under_minimum")
    if (
        official_family_count > ZERO
        and official_family_ratio >= config.official_family_concentration_threshold
    ):
        reason_codes.append("official_family_concentration")
    if single_source_dependency_count > ZERO:
        reason_codes.append("single_source_dependency_present")
    if not reason_codes:
        reason_codes.append("source_family_redundancy_pass")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _redundancy_status(reason_codes: tuple[str, ...]) -> str:
    if "source_family_contradiction_present" in reason_codes:
        return "block"
    if "source_family_count_below_minimum" in reason_codes:
        return "block"
    if reason_codes == ("source_family_redundancy_pass",):
        return "pass"
    return "watch"


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if "source_family_contradiction_present" in reason_codes:
        return "pause_paper_event_and_resolve_source_contradictions"
    if "source_family_count_below_minimum" in reason_codes:
        return "pause_paper_event_and_collect_more_source_families"
    if status == "watch":
        return "manually_add_independent_source_family"
    return "continue_paper_review_with_current_source_mix"


def _validate_report_consistency(
    report: ProbabilityEventSourceFamilyRedundancyReport,
) -> None:
    expected_independent_ratio = _ratio(
        report.independent_family_count,
        report.source_family_count,
    )
    if report.independent_family_ratio != expected_independent_ratio:
        raise ValueError("independent_family_ratio must match family counts")
    expected_official_ratio = _ratio(report.official_family_count, report.source_family_count)
    if report.official_family_ratio != expected_official_ratio:
        raise ValueError("official_family_ratio must match family counts")
    expected_status = _redundancy_status(report.reason_codes)
    if report.redundancy_status != expected_status:
        raise ValueError("reason_codes must match redundancy_status")
    expected_next_step = _manual_next_step(report.redundancy_status, report.reason_codes)
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match redundancy_status")


def _validate_family_counts(
    report: ProbabilityEventSourceFamilyRedundancyReport,
) -> None:
    _validate_raw_family_counts(
        source_family_count=report.source_family_count,
        official_family_count=report.official_family_count,
        independent_family_count=report.independent_family_count,
        single_source_dependency_count=report.single_source_dependency_count,
    )


def _validate_raw_family_counts(
    *,
    source_family_count: Decimal,
    official_family_count: Decimal,
    independent_family_count: Decimal,
    single_source_dependency_count: Decimal,
) -> None:
    if official_family_count > source_family_count:
        raise ValueError("official_family_count must not exceed source_family_count")
    if independent_family_count > source_family_count:
        raise ValueError("independent_family_count must not exceed source_family_count")
    if single_source_dependency_count > source_family_count:
        raise ValueError(
            "single_source_dependency_count must not exceed source_family_count",
        )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _quantize(numerator / denominator)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_config_version(value: object) -> str:
    if type(value) is not str or value != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return value


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)


def _require_manual_next_step(value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be a supported value")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload values must be JSON-ready report values")
