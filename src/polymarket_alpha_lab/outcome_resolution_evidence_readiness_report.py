"""Pure outcome resolution evidence readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_OUTCOME_RESOLUTION_EVIDENCE_READINESS_REPORT_CONFIG_VERSION = (
    "outcome-resolution-evidence-readiness-report-v0"
)

BANDS = ("ready", "attention", "blocker")
BAND_RANK = {
    "blocker": Decimal("0.000000"),
    "attention": Decimal("1.000000"),
    "ready": Decimal("2.000000"),
}

READY_REASON = "outcome_resolution_evidence_readiness_ready"
ATTENTION_REASON = "outcome_resolution_evidence_readiness_attention"
BLOCKER_REASON = "outcome_resolution_evidence_readiness_blocker"
CONFLICTING_SOURCES_REASON = "outcome_resolution_evidence_conflicting_sources"
QUORUM_GAP_REASON = "outcome_resolution_evidence_quorum_gap"
PENDING_ACK_REASON = "outcome_resolution_evidence_pending_ack"
MANUAL_REVIEW_REASON = "outcome_resolution_evidence_manual_review_required"
STALE_CHECK_REASON = "outcome_resolution_evidence_stale_check"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


@dataclass(frozen=True)
class OutcomeResolutionEvidenceReadinessConfig:
    config_version: str = (
        DEFAULT_OUTCOME_RESOLUTION_EVIDENCE_READINESS_REPORT_CONFIG_VERSION
    )
    required_resolution_source_count: Decimal = Decimal("3.000000")
    required_official_source_count: Decimal = Decimal("1.000000")
    freshness_warning_ratio: Decimal = Decimal("0.500000")
    freshness_blocker_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_resolution_source_count",
            _require_positive_integer_decimal(
                "required_resolution_source_count",
                self.required_resolution_source_count,
            ),
        )
        object.__setattr__(
            self,
            "required_official_source_count",
            _require_positive_integer_decimal(
                "required_official_source_count",
                self.required_official_source_count,
            ),
        )
        object.__setattr__(
            self,
            "freshness_warning_ratio",
            _require_ratio_decimal("freshness_warning_ratio", self.freshness_warning_ratio),
        )
        object.__setattr__(
            self,
            "freshness_blocker_ratio",
            _require_ratio_decimal("freshness_blocker_ratio", self.freshness_blocker_ratio),
        )
        if self.freshness_warning_ratio > self.freshness_blocker_ratio:
            raise ValueError("freshness_warning_ratio cannot exceed freshness_blocker_ratio")
        reject_unsafe_surface_fields("outcome resolution evidence readiness config", self)
        require_paper_only_flags("outcome resolution evidence readiness config", self)


@dataclass(frozen=True)
class OutcomeResolutionEvidenceReadinessInput:
    event_id: str
    outcome_id: str
    resolution_source_count: Decimal
    official_source_count: Decimal
    conflicting_source_count: Decimal
    last_checked_age_seconds: Decimal
    pending_ack: bool
    manual_review_required: bool
    settlement_window_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        _require_public_string("outcome_id", self.outcome_id)
        object.__setattr__(
            self,
            "resolution_source_count",
            _require_nonnegative_integer_decimal(
                "resolution_source_count",
                self.resolution_source_count,
            ),
        )
        object.__setattr__(
            self,
            "official_source_count",
            _require_nonnegative_integer_decimal(
                "official_source_count",
                self.official_source_count,
            ),
        )
        object.__setattr__(
            self,
            "conflicting_source_count",
            _require_nonnegative_integer_decimal(
                "conflicting_source_count",
                self.conflicting_source_count,
            ),
        )
        object.__setattr__(
            self,
            "last_checked_age_seconds",
            _require_nonnegative_decimal(
                "last_checked_age_seconds",
                self.last_checked_age_seconds,
            ),
        )
        _require_bool("pending_ack", self.pending_ack)
        _require_bool("manual_review_required", self.manual_review_required)
        object.__setattr__(
            self,
            "settlement_window_seconds",
            _require_positive_decimal(
                "settlement_window_seconds",
                self.settlement_window_seconds,
            ),
        )
        _validate_input_counts(self)
        reject_unsafe_surface_fields("outcome resolution evidence readiness input", self)
        require_paper_only_flags("outcome resolution evidence readiness input", self)


@dataclass(frozen=True)
class OutcomeResolutionEvidenceReadinessRow:
    event_id: str
    outcome_id: str
    band: str
    reason_codes: tuple[str, ...]
    resolution_source_count: Decimal
    official_source_count: Decimal
    conflicting_source_count: Decimal
    evidence_quorum_gap: Decimal
    official_source_gap: Decimal
    last_checked_age_seconds: Decimal
    pending_ack: bool
    pending_ack_age_seconds: Decimal
    manual_review_required: bool
    settlement_window_seconds: Decimal
    freshness_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        _require_public_string("outcome_id", self.outcome_id)
        _require_band("band", self.band)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        for field_name in (
            "resolution_source_count",
            "official_source_count",
            "conflicting_source_count",
            "evidence_quorum_gap",
            "official_source_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "last_checked_age_seconds",
            "pending_ack_age_seconds",
            "settlement_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name))
                if field_name == "settlement_window_seconds"
                else _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("pending_ack", self.pending_ack)
        _require_bool("manual_review_required", self.manual_review_required)
        object.__setattr__(
            self,
            "freshness_ratio",
            _require_ratio_decimal("freshness_ratio", self.freshness_ratio),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("outcome resolution evidence readiness row", self)
        require_paper_only_flags("outcome resolution evidence readiness row", self)


@dataclass(frozen=True)
class OutcomeResolutionEvidenceReadinessReport:
    config_version: str
    report_band: str
    reason_codes: tuple[str, ...]
    item_count: Decimal
    ready_count: Decimal
    attention_count: Decimal
    blocker_count: Decimal
    readiness_ratio: Decimal
    max_evidence_quorum_gap: Decimal
    max_pending_ack_age_seconds: Decimal
    max_last_checked_age_seconds: Decimal
    rows: tuple[OutcomeResolutionEvidenceReadinessRow, ...]
    inputs: tuple[OutcomeResolutionEvidenceReadinessInput, ...]
    public_payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        _require_band("report_band", self.report_band)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        for field_name in (
            "item_count",
            "ready_count",
            "attention_count",
            "blocker_count",
            "max_evidence_quorum_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pending_ack_age_seconds",
            "max_last_checked_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "readiness_ratio",
            _require_ratio_decimal("readiness_ratio", self.readiness_ratio),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "inputs", _normalize_inputs(self.inputs))
        _require_digest("public_payload_digest", self.public_payload_digest)
        _validate_report(self)
        reject_unsafe_surface_fields("outcome resolution evidence readiness report", self)
        require_paper_only_flags("outcome resolution evidence readiness report", self)


def build_outcome_resolution_evidence_readiness_report(
    items: tuple[OutcomeResolutionEvidenceReadinessInput, ...]
    | list[OutcomeResolutionEvidenceReadinessInput],
    *,
    config: OutcomeResolutionEvidenceReadinessConfig,
) -> OutcomeResolutionEvidenceReadinessReport:
    if type(config) is not OutcomeResolutionEvidenceReadinessConfig:
        raise ValueError("config must be an OutcomeResolutionEvidenceReadinessConfig")
    require_paper_only_flags("config", config)
    input_items = _normalize_inputs(items)
    rows = tuple(
        sorted(
            (_row_from_input(item, config) for item in input_items),
            key=_row_sort_key,
        ),
    )
    report_without_digest = OutcomeResolutionEvidenceReadinessReport(
        config_version=config.config_version,
        report_band=_report_band(rows),
        reason_codes=_report_reason_codes(rows),
        item_count=_count(len(rows)),
        ready_count=_row_band_count(rows, "ready"),
        attention_count=_row_band_count(rows, "attention"),
        blocker_count=_row_band_count(rows, "blocker"),
        readiness_ratio=_safe_ratio(_row_band_count(rows, "ready"), _count(len(rows))),
        max_evidence_quorum_gap=_max_decimal(
            tuple(row.evidence_quorum_gap for row in rows),
        ),
        max_pending_ack_age_seconds=_max_decimal(
            tuple(row.pending_ack_age_seconds for row in rows),
        ),
        max_last_checked_age_seconds=_max_decimal(
            tuple(row.last_checked_age_seconds for row in rows),
        ),
        rows=rows,
        inputs=tuple(sorted(input_items, key=_input_sort_key)),
        public_payload_digest="0" * 64,
    )
    digest = _public_payload_digest(report_without_digest)
    return OutcomeResolutionEvidenceReadinessReport(
        config_version=report_without_digest.config_version,
        report_band=report_without_digest.report_band,
        reason_codes=report_without_digest.reason_codes,
        item_count=report_without_digest.item_count,
        ready_count=report_without_digest.ready_count,
        attention_count=report_without_digest.attention_count,
        blocker_count=report_without_digest.blocker_count,
        readiness_ratio=report_without_digest.readiness_ratio,
        max_evidence_quorum_gap=report_without_digest.max_evidence_quorum_gap,
        max_pending_ack_age_seconds=report_without_digest.max_pending_ack_age_seconds,
        max_last_checked_age_seconds=report_without_digest.max_last_checked_age_seconds,
        rows=report_without_digest.rows,
        inputs=report_without_digest.inputs,
        public_payload_digest=digest,
    )


def outcome_resolution_evidence_readiness_payload(
    report: OutcomeResolutionEvidenceReadinessReport,
) -> dict[str, Any]:
    if type(report) is not OutcomeResolutionEvidenceReadinessReport:
        raise ValueError("report must be an OutcomeResolutionEvidenceReadinessReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("outcome resolution evidence readiness report", report)
    return json_ready_no_floats(report)


def _row_from_input(
    item: OutcomeResolutionEvidenceReadinessInput,
    config: OutcomeResolutionEvidenceReadinessConfig,
) -> OutcomeResolutionEvidenceReadinessRow:
    evidence_quorum_gap = _nonnegative_difference(
        config.required_resolution_source_count,
        item.resolution_source_count,
    )
    official_source_gap = _nonnegative_difference(
        config.required_official_source_count,
        item.official_source_count,
    )
    freshness_ratio = _freshness_ratio(
        item.last_checked_age_seconds,
        item.settlement_window_seconds,
    )
    band = _row_band(
        evidence_quorum_gap=evidence_quorum_gap,
        official_source_gap=official_source_gap,
        conflicting_source_count=item.conflicting_source_count,
        pending_ack=item.pending_ack,
        manual_review_required=item.manual_review_required,
        freshness_ratio=freshness_ratio,
        config=config,
    )
    return OutcomeResolutionEvidenceReadinessRow(
        event_id=item.event_id,
        outcome_id=item.outcome_id,
        band=band,
        reason_codes=_row_reason_codes(
            band=band,
            evidence_quorum_gap=evidence_quorum_gap,
            official_source_gap=official_source_gap,
            conflicting_source_count=item.conflicting_source_count,
            pending_ack=item.pending_ack,
            manual_review_required=item.manual_review_required,
            freshness_ratio=freshness_ratio,
            config=config,
        ),
        resolution_source_count=item.resolution_source_count,
        official_source_count=item.official_source_count,
        conflicting_source_count=item.conflicting_source_count,
        evidence_quorum_gap=evidence_quorum_gap,
        official_source_gap=official_source_gap,
        last_checked_age_seconds=item.last_checked_age_seconds,
        pending_ack=item.pending_ack,
        pending_ack_age_seconds=(
            item.last_checked_age_seconds if item.pending_ack else ZERO
        ),
        manual_review_required=item.manual_review_required,
        settlement_window_seconds=item.settlement_window_seconds,
        freshness_ratio=freshness_ratio,
    )


def _row_band(
    *,
    evidence_quorum_gap: Decimal,
    official_source_gap: Decimal,
    conflicting_source_count: Decimal,
    pending_ack: bool,
    manual_review_required: bool,
    freshness_ratio: Decimal,
    config: OutcomeResolutionEvidenceReadinessConfig,
) -> str:
    if (
        conflicting_source_count > ZERO
        or evidence_quorum_gap > ZERO
        or official_source_gap > ZERO
        or manual_review_required
        or freshness_ratio >= config.freshness_blocker_ratio
    ):
        return "blocker"
    if pending_ack or freshness_ratio >= config.freshness_warning_ratio:
        return "attention"
    return "ready"


def _row_reason_codes(
    *,
    band: str,
    evidence_quorum_gap: Decimal,
    official_source_gap: Decimal,
    conflicting_source_count: Decimal,
    pending_ack: bool,
    manual_review_required: bool,
    freshness_ratio: Decimal,
    config: OutcomeResolutionEvidenceReadinessConfig,
) -> tuple[str, ...]:
    codes = [_band_reason(band)]
    if conflicting_source_count > ZERO:
        codes.append(CONFLICTING_SOURCES_REASON)
    if evidence_quorum_gap > ZERO or official_source_gap > ZERO:
        codes.append(QUORUM_GAP_REASON)
    if pending_ack:
        codes.append(PENDING_ACK_REASON)
    if manual_review_required:
        codes.append(MANUAL_REVIEW_REASON)
    if freshness_ratio >= config.freshness_warning_ratio:
        codes.append(STALE_CHECK_REASON)
    return tuple(codes)


def _report_band(rows: tuple[OutcomeResolutionEvidenceReadinessRow, ...]) -> str:
    if any(row.band == "blocker" for row in rows):
        return "blocker"
    if any(row.band == "attention" for row in rows):
        return "attention"
    return "ready"


def _report_reason_codes(rows: tuple[OutcomeResolutionEvidenceReadinessRow, ...]) -> tuple[str, ...]:
    band = _report_band(rows)
    codes = [_band_reason(band)]
    if any(row.conflicting_source_count > ZERO for row in rows):
        codes.append(CONFLICTING_SOURCES_REASON)
    if any(row.evidence_quorum_gap > ZERO or row.official_source_gap > ZERO for row in rows):
        codes.append(QUORUM_GAP_REASON)
    if any(row.pending_ack for row in rows):
        codes.append(PENDING_ACK_REASON)
    if any(row.manual_review_required for row in rows):
        codes.append(MANUAL_REVIEW_REASON)
    if any(STALE_CHECK_REASON in row.reason_codes for row in rows):
        codes.append(STALE_CHECK_REASON)
    return tuple(codes)


def _band_reason(band: str) -> str:
    if band == "ready":
        return READY_REASON
    if band == "attention":
        return ATTENTION_REASON
    if band == "blocker":
        return BLOCKER_REASON
    raise ValueError("band is invalid")


def _normalize_inputs(
    items: tuple[OutcomeResolutionEvidenceReadinessInput, ...]
    | list[OutcomeResolutionEvidenceReadinessInput],
) -> tuple[OutcomeResolutionEvidenceReadinessInput, ...]:
    if type(items) not in (tuple, list):
        raise ValueError("items must be a tuple or list")
    normalized = tuple(items)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not OutcomeResolutionEvidenceReadinessInput:
            raise ValueError("items must contain OutcomeResolutionEvidenceReadinessInput values")
        require_paper_only_flags("item", item)
        key = (item.event_id, item.outcome_id)
        if key in seen:
            raise ValueError("items must not contain duplicate event_id outcome_id pairs")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: tuple[OutcomeResolutionEvidenceReadinessRow, ...]
    | list[OutcomeResolutionEvidenceReadinessRow],
) -> tuple[OutcomeResolutionEvidenceReadinessRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not OutcomeResolutionEvidenceReadinessRow:
            raise ValueError("rows must contain OutcomeResolutionEvidenceReadinessRow values")
        require_paper_only_flags("row", row)
        key = (row.event_id, row.outcome_id)
        if key in seen:
            raise ValueError("rows must not contain duplicate event_id outcome_id pairs")
        seen.add(key)
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    for code in reason_codes:
        _require_public_string("reason_code", code)
    return reason_codes


def _row_sort_key(row: OutcomeResolutionEvidenceReadinessRow) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        BAND_RANK[row.band],
        -row.evidence_quorum_gap,
        -row.pending_ack_age_seconds,
        row.event_id,
        row.outcome_id,
    )


def _input_sort_key(item: OutcomeResolutionEvidenceReadinessInput) -> tuple[str, str]:
    return (item.event_id, item.outcome_id)


def _row_band_count(
    rows: tuple[OutcomeResolutionEvidenceReadinessRow, ...],
    band: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.band == band))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _freshness_ratio(age_seconds: Decimal, settlement_window_seconds: Decimal) -> Decimal:
    ratio = _safe_ratio(age_seconds, settlement_window_seconds)
    if ratio > ONE:
        return ONE
    return ratio


def _nonnegative_difference(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = first - second
    if value < ZERO:
        return ZERO
    return value.quantize(QUANT)


def _validate_input_counts(item: OutcomeResolutionEvidenceReadinessInput) -> None:
    if item.official_source_count > item.resolution_source_count:
        raise ValueError("official_source_count cannot exceed resolution_source_count")
    if item.conflicting_source_count > item.resolution_source_count:
        raise ValueError("conflicting_source_count cannot exceed resolution_source_count")


def _validate_row(row: OutcomeResolutionEvidenceReadinessRow) -> None:
    _validate_input_counts(
        OutcomeResolutionEvidenceReadinessInput(
            event_id=row.event_id,
            outcome_id=row.outcome_id,
            resolution_source_count=row.resolution_source_count,
            official_source_count=row.official_source_count,
            conflicting_source_count=row.conflicting_source_count,
            last_checked_age_seconds=row.last_checked_age_seconds,
            pending_ack=row.pending_ack,
            manual_review_required=row.manual_review_required,
            settlement_window_seconds=row.settlement_window_seconds,
        ),
    )
    if row.pending_ack_age_seconds != (
        row.last_checked_age_seconds if row.pending_ack else ZERO
    ):
        raise ValueError("pending_ack_age_seconds must match pending_ack state")
    if row.freshness_ratio != _freshness_ratio(
        row.last_checked_age_seconds,
        row.settlement_window_seconds,
    ):
        raise ValueError("freshness_ratio must match age and settlement window")
    if row.reason_codes[0] != _band_reason(row.band):
        raise ValueError("reason_codes must start with band reason")


def _validate_report(report: OutcomeResolutionEvidenceReadinessReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.ready_count != _row_band_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.attention_count != _row_band_count(report.rows, "attention"):
        raise ValueError("attention_count must match rows")
    if report.blocker_count != _row_band_count(report.rows, "blocker"):
        raise ValueError("blocker_count must match rows")
    if report.readiness_ratio != _safe_ratio(report.ready_count, report.item_count):
        raise ValueError("readiness_ratio must match ready_count and item_count")
    if report.max_evidence_quorum_gap != _max_decimal(
        tuple(row.evidence_quorum_gap for row in report.rows),
    ):
        raise ValueError("max_evidence_quorum_gap must match rows")
    if report.max_pending_ack_age_seconds != _max_decimal(
        tuple(row.pending_ack_age_seconds for row in report.rows),
    ):
        raise ValueError("max_pending_ack_age_seconds must match rows")
    if report.max_last_checked_age_seconds != _max_decimal(
        tuple(row.last_checked_age_seconds for row in report.rows),
    ):
        raise ValueError("max_last_checked_age_seconds must match rows")
    if report.report_band != _report_band(report.rows):
        raise ValueError("report_band must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if len(report.inputs) != len(report.rows):
        raise ValueError("inputs must match rows")


def _public_payload_digest(report: OutcomeResolutionEvidenceReadinessReport) -> str:
    payload = json_ready_no_floats(report)
    payload["public_payload_digest"] = "0" * 64
    encoded = dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_public_string(name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_band(name: str, value: str) -> None:
    if value not in BANDS:
        raise ValueError(f"{name} must be one of {BANDS}")


def _require_bool(name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_integer_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer Decimal")
    return normalized


def _require_positive_integer_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_positive_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer Decimal")
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be less than or equal to 1")
    return normalized


def _require_digest(name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a 64 character hex digest")
    if set(value) - set("0123456789abcdef"):
        raise ValueError(f"{name} must be a 64 character hex digest")


__all__ = (
    "DEFAULT_OUTCOME_RESOLUTION_EVIDENCE_READINESS_REPORT_CONFIG_VERSION",
    "OutcomeResolutionEvidenceReadinessConfig",
    "OutcomeResolutionEvidenceReadinessInput",
    "OutcomeResolutionEvidenceReadinessReport",
    "OutcomeResolutionEvidenceReadinessRow",
    "build_outcome_resolution_evidence_readiness_report",
    "outcome_resolution_evidence_readiness_payload",
)
