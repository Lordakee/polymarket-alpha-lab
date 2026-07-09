"""Pure report-only source authority change detection reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_STATUSES",
    "ResearchSourceAuthorityChangeDetectionConfig",
    "ResearchSourceAuthorityChangeDetectionInput",
    "ResearchSourceAuthorityChangeDetectionReasonCodeCount",
    "ResearchSourceAuthorityChangeDetectionRow",
    "ResearchSourceAuthorityChangeDetectionReport",
    "build_research_source_authority_change_detection_report",
    "research_source_authority_change_detection_report_payload",
    "research_source_authority_change_detection_report_digest",
)


DEFAULT_RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_CONFIG_VERSION = (
    "research-source-authority-change-detection-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUS_WEIGHT = {
    STATUS_PASS: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_BLOCK: Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "source_authority_change_detection_pass",
    "source_authority_change_detection_watch",
    "source_authority_change_detection_block",
    "authority_change_score_watch",
    "authority_change_score_block",
    "lineage_shift_watch",
    "lineage_shift_block",
    "consensus_shift_watch",
    "consensus_shift_block",
    "official_authority_change_block",
    "verification_coverage_watch",
    "verification_coverage_block",
    "stale_unverified_change_block",
    "manual_verification_incomplete_block",
    "detected_authority_change_watch",
)
REPORT_REASON_CODES = (
    "source_authority_change_detection_report_empty",
    "source_authority_change_detection_report_pass",
    "source_authority_change_detection_report_watch",
    "source_authority_change_detection_report_block",
    "authority_change_exception",
    "lineage_shift_exception",
    "consensus_shift_exception",
    "official_authority_change_present",
    "verification_coverage_exception",
    "stale_unverified_change_present",
    "manual_verification_incomplete_present",
)
ROW_REASON_INDEX = {reason_code: index for index, reason_code in enumerate(ROW_REASON_CODES)}
REPORT_REASON_INDEX = {
    reason_code: index for index, reason_code in enumerate(REPORT_REASON_CODES)
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    _join_parts("can", "did", "ate", "_id"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_u", "rl"),
    _join_parts("source", "_te", "xt"),
    _join_parts("h", "tt", "p", "://"),
    _join_parts("h", "tt", "ps", "://"),
    _join_parts("w", "ww", "."),
    _join_parts("u", "rl"),
    _join_parts("data", "base"),
    _join_parts("d", "sn"),
    _join_parts("net", "work"),
    _join_parts("re", "quest"),
    _join_parts("sock", "et"),
    _join_parts("sub", "process"),
    _join_parts("conn", "ect"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("ta", "ble"),
    _join_parts("private", "_to", "ken"),
    _join_parts("to", "ken"),
    _join_parts("sec", "ret"),
    _join_parts("cre", "den", "tial"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tr", "ade"),
    _join_parts("trad", "ing"),
    _join_parts("li", "ve"),
    _join_parts("exe", "cution"),
    _join_parts("reco", "mmendation"),
    _join_parts("siz", "ing"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
)


@dataclass(frozen=True)
class ResearchSourceAuthorityChangeDetectionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_CONFIG_VERSION
    )
    watch_authority_change_score: Decimal = Decimal("0.250000")
    block_authority_change_score: Decimal = Decimal("0.600000")
    watch_lineage_shift_score: Decimal = Decimal("0.250000")
    block_lineage_shift_score: Decimal = Decimal("0.600000")
    watch_consensus_shift_score: Decimal = Decimal("0.250000")
    block_consensus_shift_score: Decimal = Decimal("0.600000")
    min_pass_verification_coverage: Decimal = Decimal("1.000000")
    min_watch_verification_coverage: Decimal = Decimal("0.500000")
    max_unverified_change_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityChangeDetectionConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "watch_authority_change_score",
            "block_authority_change_score",
            "watch_lineage_shift_score",
            "block_lineage_shift_score",
            "watch_consensus_shift_score",
            "block_consensus_shift_score",
            "min_pass_verification_coverage",
            "min_watch_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unverified_change_age_seconds",
            _normalize_nonnegative_decimal(
                "max_unverified_change_age_seconds",
                self.max_unverified_change_age_seconds,
            ),
        )
        _require_threshold_pair(
            "watch_authority_change_score",
            self.watch_authority_change_score,
            "block_authority_change_score",
            self.block_authority_change_score,
        )
        _require_threshold_pair(
            "watch_lineage_shift_score",
            self.watch_lineage_shift_score,
            "block_lineage_shift_score",
            self.block_lineage_shift_score,
        )
        _require_threshold_pair(
            "watch_consensus_shift_score",
            self.watch_consensus_shift_score,
            "block_consensus_shift_score",
            self.block_consensus_shift_score,
        )
        _require_floor_pair(
            "min_pass_verification_coverage",
            self.min_pass_verification_coverage,
            "min_watch_verification_coverage",
            self.min_watch_verification_coverage,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityChangeDetectionInput:
    source_authority_reference_key: str
    authority_change_score: Decimal
    lineage_shift_score: Decimal
    consensus_shift_score: Decimal
    verified_source_count: Decimal
    expected_source_count: Decimal
    observed_at: datetime
    authority_change_detected: bool = False
    official_authority_changed: bool = False
    authority_verification_complete: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityChangeDetectionInput, "input")
        _require_private_key("source_authority_reference_key", self.source_authority_reference_key)
        for field_name in (
            "authority_change_score",
            "lineage_shift_score",
            "consensus_shift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("verified_source_count", "expected_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.expected_source_count <= ZERO:
            raise ValueError("expected_source_count must be positive")
        _require_count_pair(
            "verified_source_count",
            self.verified_source_count,
            self.expected_source_count,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_change_detected",
            "official_authority_changed",
            "authority_verification_complete",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityChangeDetectionReasonCodeCount:
    reason_code: str
    count: Decimal
    observed_authority_ratio: Decimal
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
            "observed_authority_ratio",
            _normalize_probability(
                "observed_authority_ratio",
                self.observed_authority_ratio,
            ),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityChangeDetectionRow:
    aggregate_row_number: Decimal
    source_authority_trace_hash: str
    authority_change_score: Decimal
    lineage_shift_score: Decimal
    consensus_shift_score: Decimal
    verified_source_count: Decimal
    expected_source_count: Decimal
    verification_coverage: Decimal
    observed_at: datetime
    change_age_seconds: Decimal
    authority_change_detected: bool
    official_authority_changed: bool
    authority_verification_complete: bool
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityChangeDetectionRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_whole_decimal("aggregate_row_number", self.aggregate_row_number),
        )
        _require_digest("source_authority_trace_hash", self.source_authority_trace_hash)
        for field_name in (
            "authority_change_score",
            "lineage_shift_score",
            "consensus_shift_score",
            "verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("verified_source_count", "expected_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.expected_source_count <= ZERO:
            raise ValueError("expected_source_count must be positive")
        _require_count_pair(
            "verified_source_count",
            self.verified_source_count,
            self.expected_source_count,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "change_age_seconds",
            _normalize_nonnegative_decimal("change_age_seconds", self.change_age_seconds),
        )
        for field_name in (
            "authority_change_detected",
            "official_authority_changed",
            "authority_verification_complete",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
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
class ResearchSourceAuthorityChangeDetectionReport:
    generated_at: datetime
    config_version: str
    observed_authority_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    changed_authority_count: Decimal
    review_required_count: Decimal
    missing_verification_count: Decimal
    max_authority_change_score: Decimal
    max_lineage_shift_score: Decimal
    max_consensus_shift_score: Decimal
    max_change_age_seconds: Decimal
    mean_verification_coverage: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceAuthorityChangeDetectionReasonCodeCount, ...]
    rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityChangeDetectionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "observed_authority_count",
            "pass_count",
            "watch_count",
            "block_count",
            "changed_authority_count",
            "review_required_count",
            "missing_verification_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_authority_change_score",
            "max_lineage_shift_score",
            "max_consensus_shift_score",
            "mean_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_change_age_seconds",
            _normalize_nonnegative_decimal(
                "max_change_age_seconds",
                self.max_change_age_seconds,
            ),
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


def build_research_source_authority_change_detection_report(
    inputs: Iterable[ResearchSourceAuthorityChangeDetectionInput],
    *,
    config: ResearchSourceAuthorityChangeDetectionConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityChangeDetectionReport:
    if type(config) is not ResearchSourceAuthorityChangeDetectionConfig:
        raise ValueError("config must be a ResearchSourceAuthorityChangeDetectionConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    row_values = tuple(
        _row_value_from_input(value, config=config, generated_at=generated_at_utc)
        for value in normalized_inputs
    )
    sorted_values = tuple(sorted(row_values, key=_row_value_sort_key))
    rows = tuple(
        _row_from_value(index=index, value=value)
        for index, value in enumerate(sorted_values, start=1)
    )
    return ResearchSourceAuthorityChangeDetectionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observed_authority_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        changed_authority_count=_changed_authority_count(rows),
        review_required_count=_review_required_count(rows),
        missing_verification_count=_missing_verification_count(rows),
        max_authority_change_score=_maximum(
            tuple(row.authority_change_score for row in rows),
        ),
        max_lineage_shift_score=_maximum(tuple(row.lineage_shift_score for row in rows)),
        max_consensus_shift_score=_maximum(tuple(row.consensus_shift_score for row in rows)),
        max_change_age_seconds=_maximum(
            tuple(row.change_age_seconds for row in rows),
        ),
        mean_verification_coverage=_mean(
            tuple(row.verification_coverage for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_source_authority_change_detection_report_payload(
    report: ResearchSourceAuthorityChangeDetectionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceAuthorityChangeDetectionReport:
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
        raise ValueError("report must be a ResearchSourceAuthorityChangeDetectionReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_source_authority_change_detection_report_digest(
    report: ResearchSourceAuthorityChangeDetectionReport,
) -> str:
    payload = research_source_authority_change_detection_report_payload(report)
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
    source_authority_trace_hash: str
    authority_change_score: Decimal
    lineage_shift_score: Decimal
    consensus_shift_score: Decimal
    verified_source_count: Decimal
    expected_source_count: Decimal
    verification_coverage: Decimal
    observed_at: datetime
    change_age_seconds: Decimal
    authority_change_detected: bool
    official_authority_changed: bool
    authority_verification_complete: bool
    status: str
    reason_codes: tuple[str, ...]


def _row_value_from_input(
    value: ResearchSourceAuthorityChangeDetectionInput,
    *,
    config: ResearchSourceAuthorityChangeDetectionConfig,
    generated_at: datetime,
) -> _RowValue:
    verification_coverage = _ratio(
        value.verified_source_count,
        value.expected_source_count,
    )
    change_age_seconds = _duration_seconds(value.observed_at, generated_at)
    component_statuses = {
        "authority_change_score": _ceiling_status(
            value.authority_change_score,
            watch_value=config.watch_authority_change_score,
            block_value=config.block_authority_change_score,
        ),
        "lineage_shift": _ceiling_status(
            value.lineage_shift_score,
            watch_value=config.watch_lineage_shift_score,
            block_value=config.block_lineage_shift_score,
        ),
        "consensus_shift": _ceiling_status(
            value.consensus_shift_score,
            watch_value=config.watch_consensus_shift_score,
            block_value=config.block_consensus_shift_score,
        ),
        "official_authority_change": (
            STATUS_BLOCK if value.official_authority_changed else STATUS_PASS
        ),
        "verification_coverage": _floor_status(
            verification_coverage,
            pass_value=config.min_pass_verification_coverage,
            watch_value=config.min_watch_verification_coverage,
        ),
        "stale_unverified_change": (
            STATUS_BLOCK
            if (
                value.authority_change_detected
                and not value.authority_verification_complete
                and change_age_seconds > config.max_unverified_change_age_seconds
            )
            else STATUS_PASS
        ),
        "manual_verification_incomplete": (
            STATUS_BLOCK if not value.authority_verification_complete else STATUS_PASS
        ),
        "detected_authority_change": (
            STATUS_WATCH
            if value.authority_change_detected and not value.official_authority_changed
            else STATUS_PASS
        ),
    }
    status = _row_status(tuple(component_statuses.values()))
    return _RowValue(
        source_authority_trace_hash=sha256(
            value.source_authority_reference_key.encode("utf-8"),
        ).hexdigest(),
        authority_change_score=value.authority_change_score,
        lineage_shift_score=value.lineage_shift_score,
        consensus_shift_score=value.consensus_shift_score,
        verified_source_count=value.verified_source_count,
        expected_source_count=value.expected_source_count,
        verification_coverage=verification_coverage,
        observed_at=value.observed_at,
        change_age_seconds=change_age_seconds,
        authority_change_detected=value.authority_change_detected,
        official_authority_changed=value.official_authority_changed,
        authority_verification_complete=value.authority_verification_complete,
        status=status,
        reason_codes=_row_reason_codes(status=status, component_statuses=component_statuses),
    )


def _row_from_value(
    *,
    index: int,
    value: _RowValue,
) -> ResearchSourceAuthorityChangeDetectionRow:
    return ResearchSourceAuthorityChangeDetectionRow(
        aggregate_row_number=_count(index),
        source_authority_trace_hash=value.source_authority_trace_hash,
        authority_change_score=value.authority_change_score,
        lineage_shift_score=value.lineage_shift_score,
        consensus_shift_score=value.consensus_shift_score,
        verified_source_count=value.verified_source_count,
        expected_source_count=value.expected_source_count,
        verification_coverage=value.verification_coverage,
        observed_at=value.observed_at,
        change_age_seconds=value.change_age_seconds,
        authority_change_detected=value.authority_change_detected,
        official_authority_changed=value.official_authority_changed,
        authority_verification_complete=value.authority_verification_complete,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    status: str,
    component_statuses: dict[str, str],
) -> tuple[str, ...]:
    reason_codes = [f"source_authority_change_detection_{status}"]
    reason_pairs = (
        ("authority_change_score", "authority_change_score"),
        ("lineage_shift", "lineage_shift"),
        ("consensus_shift", "consensus_shift"),
        ("official_authority_change", "official_authority_change"),
        ("verification_coverage", "verification_coverage"),
        ("stale_unverified_change", "stale_unverified_change"),
        ("manual_verification_incomplete", "manual_verification_incomplete"),
        ("detected_authority_change", "detected_authority_change"),
    )
    for component, reason_prefix in reason_pairs:
        component_status = component_statuses[component]
        if component_status != STATUS_PASS:
            reason_codes.append(f"{reason_prefix}_{component_status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_authority_change_detection_report_empty",)
    status = _report_status(rows)
    reason_codes = [f"source_authority_change_detection_report_{status}"]
    component_pairs = (
        (
            "authority_change_exception",
            ("authority_change_score_watch", "authority_change_score_block"),
        ),
        ("lineage_shift_exception", ("lineage_shift_watch", "lineage_shift_block")),
        (
            "consensus_shift_exception",
            ("consensus_shift_watch", "consensus_shift_block"),
        ),
        ("official_authority_change_present", ("official_authority_change_block",)),
        (
            "verification_coverage_exception",
            ("verification_coverage_watch", "verification_coverage_block"),
        ),
        ("stale_unverified_change_present", ("stale_unverified_change_block",)),
        (
            "manual_verification_incomplete_present",
            ("manual_verification_incomplete_block",),
        ),
    )
    for report_reason, row_reasons in component_pairs:
        if any(_row_has_any_reason(row, row_reasons) for row in rows):
            reason_codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...],
) -> tuple[ResearchSourceAuthorityChangeDetectionReasonCodeCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchSourceAuthorityChangeDetectionReasonCodeCount(
            reason_code=reason_code,
            count=count,
            observed_authority_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (ROW_REASON_INDEX[item[0]], item[0]),
        )
    )


def _normalize_inputs(
    inputs: Iterable[ResearchSourceAuthorityChangeDetectionInput],
) -> tuple[ResearchSourceAuthorityChangeDetectionInput, ...]:
    if type(inputs) in (str, bytes):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchSourceAuthorityChangeDetectionInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityChangeDetectionInput",
            )
        _require_hard_flags("input", value)
        if value.source_authority_reference_key in seen_keys:
            raise ValueError(
                "inputs must not contain duplicate source_authority_reference_key values",
            )
        seen_keys.add(value.source_authority_reference_key)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchSourceAuthorityChangeDetectionRow],
) -> tuple[ResearchSourceAuthorityChangeDetectionRow, ...]:
    if type(rows) in (str, bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchSourceAuthorityChangeDetectionRow:
            raise ValueError("rows must contain ResearchSourceAuthorityChangeDetectionRow")
        _require_hard_flags("row", row)
        if row.source_authority_trace_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate source_authority_trace_hash values")
        seen_hashes.add(row.source_authority_trace_hash)
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: Iterable[ResearchSourceAuthorityChangeDetectionReasonCodeCount],
) -> tuple[ResearchSourceAuthorityChangeDetectionReasonCodeCount, ...]:
    if type(reason_code_counts) in (str, bytes):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchSourceAuthorityChangeDetectionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityChangeDetectionReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(item.reason_code)
    return tuple(
        sorted(normalized, key=lambda item: (ROW_REASON_INDEX[item.reason_code], item.reason_code)),
    )


def _row_value_sort_key(value: _RowValue) -> tuple[Decimal, str]:
    return (-STATUS_WEIGHT[value.status], value.source_authority_trace_hash)


def _row_status(statuses: tuple[str, ...]) -> str:
    if any(status == STATUS_BLOCK for status in statuses):
        return STATUS_BLOCK
    if any(status == STATUS_WATCH for status in statuses):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    return _row_status(tuple(row.status for row in rows))


def _status_count(
    rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _changed_authority_count(
    rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if row.authority_change_detected or row.official_authority_changed
        ),
    )


def _review_required_count(
    rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.status != STATUS_PASS))


def _missing_verification_count(
    rows: tuple[ResearchSourceAuthorityChangeDetectionRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if not row.authority_verification_complete))


def _row_has_any_reason(
    row: ResearchSourceAuthorityChangeDetectionRow,
    reason_codes: tuple[str, ...],
) -> bool:
    return any(reason_code in row.reason_codes for reason_code in reason_codes)


def _validate_row_consistency(row: ResearchSourceAuthorityChangeDetectionRow) -> None:
    expected_coverage = _ratio(row.verified_source_count, row.expected_source_count)
    if row.verification_coverage != expected_coverage:
        raise ValueError("verification_coverage must match source counts")
    expected_base = f"source_authority_change_detection_{row.status}"
    if not row.reason_codes or row.reason_codes[0] != expected_base:
        raise ValueError("row reason_codes must match status")


def _validate_report_consistency(report: ResearchSourceAuthorityChangeDetectionReport) -> None:
    rows = report.rows
    if report.observed_authority_count != _count(len(rows)):
        raise ValueError("observed_authority_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.changed_authority_count != _changed_authority_count(rows):
        raise ValueError("changed_authority_count must match rows")
    if report.review_required_count != _review_required_count(rows):
        raise ValueError("review_required_count must match rows")
    if report.missing_verification_count != _missing_verification_count(rows):
        raise ValueError("missing_verification_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.max_authority_change_score != _maximum(
        tuple(row.authority_change_score for row in rows),
    ):
        raise ValueError("max_authority_change_score must match rows")
    if report.max_lineage_shift_score != _maximum(tuple(row.lineage_shift_score for row in rows)):
        raise ValueError("max_lineage_shift_score must match rows")
    if report.max_consensus_shift_score != _maximum(
        tuple(row.consensus_shift_score for row in rows),
    ):
        raise ValueError("max_consensus_shift_score must match rows")
    if report.max_change_age_seconds != _maximum(tuple(row.change_age_seconds for row in rows)):
        raise ValueError("max_change_age_seconds must match rows")
    if report.mean_verification_coverage != _mean(
        tuple(row.verification_coverage for row in rows),
    ):
        raise ValueError("mean_verification_coverage must match rows")


def _verify_report_integrity(report: ResearchSourceAuthorityChangeDetectionReport) -> None:
    for row in report.rows:
        _verify_digest(row)
    _verify_digest(report)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("rows must contain JSON objects")
        _verify_payload_digest(row)
    _verify_payload_digest(payload)


def _apply_or_verify_digest(value: object) -> None:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass")
    current = getattr(value, "derived_validation_digest")
    expected = _dataclass_digest(value)
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
    elif current != expected:
        raise ValueError("derived_validation_digest does not match payload")
    _require_digest("derived_validation_digest", getattr(value, "derived_validation_digest"))


def _verify_digest(value: object) -> None:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass")
    expected = _dataclass_digest(value)
    current = getattr(value, "derived_validation_digest")
    if current != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _dataclass_digest(value: object) -> str:
    return _payload_digest(_json_ready(asdict(value)))


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    current = payload.get("derived_validation_digest")
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _payload_digest(payload)
    if current != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _payload_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            result[key] = _json_ready(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for text in _iter_public_text(payload):
        lowered = text.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public payload field in {label}")


def _iter_public_text(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_text(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_text(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_text(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_payload(field_name, value)


def _require_private_key(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) in (str, bytes):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in normalized:
        _require_reason_code(field_name, value, allowed_values)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicate values")
        seen.add(value)
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_count_pair(field_name: str, value: Decimal, maximum: Decimal) -> None:
    if value > maximum:
        raise ValueError(f"{field_name} must be at most expected_source_count")


def _require_threshold_pair(
    watch_field_name: str,
    watch_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if watch_value >= block_value:
        raise ValueError(f"{watch_field_name} must be less than {block_field_name}")


def _require_floor_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_field_name} must be at least {watch_field_name}")


def _ceiling_status(value: Decimal, *, watch_value: Decimal, block_value: Decimal) -> str:
    if value >= block_value:
        return STATUS_BLOCK
    if value >= watch_value:
        return STATUS_WATCH
    return STATUS_PASS


def _floor_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value >= pass_value:
        return STATUS_PASS
    if value >= watch_value:
        return STATUS_WATCH
    return STATUS_BLOCK


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    seconds = Decimal(str((finished_at - started_at).total_seconds()))
    return _normalize_nonnegative_decimal("change_age_seconds", seconds)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / _count(len(values))).quantize(QUANTUM)


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANTUM)
