"""Pure public domain catalyst monitoring backlog reducer."""

from __future__ import annotations

import json
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_DOMAIN_CATALYST_MONITORING_BACKLOG_CONFIG_VERSION = (
    "research-domain-catalyst-monitoring-backlog-v0"
)

DOMAIN_SEQUENCE = (
    "politics",
    "crypto",
    "equities",
    "gold",
    "soccer",
    "basketball",
)

STATUS_VALUES = ("pass", "watch", "block")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "research_domain_catalyst_monitoring_backlog_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
MISSING_DOMAIN_COVERAGE_REASON = f"{REASON_PREFIX}missing_domain_coverage"
IMPACT_BLOCK_REASON = f"{REASON_PREFIX}impact_block"
LOW_FRESHNESS_REASON = f"{REASON_PREFIX}low_freshness"
STALE_METRIC_REASON = f"{REASON_PREFIX}stale_metric"
LOW_COVERAGE_REASON = f"{REASON_PREFIX}low_coverage"
IMPACT_WATCH_REASON = f"{REASON_PREFIX}impact_watch"
PASS_REASON = f"{REASON_PREFIX}pass"

ROW_REASON_CODE_SEQUENCE = (
    IMPACT_BLOCK_REASON,
    LOW_FRESHNESS_REASON,
    STALE_METRIC_REASON,
    LOW_COVERAGE_REASON,
    IMPACT_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    MISSING_DOMAIN_COVERAGE_REASON,
    IMPACT_BLOCK_REASON,
    IMPACT_WATCH_REASON,
    LOW_FRESHNESS_REASON,
    STALE_METRIC_REASON,
    LOW_COVERAGE_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_domain_catalyst_backlog",
    STATUS_WATCH: "watch_report_only_domain_catalyst_backlog",
    STATUS_BLOCK: "block_report_only_domain_catalyst_backlog",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class ResearchDomainCatalystMonitoringBacklogConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_CATALYST_MONITORING_BACKLOG_CONFIG_VERSION
    )
    fresh_metric_max_age_seconds: Decimal = Decimal("86400.000000")
    min_freshness_score: Decimal = Decimal("0.700000")
    min_coverage_score: Decimal = Decimal("0.600000")
    min_public_evidence_count: Decimal = Decimal("2")
    impact_watch_threshold: Decimal = Decimal("0.650000")
    impact_block_threshold: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainCatalystMonitoringBacklogConfig:
            raise TypeError(
                "ResearchDomainCatalystMonitoringBacklogConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCatalystMonitoringBacklogConfig:
            raise ValueError(
                "config must be exactly ResearchDomainCatalystMonitoringBacklogConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_metric_max_age_seconds",
            _require_nonnegative_decimal(
                "fresh_metric_max_age_seconds",
                self.fresh_metric_max_age_seconds,
            ),
        )
        for field_name in (
            "min_freshness_score",
            "min_coverage_score",
            "impact_watch_threshold",
            "impact_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_public_evidence_count",
            _require_nonnegative_count_decimal(
                "min_public_evidence_count",
                self.min_public_evidence_count,
            ),
        )
        if self.impact_watch_threshold > self.impact_block_threshold:
            raise ValueError(
                "impact_block_threshold must be at least impact_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainCatalystMonitoringBacklogInputRow:
    domain: str
    catalyst_theme: str
    metrics_updated_at: datetime
    freshness_score: Decimal
    impact_score: Decimal
    coverage_score: Decimal
    public_evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainCatalystMonitoringBacklogInputRow:
            raise TypeError(
                "ResearchDomainCatalystMonitoringBacklogInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCatalystMonitoringBacklogInputRow:
            raise ValueError(
                "input row must be exactly "
                "ResearchDomainCatalystMonitoringBacklogInputRow",
            )
        _require_domain("domain", self.domain)
        _require_public_string("catalyst_theme", self.catalyst_theme)
        object.__setattr__(
            self,
            "metrics_updated_at",
            _as_utc("metrics_updated_at", self.metrics_updated_at),
        )
        for field_name in ("freshness_score", "impact_score", "coverage_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_evidence_count",
            _require_nonnegative_count_decimal(
                "public_evidence_count",
                self.public_evidence_count,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchDomainCatalystMonitoringBacklogRow:
    domain: str
    catalyst_theme: str
    generated_at: datetime
    metrics_updated_at: datetime
    metric_age_seconds: Decimal
    freshness_score: Decimal
    impact_score: Decimal
    coverage_score: Decimal
    public_evidence_count: Decimal
    catalyst_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchDomainCatalystMonitoringBacklogConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainCatalystMonitoringBacklogRow:
            raise TypeError(
                "ResearchDomainCatalystMonitoringBacklogRow does not support "
                "subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchDomainCatalystMonitoringBacklogConfig | None,
    ) -> None:
        if type(self) is not ResearchDomainCatalystMonitoringBacklogRow:
            raise ValueError(
                "row must be exactly ResearchDomainCatalystMonitoringBacklogRow",
            )
        _require_domain("domain", self.domain)
        _require_public_string("catalyst_theme", self.catalyst_theme)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "metrics_updated_at",
            _as_utc("metrics_updated_at", self.metrics_updated_at),
        )
        object.__setattr__(
            self,
            "metric_age_seconds",
            _require_nonnegative_decimal(
                "metric_age_seconds",
                self.metric_age_seconds,
            ),
        )
        for field_name in ("freshness_score", "impact_score", "coverage_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_evidence_count",
            _require_nonnegative_count_decimal(
                "public_evidence_count",
                self.public_evidence_count,
            ),
        )
        _require_status("catalyst_status", self.catalyst_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainCatalystMonitoringBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    catalyst_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainCatalystMonitoringBacklogReasonCodeCount:
            raise TypeError(
                "ResearchDomainCatalystMonitoringBacklogReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCatalystMonitoringBacklogReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDomainCatalystMonitoringBacklogReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "catalyst_ratio",
            _require_ratio_decimal("catalyst_ratio", self.catalyst_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchDomainCatalystMonitoringBacklogReport:
    generated_at: datetime
    config_version: str
    backlog_status: str
    next_step: str
    catalyst_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_domain_count: Decimal
    high_impact_count: Decimal
    low_coverage_count: Decimal
    low_freshness_count: Decimal
    stale_metric_count: Decimal
    average_freshness_score: Decimal
    average_impact_score: Decimal
    average_coverage_score: Decimal
    average_public_evidence_count: Decimal
    max_metric_age_seconds: Decimal
    missing_domains: tuple[str, ...]
    rows: tuple[ResearchDomainCatalystMonitoringBacklogRow, ...]
    reason_code_counts: tuple[
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainCatalystMonitoringBacklogReport:
            raise TypeError(
                "ResearchDomainCatalystMonitoringBacklogReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCatalystMonitoringBacklogReport:
            raise ValueError(
                "report must be exactly ResearchDomainCatalystMonitoringBacklogReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("backlog_status", self.backlog_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "catalyst_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_domain_count",
            "high_impact_count",
            "low_coverage_count",
            "low_freshness_count",
            "stale_metric_count",
            "average_freshness_score",
            "average_impact_score",
            "average_coverage_score",
            "average_public_evidence_count",
            "max_metric_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_domains",
            _normalize_domains("missing_domains", self.missing_domains),
        )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchDomainCatalystMonitoringBacklogRow:
                raise ValueError(
                    "rows must contain ResearchDomainCatalystMonitoringBacklogRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchDomainCatalystMonitoringBacklogReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchDomainCatalystMonitoringBacklogReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_domain_catalyst_monitoring_backlog(
    input_rows: list[ResearchDomainCatalystMonitoringBacklogInputRow]
    | tuple[ResearchDomainCatalystMonitoringBacklogInputRow, ...],
    *,
    config: ResearchDomainCatalystMonitoringBacklogConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainCatalystMonitoringBacklogReport:
    cfg = config or ResearchDomainCatalystMonitoringBacklogConfig()
    if type(cfg) is not ResearchDomainCatalystMonitoringBacklogConfig:
        raise ValueError(
            "config must be a ResearchDomainCatalystMonitoringBacklogConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    catalyst_count = _count(len(ranked_rows))
    missing_domains = _missing_domains(ranked_rows)
    reason_code_counts = _reason_code_counts(ranked_rows)
    if not ranked_rows:
        reason_code_counts = (
            ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                catalyst_ratio=ONE,
            ),
        )
    pass_count = _status_count(ranked_rows, STATUS_PASS)
    watch_count = _status_count(ranked_rows, STATUS_WATCH)
    block_count = _status_count(ranked_rows, STATUS_BLOCK)
    backlog_status = _report_status(
        has_inputs=bool(ranked_rows),
        missing_domains=missing_domains,
        block_count=block_count,
        watch_count=watch_count,
    )
    return ResearchDomainCatalystMonitoringBacklogReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        backlog_status=backlog_status,
        next_step=NEXT_STEPS[backlog_status],
        catalyst_count=catalyst_count,
        domain_count=_count(len({row.domain for row in ranked_rows})),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        missing_domain_count=_count(len(missing_domains)),
        high_impact_count=_reason_count(ranked_rows, IMPACT_BLOCK_REASON)
        + _reason_count(ranked_rows, IMPACT_WATCH_REASON),
        low_coverage_count=_reason_count(ranked_rows, LOW_COVERAGE_REASON),
        low_freshness_count=_reason_count(ranked_rows, LOW_FRESHNESS_REASON),
        stale_metric_count=_reason_count(ranked_rows, STALE_METRIC_REASON),
        average_freshness_score=_ratio(
            _sum_decimal(row.freshness_score for row in ranked_rows),
            catalyst_count,
        ),
        average_impact_score=_ratio(
            _sum_decimal(row.impact_score for row in ranked_rows),
            catalyst_count,
        ),
        average_coverage_score=_ratio(
            _sum_decimal(row.coverage_score for row in ranked_rows),
            catalyst_count,
        ),
        average_public_evidence_count=_ratio(
            _sum_decimal(row.public_evidence_count for row in ranked_rows),
            catalyst_count,
        ),
        max_metric_age_seconds=max(
            (row.metric_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        missing_domains=missing_domains,
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_report_reason_codes(reason_code_counts, missing_domains),
    )


def research_domain_catalyst_monitoring_backlog_payload(
    report: ResearchDomainCatalystMonitoringBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDomainCatalystMonitoringBacklogReport:
        raise ValueError(
            "report must be a ResearchDomainCatalystMonitoringBacklogReport",
        )
    _require_hard_flags("report", report)
    _reject_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_flags("payload", payload)
    _reject_public_payload("payload", payload)
    return payload


def research_domain_catalyst_monitoring_backlog_digest(
    report: ResearchDomainCatalystMonitoringBacklogReport,
) -> str:
    payload = research_domain_catalyst_monitoring_backlog_payload(report)
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _build_row(
    row: ResearchDomainCatalystMonitoringBacklogInputRow,
    *,
    config: ResearchDomainCatalystMonitoringBacklogConfig,
    generated_at: datetime,
) -> ResearchDomainCatalystMonitoringBacklogRow:
    metric_age_seconds = _datetime_delta_seconds(generated_at, row.metrics_updated_at)
    reason_codes = _row_reason_codes(
        metric_age_seconds=metric_age_seconds,
        freshness_score=row.freshness_score,
        impact_score=row.impact_score,
        coverage_score=row.coverage_score,
        public_evidence_count=row.public_evidence_count,
        config=config,
    )
    catalyst_status = _row_status(reason_codes)
    return ResearchDomainCatalystMonitoringBacklogRow(
        domain=row.domain,
        catalyst_theme=row.catalyst_theme,
        generated_at=generated_at,
        metrics_updated_at=row.metrics_updated_at,
        metric_age_seconds=metric_age_seconds,
        freshness_score=row.freshness_score,
        impact_score=row.impact_score,
        coverage_score=row.coverage_score,
        public_evidence_count=row.public_evidence_count,
        catalyst_status=catalyst_status,
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchDomainCatalystMonitoringBacklogInputRow]
    | tuple[ResearchDomainCatalystMonitoringBacklogInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchDomainCatalystMonitoringBacklogInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchDomainCatalystMonitoringBacklogInputRow:
            raise ValueError(
                "input rows must contain ResearchDomainCatalystMonitoringBacklogInputRow",
            )
        _require_hard_flags("input row", row)
        if row.metrics_updated_at > generated_at:
            raise ValueError("metrics_updated_at must be on or before generated_at")
        key = (row.domain, row.catalyst_theme)
        if key in seen:
            raise ValueError("input rows must not repeat domain and catalyst_theme")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    metric_age_seconds: Decimal,
    freshness_score: Decimal,
    impact_score: Decimal,
    coverage_score: Decimal,
    public_evidence_count: Decimal,
    config: ResearchDomainCatalystMonitoringBacklogConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if impact_score >= config.impact_block_threshold:
        reason_codes.append(IMPACT_BLOCK_REASON)
    elif impact_score >= config.impact_watch_threshold:
        reason_codes.append(IMPACT_WATCH_REASON)
    if freshness_score < config.min_freshness_score:
        reason_codes.append(LOW_FRESHNESS_REASON)
    if metric_age_seconds > config.fresh_metric_max_age_seconds:
        reason_codes.append(STALE_METRIC_REASON)
    if (
        coverage_score < config.min_coverage_score
        or public_evidence_count < config.min_public_evidence_count
    ):
        reason_codes.append(LOW_COVERAGE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if IMPACT_BLOCK_REASON in reason_codes:
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    missing_domains: tuple[str, ...],
    block_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not has_inputs or missing_domains or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchDomainCatalystMonitoringBacklogRow, ...],
) -> tuple[ResearchDomainCatalystMonitoringBacklogRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.catalyst_status),
                -row.impact_score,
                _domain_rank(row.domain),
                row.catalyst_theme,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _domain_rank(value: str) -> int:
    return DOMAIN_SEQUENCE.index(value)


def _missing_domains(
    rows: tuple[ResearchDomainCatalystMonitoringBacklogRow, ...],
) -> tuple[str, ...]:
    observed = {row.domain for row in rows}
    return tuple(domain for domain in DOMAIN_SEQUENCE if domain not in observed)


def _reason_code_counts(
    rows: tuple[ResearchDomainCatalystMonitoringBacklogRow, ...],
) -> tuple[ResearchDomainCatalystMonitoringBacklogReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
            reason_code=reason_code,
            count=_quantize(counts[reason_code]),
            catalyst_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _report_reason_codes(
    reason_code_counts: tuple[
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount,
        ...,
    ],
    missing_domains: tuple[str, ...],
) -> tuple[str, ...]:
    raw_codes = [row.reason_code for row in reason_code_counts]
    if missing_domains:
        raw_codes.append(MISSING_DOMAIN_COVERAGE_REASON)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in raw_codes
    )


def _validate_row(
    row: ResearchDomainCatalystMonitoringBacklogRow,
    *,
    config: ResearchDomainCatalystMonitoringBacklogConfig | None,
) -> None:
    if config is None:
        config = ResearchDomainCatalystMonitoringBacklogConfig()
    if type(config) is not ResearchDomainCatalystMonitoringBacklogConfig:
        raise ValueError(
            "validation_config must be a ResearchDomainCatalystMonitoringBacklogConfig",
        )
    expected_age = _datetime_delta_seconds(row.generated_at, row.metrics_updated_at)
    if row.metric_age_seconds != expected_age:
        raise ValueError("metric_age_seconds must match timestamps")
    expected_reason_codes = _row_reason_codes(
        metric_age_seconds=row.metric_age_seconds,
        freshness_score=row.freshness_score,
        impact_score=row.impact_score,
        coverage_score=row.coverage_score,
        public_evidence_count=row.public_evidence_count,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.catalyst_status != _row_status(row.reason_codes):
        raise ValueError("catalyst_status must match reason_codes")


def _validate_report(report: ResearchDomainCatalystMonitoringBacklogReport) -> None:
    if report.next_step != NEXT_STEPS[report.backlog_status]:
        raise ValueError("next_step must match backlog_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.catalyst_count != _count(len(report.rows)):
        raise ValueError("catalyst_count must match rows")
    if report.domain_count != _count(len({row.domain for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    expected_missing_domains = _missing_domains(report.rows)
    if report.missing_domains != expected_missing_domains:
        raise ValueError("missing_domains must match rows")
    if report.missing_domain_count != _count(len(expected_missing_domains)):
        raise ValueError("missing_domain_count must match rows")
    expected_high_impact = _reason_count(report.rows, IMPACT_BLOCK_REASON) + _reason_count(
        report.rows,
        IMPACT_WATCH_REASON,
    )
    if report.high_impact_count != expected_high_impact:
        raise ValueError("high_impact_count must match rows")
    if report.low_coverage_count != _reason_count(report.rows, LOW_COVERAGE_REASON):
        raise ValueError("low_coverage_count must match rows")
    if report.low_freshness_count != _reason_count(report.rows, LOW_FRESHNESS_REASON):
        raise ValueError("low_freshness_count must match rows")
    if report.stale_metric_count != _reason_count(report.rows, STALE_METRIC_REASON):
        raise ValueError("stale_metric_count must match rows")
    if report.average_freshness_score != _ratio(
        _sum_decimal(row.freshness_score for row in report.rows),
        report.catalyst_count,
    ):
        raise ValueError("average_freshness_score must match rows")
    if report.average_impact_score != _ratio(
        _sum_decimal(row.impact_score for row in report.rows),
        report.catalyst_count,
    ):
        raise ValueError("average_impact_score must match rows")
    if report.average_coverage_score != _ratio(
        _sum_decimal(row.coverage_score for row in report.rows),
        report.catalyst_count,
    ):
        raise ValueError("average_coverage_score must match rows")
    if report.average_public_evidence_count != _ratio(
        _sum_decimal(row.public_evidence_count for row in report.rows),
        report.catalyst_count,
    ):
        raise ValueError("average_public_evidence_count must match rows")
    expected_max_age = max(
        (row.metric_age_seconds for row in report.rows),
        default=ZERO,
    )
    if report.max_metric_age_seconds != expected_max_age:
        raise ValueError("max_metric_age_seconds must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                catalyst_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_codes = _report_reason_codes(expected_counts, expected_missing_domains)
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        missing_domains=report.missing_domains,
        block_count=report.block_count,
        watch_count=report.watch_count,
    )
    if report.backlog_status != expected_status:
        raise ValueError("backlog_status must match rows")


def _status_count(
    rows: tuple[ResearchDomainCatalystMonitoringBacklogRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.catalyst_status == status))


def _reason_count(
    rows: tuple[ResearchDomainCatalystMonitoringBacklogRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_domains(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for domain in value:
        _require_domain(field_name, domain)
    normalized = tuple(domain for domain in DOMAIN_SEQUENCE if domain in value)
    if normalized != value:
        raise ValueError(f"{field_name} must be unique and sorted")
    return normalized


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
        raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REPORT_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REPORT_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_domain(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported domain")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_public_text(field_name, value)
    return value


def _reject_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in _blocked_text_fragments():
        if fragment in lowered:
            raise ValueError(f"{field_name} has unsafe text")


def _blocked_text_fragments() -> tuple[str, ...]:
    parts = (
        ("event", "_", "id"),
        ("event", "-", "id"),
        ("event", " ", "id"),
        ("market", "_", "id"),
        ("market", "-", "id"),
        ("market", " ", "id"),
        ("source", "_", "id"),
        ("source", "-", "id"),
        ("source", " ", "id"),
        ("wal", "let"),
        ("au", "th"),
        ("or", "der"),
        ("tra", "de"),
        ("pri", "vate", "-", "key"),
        ("pri", "vate", "_", "key"),
        ("live", " ", "execution"),
        ("b", "uy"),
        ("s", "ell"),
        ("re", "commend"),
        ("ad", "vice"),
        ("api", "_", "key"),
        ("api", "-", "key"),
        ("sec", "ret"),
        ("pos", "ition"),
        ("sta", "ke"),
        ("cli", "ent"),
        ("data", "base"),
        ("net", "work"),
        ("ht", "tp"),
        ("sock", "et"),
        ("sub", "process"),
    )
    return tuple("".join(part) for part in parts)


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in HARD_FLAG_NAMES:
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_payload_flags(label: str, value: dict[str, Any]) -> None:
    for flag_name in HARD_FLAG_NAMES:
        if value.get(flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("metrics_updated_at must be on or before generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(whole_seconds + fractional_seconds)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("aggregate values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _reject_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_public_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            lowered_key = key.lower()
            for fragment in _blocked_text_fragments():
                if fragment in lowered_key:
                    raise ValueError(f"unsafe surface field in {label}: {key}")
            if key in HARD_FLAG_NAMES and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")
