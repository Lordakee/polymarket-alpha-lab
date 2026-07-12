"""Phase 1 probability event resolution rule evidence gap report."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import json
from hashlib import sha256
from typing import Any


DEFAULT_PROBABILITY_EVENT_RESOLUTION_RULE_EVIDENCE_GAP_CONFIG_VERSION = (
    "probability-event-resolution-rule-evidence-gap-report-v0"
)
READINESS_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "resolution_rule_text_missing",
    "resolution_rule_text_present",
    "official_resolution_source_missing",
    "official_resolution_source_present",
    "rule_hash_missing",
    "rule_hash_present",
    "resolution_rule_ambiguity_present",
    "resolution_rule_unambiguous",
    "resolution_source_refresh_stale",
    "resolution_source_fresh",
)
REPORT_REASON_CODES = (
    "resolution_rule_evidence_ready",
    "resolution_rule_ambiguity_present",
    "resolution_rule_text_missing",
    "official_resolution_source_missing",
    "rule_hash_missing",
    "resolution_source_refresh_stale",
    "manual_resolution_rule_review_required",
)

COUNT_QUANTUM = Decimal("1")
HOURS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_HOURS = Decimal("0.000000")
STALE_REFRESH_AGE_HOURS = Decimal("48.000000")
STATUS_WEIGHT = {
    "pass": Decimal("0"),
    "watch": Decimal("1"),
    "blocked": Decimal("2"),
}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class ProbabilityEventResolutionRuleEvidenceGapConfig:
    config_version: str = DEFAULT_PROBABILITY_EVENT_RESOLUTION_RULE_EVIDENCE_GAP_CONFIG_VERSION
    stale_refresh_age_hours: Decimal = STALE_REFRESH_AGE_HOURS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_refresh_age_hours",
            _normalize_nonnegative_hours(
                "stale_refresh_age_hours",
                self.stale_refresh_age_hours,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventResolutionRuleEvidenceGapInput:
    event_id: str
    resolution_rule_text_present: bool
    official_resolution_source_present: bool
    rule_hash_present: bool
    rule_ambiguity_count: Decimal
    source_refresh_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_id("event_id", self.event_id)
        for field_name in (
            "resolution_rule_text_present",
            "official_resolution_source_present",
            "rule_hash_present",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "rule_ambiguity_count",
            _normalize_nonnegative_count(
                "rule_ambiguity_count",
                self.rule_ambiguity_count,
            ),
        )
        object.__setattr__(
            self,
            "source_refresh_age_hours",
            _normalize_nonnegative_hours(
                "source_refresh_age_hours",
                self.source_refresh_age_hours,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventResolutionRuleEvidenceGapRow:
    event_id: str
    resolution_rule_text_present: bool
    official_resolution_source_present: bool
    rule_hash_present: bool
    rule_ambiguity_count: Decimal
    source_refresh_age_hours: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_id("event_id", self.event_id)
        for field_name in (
            "resolution_rule_text_present",
            "official_resolution_source_present",
            "rule_hash_present",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "rule_ambiguity_count",
            _normalize_nonnegative_count(
                "rule_ambiguity_count",
                self.rule_ambiguity_count,
            ),
        )
        object.__setattr__(
            self,
            "source_refresh_age_hours",
            _normalize_nonnegative_hours(
                "source_refresh_age_hours",
                self.source_refresh_age_hours,
            ),
        )
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_canonical_string("manual_next_step", self.manual_next_step)
        _validate_row(self)
        object.__setattr__(self, "derived_validation_digest", _row_digest(self))
        _require_digest_shape("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ProbabilityEventResolutionRuleEvidenceGapReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    rows: tuple[ProbabilityEventResolutionRuleEvidenceGapRow, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_event_count",
            "watch_event_count",
            "blocked_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_canonical_string("manual_next_step", self.manual_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        object.__setattr__(self, "derived_validation_digest", _report_digest(self))
        _require_digest_shape("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)


def build_probability_event_resolution_rule_evidence_gap_report(
    inputs: list[ProbabilityEventResolutionRuleEvidenceGapInput]
    | tuple[ProbabilityEventResolutionRuleEvidenceGapInput, ...],
    *,
    config: ProbabilityEventResolutionRuleEvidenceGapConfig,
    generated_at: datetime,
) -> ProbabilityEventResolutionRuleEvidenceGapReport:
    if type(config) is not ProbabilityEventResolutionRuleEvidenceGapConfig:
        raise ValueError(
            "config must be a ProbabilityEventResolutionRuleEvidenceGapConfig",
        )
    _require_hard_flags("config", config)
    rows = tuple(_row_from_input(row, config) for row in _normalize_inputs(inputs))
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return ProbabilityEventResolutionRuleEvidenceGapReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        event_count=_count(len(sorted_rows)),
        pass_event_count=_status_count(sorted_rows, "pass"),
        watch_event_count=_status_count(sorted_rows, "watch"),
        blocked_event_count=_status_count(sorted_rows, "blocked"),
        readiness_status=_status_rollup(tuple(row.readiness_status for row in sorted_rows)),
        reason_codes=_report_reason_codes(sorted_rows),
        manual_next_step=_report_manual_next_step(sorted_rows),
        rows=sorted_rows,
    )


def probability_event_resolution_rule_evidence_gap_report_payload(
    report: ProbabilityEventResolutionRuleEvidenceGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ProbabilityEventResolutionRuleEvidenceGapReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        _require_report_digest(report)
        _reject_unsafe_public_value("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_value("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ProbabilityEventResolutionRuleEvidenceGapReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_value("payload", payload)
    _validate_payload_digest(payload)
    return payload


class _DictFlags:
    def __init__(self, value: dict[str, Any]) -> None:
        self._value = value

    @property
    def paper_only(self) -> object:
        return self._value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self._value.get("report_only")

    @property
    def readonly(self) -> object:
        return self._value.get("readonly")


def _normalize_inputs(
    inputs: list[ProbabilityEventResolutionRuleEvidenceGapInput]
    | tuple[ProbabilityEventResolutionRuleEvidenceGapInput, ...],
) -> tuple[ProbabilityEventResolutionRuleEvidenceGapInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ProbabilityEventResolutionRuleEvidenceGapInput:
            raise ValueError(
                "inputs must contain ProbabilityEventResolutionRuleEvidenceGapInput values",
            )
        _require_hard_flags("input", row)
        if row.event_id in seen:
            raise ValueError("inputs must not contain duplicate event_id values")
        seen.add(row.event_id)
    return rows


def _row_from_input(
    row: ProbabilityEventResolutionRuleEvidenceGapInput,
    config: ProbabilityEventResolutionRuleEvidenceGapConfig,
) -> ProbabilityEventResolutionRuleEvidenceGapRow:
    return ProbabilityEventResolutionRuleEvidenceGapRow(
        event_id=row.event_id,
        resolution_rule_text_present=row.resolution_rule_text_present,
        official_resolution_source_present=row.official_resolution_source_present,
        rule_hash_present=row.rule_hash_present,
        rule_ambiguity_count=row.rule_ambiguity_count,
        source_refresh_age_hours=row.source_refresh_age_hours,
        readiness_status=_row_status(row, config),
        reason_codes=_row_reason_codes(row, config),
        manual_next_step=_row_manual_next_step(row, config),
    )


def _row_status(
    row: ProbabilityEventResolutionRuleEvidenceGapInput,
    config: ProbabilityEventResolutionRuleEvidenceGapConfig,
) -> str:
    if (
        not row.resolution_rule_text_present
        or not row.official_resolution_source_present
        or not row.rule_hash_present
        or row.rule_ambiguity_count > ZERO_COUNT
    ):
        return "blocked"
    if row.source_refresh_age_hours > config.stale_refresh_age_hours:
        return "watch"
    return "pass"


def _row_reason_codes(
    row: ProbabilityEventResolutionRuleEvidenceGapInput,
    config: ProbabilityEventResolutionRuleEvidenceGapConfig,
) -> tuple[str, ...]:
    codes = []
    codes.append(
        "resolution_rule_text_present"
        if row.resolution_rule_text_present
        else "resolution_rule_text_missing",
    )
    codes.append(
        "official_resolution_source_present"
        if row.official_resolution_source_present
        else "official_resolution_source_missing",
    )
    codes.append("rule_hash_present" if row.rule_hash_present else "rule_hash_missing")
    codes.append(
        "resolution_rule_ambiguity_present"
        if row.rule_ambiguity_count > ZERO_COUNT
        else "resolution_rule_unambiguous",
    )
    codes.append(
        "resolution_source_refresh_stale"
        if row.source_refresh_age_hours > config.stale_refresh_age_hours
        else "resolution_source_fresh",
    )
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _row_manual_next_step(
    row: ProbabilityEventResolutionRuleEvidenceGapInput,
    config: ProbabilityEventResolutionRuleEvidenceGapConfig,
) -> str:
    if not row.resolution_rule_text_present:
        return "attach_resolution_rule_text_before_probability_use"
    if not row.official_resolution_source_present:
        return "attach_official_resolution_source_before_probability_use"
    if not row.rule_hash_present:
        return "compute_rule_hash_before_probability_use"
    if row.rule_ambiguity_count > ZERO_COUNT:
        return "escalate_unclear_resolution_rule_before_probability_use"
    if row.source_refresh_age_hours > config.stale_refresh_age_hours:
        return "refresh_official_resolution_source_evidence"
    return "no_manual_resolution_rule_action_required"


def _report_reason_codes(
    rows: tuple[ProbabilityEventResolutionRuleEvidenceGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_rule_evidence_ready",)
    codes: list[str] = []
    if any(not row.resolution_rule_text_present for row in rows):
        codes.append("resolution_rule_text_missing")
    if any(not row.official_resolution_source_present for row in rows):
        codes.append("official_resolution_source_missing")
    if any(not row.rule_hash_present for row in rows):
        codes.append("rule_hash_missing")
    if any(row.rule_ambiguity_count > ZERO_COUNT for row in rows):
        codes.append("resolution_rule_ambiguity_present")
    if any(row.reason_codes[-1] == "resolution_source_refresh_stale" for row in rows):
        codes.append("resolution_source_refresh_stale")
    if codes:
        codes.append("manual_resolution_rule_review_required")
    else:
        codes.append("resolution_rule_evidence_ready")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _report_manual_next_step(
    rows: tuple[ProbabilityEventResolutionRuleEvidenceGapRow, ...],
) -> str:
    if not rows:
        return "no_manual_resolution_rule_action_required"
    for step in (
        "attach_resolution_rule_text_before_probability_use",
        "escalate_unclear_resolution_rule_before_probability_use",
        "attach_official_resolution_source_before_probability_use",
        "compute_rule_hash_before_probability_use",
        "refresh_official_resolution_source_evidence",
    ):
        if any(row.manual_next_step == step for row in rows):
            return step
    return "no_manual_resolution_rule_action_required"


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ProbabilityEventResolutionRuleEvidenceGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _row_sort_key(
    row: ProbabilityEventResolutionRuleEvidenceGapRow,
) -> tuple[Decimal, str]:
    return (-STATUS_WEIGHT[row.readiness_status], row.event_id)


def _normalize_rows(
    value: object,
) -> tuple[ProbabilityEventResolutionRuleEvidenceGapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ProbabilityEventResolutionRuleEvidenceGapRow:
            raise ValueError(
                "rows must contain ProbabilityEventResolutionRuleEvidenceGapRow values",
            )
        _require_hard_flags("row", row)
        _require_row_digest(row)
        if row.event_id in seen:
            raise ValueError("rows must not contain duplicate event_id values")
        seen.add(row.event_id)
    return rows


def _validate_row(row: ProbabilityEventResolutionRuleEvidenceGapRow) -> None:
    input_row = ProbabilityEventResolutionRuleEvidenceGapInput(
        event_id=row.event_id,
        resolution_rule_text_present=row.resolution_rule_text_present,
        official_resolution_source_present=row.official_resolution_source_present,
        rule_hash_present=row.rule_hash_present,
        rule_ambiguity_count=row.rule_ambiguity_count,
        source_refresh_age_hours=row.source_refresh_age_hours,
    )
    config = ProbabilityEventResolutionRuleEvidenceGapConfig()
    if row.readiness_status != _row_status(input_row, config):
        raise ValueError("readiness_status must match evidence gaps")
    if row.reason_codes != _row_reason_codes(input_row, config):
        raise ValueError("reason_codes must match evidence gaps")
    if row.manual_next_step != _row_manual_next_step(input_row, config):
        raise ValueError("manual_next_step must match evidence gaps")


def _validate_report(report: ProbabilityEventResolutionRuleEvidenceGapReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_event_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_event_count must match rows")
    if report.watch_event_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_event_count must match rows")
    if report.blocked_event_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_event_count must match rows")
    if report.readiness_status != _status_rollup(
        tuple(row.readiness_status for row in report.rows),
    ):
        raise ValueError("readiness_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.manual_next_step != _report_manual_next_step(report.rows):
        raise ValueError("manual_next_step must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    for row in report.rows:
        _require_row_digest(row)


def _row_digest(row: ProbabilityEventResolutionRuleEvidenceGapRow) -> str:
    return _payload_digest(_payload_without_digest(_json_object(row)))


def _report_digest(report: ProbabilityEventResolutionRuleEvidenceGapReport) -> str:
    return _payload_digest(_payload_without_digest(_json_object(report)))


def _require_row_digest(row: ProbabilityEventResolutionRuleEvidenceGapRow) -> None:
    _require_digest_shape("derived_validation_digest", row.derived_validation_digest)
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _require_report_digest(report: ProbabilityEventResolutionRuleEvidenceGapReport) -> None:
    _require_digest_shape("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list in public payload")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        row_digest = row.get("derived_validation_digest")
        _require_digest_shape("derived_validation_digest", row_digest)
        if row_digest != _payload_digest(_payload_without_digest(row)):
            raise ValueError("derived_validation_digest must match row payload")
    report_digest = payload.get("derived_validation_digest")
    _require_digest_shape("derived_validation_digest", report_digest)
    if report_digest != _payload_digest(_payload_without_digest(payload)):
        raise ValueError("derived_validation_digest must match report payload")


def _json_object(value: object) -> dict[str, Any]:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _payload_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_digest_shape(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


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
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) in (bool, str):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field_info in fields(value):
            if _has_unsafe_public_text(field_info.name):
                raise ValueError(f"unsafe public key in {label}: {field_info.name}")
            _reject_unsafe_public_value(label, getattr(value, field_info.name))
        return
    if type(value) is str:
        if _has_unsafe_public_text(value):
            raise ValueError(f"{label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("public value must not be a float")
    if type(value) is int:
        raise ValueError("public value must use Decimal-derived strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_text(key):
                raise ValueError(f"unsafe public key in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_value(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_value(label, item)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    fragments = (
        "credential",
        "private" + "_key",
        "wal" + "let",
        "acc" + "ount",
        "bal" + "ance",
        "or" + "der",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
        "auth",
        "net" + "work",
        "data" + "base",
        "pers" + "ist",
        "li" + "ve",
        "b" + "uy",
        "se" + "ll",
        "trade",
    )
    return any(fragment in lowered for fragment in fragments)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_hours(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_HOURS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(HOURS_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_public_id(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


__all__ = (
    "DEFAULT_PROBABILITY_EVENT_RESOLUTION_RULE_EVIDENCE_GAP_CONFIG_VERSION",
    "ProbabilityEventResolutionRuleEvidenceGapConfig",
    "ProbabilityEventResolutionRuleEvidenceGapInput",
    "ProbabilityEventResolutionRuleEvidenceGapRow",
    "ProbabilityEventResolutionRuleEvidenceGapReport",
    "build_probability_event_resolution_rule_evidence_gap_report",
    "probability_event_resolution_rule_evidence_gap_report_payload",
)
