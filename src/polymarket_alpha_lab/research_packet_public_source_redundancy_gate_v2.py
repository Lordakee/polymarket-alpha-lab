"""Phase 1 public-source redundancy gate for research packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_PACKET_PUBLIC_SOURCE_REDUNDANCY_GATE_V2_CONFIG_VERSION = (
    "research-packet-public-source-redundancy-gate-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_REPORT_STATUSES = frozenset(("pass", "watch", "block", "empty"))
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
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
_REASON_CODE_SEQUENCE = (
    "insufficient_public_sources",
    "low_independence",
    "duplicate_sources_present",
    "proxy_sources_present",
    "public_source_redundancy_pass",
)


@dataclass(frozen=True)
class ResearchPacketPublicSourceRedundancyGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_PUBLIC_SOURCE_REDUNDANCY_GATE_V2_CONFIG_VERSION
    )
    min_public_source_count: Decimal = Decimal("3.000000")
    min_independence_ratio: Decimal = Decimal("0.666667")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketPublicSourceRedundancyGateConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketPublicSourceRedundancyGateConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketPublicSourceRedundancyGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_PUBLIC_SOURCE_REDUNDANCY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_positive_count_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        object.__setattr__(
            self,
            "min_independence_ratio",
            _require_ratio_decimal("min_independence_ratio", self.min_independence_ratio),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketPublicSourceRedundancyGateInput:
    packet_id: str
    event_slug: str
    category: str
    public_source_count: Decimal
    independent_source_family_count: Decimal
    duplicate_source_count: Decimal = _ZERO
    official_source_count: Decimal = _ZERO
    proxy_source_count: Decimal = _ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketPublicSourceRedundancyGateInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketPublicSourceRedundancyGateInput:
            raise ValueError(
                "input must be exactly ResearchPacketPublicSourceRedundancyGateInput",
            )
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "public_source_count",
            "independent_source_family_count",
            "duplicate_source_count",
            "official_source_count",
            "proxy_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_input_counts(self)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchPacketPublicSourceRedundancyGateRow:
    packet_id: str
    event_slug: str
    category: str
    public_source_count: Decimal
    independent_source_family_count: Decimal
    duplicate_source_count: Decimal
    official_source_count: Decimal
    proxy_source_count: Decimal
    redundancy_score: Decimal
    independence_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketPublicSourceRedundancyGateRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketPublicSourceRedundancyGateRow:
            raise ValueError(
                "row must be exactly ResearchPacketPublicSourceRedundancyGateRow",
            )
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "public_source_count",
            "independent_source_family_count",
            "duplicate_source_count",
            "official_source_count",
            "proxy_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("redundancy_score", "independence_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_input_counts(self)
        _validate_row_reason_status(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketPublicSourceRedundancyGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketPublicSourceRedundancyGateReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketPublicSourceRedundancyGateReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchPacketPublicSourceRedundancyGateReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchPacketPublicSourceRedundancyGateReport:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    insufficient_public_source_count: Decimal
    low_independence_count: Decimal
    duplicate_source_count: Decimal
    min_redundancy_score: Decimal
    rows: tuple[ResearchPacketPublicSourceRedundancyGateRow, ...]
    reason_code_counts: tuple[
        ResearchPacketPublicSourceRedundancyGateReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketPublicSourceRedundancyGateReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketPublicSourceRedundancyGateReport:
            raise ValueError(
                "report must be exactly ResearchPacketPublicSourceRedundancyGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_PUBLIC_SOURCE_REDUNDANCY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "insufficient_public_source_count",
            "low_independence_count",
            "duplicate_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_redundancy_score",
            _require_ratio_decimal("min_redundancy_score", self.min_redundancy_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
            return
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketPublicSourceRedundancyGateReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


def build_research_packet_public_source_redundancy_gate_v2_report(
    rows: Iterable[ResearchPacketPublicSourceRedundancyGateInput],
    *,
    generated_at: datetime,
    config: ResearchPacketPublicSourceRedundancyGateConfig | None = None,
) -> ResearchPacketPublicSourceRedundancyGateReport:
    """Build a deterministic report-only public-source redundancy gate snapshot."""

    if config is None:
        config = ResearchPacketPublicSourceRedundancyGateConfig()
    if type(config) is not ResearchPacketPublicSourceRedundancyGateConfig:
        raise ValueError(
            "config must be a ResearchPacketPublicSourceRedundancyGateConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    gate_rows = tuple(_row_for_input(item, config) for item in normalized_inputs)
    reason_code_counts = _reason_code_counts(gate_rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(gate_rows),
        "packet_count": _decimal_count(len(gate_rows)),
        "pass_count": _status_count(gate_rows, "pass"),
        "watch_count": _status_count(gate_rows, "watch"),
        "block_count": _status_count(gate_rows, "block"),
        "insufficient_public_source_count": _reason_count(
            gate_rows,
            "insufficient_public_sources",
        ),
        "low_independence_count": _reason_count(gate_rows, "low_independence"),
        "duplicate_source_count": _sum_counts(
            row.duplicate_source_count for row in gate_rows
        ),
        "min_redundancy_score": min(
            (row.redundancy_score for row in gate_rows),
            default=_ZERO,
        ),
        "rows": gate_rows,
        "reason_code_counts": reason_code_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketPublicSourceRedundancyGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_input(
    item: ResearchPacketPublicSourceRedundancyGateInput,
    config: ResearchPacketPublicSourceRedundancyGateConfig,
) -> ResearchPacketPublicSourceRedundancyGateRow:
    redundancy_score = _redundancy_score(item, config)
    independence_ratio = _independence_ratio(item)
    reason_codes = _row_reason_codes(
        item,
        independence_ratio=independence_ratio,
        config=config,
    )
    return ResearchPacketPublicSourceRedundancyGateRow(
        packet_id=item.packet_id,
        event_slug=item.event_slug,
        category=item.category,
        public_source_count=item.public_source_count,
        independent_source_family_count=item.independent_source_family_count,
        duplicate_source_count=item.duplicate_source_count,
        official_source_count=item.official_source_count,
        proxy_source_count=item.proxy_source_count,
        redundancy_score=redundancy_score,
        independence_ratio=independence_ratio,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchPacketPublicSourceRedundancyGateInput,
    *,
    independence_ratio: Decimal,
    config: ResearchPacketPublicSourceRedundancyGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.public_source_count < config.min_public_source_count:
        reason_codes.append("insufficient_public_sources")
    if independence_ratio < config.min_independence_ratio:
        reason_codes.append("low_independence")
    if item.duplicate_source_count > _ZERO:
        reason_codes.append("duplicate_sources_present")
    if item.proxy_source_count > _ZERO:
        reason_codes.append("proxy_sources_present")
    if not reason_codes:
        return ("public_source_redundancy_pass",)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "insufficient_public_sources" in reason_codes
        or "low_independence" in reason_codes
    ):
        return "block"
    if reason_codes == ("public_source_redundancy_pass",):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchPacketPublicSourceRedundancyGateRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _redundancy_score(
    item: ResearchPacketPublicSourceRedundancyGateInput,
    config: ResearchPacketPublicSourceRedundancyGateConfig,
) -> Decimal:
    effective_count = max(item.public_source_count - item.duplicate_source_count, _ZERO)
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(effective_count / config.min_public_source_count)


def _independence_ratio(item: ResearchPacketPublicSourceRedundancyGateInput) -> Decimal:
    if item.public_source_count == _ZERO:
        return _ZERO
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(
            item.independent_source_family_count / item.public_source_count,
        )


def _validate_input_counts(
    value: ResearchPacketPublicSourceRedundancyGateInput
    | ResearchPacketPublicSourceRedundancyGateRow,
) -> None:
    if value.independent_source_family_count > value.public_source_count:
        raise ValueError(
            "independent_source_family_count must not exceed public_source_count",
        )
    if value.duplicate_source_count > value.public_source_count:
        raise ValueError("duplicate_source_count must not exceed public_source_count")
    if value.official_source_count > value.public_source_count:
        raise ValueError("official_source_count must not exceed public_source_count")
    if value.proxy_source_count > value.public_source_count:
        raise ValueError("proxy_source_count must not exceed public_source_count")


def _validate_row_reason_status(
    row: ResearchPacketPublicSourceRedundancyGateRow,
) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchPacketPublicSourceRedundancyGateReport,
) -> None:
    rows = report.rows
    if report.packet_count != _decimal_count(len(rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.insufficient_public_source_count != _reason_count(
        rows,
        "insufficient_public_sources",
    ):
        raise ValueError("insufficient_public_source_count must match rows")
    if report.low_independence_count != _reason_count(rows, "low_independence"):
        raise ValueError("low_independence_count must match rows")
    if report.duplicate_source_count != _sum_counts(
        row.duplicate_source_count for row in rows
    ):
        raise ValueError("duplicate_source_count must match rows")
    if report.min_redundancy_score != min(
        (row.redundancy_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_redundancy_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    value: Iterable[ResearchPacketPublicSourceRedundancyGateInput],
) -> tuple[ResearchPacketPublicSourceRedundancyGateInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of gate inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of gate inputs") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketPublicSourceRedundancyGateInput:
            raise ValueError(
                "rows must contain ResearchPacketPublicSourceRedundancyGateInput",
            )
        _require_hard_flags("input", row)
        if row.packet_id in seen_ids:
            raise ValueError("packet_id values must be unique")
        seen_ids.add(row.packet_id)
    return tuple(sorted(rows, key=lambda row: (row.packet_id, row.event_slug, row.category)))


def _normalize_rows(
    value: Iterable[ResearchPacketPublicSourceRedundancyGateRow],
) -> tuple[ResearchPacketPublicSourceRedundancyGateRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of gate rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of gate rows") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketPublicSourceRedundancyGateRow:
            raise ValueError(
                "rows must contain ResearchPacketPublicSourceRedundancyGateRow",
            )
        _require_hard_flags("row", row)
        if row.packet_id in seen_ids:
            raise ValueError("rows packet_id values must be unique")
        seen_ids.add(row.packet_id)
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (row.packet_id, row.event_slug, row.category)),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchPacketPublicSourceRedundancyGateReasonCodeCount],
) -> tuple[ResearchPacketPublicSourceRedundancyGateReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketPublicSourceRedundancyGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketPublicSourceRedundancyGateReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(row.reason_code)
    sorted_rows = tuple(sorted(rows, key=lambda row: _REASON_CODE_SEQUENCE.index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _reason_code_counts(
    rows: tuple[ResearchPacketPublicSourceRedundancyGateRow, ...],
) -> tuple[ResearchPacketPublicSourceRedundancyGateReasonCodeCount, ...]:
    counts: list[ResearchPacketPublicSourceRedundancyGateReasonCodeCount] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > _ZERO:
            counts.append(
                ResearchPacketPublicSourceRedundancyGateReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[ResearchPacketPublicSourceRedundancyGateRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchPacketPublicSourceRedundancyGateRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _sum_counts(values: Iterable[Decimal]) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return _quantize(sum(values, _ZERO))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_member(field_name: str, value: object, members: frozenset[str]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return _quantize(value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if "public_source_redundancy_pass" in normalized and len(normalized) > 1:
        raise ValueError("pass reason must stand alone")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchPacketPublicSourceRedundancyGateReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_PUBLIC_SOURCE_REDUNDANCY_GATE_V2_CONFIG_VERSION",
    "ResearchPacketPublicSourceRedundancyGateConfig",
    "ResearchPacketPublicSourceRedundancyGateInput",
    "ResearchPacketPublicSourceRedundancyGateReasonCodeCount",
    "ResearchPacketPublicSourceRedundancyGateReport",
    "ResearchPacketPublicSourceRedundancyGateRow",
    "build_research_packet_public_source_redundancy_gate_v2_report",
)
