from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_CONFIG_VERSION = "research-event-authority-evidence-timing-floor-report-v0"
STATUS_VALUES = frozenset(("pass", "watch", "block"))
DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


@dataclass(frozen=True)
class ResearchEventAuthorityEvidenceTimingFloorConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_evidence_age_seconds: Decimal = Decimal("600.000000")
    block_evidence_age_seconds: Decimal = Decimal("1800.000000")
    watch_authority_evidence_lag_seconds: Decimal = Decimal("900.000000")
    block_authority_evidence_lag_seconds: Decimal = Decimal("1200.000000")
    watch_timing_floor_remaining_seconds: Decimal = Decimal("600.000000")
    block_timing_floor_remaining_seconds: Decimal = Decimal("60.000000")
    min_authority_evidence_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityEvidenceTimingFloorConfig:
            raise ValueError("config must be exactly ResearchEventAuthorityEvidenceTimingFloorConfig")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_evidence_age_seconds",
            "block_evidence_age_seconds",
            "watch_authority_evidence_lag_seconds",
            "block_authority_evidence_lag_seconds",
            "watch_timing_floor_remaining_seconds",
            "block_timing_floor_remaining_seconds",
            "min_authority_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_evidence_age_seconds > self.block_evidence_age_seconds:
            raise ValueError("watch_evidence_age_seconds must not exceed block_evidence_age_seconds")
        if self.watch_authority_evidence_lag_seconds > self.block_authority_evidence_lag_seconds:
            raise ValueError(
                "watch_authority_evidence_lag_seconds must not exceed "
                "block_authority_evidence_lag_seconds",
            )
        if self.block_timing_floor_remaining_seconds > self.watch_timing_floor_remaining_seconds:
            raise ValueError(
                "block_timing_floor_remaining_seconds must not exceed "
                "watch_timing_floor_remaining_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventAuthorityEvidenceTimingFloorInput:
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_market_question: str
    source_url: str
    source_text: str
    authority_observed_at: datetime
    evidence_observed_at: datetime
    timing_floor_at: datetime
    authority_evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityEvidenceTimingFloorInput:
            raise ValueError("input must be exactly ResearchEventAuthorityEvidenceTimingFloorInput")
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_market_question",
            "source_url",
            "source_text",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        for field_name in (
            "authority_observed_at",
            "evidence_observed_at",
            "timing_floor_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "authority_evidence_count",
            _require_nonnegative_decimal(
                "authority_evidence_count",
                self.authority_evidence_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventAuthorityEvidenceTimingFloorRow:
    event_ref: str
    status: str
    authority_observed_at: datetime
    evidence_observed_at: datetime
    timing_floor_at: datetime
    evidence_age_seconds: Decimal
    authority_evidence_lag_seconds: Decimal
    timing_floor_remaining_seconds: Decimal
    authority_evidence_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityEvidenceTimingFloorRow:
            raise ValueError("row must be exactly ResearchEventAuthorityEvidenceTimingFloorRow")
        _require_public_string("event_ref", self.event_ref)
        _require_status("status", self.status)
        for field_name in (
            "authority_observed_at",
            "evidence_observed_at",
            "timing_floor_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_age_seconds",
            "authority_evidence_lag_seconds",
            "timing_floor_remaining_seconds",
            "authority_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount",
            )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )


@dataclass(frozen=True)
class ResearchEventAuthorityEvidenceTimingFloorReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_timing_floor_remaining_seconds: Decimal
    max_authority_evidence_lag_seconds: Decimal
    max_evidence_age_seconds: Decimal
    rows: tuple[ResearchEventAuthorityEvidenceTimingFloorRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityEvidenceTimingFloorReport:
            raise ValueError("report must be exactly ResearchEventAuthorityEvidenceTimingFloorReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_timing_floor_remaining_seconds",
            "max_authority_evidence_lag_seconds",
            "max_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchEventAuthorityEvidenceTimingFloorRow:
                raise ValueError("rows must contain timing floor rows")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for item in self.reason_code_counts:
            if type(item) is not ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount:
                raise ValueError("reason_code_counts must contain reason count rows")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)


def build_research_event_authority_evidence_timing_floor_report(
    inputs: tuple[ResearchEventAuthorityEvidenceTimingFloorInput, ...] | list[object] | tuple[object, ...],
    *,
    config: ResearchEventAuthorityEvidenceTimingFloorConfig | None = None,
    generated_at: datetime,
) -> ResearchEventAuthorityEvidenceTimingFloorReport:
    cfg = config if config is not None else ResearchEventAuthorityEvidenceTimingFloorConfig()
    if type(cfg) is not ResearchEventAuthorityEvidenceTimingFloorConfig:
        raise ValueError("config must be a ResearchEventAuthorityEvidenceTimingFloorConfig")
    observed_at = _as_utc("generated_at", generated_at)
    normalized_inputs = tuple(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(index, item, cfg, observed_at)
                for index, item in enumerate(normalized_inputs, start=1)
            ),
            key=lambda row: (_status_sort_key(row.status), row.event_ref),
        )
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(reason_codes, _decimal_count(len(rows)))
    report = ResearchEventAuthorityEvidenceTimingFloorReport(
        generated_at=observed_at,
        config_version=cfg.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_decimal_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_decimal_count(sum(1 for row in rows if row.status == "block")),
        min_timing_floor_remaining_seconds=_min_decimal(
            row.timing_floor_remaining_seconds for row in rows
        ),
        max_authority_evidence_lag_seconds=_max_decimal(
            row.authority_evidence_lag_seconds for row in rows
        ),
        max_evidence_age_seconds=_max_decimal(row.evidence_age_seconds for row in rows),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        derived_validation_digest="0" * 64,
    )
    payload = _report_payload(report, include_digest=False)
    digest = _digest_payload(payload)
    return ResearchEventAuthorityEvidenceTimingFloorReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        input_count=report.input_count,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        min_timing_floor_remaining_seconds=report.min_timing_floor_remaining_seconds,
        max_authority_evidence_lag_seconds=report.max_authority_evidence_lag_seconds,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        rows=report.rows,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        derived_validation_digest=digest,
    )


def research_event_authority_evidence_timing_floor_report_payload(
    report: ResearchEventAuthorityEvidenceTimingFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventAuthorityEvidenceTimingFloorReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    else:
        raise ValueError("report must be a ResearchEventAuthorityEvidenceTimingFloorReport")
    validate_research_event_authority_evidence_timing_floor_public_payload(payload)
    return payload


def validate_research_event_authority_evidence_timing_floor_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _require_digest("derived_validation_digest", payload.get("derived_validation_digest"))
    _require_status("status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_status("row.status", row.get("status"))
        _require_hard_flags("row", _PayloadFlags(row))
    digest = payload["derived_validation_digest"]
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    if digest != _digest_payload(payload_without_digest):
        raise ValueError("derived_validation_digest does not match public payload")


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


def _row_from_input(
    index: int,
    item: object,
    config: ResearchEventAuthorityEvidenceTimingFloorConfig,
    generated_at: datetime,
) -> ResearchEventAuthorityEvidenceTimingFloorRow:
    if type(item) is not ResearchEventAuthorityEvidenceTimingFloorInput:
        raise ValueError("inputs must contain ResearchEventAuthorityEvidenceTimingFloorInput")
    evidence_age_seconds = _seconds_between(item.evidence_observed_at, generated_at)
    authority_lag_seconds = _seconds_between(
        item.authority_observed_at,
        item.evidence_observed_at,
    )
    timing_remaining_seconds = _seconds_between(generated_at, item.timing_floor_at)
    reason_codes = _row_reason_codes(
        evidence_age_seconds,
        authority_lag_seconds,
        timing_remaining_seconds,
        item.authority_evidence_count,
        config,
    )
    return ResearchEventAuthorityEvidenceTimingFloorRow(
        event_ref=f"event_ref_{index:06d}",
        status=_status_from_reason_codes(reason_codes),
        authority_observed_at=item.authority_observed_at,
        evidence_observed_at=item.evidence_observed_at,
        timing_floor_at=item.timing_floor_at,
        evidence_age_seconds=evidence_age_seconds,
        authority_evidence_lag_seconds=authority_lag_seconds,
        timing_floor_remaining_seconds=timing_remaining_seconds,
        authority_evidence_count=item.authority_evidence_count,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    evidence_age_seconds: Decimal,
    authority_lag_seconds: Decimal,
    timing_remaining_seconds: Decimal,
    authority_evidence_count: Decimal,
    config: ResearchEventAuthorityEvidenceTimingFloorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_age_seconds >= config.block_evidence_age_seconds:
        reason_codes.append("event_authority_evidence_stale_block")
    elif evidence_age_seconds >= config.watch_evidence_age_seconds:
        reason_codes.append("event_authority_evidence_stale_watch")
    if authority_lag_seconds >= config.block_authority_evidence_lag_seconds:
        reason_codes.append("event_authority_evidence_lag_block")
    elif authority_lag_seconds >= config.watch_authority_evidence_lag_seconds:
        reason_codes.append("event_authority_evidence_lag_watch")
    if timing_remaining_seconds <= config.block_timing_floor_remaining_seconds:
        reason_codes.append("event_authority_evidence_timing_floor_block")
    elif timing_remaining_seconds <= config.watch_timing_floor_remaining_seconds:
        reason_codes.append("event_authority_evidence_timing_floor_watch")
    if authority_evidence_count < config.min_authority_evidence_count:
        reason_codes.append("event_authority_evidence_quorum_block")
    if not reason_codes:
        reason_codes.append("event_authority_evidence_timing_floor_pass")
    return tuple(reason_codes)


def _report_status(rows: tuple[ResearchEventAuthorityEvidenceTimingFloorRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventAuthorityEvidenceTimingFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("event_authority_evidence_timing_floor_empty",)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code.endswith("_pass"):
                continue
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    if any(row.status == "watch" for row in rows):
        reason_codes.append("event_authority_evidence_timing_floor_watch_present")
    if not reason_codes:
        return ("event_authority_evidence_timing_floor_clear",)
    return tuple(reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    row_count: Decimal,
) -> tuple[ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount, ...]:
    return tuple(
        ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount(
            reason_code=reason_code,
            count=ONE,
            row_ratio=(
                ZERO if row_count == ZERO else (ONE / row_count).quantize(DECIMAL_QUANT)
            ),
        )
        for reason_code in reason_codes
    )


def _status_sort_key(status: str) -> int:
    if status == "block":
        return 0
    if status == "watch":
        return 1
    return 2


def _report_payload(
    report: ResearchEventAuthorityEvidenceTimingFloorReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "input_count": _decimal_payload(report.input_count),
        "row_count": _decimal_payload(report.row_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "min_timing_floor_remaining_seconds": _decimal_payload(
            report.min_timing_floor_remaining_seconds,
        ),
        "max_authority_evidence_lag_seconds": _decimal_payload(
            report.max_authority_evidence_lag_seconds,
        ),
        "max_evidence_age_seconds": _decimal_payload(report.max_evidence_age_seconds),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchEventAuthorityEvidenceTimingFloorRow) -> dict[str, Any]:
    return {
        "event_ref": row.event_ref,
        "status": row.status,
        "authority_observed_at": row.authority_observed_at.isoformat(),
        "evidence_observed_at": row.evidence_observed_at.isoformat(),
        "timing_floor_at": row.timing_floor_at.isoformat(),
        "evidence_age_seconds": _decimal_payload(row.evidence_age_seconds),
        "authority_evidence_lag_seconds": _decimal_payload(
            row.authority_evidence_lag_seconds,
        ),
        "timing_floor_remaining_seconds": _decimal_payload(
            row.timing_floor_remaining_seconds,
        ),
        "authority_evidence_count": _decimal_payload(row.authority_evidence_count),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    item: ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "row_ratio": _decimal_payload(item.row_ratio),
    }


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON value must use Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return _decimal_payload(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) in {int, float}:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
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


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal(str((end - start).total_seconds()))
    if seconds < ZERO:
        return ZERO
    return seconds.quantize(DECIMAL_QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANT)


def _decimal_payload(value: Decimal) -> str:
    value = _require_nonnegative_decimal("decimal_payload", value)
    return str(value.quantize(DECIMAL_QUANT))


def _min_decimal(values: Any) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return min(collected).quantize(DECIMAL_QUANT)


def _max_decimal(values: Any) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return max(collected).quantize(DECIMAL_QUANT)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        _require_public_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(DECIMAL_QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _reject_public_numerics(value: object) -> None:
    if type(value) in {int, float}:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    unsafe_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
        "sizing",
        "recommendation",
        "database",
        "network",
    )
    return any(fragment in lowered for fragment in unsafe_fragments)
