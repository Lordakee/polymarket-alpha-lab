"""Pure report-only event resolution authority traceability reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_STATUSES",
    "ResearchEventResolutionAuthorityTraceabilityConfig",
    "ResearchEventResolutionAuthorityTraceabilityInput",
    "ResearchEventResolutionAuthorityTraceabilityReasonCodeCount",
    "ResearchEventResolutionAuthorityTraceabilityRow",
    "ResearchEventResolutionAuthorityTraceabilityReport",
    "build_research_event_resolution_authority_traceability_report",
    "research_event_resolution_authority_traceability_report_payload",
    "research_event_resolution_authority_traceability_report_digest",
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_CONFIG_VERSION = (
    "research-event-resolution-authority-traceability-report-v0"
)
RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUS_WEIGHT = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "event_resolution_authority_traceability_pass",
    "event_resolution_authority_traceability_watch",
    "event_resolution_authority_traceability_block",
    "rule_clarity_watch",
    "rule_clarity_block",
    "source_authority_watch",
    "source_authority_block",
    "ambiguity_risk_watch",
    "ambiguity_risk_block",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "stale_rule_age_watch",
    "stale_rule_age_block",
    "manual_verification_coverage_watch",
    "manual_verification_coverage_block",
)
REPORT_REASON_CODES = (
    "event_resolution_authority_traceability_report_empty",
    "event_resolution_authority_traceability_report_pass",
    "event_resolution_authority_traceability_report_watch",
    "event_resolution_authority_traceability_report_block",
    "rule_clarity_exception",
    "source_authority_exception",
    "ambiguity_risk_exception",
    "contradiction_pressure_exception",
    "stale_rule_age_exception",
    "manual_verification_coverage_exception",
)
ROW_REASON_INDEX = {reason_code: index for index, reason_code in enumerate(ROW_REASON_CODES)}
REPORT_REASON_INDEX = {
    reason_code: index for index, reason_code in enumerate(REPORT_REASON_CODES)
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_id"),
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("h", "tt", "p", "://"),
    _join_parts("h", "tt", "ps", "://"),
    _join_parts("w", "ww", "."),
    _join_parts("u", "rl"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("ta", "ble"),
    _join_parts("pri", "vate", "_to", "ken"),
    _join_parts("to", "ken"),
    _join_parts("sec", "ret"),
    _join_parts("cre", "den", "tial"),
    _join_parts("wa", "ll", "et"),
    _join_parts("or", "der"),
    _join_parts("tr", "ade"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmendation"),
    _join_parts("siz", "ing"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityTraceabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_CONFIG_VERSION
    )
    min_pass_rule_clarity: Decimal = Decimal("0.800000")
    min_watch_rule_clarity: Decimal = Decimal("0.600000")
    min_pass_source_authority: Decimal = Decimal("0.800000")
    min_watch_source_authority: Decimal = Decimal("0.600000")
    max_pass_ambiguity_risk: Decimal = Decimal("0.100000")
    max_watch_ambiguity_risk: Decimal = Decimal("0.300000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.300000")
    max_pass_stale_rule_age_days: Decimal = Decimal("7.000000")
    max_watch_stale_rule_age_days: Decimal = Decimal("30.000000")
    min_pass_manual_verification_coverage: Decimal = Decimal("0.900000")
    min_watch_manual_verification_coverage: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionAuthorityTraceabilityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "min_pass_rule_clarity",
            "min_watch_rule_clarity",
            "min_pass_source_authority",
            "min_watch_source_authority",
            "max_pass_ambiguity_risk",
            "max_watch_ambiguity_risk",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "min_pass_manual_verification_coverage",
            "min_watch_manual_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_rule_age_days",
            "max_watch_stale_rule_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "min_pass_rule_clarity",
            self.min_pass_rule_clarity,
            "min_watch_rule_clarity",
            self.min_watch_rule_clarity,
        )
        _require_floor_pair(
            "min_pass_source_authority",
            self.min_pass_source_authority,
            "min_watch_source_authority",
            self.min_watch_source_authority,
        )
        _require_floor_pair(
            "min_pass_manual_verification_coverage",
            self.min_pass_manual_verification_coverage,
            "min_watch_manual_verification_coverage",
            self.min_watch_manual_verification_coverage,
        )
        _require_ceiling_pair(
            "max_pass_ambiguity_risk",
            self.max_pass_ambiguity_risk,
            self.max_watch_ambiguity_risk,
        )
        _require_ceiling_pair(
            "max_pass_contradiction_pressure",
            self.max_pass_contradiction_pressure,
            self.max_watch_contradiction_pressure,
        )
        _require_ceiling_pair(
            "max_pass_stale_rule_age_days",
            self.max_pass_stale_rule_age_days,
            self.max_watch_stale_rule_age_days,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityTraceabilityInput:
    event_reference_key: str
    rule_clarity: Decimal
    source_authority: Decimal
    ambiguity_risk: Decimal
    contradiction_pressure: Decimal
    stale_rule_age_days: Decimal
    manual_verification_required_count: Decimal
    manual_verification_completed_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityTraceabilityInput, "input")
        _require_private_key("event_reference_key", self.event_reference_key)
        for field_name in (
            "rule_clarity",
            "source_authority",
            "ambiguity_risk",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_rule_age_days",
            "manual_verification_required_count",
            "manual_verification_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_count_pair(
            "manual_verification_completed_count",
            self.manual_verification_completed_count,
            self.manual_verification_required_count,
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityTraceabilityReasonCodeCount:
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
class ResearchEventResolutionAuthorityTraceabilityRow:
    aggregate_row_number: Decimal
    event_trace_hash: str
    rule_clarity: Decimal
    source_authority: Decimal
    ambiguity_risk: Decimal
    contradiction_pressure: Decimal
    stale_rule_age_days: Decimal
    manual_verification_required_count: Decimal
    manual_verification_completed_count: Decimal
    manual_verification_coverage: Decimal
    authority_traceability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityTraceabilityRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_digest("event_trace_hash", self.event_trace_hash)
        for field_name in (
            "rule_clarity",
            "source_authority",
            "ambiguity_risk",
            "contradiction_pressure",
            "manual_verification_coverage",
            "authority_traceability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_rule_age_days",
            "manual_verification_required_count",
            "manual_verification_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_count_pair(
            "manual_verification_completed_count",
            self.manual_verification_completed_count,
            self.manual_verification_required_count,
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
class ResearchEventResolutionAuthorityTraceabilityReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_authority_traceability_score: Decimal
    min_rule_clarity: Decimal
    min_source_authority: Decimal
    max_ambiguity_risk: Decimal
    max_contradiction_pressure: Decimal
    max_stale_rule_age_days: Decimal
    mean_manual_verification_coverage: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventResolutionAuthorityTraceabilityReasonCodeCount, ...]
    rows: tuple[ResearchEventResolutionAuthorityTraceabilityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityTraceabilityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_stale_rule_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_authority_traceability_score",
            "min_rule_clarity",
            "min_source_authority",
            "max_ambiguity_risk",
            "max_contradiction_pressure",
            "mean_manual_verification_coverage",
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


def build_research_event_resolution_authority_traceability_report(
    inputs: Iterable[ResearchEventResolutionAuthorityTraceabilityInput],
    *,
    config: ResearchEventResolutionAuthorityTraceabilityConfig,
    generated_at: datetime,
) -> ResearchEventResolutionAuthorityTraceabilityReport:
    if type(config) is not ResearchEventResolutionAuthorityTraceabilityConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionAuthorityTraceabilityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    row_values = tuple(_row_value_from_input(value, config=config) for value in normalized_inputs)
    row_values = tuple(sorted(row_values, key=_row_value_sort_key))
    rows = tuple(
        _row_from_value(index=index, value=value)
        for index, value in enumerate(row_values, start=1)
    )
    return ResearchEventResolutionAuthorityTraceabilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_authority_traceability_score=_mean(
            tuple(row.authority_traceability_score for row in rows),
        ),
        min_rule_clarity=_minimum(tuple(row.rule_clarity for row in rows)),
        min_source_authority=_minimum(tuple(row.source_authority for row in rows)),
        max_ambiguity_risk=_maximum(tuple(row.ambiguity_risk for row in rows)),
        max_contradiction_pressure=_maximum(
            tuple(row.contradiction_pressure for row in rows),
        ),
        max_stale_rule_age_days=_maximum_whole(tuple(row.stale_rule_age_days for row in rows)),
        mean_manual_verification_coverage=_mean(
            tuple(row.manual_verification_coverage for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_event_resolution_authority_traceability_report_payload(
    report: ResearchEventResolutionAuthorityTraceabilityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionAuthorityTraceabilityReport:
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
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityTraceabilityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_event_resolution_authority_traceability_report_digest(
    report: ResearchEventResolutionAuthorityTraceabilityReport,
) -> str:
    payload = research_event_resolution_authority_traceability_report_payload(report)
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
    event_trace_hash: str
    rule_clarity: Decimal
    source_authority: Decimal
    ambiguity_risk: Decimal
    contradiction_pressure: Decimal
    stale_rule_age_days: Decimal
    manual_verification_required_count: Decimal
    manual_verification_completed_count: Decimal
    manual_verification_coverage: Decimal
    authority_traceability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _row_value_from_input(
    value: ResearchEventResolutionAuthorityTraceabilityInput,
    *,
    config: ResearchEventResolutionAuthorityTraceabilityConfig,
) -> _RowValue:
    manual_verification_coverage = _coverage_ratio(
        value.manual_verification_completed_count,
        value.manual_verification_required_count,
    )
    stale_rule_freshness = _stale_rule_freshness(
        value.stale_rule_age_days,
        config.max_watch_stale_rule_age_days,
    )
    ambiguity_clarity = ONE - value.ambiguity_risk
    contradiction_clarity = ONE - value.contradiction_pressure
    authority_traceability_score = _mean(
        (
            value.rule_clarity,
            value.source_authority,
            ambiguity_clarity,
            contradiction_clarity,
            stale_rule_freshness,
            manual_verification_coverage,
        ),
    )
    component_statuses = {
        "rule_clarity": _floor_status(
            value.rule_clarity,
            pass_value=config.min_pass_rule_clarity,
            watch_value=config.min_watch_rule_clarity,
        ),
        "source_authority": _floor_status(
            value.source_authority,
            pass_value=config.min_pass_source_authority,
            watch_value=config.min_watch_source_authority,
        ),
        "ambiguity_risk": _ceiling_status(
            value.ambiguity_risk,
            pass_value=config.max_pass_ambiguity_risk,
            watch_value=config.max_watch_ambiguity_risk,
        ),
        "contradiction_pressure": _ceiling_status(
            value.contradiction_pressure,
            pass_value=config.max_pass_contradiction_pressure,
            watch_value=config.max_watch_contradiction_pressure,
        ),
        "stale_rule_age": _ceiling_status(
            value.stale_rule_age_days,
            pass_value=config.max_pass_stale_rule_age_days,
            watch_value=config.max_watch_stale_rule_age_days,
        ),
        "manual_verification_coverage": _floor_status(
            manual_verification_coverage,
            pass_value=config.min_pass_manual_verification_coverage,
            watch_value=config.min_watch_manual_verification_coverage,
        ),
    }
    status = _row_status(tuple(component_statuses.values()))
    return _RowValue(
        event_trace_hash=sha256(value.event_reference_key.encode("utf-8")).hexdigest(),
        rule_clarity=value.rule_clarity,
        source_authority=value.source_authority,
        ambiguity_risk=value.ambiguity_risk,
        contradiction_pressure=value.contradiction_pressure,
        stale_rule_age_days=value.stale_rule_age_days,
        manual_verification_required_count=value.manual_verification_required_count,
        manual_verification_completed_count=value.manual_verification_completed_count,
        manual_verification_coverage=manual_verification_coverage,
        authority_traceability_score=authority_traceability_score,
        status=status,
        reason_codes=_row_reason_codes(status=status, component_statuses=component_statuses),
    )


def _row_from_value(
    *,
    index: int,
    value: _RowValue,
) -> ResearchEventResolutionAuthorityTraceabilityRow:
    return ResearchEventResolutionAuthorityTraceabilityRow(
        aggregate_row_number=_count(index),
        event_trace_hash=value.event_trace_hash,
        rule_clarity=value.rule_clarity,
        source_authority=value.source_authority,
        ambiguity_risk=value.ambiguity_risk,
        contradiction_pressure=value.contradiction_pressure,
        stale_rule_age_days=value.stale_rule_age_days,
        manual_verification_required_count=value.manual_verification_required_count,
        manual_verification_completed_count=value.manual_verification_completed_count,
        manual_verification_coverage=value.manual_verification_coverage,
        authority_traceability_score=value.authority_traceability_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    status: str,
    component_statuses: dict[str, str],
) -> tuple[str, ...]:
    reason_codes = [f"event_resolution_authority_traceability_{status}"]
    for component in (
        "rule_clarity",
        "source_authority",
        "ambiguity_risk",
        "contradiction_pressure",
        "stale_rule_age",
        "manual_verification_coverage",
    ):
        component_status = component_statuses[component]
        if component_status != STATUS_PASS:
            reason_codes.append(f"{component}_{component_status}")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODES,
    )


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionAuthorityTraceabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("event_resolution_authority_traceability_report_empty",)
    status = _report_status(rows)
    reason_codes = [f"event_resolution_authority_traceability_report_{status}"]
    component_pairs = (
        ("rule_clarity_exception", ("rule_clarity_watch", "rule_clarity_block")),
        (
            "source_authority_exception",
            ("source_authority_watch", "source_authority_block"),
        ),
        ("ambiguity_risk_exception", ("ambiguity_risk_watch", "ambiguity_risk_block")),
        (
            "contradiction_pressure_exception",
            ("contradiction_pressure_watch", "contradiction_pressure_block"),
        ),
        ("stale_rule_age_exception", ("stale_rule_age_watch", "stale_rule_age_block")),
        (
            "manual_verification_coverage_exception",
            (
                "manual_verification_coverage_watch",
                "manual_verification_coverage_block",
            ),
        ),
    )
    for report_reason, row_reasons in component_pairs:
        if any(_row_has_any_reason(row, row_reasons) for row in rows):
            reason_codes.append(report_reason)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODES,
    )


def _reason_code_counts_from_rows(
    rows: tuple[ResearchEventResolutionAuthorityTraceabilityRow, ...],
) -> tuple[ResearchEventResolutionAuthorityTraceabilityReasonCodeCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventResolutionAuthorityTraceabilityReasonCodeCount(
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
    inputs: Iterable[ResearchEventResolutionAuthorityTraceabilityInput],
) -> tuple[ResearchEventResolutionAuthorityTraceabilityInput, ...]:
    if type(inputs) in (str, bytes):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchEventResolutionAuthorityTraceabilityInput:
            raise ValueError(
                "inputs must contain ResearchEventResolutionAuthorityTraceabilityInput",
            )
        _require_hard_flags("input", value)
        if value.event_reference_key in seen_keys:
            raise ValueError("inputs must not contain duplicate event_reference_key values")
        seen_keys.add(value.event_reference_key)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchEventResolutionAuthorityTraceabilityRow],
) -> tuple[ResearchEventResolutionAuthorityTraceabilityRow, ...]:
    if type(rows) in (str, bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionAuthorityTraceabilityRow:
            raise ValueError("rows must contain ResearchEventResolutionAuthorityTraceabilityRow")
        _require_hard_flags("row", row)
        if row.event_trace_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate event_trace_hash values")
        seen_hashes.add(row.event_trace_hash)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchEventResolutionAuthorityTraceabilityReasonCodeCount],
) -> tuple[ResearchEventResolutionAuthorityTraceabilityReasonCodeCount, ...]:
    if type(counts) in (str, bytes):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchEventResolutionAuthorityTraceabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionAuthorityTraceabilityReasonCodeCount",
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


def _validate_row_consistency(row: ResearchEventResolutionAuthorityTraceabilityRow) -> None:
    if row.manual_verification_coverage != _coverage_ratio(
        row.manual_verification_completed_count,
        row.manual_verification_required_count,
    ):
        raise ValueError("manual_verification_coverage must match counts")
    if row.status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchEventResolutionAuthorityTraceabilityReport) -> None:
    rows = report.rows
    if report.input_row_count != _count(len(rows)):
        raise ValueError("input_row_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.mean_authority_traceability_score != _mean(
        tuple(row.authority_traceability_score for row in rows),
    ):
        raise ValueError("mean_authority_traceability_score must match rows")
    if report.min_rule_clarity != _minimum(tuple(row.rule_clarity for row in rows)):
        raise ValueError("min_rule_clarity must match rows")
    if report.min_source_authority != _minimum(tuple(row.source_authority for row in rows)):
        raise ValueError("min_source_authority must match rows")
    if report.max_ambiguity_risk != _maximum(tuple(row.ambiguity_risk for row in rows)):
        raise ValueError("max_ambiguity_risk must match rows")
    if report.max_contradiction_pressure != _maximum(
        tuple(row.contradiction_pressure for row in rows),
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.max_stale_rule_age_days != _maximum_whole(
        tuple(row.stale_rule_age_days for row in rows),
    ):
        raise ValueError("max_stale_rule_age_days must match rows")
    if report.mean_manual_verification_coverage != _mean(
        tuple(row.manual_verification_coverage for row in rows),
    ):
        raise ValueError("mean_manual_verification_coverage must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")


def _verify_report_integrity(report: ResearchEventResolutionAuthorityTraceabilityReport) -> None:
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
    value: ResearchEventResolutionAuthorityTraceabilityRow
    | ResearchEventResolutionAuthorityTraceabilityReport,
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
    value: ResearchEventResolutionAuthorityTraceabilityRow
    | ResearchEventResolutionAuthorityTraceabilityReport,
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
        or value not in RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_STATUSES
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


def _require_count_pair(
    completed_field_name: str,
    completed_value: Decimal,
    required_value: Decimal,
) -> None:
    if completed_value > required_value:
        raise ValueError(f"{completed_field_name} must not exceed required count")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(normalized)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_string(value: Decimal) -> str:
    return format(value.quantize(QUANTUM), "f")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
    return total.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < ZERO:
        value = ZERO
    if value > ONE:
        value = ONE
    return _quantize_decimal(value)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _ratio(_sum_decimal(values), _count(len(values)))


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return min(values).quantize(QUANTUM)


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return max(values).quantize(QUANTUM)


def _maximum_whole(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return max(values).quantize(COUNT_QUANTUM)


def _coverage_ratio(completed_count: Decimal, required_count: Decimal) -> Decimal:
    if required_count == ZERO:
        return ONE.quantize(QUANTUM)
    return _ratio(completed_count, required_count)


def _stale_rule_freshness(age_days: Decimal, max_watch_age_days: Decimal) -> Decimal:
    if max_watch_age_days == ZERO:
        return ONE.quantize(QUANTUM) if age_days == ZERO else ZERO.quantize(QUANTUM)
    freshness = ONE - _ratio(age_days, max_watch_age_days)
    if freshness < ZERO:
        return ZERO.quantize(QUANTUM)
    return _quantize_decimal(freshness)


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


def _report_status(rows: tuple[ResearchEventResolutionAuthorityTraceabilityRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    return _row_status(tuple(row.status for row in rows))


def _status_count(
    rows: tuple[ResearchEventResolutionAuthorityTraceabilityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code, allowed_values)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    index = ROW_REASON_INDEX if allowed_values is ROW_REASON_CODES else REPORT_REASON_INDEX
    expected = tuple(sorted(reason_codes, key=lambda item: (index[item], item)))
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use canonical sequence")
    return reason_codes


def _row_has_any_reason(
    row: ResearchEventResolutionAuthorityTraceabilityRow,
    reason_codes: tuple[str, ...],
) -> bool:
    return any(reason_code in row.reason_codes for reason_code in reason_codes)


def _row_sort_key(row: ResearchEventResolutionAuthorityTraceabilityRow) -> tuple[Decimal, str]:
    return (STATUS_WEIGHT[row.status], row.event_trace_hash)


def _row_value_sort_key(value: _RowValue) -> tuple[Decimal, str]:
    return (STATUS_WEIGHT[value.status], value.event_trace_hash)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
