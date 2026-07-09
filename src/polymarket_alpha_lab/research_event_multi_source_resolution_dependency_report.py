"""Pure report-only reducer for event multi-source resolution dependencies."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


__all__ = (
    "DEFAULT_RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_STATUSES",
    "ResearchEventMultiSourceResolutionDependencyConfig",
    "ResearchEventMultiSourceResolutionDependencyInput",
    "ResearchEventMultiSourceResolutionDependencyReasonCodeCount",
    "ResearchEventMultiSourceResolutionDependencyRow",
    "ResearchEventMultiSourceResolutionDependencyReport",
    "build_research_event_multi_source_resolution_dependency_report",
    "research_event_multi_source_resolution_dependency_report_payload",
    "research_event_multi_source_resolution_dependency_report_digest",
)


DEFAULT_RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_CONFIG_VERSION = (
    "research-event-multi-source-resolution-dependency-report-v0"
)
RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUS_SORT = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "event_multi_source_resolution_dependency_pass",
    "event_multi_source_resolution_dependency_watch",
    "event_multi_source_resolution_dependency_block",
    "authority_mix_watch",
    "authority_mix_block",
    "source_timing_watch",
    "source_timing_block",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "ambiguity_risk_watch",
    "ambiguity_risk_block",
    "reviewer_verification_coverage_watch",
    "reviewer_verification_coverage_block",
)
REPORT_REASON_CODES = (
    "event_multi_source_resolution_dependency_report_empty",
    "event_multi_source_resolution_dependency_report_pass",
    "event_multi_source_resolution_dependency_report_watch",
    "event_multi_source_resolution_dependency_report_block",
    "authority_mix_exception",
    "source_timing_exception",
    "contradiction_pressure_exception",
    "ambiguity_risk_exception",
    "reviewer_verification_coverage_exception",
)
ROW_REASON_INDEX = {reason_code: index for index, reason_code in enumerate(ROW_REASON_CODES)}
REPORT_REASON_INDEX = {
    reason_code: index for index, reason_code in enumerate(REPORT_REASON_CODES)
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_id"),
    _join_parts("raw", "id"),
    _join_parts("can", "did", "ate"),
    _join_parts("can", "did", "ate", "id"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("mar", "ket", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("sou", "rce", "u", "rl"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("sou", "rce", "te", "xt"),
    _join_parts("h", "tt", "p", "://"),
    _join_parts("h", "tt", "ps", "://"),
    _join_parts("w", "ww", "."),
    _join_parts("u", "rl"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("ta", "ble", "na", "me"),
    _join_parts("ta", "ble"),
    _join_parts("pri", "vate", "_to", "ken"),
    _join_parts("pri", "vate", "to", "ken"),
    _join_parts("to", "ken"),
    _join_parts("sec", "ret"),
    _join_parts("cre", "den", "tial"),
    _join_parts("wa", "ll", "et"),
    _join_parts("or", "der"),
    _join_parts("tr", "ade"),
    _join_parts("li", "ve"),
)


@dataclass(frozen=True)
class ResearchEventMultiSourceResolutionDependencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_CONFIG_VERSION
    )
    min_pass_authority_mix_score: Decimal = Decimal("0.800000")
    min_watch_authority_mix_score: Decimal = Decimal("0.600000")
    min_pass_source_timing_score: Decimal = Decimal("0.800000")
    min_watch_source_timing_score: Decimal = Decimal("0.600000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.300000")
    max_pass_ambiguity_risk: Decimal = Decimal("0.100000")
    max_watch_ambiguity_risk: Decimal = Decimal("0.300000")
    min_pass_reviewer_verification_coverage: Decimal = Decimal("0.900000")
    min_watch_reviewer_verification_coverage: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventMultiSourceResolutionDependencyConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "min_pass_authority_mix_score",
            "min_watch_authority_mix_score",
            "min_pass_source_timing_score",
            "min_watch_source_timing_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "max_pass_ambiguity_risk",
            "max_watch_ambiguity_risk",
            "min_pass_reviewer_verification_coverage",
            "min_watch_reviewer_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "min_pass_authority_mix_score",
            self.min_pass_authority_mix_score,
            "min_watch_authority_mix_score",
            self.min_watch_authority_mix_score,
        )
        _require_floor_pair(
            "min_pass_source_timing_score",
            self.min_pass_source_timing_score,
            "min_watch_source_timing_score",
            self.min_watch_source_timing_score,
        )
        _require_floor_pair(
            "min_pass_reviewer_verification_coverage",
            self.min_pass_reviewer_verification_coverage,
            "min_watch_reviewer_verification_coverage",
            self.min_watch_reviewer_verification_coverage,
        )
        _require_ceiling_pair(
            "max_pass_contradiction_pressure",
            self.max_pass_contradiction_pressure,
            self.max_watch_contradiction_pressure,
        )
        _require_ceiling_pair(
            "max_pass_ambiguity_risk",
            self.max_pass_ambiguity_risk,
            self.max_watch_ambiguity_risk,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventMultiSourceResolutionDependencyInput:
    event_reference_key: str
    primary_authority_family_count: Decimal
    secondary_authority_family_count: Decimal
    total_source_family_count: Decimal
    stale_source_family_count: Decimal
    contradicting_source_family_count: Decimal
    ambiguity_risk: Decimal
    reviewer_verification_required_count: Decimal
    reviewer_verification_completed_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventMultiSourceResolutionDependencyInput, "input")
        _require_private_key("event_reference_key", self.event_reference_key)
        for field_name in (
            "primary_authority_family_count",
            "secondary_authority_family_count",
            "total_source_family_count",
            "stale_source_family_count",
            "contradicting_source_family_count",
            "reviewer_verification_required_count",
            "reviewer_verification_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ambiguity_risk",
            _normalize_probability("ambiguity_risk", self.ambiguity_risk),
        )
        _require_component_count(
            "primary_authority_family_count",
            self.primary_authority_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "secondary_authority_family_count",
            self.secondary_authority_family_count,
            self.total_source_family_count,
        )
        _require_combined_authority_count(
            self.primary_authority_family_count,
            self.secondary_authority_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "stale_source_family_count",
            self.stale_source_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "contradicting_source_family_count",
            self.contradicting_source_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "reviewer_verification_completed_count",
            self.reviewer_verification_completed_count,
            self.reviewer_verification_required_count,
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventMultiSourceResolutionDependencyReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventMultiSourceResolutionDependencyRow:
    aggregate_row_number: Decimal
    event_dependency_hash: str
    primary_authority_family_count: Decimal
    secondary_authority_family_count: Decimal
    total_source_family_count: Decimal
    stale_source_family_count: Decimal
    contradicting_source_family_count: Decimal
    authority_mix_score: Decimal
    source_timing_score: Decimal
    contradiction_pressure: Decimal
    ambiguity_risk: Decimal
    reviewer_verification_required_count: Decimal
    reviewer_verification_completed_count: Decimal
    reviewer_verification_coverage: Decimal
    dependency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventMultiSourceResolutionDependencyRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_digest("event_dependency_hash", self.event_dependency_hash)
        for field_name in (
            "primary_authority_family_count",
            "secondary_authority_family_count",
            "total_source_family_count",
            "stale_source_family_count",
            "contradicting_source_family_count",
            "reviewer_verification_required_count",
            "reviewer_verification_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_mix_score",
            "source_timing_score",
            "contradiction_pressure",
            "ambiguity_risk",
            "reviewer_verification_coverage",
            "dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_component_count(
            "primary_authority_family_count",
            self.primary_authority_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "secondary_authority_family_count",
            self.secondary_authority_family_count,
            self.total_source_family_count,
        )
        _require_combined_authority_count(
            self.primary_authority_family_count,
            self.secondary_authority_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "stale_source_family_count",
            self.stale_source_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "contradicting_source_family_count",
            self.contradicting_source_family_count,
            self.total_source_family_count,
        )
        _require_component_count(
            "reviewer_verification_completed_count",
            self.reviewer_verification_completed_count,
            self.reviewer_verification_required_count,
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventMultiSourceResolutionDependencyReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_dependency_score: Decimal
    mean_authority_mix_score: Decimal
    min_source_timing_score: Decimal
    max_contradiction_pressure: Decimal
    max_ambiguity_risk: Decimal
    mean_reviewer_verification_coverage: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchEventMultiSourceResolutionDependencyReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchEventMultiSourceResolutionDependencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventMultiSourceResolutionDependencyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in ("input_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_dependency_score",
            "mean_authority_mix_score",
            "min_source_timing_score",
            "max_contradiction_pressure",
            "max_ambiguity_risk",
            "mean_reviewer_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_event_multi_source_resolution_dependency_report(
    inputs: Iterable[ResearchEventMultiSourceResolutionDependencyInput],
    *,
    config: ResearchEventMultiSourceResolutionDependencyConfig,
    generated_at: datetime,
) -> ResearchEventMultiSourceResolutionDependencyReport:
    if type(config) is not ResearchEventMultiSourceResolutionDependencyConfig:
        raise ValueError("config must be a ResearchEventMultiSourceResolutionDependencyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    row_values = tuple(_row_value_from_input(value, config=config) for value in normalized_inputs)
    row_values = tuple(sorted(row_values, key=_row_value_sort_key))
    rows = tuple(
        _row_from_value(index=index, value=value)
        for index, value in enumerate(row_values, start=1)
    )
    return ResearchEventMultiSourceResolutionDependencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_dependency_score=_mean(tuple(row.dependency_score for row in rows)),
        mean_authority_mix_score=_mean(tuple(row.authority_mix_score for row in rows)),
        min_source_timing_score=_minimum(tuple(row.source_timing_score for row in rows)),
        max_contradiction_pressure=_maximum(
            tuple(row.contradiction_pressure for row in rows),
        ),
        max_ambiguity_risk=_maximum(tuple(row.ambiguity_risk for row in rows)),
        mean_reviewer_verification_coverage=_mean(
            tuple(row.reviewer_verification_coverage for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_event_multi_source_resolution_dependency_report_payload(
    report: ResearchEventMultiSourceResolutionDependencyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventMultiSourceResolutionDependencyReport:
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_unsafe_public_payload("payload", payload)
        _verify_public_payload_integrity(payload)
    else:
        raise ValueError("report must be a ResearchEventMultiSourceResolutionDependencyReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_event_multi_source_resolution_dependency_report_digest(
    report: ResearchEventMultiSourceResolutionDependencyReport,
) -> str:
    payload = research_event_multi_source_resolution_dependency_report_payload(report)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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


@dataclass(frozen=True)
class _RowValue:
    event_dependency_hash: str
    primary_authority_family_count: Decimal
    secondary_authority_family_count: Decimal
    total_source_family_count: Decimal
    stale_source_family_count: Decimal
    contradicting_source_family_count: Decimal
    authority_mix_score: Decimal
    source_timing_score: Decimal
    contradiction_pressure: Decimal
    ambiguity_risk: Decimal
    reviewer_verification_required_count: Decimal
    reviewer_verification_completed_count: Decimal
    reviewer_verification_coverage: Decimal
    dependency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _row_value_from_input(
    value: ResearchEventMultiSourceResolutionDependencyInput,
    *,
    config: ResearchEventMultiSourceResolutionDependencyConfig,
) -> _RowValue:
    authority_mix_score = _authority_mix_score(
        value.primary_authority_family_count,
        value.secondary_authority_family_count,
        value.total_source_family_count,
    )
    source_timing_score = _source_timing_score(
        value.stale_source_family_count,
        value.total_source_family_count,
    )
    contradiction_pressure = _contradiction_pressure(
        value.contradicting_source_family_count,
        value.total_source_family_count,
    )
    reviewer_verification_coverage = _coverage_ratio(
        value.reviewer_verification_completed_count,
        value.reviewer_verification_required_count,
    )
    dependency_score = _mean(
        (
            authority_mix_score,
            source_timing_score,
            ONE - contradiction_pressure,
            ONE - value.ambiguity_risk,
            reviewer_verification_coverage,
        ),
    )
    component_statuses = {
        "authority_mix": _floor_status(
            authority_mix_score,
            pass_value=config.min_pass_authority_mix_score,
            watch_value=config.min_watch_authority_mix_score,
        ),
        "source_timing": _floor_status(
            source_timing_score,
            pass_value=config.min_pass_source_timing_score,
            watch_value=config.min_watch_source_timing_score,
        ),
        "contradiction_pressure": _ceiling_status(
            contradiction_pressure,
            pass_value=config.max_pass_contradiction_pressure,
            watch_value=config.max_watch_contradiction_pressure,
        ),
        "ambiguity_risk": _ceiling_status(
            value.ambiguity_risk,
            pass_value=config.max_pass_ambiguity_risk,
            watch_value=config.max_watch_ambiguity_risk,
        ),
        "reviewer_verification_coverage": _floor_status(
            reviewer_verification_coverage,
            pass_value=config.min_pass_reviewer_verification_coverage,
            watch_value=config.min_watch_reviewer_verification_coverage,
        ),
    }
    status = _row_status(tuple(component_statuses.values()))
    return _RowValue(
        event_dependency_hash=sha256(value.event_reference_key.encode("utf-8")).hexdigest(),
        primary_authority_family_count=value.primary_authority_family_count,
        secondary_authority_family_count=value.secondary_authority_family_count,
        total_source_family_count=value.total_source_family_count,
        stale_source_family_count=value.stale_source_family_count,
        contradicting_source_family_count=value.contradicting_source_family_count,
        authority_mix_score=authority_mix_score,
        source_timing_score=source_timing_score,
        contradiction_pressure=contradiction_pressure,
        ambiguity_risk=value.ambiguity_risk,
        reviewer_verification_required_count=value.reviewer_verification_required_count,
        reviewer_verification_completed_count=value.reviewer_verification_completed_count,
        reviewer_verification_coverage=reviewer_verification_coverage,
        dependency_score=dependency_score,
        status=status,
        reason_codes=_row_reason_codes(status=status, component_statuses=component_statuses),
    )


def _row_from_value(
    *,
    index: int,
    value: _RowValue,
) -> ResearchEventMultiSourceResolutionDependencyRow:
    return ResearchEventMultiSourceResolutionDependencyRow(
        aggregate_row_number=_count(index),
        event_dependency_hash=value.event_dependency_hash,
        primary_authority_family_count=value.primary_authority_family_count,
        secondary_authority_family_count=value.secondary_authority_family_count,
        total_source_family_count=value.total_source_family_count,
        stale_source_family_count=value.stale_source_family_count,
        contradicting_source_family_count=value.contradicting_source_family_count,
        authority_mix_score=value.authority_mix_score,
        source_timing_score=value.source_timing_score,
        contradiction_pressure=value.contradiction_pressure,
        ambiguity_risk=value.ambiguity_risk,
        reviewer_verification_required_count=value.reviewer_verification_required_count,
        reviewer_verification_completed_count=value.reviewer_verification_completed_count,
        reviewer_verification_coverage=value.reviewer_verification_coverage,
        dependency_score=value.dependency_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    status: str,
    component_statuses: dict[str, str],
) -> tuple[str, ...]:
    reason_codes = [f"event_multi_source_resolution_dependency_{status}"]
    for component in (
        "authority_mix",
        "source_timing",
        "contradiction_pressure",
        "ambiguity_risk",
        "reviewer_verification_coverage",
    ):
        component_status = component_statuses[component]
        if component_status != STATUS_PASS:
            reason_codes.append(f"{component}_{component_status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[ResearchEventMultiSourceResolutionDependencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("event_multi_source_resolution_dependency_report_empty",)
    status = _report_status(rows)
    reason_codes = [f"event_multi_source_resolution_dependency_report_{status}"]
    component_pairs = (
        ("authority_mix_exception", ("authority_mix_watch", "authority_mix_block")),
        ("source_timing_exception", ("source_timing_watch", "source_timing_block")),
        (
            "contradiction_pressure_exception",
            ("contradiction_pressure_watch", "contradiction_pressure_block"),
        ),
        ("ambiguity_risk_exception", ("ambiguity_risk_watch", "ambiguity_risk_block")),
        (
            "reviewer_verification_coverage_exception",
            (
                "reviewer_verification_coverage_watch",
                "reviewer_verification_coverage_block",
            ),
        ),
    )
    for report_reason, row_reasons in component_pairs:
        if any(_row_has_any_reason(row, row_reasons) for row in rows):
            reason_codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchEventMultiSourceResolutionDependencyRow, ...],
) -> tuple[ResearchEventMultiSourceResolutionDependencyReasonCodeCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventMultiSourceResolutionDependencyReasonCodeCount(
            reason_code=reason_code,
            count=count,
            input_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (ROW_REASON_INDEX[item[0]], item[0]),
        )
    )


def _normalize_inputs(
    inputs: Iterable[ResearchEventMultiSourceResolutionDependencyInput],
) -> tuple[ResearchEventMultiSourceResolutionDependencyInput, ...]:
    if type(inputs) in (str, bytes):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchEventMultiSourceResolutionDependencyInput:
            raise ValueError(
                "inputs must contain ResearchEventMultiSourceResolutionDependencyInput",
            )
        _require_hard_flags("input", value)
        if value.event_reference_key in seen_keys:
            raise ValueError("inputs must not contain duplicate event_reference_key values")
        seen_keys.add(value.event_reference_key)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchEventMultiSourceResolutionDependencyRow],
) -> tuple[ResearchEventMultiSourceResolutionDependencyRow, ...]:
    if type(rows) in (str, bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventMultiSourceResolutionDependencyRow:
            raise ValueError("rows must contain ResearchEventMultiSourceResolutionDependencyRow")
        _require_hard_flags("row", row)
        if row.event_dependency_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate event_dependency_hash values")
        seen_hashes.add(row.event_dependency_hash)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchEventMultiSourceResolutionDependencyReasonCodeCount],
) -> tuple[ResearchEventMultiSourceResolutionDependencyReasonCodeCount, ...]:
    if type(counts) in (str, bytes):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchEventMultiSourceResolutionDependencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventMultiSourceResolutionDependencyReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        seen_codes.add(value.reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (ROW_REASON_INDEX[item.reason_code], item.reason_code),
        ),
    )


def _validate_row_consistency(row: ResearchEventMultiSourceResolutionDependencyRow) -> None:
    if row.authority_mix_score != _authority_mix_score(
        row.primary_authority_family_count,
        row.secondary_authority_family_count,
        row.total_source_family_count,
    ):
        raise ValueError("authority_mix_score must match family counts")
    if row.source_timing_score != _source_timing_score(
        row.stale_source_family_count,
        row.total_source_family_count,
    ):
        raise ValueError("source_timing_score must match family counts")
    if row.contradiction_pressure != _contradiction_pressure(
        row.contradicting_source_family_count,
        row.total_source_family_count,
    ):
        raise ValueError("contradiction_pressure must match family counts")
    if row.reviewer_verification_coverage != _coverage_ratio(
        row.reviewer_verification_completed_count,
        row.reviewer_verification_required_count,
    ):
        raise ValueError("reviewer_verification_coverage must match counts")
    if row.dependency_score != _mean(
        (
            row.authority_mix_score,
            row.source_timing_score,
            ONE - row.contradiction_pressure,
            ONE - row.ambiguity_risk,
            row.reviewer_verification_coverage,
        ),
    ):
        raise ValueError("dependency_score must match components")
    if row.status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchEventMultiSourceResolutionDependencyReport) -> None:
    rows = report.rows
    if report.input_row_count != _count(len(rows)):
        raise ValueError("input_row_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.mean_dependency_score != _mean(tuple(row.dependency_score for row in rows)):
        raise ValueError("mean_dependency_score must match rows")
    if report.mean_authority_mix_score != _mean(
        tuple(row.authority_mix_score for row in rows),
    ):
        raise ValueError("mean_authority_mix_score must match rows")
    if report.min_source_timing_score != _minimum(
        tuple(row.source_timing_score for row in rows),
    ):
        raise ValueError("min_source_timing_score must match rows")
    if report.max_contradiction_pressure != _maximum(
        tuple(row.contradiction_pressure for row in rows),
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.max_ambiguity_risk != _maximum(tuple(row.ambiguity_risk for row in rows)):
        raise ValueError("max_ambiguity_risk must match rows")
    if report.mean_reviewer_verification_coverage != _mean(
        tuple(row.reviewer_verification_coverage for row in rows),
    ):
        raise ValueError("mean_reviewer_verification_coverage must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")


def _verify_report_integrity(report: ResearchEventMultiSourceResolutionDependencyReport) -> None:
    if report.derived_validation_digest != _payload_digest(_unsigned_payload(report)):
        raise ValueError("derived_validation_digest does not match report payload")
    for row in report.rows:
        if row.derived_validation_digest != _payload_digest(_unsigned_payload(row)):
            raise ValueError("derived_validation_digest does not match row payload")


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if type(rows) is list:
        for row in rows:
            if type(row) is not dict:
                raise ValueError("rows must contain payload objects")
            _verify_payload_digest(row)
    _verify_payload_digest(payload)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    supplied = payload.get("derived_validation_digest")
    if type(supplied) is not str:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    _require_digest("derived_validation_digest", supplied)
    base_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest does not match payload fields")


def _apply_or_verify_digest(
    value: ResearchEventMultiSourceResolutionDependencyRow
    | ResearchEventMultiSourceResolutionDependencyReport,
) -> None:
    expected_digest = _payload_digest(_unsigned_payload(value))
    supplied_digest = value.derived_validation_digest
    if supplied_digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
        return
    _require_digest("derived_validation_digest", supplied_digest)
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _unsigned_payload(
    value: ResearchEventMultiSourceResolutionDependencyRow
    | ResearchEventMultiSourceResolutionDependencyReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload must not contain primitive numerics")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload content")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_private_key(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64 or any(item not in "0123456789abcdef" for item in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or value not in RESEARCH_EVENT_MULTI_SOURCE_RESOLUTION_DEPENDENCY_REPORT_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_floor_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_field_name} must be at least {watch_field_name}")


def _require_ceiling_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_field_name} must not exceed paired watch value")


def _require_component_count(
    component_field_name: str,
    component_value: Decimal,
    total_value: Decimal,
) -> None:
    if component_value > total_value:
        raise ValueError(f"{component_field_name} must not exceed total count")


def _require_combined_authority_count(
    primary_value: Decimal,
    secondary_value: Decimal,
    total_value: Decimal,
) -> None:
    if primary_value + secondary_value > total_value:
        raise ValueError("authority family counts must not exceed total count")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_string(value: Decimal) -> str:
    return format(_decimal("value", value), "f")


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE:
        return ONE
    return value


def _authority_mix_score(
    primary_count: Decimal,
    secondary_count: Decimal,
    total_count: Decimal,
) -> Decimal:
    authority_points = primary_count + secondary_count * HALF
    return _capped_ratio(authority_points, total_count)


def _source_timing_score(stale_count: Decimal, total_count: Decimal) -> Decimal:
    if total_count == ZERO:
        return ZERO
    return _ratio(total_count - stale_count, total_count)


def _contradiction_pressure(contradicting_count: Decimal, total_count: Decimal) -> Decimal:
    if total_count == ZERO:
        return ONE
    return _ratio(contradicting_count, total_count)


def _coverage_ratio(completed_count: Decimal, required_count: Decimal) -> Decimal:
    return _ratio(completed_count, required_count)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANTUM)


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _floor_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value >= pass_value:
        return STATUS_PASS
    if value >= watch_value:
        return STATUS_WATCH
    return STATUS_BLOCK


def _ceiling_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value <= pass_value:
        return STATUS_PASS
    if value <= watch_value:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_status(statuses: tuple[str, ...]) -> str:
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    prefix = reason_codes[0]
    if prefix == "event_multi_source_resolution_dependency_block":
        return STATUS_BLOCK
    if prefix == "event_multi_source_resolution_dependency_watch":
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchEventMultiSourceResolutionDependencyRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchEventMultiSourceResolutionDependencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_has_any_reason(
    row: ResearchEventMultiSourceResolutionDependencyRow,
    reason_codes: tuple[str, ...],
) -> bool:
    return any(reason_code in row.reason_codes for reason_code in reason_codes)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen_codes: set[str] = set()
    for reason_code in normalized:
        _require_reason_code(field_name, reason_code, allowed_values)
        if reason_code in seen_codes:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen_codes.add(reason_code)
    index_map = ROW_REASON_INDEX if allowed_values is ROW_REASON_CODES else REPORT_REASON_INDEX
    if tuple(sorted(normalized, key=lambda item: (index_map[item], item))) != normalized:
        raise ValueError(f"{field_name} must use deterministic sequence")
    if allowed_values is ROW_REASON_CODES:
        _validate_row_reason_prefix(normalized)
    else:
        _validate_report_reason_prefix(normalized)
    return normalized


def _validate_row_reason_prefix(reason_codes: tuple[str, ...]) -> None:
    if reason_codes[0] not in ROW_REASON_CODES[:3]:
        raise ValueError("row reason_codes must start with a status reason")
    if reason_codes[0].endswith("_pass") and len(reason_codes) != 1:
        raise ValueError("pass row reason_codes must stand alone")
    if not reason_codes[0].endswith("_pass") and len(reason_codes) == 1:
        raise ValueError("watch or block row reason_codes require detail reasons")
    if reason_codes[0].endswith("_watch") and any(
        reason_code.endswith("_block") for reason_code in reason_codes[1:]
    ):
        raise ValueError("watch row reason_codes must not contain block reasons")


def _validate_report_reason_prefix(reason_codes: tuple[str, ...]) -> None:
    if reason_codes[0] not in REPORT_REASON_CODES[:4]:
        raise ValueError("report reason_codes must start with a status reason")
    if reason_codes[0].endswith("_empty") and len(reason_codes) != 1:
        raise ValueError("empty report reason_codes must stand alone")
    if reason_codes[0].endswith("_pass") and len(reason_codes) != 1:
        raise ValueError("pass report reason_codes must stand alone")
    if reason_codes[0].endswith(("_watch", "_block")) and len(reason_codes) == 1:
        raise ValueError("watch or block report reason_codes require detail reasons")


def _row_value_sort_key(value: _RowValue) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT[value.status],
        value.dependency_score,
        value.event_dependency_hash,
    )


def _row_sort_key(row: ResearchEventMultiSourceResolutionDependencyRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT[row.status],
        row.dependency_score,
        row.event_dependency_hash,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
