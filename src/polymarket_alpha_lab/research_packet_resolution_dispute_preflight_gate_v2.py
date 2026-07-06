"""Pure Phase 1 research packet resolution dispute preflight gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-packet-resolution-dispute-preflight-gate-v2"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")
STATUSES = ("pass", "review", "block")
INPUT_REASON_CODES = (
    "official_resolution_source_present",
    "official_resolution_source_missing",
    "resolution_language_clear",
    "ambiguous_resolution_language",
    "conflicting_resolution_evidence",
    "prior_resolution_dispute_history",
)
ROW_REASON_CODES = (
    "official_source_missing",
    "ambiguous_resolution_penalty_applied",
    "conflicting_resolution_evidence_penalty_applied",
    "dispute_history_penalty_applied",
    "preflight_pass",
    "preflight_review",
    "preflight_block",
)
REPORT_REASON_CODES = (
    "no_research_packets",
    "resolution_dispute_preflight_clear",
    "resolution_dispute_preflight_review_required",
    "resolution_dispute_preflight_block_recommended",
    "official_source_missing_detected",
    "ambiguous_resolution_detected",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class ResearchPacketResolutionDisputePreflightConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    ambiguous_resolution_penalty_weight: Decimal = Decimal("0.350000")
    missing_official_source_penalty: Decimal = Decimal("0.250000")
    contradiction_penalty_weight: Decimal = Decimal("0.250000")
    dispute_history_weight: Decimal = Decimal("0.150000")
    review_threshold: Decimal = Decimal("0.350000")
    block_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "ambiguous_resolution_penalty_weight",
            "missing_official_source_penalty",
            "contradiction_penalty_weight",
            "dispute_history_weight",
            "review_threshold",
            "block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.review_threshold > self.block_threshold:
            raise ValueError("review_threshold must not exceed block_threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketResolutionDisputePreflightInput:
    packet_id: str
    research_reference: str
    resolution_summary: str
    official_source_count: Decimal
    independent_source_count: Decimal
    ambiguity_score: Decimal
    contradiction_score: Decimal
    dispute_history_rate: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("packet_id", self.packet_id)
        _require_safe_canonical_string("research_reference", self.research_reference)
        _require_safe_canonical_string("resolution_summary", self.resolution_summary)
        object.__setattr__(
            self,
            "official_source_count",
            _normalize_count_decimal("official_source_count", self.official_source_count),
        )
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_count_decimal(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        for field_name in (
            "ambiguity_score",
            "contradiction_score",
            "dispute_history_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _validate_input_reason_codes(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchPacketResolutionDisputePreflightRow:
    packet_id: str
    research_reference: str
    resolution_summary: str
    official_source_count: Decimal
    independent_source_count: Decimal
    official_source_missing: bool
    ambiguity_score: Decimal
    contradiction_score: Decimal
    dispute_history_rate: Decimal
    ambiguity_penalty: Decimal
    missing_official_source_penalty: Decimal
    contradiction_penalty: Decimal
    dispute_history_penalty: Decimal
    dispute_preflight_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("packet_id", self.packet_id)
        _require_safe_canonical_string("research_reference", self.research_reference)
        _require_safe_canonical_string("resolution_summary", self.resolution_summary)
        object.__setattr__(
            self,
            "official_source_count",
            _normalize_count_decimal("official_source_count", self.official_source_count),
        )
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_count_decimal(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        if type(self.official_source_missing) is not bool:
            raise ValueError("official_source_missing must be a bool")
        for field_name in (
            "ambiguity_score",
            "contradiction_score",
            "dispute_history_rate",
            "ambiguity_penalty",
            "missing_official_source_penalty",
            "contradiction_penalty",
            "dispute_history_penalty",
            "dispute_preflight_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.status) is not str or self.status not in STATUSES:
            raise ValueError("status must be pass, review, or block")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _set_or_validate_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchPacketResolutionDisputePreflightReport:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    review_count: Decimal
    block_count: Decimal
    missing_official_source_count: Decimal
    ambiguous_resolution_count: Decimal
    max_dispute_preflight_score: Decimal
    average_dispute_preflight_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketResolutionDisputePreflightRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "pass_count",
            "review_count",
            "block_count",
            "missing_official_source_count",
            "ambiguous_resolution_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_dispute_preflight_score",
            "average_dispute_preflight_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _set_or_validate_digest(self)


def build_research_packet_resolution_dispute_preflight_gate_v2(
    inputs: object,
    *,
    config: ResearchPacketResolutionDisputePreflightConfig,
    generated_at: datetime,
) -> ResearchPacketResolutionDisputePreflightReport:
    if type(config) is not ResearchPacketResolutionDisputePreflightConfig:
        raise ValueError(
            "config must be a ResearchPacketResolutionDisputePreflightConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    checked_inputs = _normalize_inputs(inputs)
    rows = tuple(_row_for_input(row, config) for row in checked_inputs)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.dispute_preflight_score,
                row.packet_id,
                row.research_reference,
            ),
        ),
    )
    packet_count = _decimal_count(len(sorted_rows))
    pass_count = _decimal_count(sum(row.status == "pass" for row in sorted_rows))
    review_count = _decimal_count(sum(row.status == "review" for row in sorted_rows))
    block_count = _decimal_count(sum(row.status == "block" for row in sorted_rows))
    missing_count = _decimal_count(
        sum(row.official_source_missing for row in sorted_rows),
    )
    ambiguous_count = _decimal_count(
        sum(row.ambiguity_score > ZERO for row in sorted_rows),
    )
    max_score = (
        max((row.dispute_preflight_score for row in sorted_rows), default=ZERO)
        if sorted_rows
        else ZERO
    )
    average_score = _average_score(sorted_rows)
    return ResearchPacketResolutionDisputePreflightReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        packet_count=packet_count,
        pass_count=pass_count,
        review_count=review_count,
        block_count=block_count,
        missing_official_source_count=missing_count,
        ambiguous_resolution_count=ambiguous_count,
        max_dispute_preflight_score=max_score,
        average_dispute_preflight_score=average_score,
        reason_codes=_report_reason_codes(
            packet_count=packet_count,
            review_count=review_count,
            block_count=block_count,
            missing_official_source_count=missing_count,
            ambiguous_resolution_count=ambiguous_count,
        ),
        rows=sorted_rows,
    )


def research_packet_resolution_dispute_preflight_gate_v2_payload(
    report: ResearchPacketResolutionDisputePreflightReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketResolutionDisputePreflightReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchPacketResolutionDisputePreflightReport",
        )
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


def _normalize_inputs(
    inputs: object,
) -> tuple[ResearchPacketResolutionDisputePreflightInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    checked: list[ResearchPacketResolutionDisputePreflightInput] = []
    seen: set[str] = set()
    for row in inputs:
        if type(row) is not ResearchPacketResolutionDisputePreflightInput:
            raise ValueError(
                "inputs items must be ResearchPacketResolutionDisputePreflightInput",
            )
        _require_hard_flags("input", row)
        if row.packet_id in seen:
            raise ValueError("inputs must not contain duplicate packet_id values")
        seen.add(row.packet_id)
        checked.append(row)
    return tuple(checked)


def _row_for_input(
    row: ResearchPacketResolutionDisputePreflightInput,
    config: ResearchPacketResolutionDisputePreflightConfig,
) -> ResearchPacketResolutionDisputePreflightRow:
    official_source_missing = row.official_source_count == ZERO
    ambiguity_penalty = _product_ratio(
        row.ambiguity_score,
        config.ambiguous_resolution_penalty_weight,
    )
    missing_penalty = (
        config.missing_official_source_penalty if official_source_missing else ZERO
    )
    contradiction_penalty = _product_ratio(
        row.contradiction_score,
        config.contradiction_penalty_weight,
    )
    dispute_history_penalty = _product_ratio(
        row.dispute_history_rate,
        config.dispute_history_weight,
    )
    dispute_preflight_score = _clamped_ratio(
        ambiguity_penalty
        + missing_penalty
        + contradiction_penalty
        + dispute_history_penalty,
    )
    status = _status_for_score(dispute_preflight_score, config)
    return ResearchPacketResolutionDisputePreflightRow(
        packet_id=row.packet_id,
        research_reference=row.research_reference,
        resolution_summary=row.resolution_summary,
        official_source_count=row.official_source_count,
        independent_source_count=row.independent_source_count,
        official_source_missing=official_source_missing,
        ambiguity_score=row.ambiguity_score,
        contradiction_score=row.contradiction_score,
        dispute_history_rate=row.dispute_history_rate,
        ambiguity_penalty=ambiguity_penalty,
        missing_official_source_penalty=missing_penalty,
        contradiction_penalty=contradiction_penalty,
        dispute_history_penalty=dispute_history_penalty,
        dispute_preflight_score=dispute_preflight_score,
        status=status,
        reason_codes=_row_reason_codes(
            official_source_missing=official_source_missing,
            ambiguity_penalty=ambiguity_penalty,
            contradiction_penalty=contradiction_penalty,
            dispute_history_penalty=dispute_history_penalty,
            status=status,
        ),
    )


def _row_reason_codes(
    *,
    official_source_missing: bool,
    ambiguity_penalty: Decimal,
    contradiction_penalty: Decimal,
    dispute_history_penalty: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_source_missing:
        reason_codes.append("official_source_missing")
    if ambiguity_penalty > ZERO:
        reason_codes.append("ambiguous_resolution_penalty_applied")
    if contradiction_penalty > ZERO:
        reason_codes.append("conflicting_resolution_evidence_penalty_applied")
    if dispute_history_penalty > ZERO:
        reason_codes.append("dispute_history_penalty_applied")
    reason_codes.append(f"preflight_{status}")
    return tuple(reason_codes)


def _report_reason_codes(
    *,
    packet_count: Decimal,
    review_count: Decimal,
    block_count: Decimal,
    missing_official_source_count: Decimal,
    ambiguous_resolution_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if packet_count == ZERO:
        reason_codes.append("no_research_packets")
    if block_count > ZERO:
        reason_codes.append("resolution_dispute_preflight_block_recommended")
    if review_count > ZERO:
        reason_codes.append("resolution_dispute_preflight_review_required")
    if missing_official_source_count > ZERO:
        reason_codes.append("official_source_missing_detected")
    if ambiguous_resolution_count > ZERO:
        reason_codes.append("ambiguous_resolution_detected")
    if not reason_codes:
        reason_codes.append("resolution_dispute_preflight_clear")
    return tuple(reason_codes)


def _validate_input_reason_codes(
    row: ResearchPacketResolutionDisputePreflightInput,
) -> None:
    expected: list[str] = []
    expected.append(
        "official_resolution_source_missing"
        if row.official_source_count == ZERO
        else "official_resolution_source_present",
    )
    if row.ambiguity_score > ZERO:
        expected.append("ambiguous_resolution_language")
    else:
        expected.append("resolution_language_clear")
    if row.contradiction_score > ZERO:
        expected.append("conflicting_resolution_evidence")
    if row.dispute_history_rate > ZERO:
        expected.append("prior_resolution_dispute_history")
    if row.reason_codes != tuple(expected):
        raise ValueError("reason_codes must match input dispute preflight features")


def _validate_row_consistency(
    row: ResearchPacketResolutionDisputePreflightRow,
) -> None:
    if row.official_source_missing != (row.official_source_count == ZERO):
        raise ValueError("official_source_missing must match official_source_count")
    expected_score = _clamped_ratio(
        row.ambiguity_penalty
        + row.missing_official_source_penalty
        + row.contradiction_penalty
        + row.dispute_history_penalty,
    )
    if row.dispute_preflight_score != expected_score:
        raise ValueError("dispute_preflight_score must match component penalties")
    if f"preflight_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(
    report: ResearchPacketResolutionDisputePreflightReport,
) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(sum(row.status == "pass" for row in report.rows)):
        raise ValueError("pass_count must match rows")
    if report.review_count != _decimal_count(
        sum(row.status == "review" for row in report.rows),
    ):
        raise ValueError("review_count must match rows")
    if report.block_count != _decimal_count(sum(row.status == "block" for row in report.rows)):
        raise ValueError("block_count must match rows")
    if report.missing_official_source_count != _decimal_count(
        sum(row.official_source_missing for row in report.rows),
    ):
        raise ValueError("missing_official_source_count must match rows")
    if report.ambiguous_resolution_count != _decimal_count(
        sum(row.ambiguity_score > ZERO for row in report.rows),
    ):
        raise ValueError("ambiguous_resolution_count must match rows")
    if report.max_dispute_preflight_score != (
        max((row.dispute_preflight_score for row in report.rows), default=ZERO)
        if report.rows
        else ZERO
    ):
        raise ValueError("max_dispute_preflight_score must match rows")
    if report.average_dispute_preflight_score != _average_score(report.rows):
        raise ValueError("average_dispute_preflight_score must match rows")
    if report.reason_codes != _report_reason_codes(
        packet_count=report.packet_count,
        review_count=report.review_count,
        block_count=report.block_count,
        missing_official_source_count=report.missing_official_source_count,
        ambiguous_resolution_count=report.ambiguous_resolution_count,
    ):
        raise ValueError("reason_codes must match report status")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketResolutionDisputePreflightRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    checked = tuple(rows)
    seen: set[str] = set()
    expected = tuple(
        sorted(
            checked,
            key=lambda row: (
                -row.dispute_preflight_score,
                row.packet_id,
                row.research_reference,
            ),
        ),
    )
    if checked != expected:
        raise ValueError("rows must be sorted by dispute preflight severity")
    for row in checked:
        if type(row) is not ResearchPacketResolutionDisputePreflightRow:
            raise ValueError(
                "rows items must be ResearchPacketResolutionDisputePreflightRow",
            )
        _require_hard_flags("row", row)
        if row.packet_id in seen:
            raise ValueError("rows packet_id values must be unique")
        seen.add(row.packet_id)
    return checked


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        value,
        INPUT_REASON_CODES,
    )


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, ROW_REASON_CODES)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, REPORT_REASON_CODES)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"{field_name} contains an unsupported reason")
        _reject_unsafe_public_string(field_name, reason_code)
    return reason_codes


def _status_for_score(
    score: Decimal,
    config: ResearchPacketResolutionDisputePreflightConfig,
) -> str:
    if score >= config.block_threshold:
        return "block"
    if score >= config.review_threshold:
        return "review"
    return "pass"


def _average_score(
    rows: tuple[ResearchPacketResolutionDisputePreflightRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    total = sum((row.dispute_preflight_score for row in rows), ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return (total / _decimal_count(len(rows))).quantize(QUANTUM)


def _product_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _normalize_decimal("ratio", value).quantize(QUANTUM)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value).quantize(QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    integral = normalized.to_integral_value()
    if normalized != integral:
        raise ValueError(f"{field_name} must be integral")
    return integral


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return +value
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be usable") from exc


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safe_canonical_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_string(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _set_or_validate_digest(value: object) -> None:
    supplied = getattr(value, "derived_validation_digest")
    if type(supplied) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if supplied and supplied != expected:
        raise ValueError("derived_validation_digest mismatch")
    object.__setattr__(value, "derived_validation_digest", expected)


def _derived_digest(value: object) -> str:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("derived_validation_digest requires a dataclass value")
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    ready = _json_ready(payload)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
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
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if value is None:
        return None
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
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
            _reject_unsafe_public_string("public key", key)
            if key in SAFETY_FLAG_NAMES and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item, path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_string(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "ResearchPacketResolutionDisputePreflightConfig",
    "ResearchPacketResolutionDisputePreflightInput",
    "ResearchPacketResolutionDisputePreflightRow",
    "ResearchPacketResolutionDisputePreflightReport",
    "build_research_packet_resolution_dispute_preflight_gate_v2",
    "research_packet_resolution_dispute_preflight_gate_v2_payload",
)
