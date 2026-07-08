"""Pure report-only domain research risk budget reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_RESEARCH_DOMAIN_RISK_BUDGET_REPORT_CONFIG_VERSION = (
    "research-domain-risk-budget-report-v0"
)

DOMAIN_SEQUENCE = (
    "politics",
    "btc",
    "equity_index",
    "gold",
    "soccer",
    "basketball",
)
STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "research_domain_budget_clear",
    "research_domain_information_block",
    "research_domain_information_watch",
    "research_domain_resource_block",
    "research_domain_resource_watch",
    "research_domain_review_block",
    "research_domain_review_watch",
)
REPORT_REASON_CODES = (
    "research_domain_risk_budget_empty",
    "research_domain_budget_block_present",
    "research_domain_budget_watch_present",
    "research_domain_budget_clear",
    "research_domain_information_risk_present",
    "research_domain_resource_gap_present",
    "research_domain_review_capacity_gap_present",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
BLOCK_RISK_SCORE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_RISK_BUDGET_REPORT_CONFIG_VERSION",
    "ResearchDomainRiskBudgetConfig",
    "ResearchDomainRiskBudgetSignal",
    "ResearchDomainRiskBudgetRow",
    "ResearchDomainRiskBudgetReasonCodeCount",
    "ResearchDomainRiskBudgetReport",
    "build_research_domain_risk_budget_report",
    "research_domain_risk_budget_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainRiskBudgetConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_RISK_BUDGET_REPORT_CONFIG_VERSION
    watch_research_resource_coverage: Decimal = Decimal("0.800000")
    block_research_resource_coverage: Decimal = Decimal("0.500000")
    watch_review_capacity_coverage: Decimal = Decimal("0.750000")
    block_review_capacity_coverage: Decimal = Decimal("0.500000")
    watch_information_risk_score: Decimal = Decimal("0.500000")
    block_information_risk_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainRiskBudgetConfig:
            raise TypeError("ResearchDomainRiskBudgetConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainRiskBudgetConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_RISK_BUDGET_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_research_resource_coverage",
            "block_research_resource_coverage",
            "watch_review_capacity_coverage",
            "block_review_capacity_coverage",
            "watch_information_risk_score",
            "block_information_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_research_resource_coverage > self.watch_research_resource_coverage:
            raise ValueError(
                "watch_research_resource_coverage must not be below "
                "block_research_resource_coverage",
            )
        if self.block_review_capacity_coverage > self.watch_review_capacity_coverage:
            raise ValueError(
                "watch_review_capacity_coverage must not be below "
                "block_review_capacity_coverage",
            )
        if self.watch_information_risk_score > self.block_information_risk_score:
            raise ValueError(
                "watch_information_risk_score must not exceed "
                "block_information_risk_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainRiskBudgetSignal:
    domain: str
    allocated_research_units: Decimal
    required_research_units: Decimal
    available_review_units: Decimal
    required_review_units: Decimal
    information_risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainRiskBudgetSignal:
            raise TypeError("ResearchDomainRiskBudgetSignal does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainRiskBudgetSignal, "signal")
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        for field_name in ("allocated_research_units", "available_review_units"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("required_research_units", "required_review_units"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "information_risk_score",
            _require_ratio("information_risk_score", self.information_risk_score),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchDomainRiskBudgetRow:
    domain: str
    allocated_research_units: Decimal
    required_research_units: Decimal
    research_resource_coverage: Decimal
    available_review_units: Decimal
    required_review_units: Decimal
    review_capacity_coverage: Decimal
    information_risk_score: Decimal
    domain_status: str
    domain_risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainRiskBudgetRow:
            raise TypeError("ResearchDomainRiskBudgetRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainRiskBudgetRow, "row")
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        for field_name in ("allocated_research_units", "available_review_units"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("required_research_units", "required_review_units"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "research_resource_coverage",
            "review_capacity_coverage",
            "information_risk_score",
            "domain_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("domain_status", self.domain_status, STATUSES)
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainRiskBudgetReasonCodeCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainRiskBudgetReasonCodeCount:
            raise TypeError(
                "ResearchDomainRiskBudgetReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainRiskBudgetReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchDomainRiskBudgetReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_research_resource_coverage: Decimal
    average_review_capacity_coverage: Decimal
    max_information_risk_score: Decimal
    overall_risk_score: Decimal
    report_status: str
    review_step: str
    rows: tuple[ResearchDomainRiskBudgetRow, ...]
    reason_code_counts: tuple[ResearchDomainRiskBudgetReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainRiskBudgetReport:
            raise TypeError("ResearchDomainRiskBudgetReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainRiskBudgetReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_RISK_BUDGET_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_research_resource_coverage",
            "average_review_capacity_coverage",
            "max_information_risk_score",
            "overall_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, STATUSES)
        _require_canonical_string("review_step", self.review_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
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
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_risk_budget_report_payload(self)


def build_research_domain_risk_budget_report(
    signals: Iterable[ResearchDomainRiskBudgetSignal],
    *,
    config: ResearchDomainRiskBudgetConfig,
    generated_at: datetime,
) -> ResearchDomainRiskBudgetReport:
    if type(config) is not ResearchDomainRiskBudgetConfig:
        raise ValueError("config must be exactly ResearchDomainRiskBudgetConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_signals(signals)
    rows = tuple(_row_from_signal(signal, config=config) for signal in normalized)
    domain_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    report_status = _report_status(rows)

    return ResearchDomainRiskBudgetReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        domain_count=domain_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_research_resource_coverage=_average_decimal(
            row.research_resource_coverage for row in rows
        ),
        average_review_capacity_coverage=_average_decimal(
            row.review_capacity_coverage for row in rows
        ),
        max_information_risk_score=max(
            (row.information_risk_score for row in rows),
            default=ZERO,
        ),
        overall_risk_score=max((row.domain_risk_score for row in rows), default=ZERO),
        report_status=report_status,
        review_step=_review_step(report_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def research_domain_risk_budget_report_payload(
    report: ResearchDomainRiskBudgetReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDomainRiskBudgetReport:
        raise ValueError("report must be exactly ResearchDomainRiskBudgetReport")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_from_signal(
    signal: ResearchDomainRiskBudgetSignal,
    *,
    config: ResearchDomainRiskBudgetConfig,
) -> ResearchDomainRiskBudgetRow:
    research_coverage = _coverage(
        signal.allocated_research_units,
        signal.required_research_units,
    )
    review_coverage = _coverage(
        signal.available_review_units,
        signal.required_review_units,
    )
    reason_codes = _row_reason_codes(
        research_resource_coverage=research_coverage,
        review_capacity_coverage=review_coverage,
        information_risk_score=signal.information_risk_score,
        config=config,
    )
    return ResearchDomainRiskBudgetRow(
        domain=signal.domain,
        allocated_research_units=signal.allocated_research_units,
        required_research_units=signal.required_research_units,
        research_resource_coverage=research_coverage,
        available_review_units=signal.available_review_units,
        required_review_units=signal.required_review_units,
        review_capacity_coverage=review_coverage,
        information_risk_score=signal.information_risk_score,
        domain_status=_status_from_reason_codes(reason_codes),
        domain_risk_score=_domain_risk_score(
            research_resource_coverage=research_coverage,
            review_capacity_coverage=review_coverage,
            information_risk_score=signal.information_risk_score,
        ),
        upstream_reason_codes=signal.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    research_resource_coverage: Decimal,
    review_capacity_coverage: Decimal,
    information_risk_score: Decimal,
    config: ResearchDomainRiskBudgetConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if research_resource_coverage < config.block_research_resource_coverage:
        reason_codes.append("research_domain_resource_block")
    elif research_resource_coverage < config.watch_research_resource_coverage:
        reason_codes.append("research_domain_resource_watch")

    if review_capacity_coverage < config.block_review_capacity_coverage:
        reason_codes.append("research_domain_review_block")
    elif review_capacity_coverage < config.watch_review_capacity_coverage:
        reason_codes.append("research_domain_review_watch")

    if information_risk_score >= config.block_information_risk_score:
        reason_codes.append("research_domain_information_block")
    elif information_risk_score >= config.watch_information_risk_score:
        reason_codes.append("research_domain_information_watch")

    if not reason_codes:
        reason_codes.append("research_domain_budget_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == ("research_domain_budget_clear",):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[ResearchDomainRiskBudgetRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_domain_risk_budget_empty",)
    reason_codes: list[str] = []
    status = _report_status(rows)
    if status == "block":
        reason_codes.append("research_domain_budget_block_present")
    elif status == "watch":
        reason_codes.append("research_domain_budget_watch_present")
    else:
        reason_codes.append("research_domain_budget_clear")
    if _row_reason_count(rows, ("research_domain_information_block", "research_domain_information_watch")) > ZERO:
        reason_codes.append("research_domain_information_risk_present")
    if _row_reason_count(rows, ("research_domain_resource_block", "research_domain_resource_watch")) > ZERO:
        reason_codes.append("research_domain_resource_gap_present")
    if _row_reason_count(rows, ("research_domain_review_block", "research_domain_review_watch")) > ZERO:
        reason_codes.append("research_domain_review_capacity_gap_present")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchDomainRiskBudgetRow, ...],
) -> tuple[ResearchDomainRiskBudgetReasonCodeCount, ...]:
    domain_count = _count_decimal(len(rows))
    if reason_codes == ("research_domain_risk_budget_empty",):
        return (
            ResearchDomainRiskBudgetReasonCodeCount(
                reason_code="research_domain_risk_budget_empty",
                count=ONE,
                domain_ratio=ZERO,
            ),
        )
    return tuple(
        ResearchDomainRiskBudgetReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            domain_ratio=_coverage(_report_reason_count(reason_code, rows), domain_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[ResearchDomainRiskBudgetRow, ...],
) -> Decimal:
    if reason_code == "research_domain_budget_block_present":
        return _status_count(rows, "block")
    if reason_code == "research_domain_budget_watch_present":
        return _status_count(rows, "watch")
    if reason_code == "research_domain_budget_clear":
        return _status_count(rows, "pass")
    if reason_code == "research_domain_information_risk_present":
        return _row_reason_count(
            rows,
            ("research_domain_information_block", "research_domain_information_watch"),
        )
    if reason_code == "research_domain_resource_gap_present":
        return _row_reason_count(
            rows,
            ("research_domain_resource_block", "research_domain_resource_watch"),
        )
    if reason_code == "research_domain_review_capacity_gap_present":
        return _row_reason_count(
            rows,
            ("research_domain_review_block", "research_domain_review_watch"),
        )
    if reason_code == "research_domain_risk_budget_empty":
        return ONE
    raise ValueError("reason_code must be supported")


def _report_status(rows: tuple[ResearchDomainRiskBudgetRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.domain_status == "block" for row in rows):
        return "block"
    if any(row.domain_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _review_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_domain_research_budget_review"
    if status == "watch":
        return "monitor_report_only_domain_research_budget_review"
    return "hold_report_only_domain_research_budget_review"


def _domain_risk_score(
    *,
    research_resource_coverage: Decimal,
    review_capacity_coverage: Decimal,
    information_risk_score: Decimal,
) -> Decimal:
    return max(
        _gap(research_resource_coverage),
        _gap(review_capacity_coverage),
        information_risk_score,
    )


def _validate_row(row: ResearchDomainRiskBudgetRow) -> None:
    if row.research_resource_coverage != _coverage(
        row.allocated_research_units,
        row.required_research_units,
    ):
        raise ValueError("row research_resource_coverage must match units")
    if row.review_capacity_coverage != _coverage(
        row.available_review_units,
        row.required_review_units,
    ):
        raise ValueError("row review_capacity_coverage must match units")
    if row.domain_risk_score != _domain_risk_score(
        research_resource_coverage=row.research_resource_coverage,
        review_capacity_coverage=row.review_capacity_coverage,
        information_risk_score=row.information_risk_score,
    ):
        raise ValueError("row domain_risk_score must match coverage and information risk")
    if row.domain_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must match domain_status")
    if row.domain_status == "pass" and row.reason_codes != (
        "research_domain_budget_clear",
    ):
        raise ValueError("reason_codes must match domain_status")
    if row.domain_status != "pass" and "research_domain_budget_clear" in row.reason_codes:
        raise ValueError("reason_codes must match domain_status")


def _validate_report(report: ResearchDomainRiskBudgetReport) -> None:
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must be sorted by domain")
    if report.input_count != _count_decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.domain_count != _count_decimal(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.domain_count:
        raise ValueError("status counts must match rows")
    if report.average_research_resource_coverage != _average_decimal(
        row.research_resource_coverage for row in report.rows
    ):
        raise ValueError("average_research_resource_coverage must match rows")
    if report.average_review_capacity_coverage != _average_decimal(
        row.review_capacity_coverage for row in report.rows
    ):
        raise ValueError("average_review_capacity_coverage must match rows")
    if report.max_information_risk_score != max(
        (row.information_risk_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_information_risk_score must match rows")
    if report.overall_risk_score != max(
        (row.domain_risk_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("overall_risk_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.review_step != _review_step(report.report_status):
        raise ValueError("review_step must match report_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_signals(
    signals: Iterable[ResearchDomainRiskBudgetSignal],
) -> tuple[ResearchDomainRiskBudgetSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must contain ResearchDomainRiskBudgetSignal")
    normalized = tuple(signals)
    seen_domains: set[str] = set()
    for signal in normalized:
        if type(signal) is not ResearchDomainRiskBudgetSignal:
            raise ValueError("signals must contain ResearchDomainRiskBudgetSignal")
        _require_hard_flags("signal", signal)
        if signal.domain in seen_domains:
            raise ValueError("signals must not contain duplicate domain values")
        seen_domains.add(signal.domain)
    return tuple(sorted(normalized, key=_signal_sort_key))


def _normalize_rows(
    rows: Iterable[ResearchDomainRiskBudgetRow],
) -> tuple[ResearchDomainRiskBudgetRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain ResearchDomainRiskBudgetRow")
    normalized = tuple(rows)
    seen_domains: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchDomainRiskBudgetRow:
            raise ValueError("rows must contain ResearchDomainRiskBudgetRow")
        _require_hard_flags("row", row)
        if row.domain in seen_domains:
            raise ValueError("rows must not contain duplicate domain values")
        seen_domains.add(row.domain)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[ResearchDomainRiskBudgetReasonCodeCount],
) -> tuple[ResearchDomainRiskBudgetReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not ResearchDomainRiskBudgetReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        _require_hard_flags("reason code count", value)
    return tuple(sorted(normalized, key=lambda item: REPORT_REASON_CODES.index(item.reason_code)))


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        _require_member(field_name, value, allowed_values)
        if value in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(value)
    return tuple(reason_code for reason_code in allowed_values if reason_code in seen)


def _normalize_upstream_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("upstream_reason_codes must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("upstream_reason_codes", value)
        if value in seen:
            raise ValueError("upstream_reason_codes must be unique")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _signal_sort_key(signal: ResearchDomainRiskBudgetSignal) -> tuple[int, str]:
    return (DOMAIN_SEQUENCE.index(signal.domain), signal.domain)


def _row_sort_key(row: ResearchDomainRiskBudgetRow) -> tuple[int, str]:
    return (DOMAIN_SEQUENCE.index(row.domain), row.domain)


def _status_count(rows: tuple[ResearchDomainRiskBudgetRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(ONE for row in rows if row.domain_status == status))


def _row_reason_count(
    rows: tuple[ResearchDomainRiskBudgetRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            ONE
            for row in rows
            if any(reason_code in row.reason_codes for reason_code in reason_codes)
        ),
    )


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _ratio(_sum_decimal(normalized), _count_decimal(len(normalized)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += _require_decimal("value", value)
    return _quantize_decimal(total)


def _coverage(value: Decimal, required_value: Decimal) -> Decimal:
    if required_value <= ZERO:
        raise ValueError("required value must be positive")
    with localcontext(DECIMAL_CONTEXT):
        ratio = value / required_value
    if ratio > ONE:
        return ONE
    return _quantize_decimal(ratio)


def _ratio(value: Decimal, required_value: Decimal) -> Decimal:
    if required_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(value / required_value)


def _gap(value: Decimal) -> Decimal:
    return _quantize_decimal(ONE - value)


def _count_decimal(value: object) -> Decimal:
    if type(value) is Decimal:
        return _require_nonnegative_decimal("count", value)
    if type(value) is not int:
        raise ValueError("count must be an integer or Decimal")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


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


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_domain(field_name: str, value: object) -> str:
    if type(value) is not str or value not in DOMAIN_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical string")
    if not _CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload decimal must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    raise ValueError("payload value must be JSON ready")
