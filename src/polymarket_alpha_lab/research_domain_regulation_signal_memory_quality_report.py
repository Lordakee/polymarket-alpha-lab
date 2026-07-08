"""Pure regulation signal memory quality report for forecast handoff."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_REGULATION_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION",
    "ResearchDomainRegulationSignalMemoryQualityConfig",
    "ResearchDomainRegulationSignalMemoryQualityInputRow",
    "ResearchDomainRegulationSignalMemoryQualityReasonCodeCount",
    "ResearchDomainRegulationSignalMemoryQualityReport",
    "ResearchDomainRegulationSignalMemoryQualityReportRow",
    "build_research_domain_regulation_signal_memory_quality_report",
    "research_domain_regulation_signal_memory_quality_report_digest",
    "research_domain_regulation_signal_memory_quality_report_payload",
)


DEFAULT_RESEARCH_DOMAIN_REGULATION_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION = (
    "research-domain-regulation-signal-memory-quality-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}
HANDOFF_GATE_LABELS = {
    STATUS_PASS: "pass_report_only_regulation_signal_memory_forecast_handoff",
    STATUS_WATCH: "watch_report_only_regulation_signal_memory_forecast_handoff",
    STATUS_BLOCK: "block_report_only_regulation_signal_memory_forecast_handoff",
}

SIGNAL_NAMES = ("agency", "court", "rulemaking", "enforcement", "effective_date")
NO_INPUTS_REASON = "regulation_memory_quality_no_inputs"
FRESH_REASON = "regulation_memory_quality_fresh"
NO_CONFLICT_REASON = "regulation_memory_quality_no_conflict"
PASS_REASON = "regulation_memory_quality_pass"
WATCH_REASON = "regulation_memory_quality_watch"
MEMORY_SCORE_BLOCK_REASON = "regulation_memory_quality_memory_score_block"
MEMORY_SCORE_WATCH_REASON = "regulation_memory_quality_memory_score_watch"
CONFLICT_BLOCK_REASON = "regulation_memory_quality_conflict_block"
CONFLICT_WATCH_REASON = "regulation_memory_quality_conflict_watch"
REASON_CODES = tuple(
    sorted(
        (
            NO_INPUTS_REASON,
            FRESH_REASON,
            NO_CONFLICT_REASON,
            PASS_REASON,
            WATCH_REASON,
            MEMORY_SCORE_BLOCK_REASON,
            MEMORY_SCORE_WATCH_REASON,
            CONFLICT_BLOCK_REASON,
            CONFLICT_WATCH_REASON,
            *(
                f"regulation_memory_quality_{signal_name}_{condition}"
                for signal_name in SIGNAL_NAMES
                for condition in ("missing", "stale", "conflicting")
            ),
        ),
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIGNAL_COUNT = Decimal("5.000000")
HEX_CHARS = frozenset("0123456789abcdef")
SAFE_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "can" + "didate",
        "mar" + "ket",
        "slu" + "g",
        "ques" + "tion",
        "ur" + "l",
        "sou" + "rce",
        "ds" + "n",
        "tab" + "le",
        "tok" + "en",
        "wa" + "llet",
        "ord" + "er",
        "tra" + "de",
        "data" + "base",
        "net" + "work",
        "au" + "th",
        "li" + "ve",
        "si" + "ze",
        "siz" + "ing",
        "recom" + "mend",
        "recom" + "mendation",
        "pos" + "ition",
        "b" + "uy",
        "se" + "ll",
        "http",
        "www.",
        "raw",
        "quote",
        "excerpt",
        "transcript",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchDomainRegulationSignalMemoryQualityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_REGULATION_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION
    )
    fresh_agency_max_age_seconds: Decimal = Decimal("7200.000000")
    fresh_court_max_age_seconds: Decimal = Decimal("21600.000000")
    fresh_rulemaking_max_age_seconds: Decimal = Decimal("43200.000000")
    fresh_enforcement_max_age_seconds: Decimal = Decimal("43200.000000")
    fresh_effective_date_max_age_seconds: Decimal = Decimal("86400.000000")
    pass_memory_score: Decimal = Decimal("0.800000")
    watch_memory_score: Decimal = Decimal("0.550000")
    block_conflict_count: Decimal = Decimal("2.000000")
    watch_conflict_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainRegulationSignalMemoryQualityConfig,
            "config",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "fresh_agency_max_age_seconds",
            "fresh_court_max_age_seconds",
            "fresh_rulemaking_max_age_seconds",
            "fresh_enforcement_max_age_seconds",
            "fresh_effective_date_max_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_memory_score", "watch_memory_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("block_conflict_count", "watch_conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainRegulationSignalMemoryQualityInputRow(_FinalPublicDataclass):
    jurisdiction_label: str
    regulatory_area: str
    memory_scope: str
    agency_memorized_at: datetime | None
    court_memorized_at: datetime | None
    rulemaking_memorized_at: datetime | None
    enforcement_memorized_at: datetime | None
    effective_date_memorized_at: datetime | None
    agency_memory_score: Decimal
    court_memory_score: Decimal
    rulemaking_memory_score: Decimal
    enforcement_memory_score: Decimal
    effective_date_memory_score: Decimal
    agency_conflict_count: Decimal
    court_conflict_count: Decimal
    rulemaking_conflict_count: Decimal
    enforcement_conflict_count: Decimal
    effective_date_conflict_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainRegulationSignalMemoryQualityInputRow,
            "input row",
        )
        for field_name in ("jurisdiction_label", "regulatory_area", "memory_scope"):
            object.__setattr__(
                self,
                field_name,
                _require_safe_label(field_name, getattr(self, field_name)),
            )
        for field_name in _memorized_at_field_names():
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in _memory_score_field_names():
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in _conflict_count_field_names():
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchDomainRegulationSignalMemoryQualityReportRow(_FinalPublicDataclass):
    jurisdiction_label: str
    regulatory_area: str
    memory_scope: str
    public_status: str
    freshness_status: str
    conflict_status: str
    agency_memorized_at: datetime | None
    court_memorized_at: datetime | None
    rulemaking_memorized_at: datetime | None
    enforcement_memorized_at: datetime | None
    effective_date_memorized_at: datetime | None
    agency_age_seconds: Decimal | None
    court_age_seconds: Decimal | None
    rulemaking_age_seconds: Decimal | None
    enforcement_age_seconds: Decimal | None
    effective_date_age_seconds: Decimal | None
    agency_memory_score: Decimal
    court_memory_score: Decimal
    rulemaking_memory_score: Decimal
    enforcement_memory_score: Decimal
    effective_date_memory_score: Decimal
    agency_conflict_count: Decimal
    court_conflict_count: Decimal
    rulemaking_conflict_count: Decimal
    enforcement_conflict_count: Decimal
    effective_date_conflict_count: Decimal
    composite_memory_score: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainRegulationSignalMemoryQualityReportRow,
            "row",
        )
        for field_name in ("jurisdiction_label", "regulatory_area", "memory_scope"):
            object.__setattr__(
                self,
                field_name,
                _require_safe_label(field_name, getattr(self, field_name)),
            )
        for field_name in ("public_status", "freshness_status", "conflict_status"):
            _require_status(field_name, getattr(self, field_name))
        for field_name in _memorized_at_field_names():
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in _age_seconds_field_names():
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            *_memory_score_field_names(),
            "composite_memory_score",
            "freshness_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in _conflict_count_field_names():
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainRegulationSignalMemoryQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    memory_set_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainRegulationSignalMemoryQualityReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "memory_set_ratio",
            _require_ratio_decimal("memory_set_ratio", self.memory_set_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchDomainRegulationSignalMemoryQualityReport(_FinalPublicDataclass):
    generated_at: datetime
    handoff_at: datetime
    config_version: str
    report_status: str
    handoff_gate_label: str
    memory_set_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_set_count: Decimal
    conflicting_memory_set_count: Decimal
    missing_memory_set_count: Decimal
    average_memory_score: Decimal
    average_freshness_score: Decimal
    average_conflict_score: Decimal
    agency_missing_count: Decimal
    court_missing_count: Decimal
    rulemaking_missing_count: Decimal
    enforcement_missing_count: Decimal
    effective_date_missing_count: Decimal
    agency_stale_count: Decimal
    court_stale_count: Decimal
    rulemaking_stale_count: Decimal
    enforcement_stale_count: Decimal
    effective_date_stale_count: Decimal
    agency_conflicting_count: Decimal
    court_conflicting_count: Decimal
    rulemaking_conflicting_count: Decimal
    enforcement_conflicting_count: Decimal
    effective_date_conflicting_count: Decimal
    max_agency_age_seconds: Decimal
    max_court_age_seconds: Decimal
    max_rulemaking_age_seconds: Decimal
    max_enforcement_age_seconds: Decimal
    max_effective_date_age_seconds: Decimal
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...]
    reason_code_counts: tuple[
        ResearchDomainRegulationSignalMemoryQualityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainRegulationSignalMemoryQualityReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "handoff_at", _as_utc("handoff_at", self.handoff_at))
        if self.handoff_at > self.generated_at:
            raise ValueError("handoff_at must not be after generated_at")
        _require_config_version(self.config_version)
        _require_status("report_status", self.report_status)
        if self.handoff_gate_label != HANDOFF_GATE_LABELS[self.report_status]:
            raise ValueError("handoff_gate_label must match report_status")
        for field_name in _report_count_field_names():
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_score",
            "average_freshness_score",
            "average_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        digest = _report_digest_from_payload(self, include_digest=False)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", digest)
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match report payload")
        _validate_report(self)
        _reject_unsafe_public_payload(_payload_value(self, include_digest=True))

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_regulation_signal_memory_quality_report_payload(self)


def build_research_domain_regulation_signal_memory_quality_report(
    rows: Any,
    *,
    config: ResearchDomainRegulationSignalMemoryQualityConfig,
    generated_at: datetime,
    handoff_at: datetime,
) -> ResearchDomainRegulationSignalMemoryQualityReport:
    if type(config) is not ResearchDomainRegulationSignalMemoryQualityConfig:
        raise ValueError(
            "config must be exactly ResearchDomainRegulationSignalMemoryQualityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    handoff_at_utc = _as_utc("handoff_at", handoff_at)
    if handoff_at_utc > generated_at_utc:
        raise ValueError("generated_at must not be before handoff_at")
    input_rows = _normalize_input_rows(rows)
    if not input_rows:
        reason_counts = (
            ResearchDomainRegulationSignalMemoryQualityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                memory_set_ratio=ZERO,
            ),
        )
        return ResearchDomainRegulationSignalMemoryQualityReport(
            generated_at=generated_at_utc,
            handoff_at=handoff_at_utc,
            config_version=config.config_version,
            report_status=STATUS_BLOCK,
            handoff_gate_label=HANDOFF_GATE_LABELS[STATUS_BLOCK],
            memory_set_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            stale_memory_set_count=ZERO,
            conflicting_memory_set_count=ZERO,
            missing_memory_set_count=ZERO,
            average_memory_score=ZERO,
            average_freshness_score=ZERO,
            average_conflict_score=ZERO,
            agency_missing_count=ZERO,
            court_missing_count=ZERO,
            rulemaking_missing_count=ZERO,
            enforcement_missing_count=ZERO,
            effective_date_missing_count=ZERO,
            agency_stale_count=ZERO,
            court_stale_count=ZERO,
            rulemaking_stale_count=ZERO,
            enforcement_stale_count=ZERO,
            effective_date_stale_count=ZERO,
            agency_conflicting_count=ZERO,
            court_conflicting_count=ZERO,
            rulemaking_conflicting_count=ZERO,
            enforcement_conflicting_count=ZERO,
            effective_date_conflicting_count=ZERO,
            max_agency_age_seconds=ZERO,
            max_court_age_seconds=ZERO,
            max_rulemaking_age_seconds=ZERO,
            max_enforcement_age_seconds=ZERO,
            max_effective_date_age_seconds=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(
        sorted(
            (
                _report_row(row, config=config, handoff_at=handoff_at_utc)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_counts = _reason_code_counts(report_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    status = _summary_status(report_rows)
    return ResearchDomainRegulationSignalMemoryQualityReport(
        generated_at=generated_at_utc,
        handoff_at=handoff_at_utc,
        config_version=config.config_version,
        report_status=status,
        handoff_gate_label=HANDOFF_GATE_LABELS[status],
        memory_set_count=_count_decimal(len(report_rows)),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        stale_memory_set_count=_count_if(report_rows, _has_stale_signal),
        conflicting_memory_set_count=_count_if(report_rows, _has_conflicting_signal),
        missing_memory_set_count=_count_if(report_rows, _has_missing_signal),
        average_memory_score=_average(row.composite_memory_score for row in report_rows),
        average_freshness_score=_average(row.freshness_score for row in report_rows),
        average_conflict_score=_average(row.conflict_score for row in report_rows),
        agency_missing_count=_signal_missing_count(report_rows, "agency"),
        court_missing_count=_signal_missing_count(report_rows, "court"),
        rulemaking_missing_count=_signal_missing_count(report_rows, "rulemaking"),
        enforcement_missing_count=_signal_missing_count(report_rows, "enforcement"),
        effective_date_missing_count=_signal_missing_count(
            report_rows,
            "effective_date",
        ),
        agency_stale_count=_signal_stale_count(report_rows, "agency", config),
        court_stale_count=_signal_stale_count(report_rows, "court", config),
        rulemaking_stale_count=_signal_stale_count(report_rows, "rulemaking", config),
        enforcement_stale_count=_signal_stale_count(report_rows, "enforcement", config),
        effective_date_stale_count=_signal_stale_count(
            report_rows,
            "effective_date",
            config,
        ),
        agency_conflicting_count=_signal_conflicting_count(report_rows, "agency"),
        court_conflicting_count=_signal_conflicting_count(report_rows, "court"),
        rulemaking_conflicting_count=_signal_conflicting_count(report_rows, "rulemaking"),
        enforcement_conflicting_count=_signal_conflicting_count(
            report_rows,
            "enforcement",
        ),
        effective_date_conflicting_count=_signal_conflicting_count(
            report_rows,
            "effective_date",
        ),
        max_agency_age_seconds=_max_optional_age(
            row.agency_age_seconds for row in report_rows
        ),
        max_court_age_seconds=_max_optional_age(
            row.court_age_seconds for row in report_rows
        ),
        max_rulemaking_age_seconds=_max_optional_age(
            row.rulemaking_age_seconds for row in report_rows
        ),
        max_enforcement_age_seconds=_max_optional_age(
            row.enforcement_age_seconds for row in report_rows
        ),
        max_effective_date_age_seconds=_max_optional_age(
            row.effective_date_age_seconds for row in report_rows
        ),
        rows=report_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_domain_regulation_signal_memory_quality_report_payload(
    report: ResearchDomainRegulationSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainRegulationSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if report.derived_validation_digest != _report_digest_from_payload(
            report,
            include_digest=False,
        ):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _payload_value(report, include_digest=True)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload(payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload(report)
        _reject_public_numeric_values(report)
        payload = _payload_value(report, include_digest=True)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        if "derived_validation_digest" not in payload:
            raise ValueError("derived_validation_digest is required")
        supplied_digest = payload["derived_validation_digest"]
        _require_sha256_digest("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError(
        "report must be a ResearchDomainRegulationSignalMemoryQualityReport",
    )


def research_domain_regulation_signal_memory_quality_report_digest(
    report: ResearchDomainRegulationSignalMemoryQualityReport,
) -> str:
    if type(report) is not ResearchDomainRegulationSignalMemoryQualityReport:
        raise ValueError(
            "report must be exactly ResearchDomainRegulationSignalMemoryQualityReport",
        )
    _require_hard_flags("report", report)
    return _report_digest_from_payload(report, include_digest=False)


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_input_rows(
    rows: Any,
) -> tuple[ResearchDomainRegulationSignalMemoryQualityInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchDomainRegulationSignalMemoryQualityInputRow:
            raise ValueError(
                "rows must contain ResearchDomainRegulationSignalMemoryQualityInputRow",
            )
        _require_hard_flags("input row", row)
        key = (row.jurisdiction_label, row.regulatory_area, row.memory_scope)
        if key in seen:
            raise ValueError("rows must contain unique memory sets")
        seen.add(key)
    return normalized


def _report_row(
    row: ResearchDomainRegulationSignalMemoryQualityInputRow,
    *,
    config: ResearchDomainRegulationSignalMemoryQualityConfig,
    handoff_at: datetime,
) -> ResearchDomainRegulationSignalMemoryQualityReportRow:
    _reject_future_memorized_at(row, handoff_at)
    ages = _signal_ages(row, handoff_at)
    composite_memory_score = _average(_signal_scores(row))
    freshness_status = _freshness_status(ages, config)
    conflict_status = _conflict_status(row, config)
    public_status = _row_status(
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        composite_memory_score=composite_memory_score,
        config=config,
    )
    freshness_score = _freshness_score(ages, config)
    conflict_score = _conflict_score(conflict_status)
    reason_codes = _row_reason_codes(
        public_status=public_status,
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        composite_memory_score=composite_memory_score,
        ages=ages,
        row=row,
        config=config,
    )
    return ResearchDomainRegulationSignalMemoryQualityReportRow(
        jurisdiction_label=row.jurisdiction_label,
        regulatory_area=row.regulatory_area,
        memory_scope=row.memory_scope,
        public_status=public_status,
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        agency_memorized_at=row.agency_memorized_at,
        court_memorized_at=row.court_memorized_at,
        rulemaking_memorized_at=row.rulemaking_memorized_at,
        enforcement_memorized_at=row.enforcement_memorized_at,
        effective_date_memorized_at=row.effective_date_memorized_at,
        agency_age_seconds=ages["agency"],
        court_age_seconds=ages["court"],
        rulemaking_age_seconds=ages["rulemaking"],
        enforcement_age_seconds=ages["enforcement"],
        effective_date_age_seconds=ages["effective_date"],
        agency_memory_score=row.agency_memory_score,
        court_memory_score=row.court_memory_score,
        rulemaking_memory_score=row.rulemaking_memory_score,
        enforcement_memory_score=row.enforcement_memory_score,
        effective_date_memory_score=row.effective_date_memory_score,
        agency_conflict_count=row.agency_conflict_count,
        court_conflict_count=row.court_conflict_count,
        rulemaking_conflict_count=row.rulemaking_conflict_count,
        enforcement_conflict_count=row.enforcement_conflict_count,
        effective_date_conflict_count=row.effective_date_conflict_count,
        composite_memory_score=composite_memory_score,
        freshness_score=freshness_score,
        conflict_score=conflict_score,
        reason_codes=reason_codes,
    )


def _freshness_status(
    ages: dict[str, Decimal | None],
    config: ResearchDomainRegulationSignalMemoryQualityConfig,
) -> str:
    if any(value is None for value in ages.values()):
        return STATUS_BLOCK
    if any(_is_stale(signal_name, value, config) for signal_name, value in ages.items()):
        return STATUS_WATCH
    return STATUS_PASS


def _conflict_status(
    row: ResearchDomainRegulationSignalMemoryQualityInputRow,
    config: ResearchDomainRegulationSignalMemoryQualityConfig,
) -> str:
    counts = _signal_conflict_counts(row)
    if any(count >= config.block_conflict_count for count in counts):
        return STATUS_BLOCK
    if any(count >= config.watch_conflict_count for count in counts):
        return STATUS_WATCH
    return STATUS_PASS


def _row_status(
    *,
    freshness_status: str,
    conflict_status: str,
    composite_memory_score: Decimal,
    config: ResearchDomainRegulationSignalMemoryQualityConfig,
) -> str:
    if (
        freshness_status == STATUS_BLOCK
        or conflict_status == STATUS_BLOCK
        or composite_memory_score < config.watch_memory_score
    ):
        return STATUS_BLOCK
    if (
        freshness_status == STATUS_WATCH
        or conflict_status == STATUS_WATCH
        or composite_memory_score < config.pass_memory_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _freshness_score(
    ages: dict[str, Decimal | None],
    config: ResearchDomainRegulationSignalMemoryQualityConfig,
) -> Decimal:
    if any(value is None for value in ages.values()):
        return ZERO
    fresh_count = sum(
        1
        for signal_name, value in ages.items()
        if not _is_stale(signal_name, value, config)
    )
    return _ratio(Decimal(fresh_count).quantize(QUANTUM), SIGNAL_COUNT)


def _conflict_score(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return ZERO
    if status == STATUS_WATCH:
        return Decimal("0.500000")
    return ONE


def _row_reason_codes(
    *,
    public_status: str,
    freshness_status: str,
    conflict_status: str,
    composite_memory_score: Decimal,
    ages: dict[str, Decimal | None],
    row: ResearchDomainRegulationSignalMemoryQualityInputRow,
    config: ResearchDomainRegulationSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for signal_name in SIGNAL_NAMES:
        age = ages[signal_name]
        if age is None:
            reason_codes.append(f"regulation_memory_quality_{signal_name}_missing")
        elif _is_stale(signal_name, age, config):
            reason_codes.append(f"regulation_memory_quality_{signal_name}_stale")
        if getattr(row, f"{signal_name}_conflict_count") > ZERO:
            reason_codes.append(f"regulation_memory_quality_{signal_name}_conflicting")
    if conflict_status == STATUS_BLOCK:
        reason_codes.append(CONFLICT_BLOCK_REASON)
    elif conflict_status == STATUS_WATCH:
        reason_codes.append(CONFLICT_WATCH_REASON)
    if composite_memory_score < config.watch_memory_score:
        reason_codes.append(MEMORY_SCORE_BLOCK_REASON)
    elif composite_memory_score < config.pass_memory_score:
        reason_codes.append(MEMORY_SCORE_WATCH_REASON)
    if public_status == STATUS_WATCH:
        reason_codes.append(WATCH_REASON)
    if public_status == STATUS_PASS:
        if freshness_status == STATUS_PASS:
            reason_codes.append(FRESH_REASON)
        if conflict_status == STATUS_PASS:
            reason_codes.append(NO_CONFLICT_REASON)
        reason_codes.append(PASS_REASON)
    return tuple(sorted(set(reason_codes)))


def _summary_status(
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...],
) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...],
) -> tuple[ResearchDomainRegulationSignalMemoryQualityReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count_decimal(len(rows))
    return tuple(
        ResearchDomainRegulationSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
            memory_set_ratio=_ratio(_count_decimal(count), denominator),
        )
        for reason_code, count in sorted(counter.items())
    )


def _row_sort_key(
    row: ResearchDomainRegulationSignalMemoryQualityReportRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.public_status],
        -(ONE - row.composite_memory_score),
        row.jurisdiction_label,
        row.regulatory_area,
        row.memory_scope,
    )


def _normalize_rows(
    rows: Any,
) -> tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchDomainRegulationSignalMemoryQualityReportRow:
            raise ValueError(
                "rows must contain ResearchDomainRegulationSignalMemoryQualityReportRow",
            )
        _require_hard_flags("row", row)
        key = (row.jurisdiction_label, row.regulatory_area, row.memory_scope)
        if key in seen:
            raise ValueError("rows must contain unique memory sets")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_reason_code_counts(
    counts: Any,
) -> tuple[ResearchDomainRegulationSignalMemoryQualityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchDomainRegulationSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainRegulationSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
    if len({count.reason_code for count in normalized}) != len(normalized):
        raise ValueError("reason_code_counts values must be unique")
    if normalized != tuple(sorted(normalized, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _validate_config(config: ResearchDomainRegulationSignalMemoryQualityConfig) -> None:
    if config.pass_memory_score <= config.watch_memory_score:
        raise ValueError("pass_memory_score must exceed watch_memory_score")
    if config.block_conflict_count <= config.watch_conflict_count:
        raise ValueError("block_conflict_count must exceed watch_conflict_count")


def _validate_row(row: ResearchDomainRegulationSignalMemoryQualityReportRow) -> None:
    if row.public_status != _row_status_from_materialized(row):
        raise ValueError("public_status must match materialized row fields")
    if row.public_status == STATUS_PASS and row.reason_codes != (
        FRESH_REASON,
        NO_CONFLICT_REASON,
        PASS_REASON,
    ):
        raise ValueError("pass rows require clear memory reason codes")
    if row.public_status != STATUS_PASS and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not contain pass reason code")


def _row_status_from_materialized(
    row: ResearchDomainRegulationSignalMemoryQualityReportRow,
) -> str:
    if (
        row.freshness_status == STATUS_BLOCK
        or row.conflict_status == STATUS_BLOCK
        or MEMORY_SCORE_BLOCK_REASON in row.reason_codes
    ):
        return STATUS_BLOCK
    if (
        row.freshness_status == STATUS_WATCH
        or row.conflict_status == STATUS_WATCH
        or MEMORY_SCORE_WATCH_REASON in row.reason_codes
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _validate_report(report: ResearchDomainRegulationSignalMemoryQualityReport) -> None:
    rows = report.rows
    checks = {
        "memory_set_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "stale_memory_set_count": _count_if(rows, _has_stale_signal),
        "conflicting_memory_set_count": _count_if(rows, _has_conflicting_signal),
        "missing_memory_set_count": _count_if(rows, _has_missing_signal),
        "average_memory_score": _average(row.composite_memory_score for row in rows),
        "average_freshness_score": _average(row.freshness_score for row in rows),
        "average_conflict_score": _average(row.conflict_score for row in rows),
        "agency_missing_count": _signal_missing_count(rows, "agency"),
        "court_missing_count": _signal_missing_count(rows, "court"),
        "rulemaking_missing_count": _signal_missing_count(rows, "rulemaking"),
        "enforcement_missing_count": _signal_missing_count(rows, "enforcement"),
        "effective_date_missing_count": _signal_missing_count(rows, "effective_date"),
        "agency_conflicting_count": _signal_conflicting_count(rows, "agency"),
        "court_conflicting_count": _signal_conflicting_count(rows, "court"),
        "rulemaking_conflicting_count": _signal_conflicting_count(rows, "rulemaking"),
        "enforcement_conflicting_count": _signal_conflicting_count(rows, "enforcement"),
        "effective_date_conflicting_count": _signal_conflicting_count(
            rows,
            "effective_date",
        ),
        "max_agency_age_seconds": _max_optional_age(row.agency_age_seconds for row in rows),
        "max_court_age_seconds": _max_optional_age(row.court_age_seconds for row in rows),
        "max_rulemaking_age_seconds": _max_optional_age(
            row.rulemaking_age_seconds for row in rows
        ),
        "max_enforcement_age_seconds": _max_optional_age(
            row.enforcement_age_seconds for row in rows
        ),
        "max_effective_date_age_seconds": _max_optional_age(
            row.effective_date_age_seconds for row in rows
        ),
    }
    for signal_name in SIGNAL_NAMES:
        checks[f"{signal_name}_stale_count"] = _signal_stale_count(
            rows,
            signal_name,
            _ReportFreshnessConfig(report),
        )
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_code_counts != (
        (ResearchDomainRegulationSignalMemoryQualityReasonCodeCount(
            reason_code=NO_INPUTS_REASON,
            count=ONE,
            memory_set_ratio=ZERO,
        ),)
        if not rows
        else _reason_code_counts(rows)
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.report_status != (STATUS_BLOCK if not rows else _summary_status(rows)):
        raise ValueError("report_status must match rows")
    if report.handoff_gate_label != HANDOFF_GATE_LABELS[report.report_status]:
        raise ValueError("handoff_gate_label must match report_status")


@dataclass(frozen=True)
class _ReportFreshnessConfig:
    report: ResearchDomainRegulationSignalMemoryQualityReport

    fresh_agency_max_age_seconds: Decimal = Decimal("7200.000000")
    fresh_court_max_age_seconds: Decimal = Decimal("21600.000000")
    fresh_rulemaking_max_age_seconds: Decimal = Decimal("43200.000000")
    fresh_enforcement_max_age_seconds: Decimal = Decimal("43200.000000")
    fresh_effective_date_max_age_seconds: Decimal = Decimal("86400.000000")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_config_version(value: object) -> None:
    if (
        type(value) is not str
        or value
        != DEFAULT_RESEARCH_DOMAIN_REGULATION_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")


def _require_safe_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)
    if any(character not in SAFE_LABEL_CHARS for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(values: Any) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    for value in normalized:
        _require_reason_code("reason_code", value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized != tuple(sorted(normalized)):
        raise ValueError("reason_codes must be sorted deterministically")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("value must be quantizable") from exc


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average(values: Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(normalized, ZERO) / _count_decimal(len(normalized)))


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + Decimal(delta.microseconds) / Decimal("1000000"),
    )


def _signal_ages(
    row: ResearchDomainRegulationSignalMemoryQualityInputRow,
    handoff_at: datetime,
) -> dict[str, Decimal | None]:
    return {
        signal_name: (
            None
            if getattr(row, f"{signal_name}_memorized_at") is None
            else _age_seconds(handoff_at, getattr(row, f"{signal_name}_memorized_at"))
        )
        for signal_name in SIGNAL_NAMES
    }


def _signal_scores(
    row: ResearchDomainRegulationSignalMemoryQualityInputRow,
) -> tuple[Decimal, ...]:
    return tuple(getattr(row, f"{signal_name}_memory_score") for signal_name in SIGNAL_NAMES)


def _signal_conflict_counts(
    row: ResearchDomainRegulationSignalMemoryQualityInputRow,
) -> tuple[Decimal, ...]:
    return tuple(getattr(row, f"{signal_name}_conflict_count") for signal_name in SIGNAL_NAMES)


def _freshness_threshold(
    signal_name: str,
    config: ResearchDomainRegulationSignalMemoryQualityConfig | _ReportFreshnessConfig,
) -> Decimal:
    return getattr(config, f"fresh_{signal_name}_max_age_seconds")


def _is_stale(
    signal_name: str,
    age_seconds: Decimal | None,
    config: ResearchDomainRegulationSignalMemoryQualityConfig | _ReportFreshnessConfig,
) -> bool:
    return age_seconds is not None and age_seconds > _freshness_threshold(signal_name, config)


def _reject_future_memorized_at(
    row: ResearchDomainRegulationSignalMemoryQualityInputRow,
    handoff_at: datetime,
) -> None:
    for field_name in _memorized_at_field_names():
        value = getattr(row, field_name)
        if value is not None and value > handoff_at:
            raise ValueError(f"{field_name} must not be in the future")


def _status_count(
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == status))


def _count_if(
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...],
    predicate: Any,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if predicate(row)))


def _has_missing_signal(row: ResearchDomainRegulationSignalMemoryQualityReportRow) -> bool:
    return any(getattr(row, f"{signal_name}_age_seconds") is None for signal_name in SIGNAL_NAMES)


def _has_stale_signal(row: ResearchDomainRegulationSignalMemoryQualityReportRow) -> bool:
    return any(
        reason_code.endswith("_stale")
        for reason_code in row.reason_codes
        if reason_code.startswith("regulation_memory_quality_")
    )


def _has_conflicting_signal(
    row: ResearchDomainRegulationSignalMemoryQualityReportRow,
) -> bool:
    return any(
        getattr(row, f"{signal_name}_conflict_count") > ZERO for signal_name in SIGNAL_NAMES
    )


def _signal_missing_count(
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...],
    signal_name: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if getattr(row, f"{signal_name}_age_seconds") is None),
    )


def _signal_stale_count(
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...],
    signal_name: str,
    config: ResearchDomainRegulationSignalMemoryQualityConfig | _ReportFreshnessConfig,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if _is_stale(signal_name, getattr(row, f"{signal_name}_age_seconds"), config)
        ),
    )


def _signal_conflicting_count(
    rows: tuple[ResearchDomainRegulationSignalMemoryQualityReportRow, ...],
    signal_name: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if getattr(row, f"{signal_name}_conflict_count") > ZERO),
    )


def _max_optional_age(values: Any) -> Decimal:
    normalized = tuple(value for value in values if value is not None)
    if not normalized:
        return ZERO
    return max(normalized)


def _memorized_at_field_names() -> tuple[str, ...]:
    return tuple(f"{signal_name}_memorized_at" for signal_name in SIGNAL_NAMES)


def _memory_score_field_names() -> tuple[str, ...]:
    return tuple(f"{signal_name}_memory_score" for signal_name in SIGNAL_NAMES)


def _conflict_count_field_names() -> tuple[str, ...]:
    return tuple(f"{signal_name}_conflict_count" for signal_name in SIGNAL_NAMES)


def _age_seconds_field_names() -> tuple[str, ...]:
    return tuple(f"{signal_name}_age_seconds" for signal_name in SIGNAL_NAMES)


def _report_count_field_names() -> tuple[str, ...]:
    return (
        "memory_set_count",
        "pass_count",
        "watch_count",
        "block_count",
        "stale_memory_set_count",
        "conflicting_memory_set_count",
        "missing_memory_set_count",
        "agency_missing_count",
        "court_missing_count",
        "rulemaking_missing_count",
        "enforcement_missing_count",
        "effective_date_missing_count",
        "agency_stale_count",
        "court_stale_count",
        "rulemaking_stale_count",
        "enforcement_stale_count",
        "effective_date_stale_count",
        "agency_conflicting_count",
        "court_conflicting_count",
        "rulemaking_conflicting_count",
        "enforcement_conflicting_count",
        "effective_date_conflicting_count",
        "max_agency_age_seconds",
        "max_court_age_seconds",
        "max_rulemaking_age_seconds",
        "max_enforcement_age_seconds",
        "max_effective_date_age_seconds",
    )


def _payload_value(value: object, *, include_digest: bool) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        output: dict[str, object] = {}
        for field in fields(value):
            if field.name == "derived_validation_digest" and not include_digest:
                continue
            output[field.name] = _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return output
    if isinstance(value, tuple):
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item, include_digest=include_digest)
            for key, item in value.items()
        }
    return value


def _report_digest_from_payload(
    report: ResearchDomainRegulationSignalMemoryQualityReport,
    *,
    include_digest: bool,
) -> str:
    payload = _payload_value(report, include_digest=include_digest)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode()).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in HEX_CHARS for character in value)
    ):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload must not contain numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text("payload key", str(key))
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_text("payload value", value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public {field_name}")
