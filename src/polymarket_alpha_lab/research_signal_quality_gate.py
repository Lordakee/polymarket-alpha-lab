"""Pure report-only research signal quality gate."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION = (
    "research-signal-quality-gate-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_GATE_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_BLOCK_REASON_CODES = frozenset(
    (
        "traceability_block",
        "diversity_block",
        "freshness_block",
        "conflict_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_input",
    "traceability_block",
    "diversity_block",
    "freshness_block",
    "conflict_block",
    "traceability_watch",
    "diversity_watch",
    "freshness_watch",
    "conflict_watch",
    "quality_gate_pass",
)
_NEXT_STEP_BY_STATUS = {
    "pass": "research_queue_standard_review",
    "watch": "research_queue_elevated_review",
    "block": "hold_quality_rework",
}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class ResearchSignalQualityGateConfig:
    config_version: str = DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION
    min_traceability_score: Decimal = Decimal("0.600000")
    pass_traceability_score: Decimal = Decimal("0.800000")
    min_diversity_score: Decimal = Decimal("0.550000")
    pass_diversity_score: Decimal = Decimal("0.750000")
    watch_freshness_age_hours: Decimal = Decimal("24.000000")
    max_freshness_age_hours: Decimal = Decimal("72.000000")
    watch_conflict_severity_score: Decimal = Decimal("0.400000")
    block_conflict_severity_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalQualityGateConfig:
            raise TypeError("ResearchSignalQualityGateConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalQualityGateConfig:
            raise ValueError("config must be exactly ResearchSignalQualityGateConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_traceability_score",
            "pass_traceability_score",
            "min_diversity_score",
            "pass_diversity_score",
            "watch_conflict_severity_score",
            "block_conflict_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_freshness_age_hours", "max_freshness_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_traceability_score > self.pass_traceability_score:
            raise ValueError("min_traceability_score must not exceed pass threshold")
        if self.min_diversity_score > self.pass_diversity_score:
            raise ValueError("min_diversity_score must not exceed pass threshold")
        if self.watch_freshness_age_hours > self.max_freshness_age_hours:
            raise ValueError("watch_freshness_age_hours must not exceed max")
        if self.watch_conflict_severity_score > self.block_conflict_severity_score:
            raise ValueError("watch_conflict_severity_score must not exceed block")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSignalQualityInput:
    queue_item_key: str
    traceability_score: Decimal
    diversity_score: Decimal
    freshness_age_hours: Decimal
    conflict_severity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalQualityInput:
            raise TypeError("ResearchSignalQualityInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalQualityInput:
            raise ValueError("input must be exactly ResearchSignalQualityInput")
        _require_public_identifier("queue_item_key", self.queue_item_key)
        for field_name in (
            "traceability_score",
            "diversity_score",
            "conflict_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_age_hours",
            _require_nonnegative_decimal("freshness_age_hours", self.freshness_age_hours),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSignalQualityPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalQualityPublicPayloadItem:
            raise TypeError(
                "ResearchSignalQualityPublicPayloadItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalQualityPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSignalQualityPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSignalQualityGateRow:
    queue_item_key: str
    traceability_score: Decimal
    diversity_score: Decimal
    freshness_age_hours: Decimal
    freshness_score: Decimal
    conflict_severity_score: Decimal
    composite_quality_score: Decimal
    gate_status: str
    queue_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalQualityGateRow:
            raise TypeError("ResearchSignalQualityGateRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalQualityGateRow:
            raise ValueError("row must be exactly ResearchSignalQualityGateRow")
        _require_public_identifier("queue_item_key", self.queue_item_key)
        for field_name in (
            "traceability_score",
            "diversity_score",
            "freshness_score",
            "conflict_severity_score",
            "composite_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_age_hours",
            _require_nonnegative_decimal("freshness_age_hours", self.freshness_age_hours),
        )
        _require_gate_status("gate_status", self.gate_status)
        if self.queue_next_step != _NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("queue_next_step must match gate_status")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSignalQualityGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    queue_next_step: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal | None
    watch_ratio: Decimal | None
    block_ratio: Decimal | None
    average_composite_quality_score: Decimal
    max_conflict_severity_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSignalQualityGateRow, ...]
    public_payload: tuple[ResearchSignalQualityPublicPayloadItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalQualityGateReport:
            raise TypeError("ResearchSignalQualityGateReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalQualityGateReport:
            raise ValueError("report must be exactly ResearchSignalQualityGateReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        if self.queue_next_step != _NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("queue_next_step must match gate_status")
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_ratio", "watch_ratio", "block_ratio"):
            _require_optional_ratio_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "average_composite_quality_score",
            "max_conflict_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_signal_quality_gate_payload(self)


def build_research_signal_quality_gate(
    inputs: Sequence[ResearchSignalQualityInput],
    *,
    generated_at: datetime,
    config: ResearchSignalQualityGateConfig | None = None,
    public_payload: Sequence[ResearchSignalQualityPublicPayloadItem] = (),
) -> ResearchSignalQualityGateReport:
    """Build a deterministic paper-only research quality gate report."""

    if config is None:
        config = ResearchSignalQualityGateConfig()
    if type(config) is not ResearchSignalQualityGateConfig:
        raise ValueError("config must be a ResearchSignalQualityGateConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _build_rows(normalized_inputs, config)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": status,
        "queue_next_step": _NEXT_STEP_BY_STATUS[status],
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "pass_ratio": _optional_ratio(_status_count(rows, "pass"), len(rows)),
        "watch_ratio": _optional_ratio(_status_count(rows, "watch"), len(rows)),
        "block_ratio": _optional_ratio(_status_count(rows, "block"), len(rows)),
        "average_composite_quality_score": _average_ratio(
            tuple(row.composite_quality_score for row in rows),
        ),
        "max_conflict_severity_score": max(
            (row.conflict_severity_score for row in rows),
            default=_ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSignalQualityGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_signal_quality_gate_payload(
    value: ResearchSignalQualityGateReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchSignalQualityGateReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchSignalQualityGateReport or dict")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _build_rows(
    inputs: tuple[ResearchSignalQualityInput, ...],
    config: ResearchSignalQualityGateConfig,
) -> tuple[ResearchSignalQualityGateRow, ...]:
    return tuple(
        sorted(
            (_row_for_input(item, config) for item in inputs),
            key=_row_sort_key,
        ),
    )


def _row_for_input(
    item: ResearchSignalQualityInput,
    config: ResearchSignalQualityGateConfig,
) -> ResearchSignalQualityGateRow:
    freshness_score = _freshness_score(item.freshness_age_hours, config)
    composite_score = _average_ratio(
        (
            item.traceability_score,
            item.diversity_score,
            freshness_score,
            _quantize(_ONE - item.conflict_severity_score),
        ),
    )
    reason_codes = _row_reason_codes(
        traceability_score=item.traceability_score,
        diversity_score=item.diversity_score,
        freshness_age_hours=item.freshness_age_hours,
        conflict_severity_score=item.conflict_severity_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchSignalQualityGateRow(
        queue_item_key=item.queue_item_key,
        traceability_score=item.traceability_score,
        diversity_score=item.diversity_score,
        freshness_age_hours=item.freshness_age_hours,
        freshness_score=freshness_score,
        conflict_severity_score=item.conflict_severity_score,
        composite_quality_score=composite_score,
        gate_status=status,
        queue_next_step=_NEXT_STEP_BY_STATUS[status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    traceability_score: Decimal,
    diversity_score: Decimal,
    freshness_age_hours: Decimal,
    conflict_severity_score: Decimal,
    config: ResearchSignalQualityGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if traceability_score < config.min_traceability_score:
        reason_codes.append("traceability_block")
    if diversity_score < config.min_diversity_score:
        reason_codes.append("diversity_block")
    if freshness_age_hours > config.max_freshness_age_hours:
        reason_codes.append("freshness_block")
    if conflict_severity_score >= config.block_conflict_severity_score:
        reason_codes.append("conflict_block")
    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if traceability_score < config.pass_traceability_score:
            reason_codes.append("traceability_watch")
        if diversity_score < config.pass_diversity_score:
            reason_codes.append("diversity_watch")
        if freshness_age_hours > config.watch_freshness_age_hours:
            reason_codes.append("freshness_watch")
        if conflict_severity_score > config.watch_conflict_severity_score:
            reason_codes.append("conflict_watch")
    return tuple(reason_codes or ("quality_gate_pass",))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("quality_gate_pass",):
        return "pass"
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    return "watch"


def _report_status(rows: tuple[ResearchSignalQualityGateRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchSignalQualityGateRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("empty_input",)
    reason_codes: list[str] = []
    for code in _REASON_CODE_SEQUENCE:
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return tuple(reason_codes)


def _status_count(rows: tuple[ResearchSignalQualityGateRow, ...], status: str) -> int:
    return len(tuple(row for row in rows if row.gate_status == status))


def _freshness_score(
    freshness_age_hours: Decimal,
    config: ResearchSignalQualityGateConfig,
) -> Decimal:
    age_ratio = _quantize(freshness_age_hours / config.max_freshness_age_hours)
    return _clamp_ratio(_ONE - age_ratio)


def _validate_row_consistency(row: ResearchSignalQualityGateRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")


def _validate_report_consistency(report: ResearchSignalQualityGateReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _optional_ratio(_status_count(report.rows, "pass"), len(report.rows)):
        raise ValueError("pass_ratio must match rows")
    if report.watch_ratio != _optional_ratio(
        _status_count(report.rows, "watch"),
        len(report.rows),
    ):
        raise ValueError("watch_ratio must match rows")
    if report.block_ratio != _optional_ratio(
        _status_count(report.rows, "block"),
        len(report.rows),
    ):
        raise ValueError("block_ratio must match rows")
    expected_average_score = _average_ratio(
        tuple(row.composite_quality_score for row in report.rows),
    )
    if report.average_composite_quality_score != expected_average_score:
        raise ValueError("average_composite_quality_score must match rows")
    expected_max_conflict = max(
        (row.conflict_severity_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_conflict_severity_score != expected_max_conflict:
        raise ValueError("max_conflict_severity_score must match rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.queue_next_step != _NEXT_STEP_BY_STATUS[report.gate_status]:
        raise ValueError("queue_next_step must match gate_status")


def _normalize_inputs(
    inputs: Sequence[ResearchSignalQualityInput],
) -> tuple[ResearchSignalQualityInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchSignalQualityInput:
            raise ValueError("inputs items must be ResearchSignalQualityInput")
        _require_hard_flags("input", item)
    item_keys = tuple(item.queue_item_key for item in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("queue_item_key values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchSignalQualityGateRow, ...],
) -> tuple[ResearchSignalQualityGateRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSignalQualityGateRow:
            raise ValueError("rows items must be ResearchSignalQualityGateRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic quality gate ordering")
    item_keys = tuple(row.queue_item_key for row in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("row queue_item_key values must be unique")
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[ResearchSignalQualityPublicPayloadItem],
) -> tuple[ResearchSignalQualityPublicPayloadItem, ...]:
    if type(public_payload) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    normalized = tuple(public_payload)
    for item in normalized:
        if type(item) is not ResearchSignalQualityPublicPayloadItem:
            raise ValueError("public_payload items must be ResearchSignalQualityPublicPayloadItem")
        _require_hard_flags("public payload item", item)
    keys = tuple(item.key for item in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_payload must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_payload keys must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    expected_order = tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _row_sort_key(row: ResearchSignalQualityGateRow) -> tuple[int, str]:
    status_weight = {"block": 0, "watch": 1, "pass": 2}
    return (status_weight[row.gate_status], row.queue_item_key)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_optional_ratio_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _optional_ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize(Decimal(numerator) / Decimal(denominator))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    gate_status: str,
    queue_next_step: str,
    item_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    pass_ratio: Decimal | None,
    watch_ratio: Decimal | None,
    block_ratio: Decimal | None,
    average_composite_quality_score: Decimal,
    max_conflict_severity_score: Decimal,
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchSignalQualityGateRow, ...],
    public_payload: tuple[ResearchSignalQualityPublicPayloadItem, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "gate_status": gate_status,
        "queue_next_step": queue_next_step,
        "item_count": _json_ready(item_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "pass_ratio": _json_ready(pass_ratio),
        "watch_ratio": _json_ready(watch_ratio),
        "block_ratio": _json_ready(block_ratio),
        "average_composite_quality_score": _json_ready(average_composite_quality_score),
        "max_conflict_severity_score": _json_ready(max_conflict_severity_score),
        "reason_codes": list(reason_codes),
        "rows": [_row_payload(row) for row in rows],
        "public_payload": [_public_payload_item_payload(item) for item in public_payload],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: ResearchSignalQualityGateRow) -> dict[str, object]:
    return {
        "queue_item_key": row.queue_item_key,
        "traceability_score": _json_ready(row.traceability_score),
        "diversity_score": _json_ready(row.diversity_score),
        "freshness_age_hours": _json_ready(row.freshness_age_hours),
        "freshness_score": _json_ready(row.freshness_score),
        "conflict_severity_score": _json_ready(row.conflict_severity_score),
        "composite_quality_score": _json_ready(row.composite_quality_score),
        "gate_status": row.gate_status,
        "queue_next_step": row.queue_next_step,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_payload_item_payload(
    item: ResearchSignalQualityPublicPayloadItem,
) -> dict[str, object]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(report: ResearchSignalQualityGateReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        gate_status=report.gate_status,
        queue_next_step=report.queue_next_step,
        item_count=report.item_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        pass_ratio=report.pass_ratio,
        watch_ratio=report.watch_ratio,
        block_ratio=report.block_ratio,
        average_composite_quality_score=report.average_composite_quality_score,
        max_conflict_severity_score=report.max_conflict_severity_score,
        reason_codes=report.reason_codes,
        rows=report.rows,
        public_payload=report.public_payload,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: ResearchSignalQualityGateReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "gate_status": report.gate_status,
            "queue_next_step": report.queue_next_step,
            "item_count": report.item_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "pass_ratio": report.pass_ratio,
            "watch_ratio": report.watch_ratio,
            "block_ratio": report.block_ratio,
            "average_composite_quality_score": report.average_composite_quality_score,
            "max_conflict_severity_score": report.max_conflict_severity_score,
            "reason_codes": report.reason_codes,
            "rows": report.rows,
            "public_payload": report.public_payload,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        gate_status=_require_mapping_value(values, "gate_status", str),
        queue_next_step=_require_mapping_value(values, "queue_next_step", str),
        item_count=_require_mapping_value(values, "item_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        pass_ratio=_require_optional_mapping_value(values, "pass_ratio", Decimal),
        watch_ratio=_require_optional_mapping_value(values, "watch_ratio", Decimal),
        block_ratio=_require_optional_mapping_value(values, "block_ratio", Decimal),
        average_composite_quality_score=_require_mapping_value(
            values,
            "average_composite_quality_score",
            Decimal,
        ),
        max_conflict_severity_score=_require_mapping_value(
            values,
            "max_conflict_severity_score",
            Decimal,
        ),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        rows=_require_mapping_value(values, "rows", tuple),
        public_payload=_require_mapping_value(values, "public_payload", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _require_optional_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if value is None:
        return None
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__} or None")
    return value


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is ResearchSignalQualityGateReport:
        return _report_payload(value)
    if type(value) is ResearchSignalQualityGateRow:
        return _row_payload(value)
    if type(value) is ResearchSignalQualityPublicPayloadItem:
        return _public_payload_item_payload(value)
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
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchSignalQualityGateConfig,
            ResearchSignalQualityInput,
            ResearchSignalQualityPublicPayloadItem,
            ResearchSignalQualityGateRow,
            ResearchSignalQualityGateReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key == "gate_status" and item not in _GATE_STATUSES:
                raise ValueError(f"{item_path} must be pass, watch, or block")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION",
    "ResearchSignalQualityGateConfig",
    "ResearchSignalQualityGateReport",
    "ResearchSignalQualityGateRow",
    "ResearchSignalQualityInput",
    "ResearchSignalQualityPublicPayloadItem",
    "build_research_signal_quality_gate",
    "research_signal_quality_gate_payload",
)
