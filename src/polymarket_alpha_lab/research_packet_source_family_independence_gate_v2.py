"""Phase 1 report-only source-family independence gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_GATE_V2_CONFIG_VERSION = (
    "research-packet-source-family-independence-gate-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_GATE_STATUSES = frozenset(("pass", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
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
    "empty_evidence",
    "missing_corroboration",
    "insufficient_source_family_independence",
    "duplicate_source_family_penalty",
    "independent_corroboration_boost",
    "independence_score_watch",
    "source_family_independence_pass",
)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyIndependenceGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_GATE_V2_CONFIG_VERSION
    )
    min_independent_family_count: Decimal = Decimal("2.000000")
    min_independence_score: Decimal = Decimal("0.650000")
    duplicate_family_penalty_per_source: Decimal = Decimal("0.150000")
    independent_family_boost_per_family: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyIndependenceGateConfig:
            raise TypeError(
                "ResearchPacketSourceFamilyIndependenceGateConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyIndependenceGateConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketSourceFamilyIndependenceGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_independent_family_count",
            _require_positive_count_decimal(
                "min_independent_family_count",
                self.min_independent_family_count,
            ),
        )
        for field_name in (
            "min_independence_score",
            "duplicate_family_penalty_per_source",
            "independent_family_boost_per_family",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyEvidence:
    packet_id: str
    claim_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    confidence_score: Decimal
    corroborates_claim: bool = True
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyEvidence:
            raise TypeError(
                "ResearchPacketSourceFamilyEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyEvidence:
            raise ValueError(
                "evidence must be exactly ResearchPacketSourceFamilyEvidence",
            )
        for field_name in ("packet_id", "claim_id", "source_id", "source_family"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        _require_bool("corroborates_claim", self.corroborates_claim)
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyPublicPayloadItem:
            raise TypeError(
                "ResearchPacketSourceFamilyPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchPacketSourceFamilyPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(
            self,
            "value",
            _require_public_text("value", self.value),
        )
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyIndependenceGateRow:
    packet_id: str
    claim_id: str
    source_count: Decimal
    corroborating_source_count: Decimal
    source_family_count: Decimal
    duplicate_source_family_count: Decimal
    independent_corroboration_count: Decimal
    duplicate_family_penalty: Decimal
    independent_corroboration_boost: Decimal
    average_confidence_score: Decimal
    independence_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyIndependenceGateRow:
            raise TypeError(
                "ResearchPacketSourceFamilyIndependenceGateRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyIndependenceGateRow:
            raise ValueError(
                "row must be exactly ResearchPacketSourceFamilyIndependenceGateRow",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("claim_id", self.claim_id)
        for field_name in (
            "source_count",
            "corroborating_source_count",
            "source_family_count",
            "duplicate_source_family_count",
            "independent_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "duplicate_family_penalty",
            "independent_corroboration_boost",
            "average_confidence_score",
            "independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyIndependenceGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_independence_score: Decimal
    max_duplicate_family_penalty: Decimal
    rows: tuple[ResearchPacketSourceFamilyIndependenceGateRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchPacketSourceFamilyPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyIndependenceGateReport:
            raise TypeError(
                "ResearchPacketSourceFamilyIndependenceGateReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyIndependenceGateReport:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketSourceFamilyIndependenceGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        for field_name in ("packet_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_independence_score",
            "max_duplicate_family_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketSourceFamilyIndependenceGateReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_source_family_independence_gate_v2_report(
    evidence: Sequence[ResearchPacketSourceFamilyEvidence],
    *,
    generated_at: datetime,
    config: ResearchPacketSourceFamilyIndependenceGateConfig | None = None,
    public_payload: Sequence[ResearchPacketSourceFamilyPublicPayloadItem] = (),
) -> ResearchPacketSourceFamilyIndependenceGateReport:
    """Build a local report-only source-family independence gate snapshot."""

    if config is None:
        config = ResearchPacketSourceFamilyIndependenceGateConfig()
    if type(config) is not ResearchPacketSourceFamilyIndependenceGateConfig:
        raise ValueError(
            "config must be a ResearchPacketSourceFamilyIndependenceGateConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("evidence observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_evidence, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "average_independence_score": _average(
            tuple(row.independence_score for row in rows),
        ),
        "max_duplicate_family_penalty": (
            max((row.duplicate_family_penalty for row in rows), default=_ZERO)
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketSourceFamilyIndependenceGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    evidence: tuple[ResearchPacketSourceFamilyEvidence, ...],
    config: ResearchPacketSourceFamilyIndependenceGateConfig,
) -> tuple[ResearchPacketSourceFamilyIndependenceGateRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchPacketSourceFamilyEvidence]] = {}
    for item in evidence:
        grouped.setdefault((item.packet_id, item.claim_id), []).append(item)
    rows = [
        _row_for_group(packet_id, claim_id, tuple(items), config)
        for (packet_id, claim_id), items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_group(
    packet_id: str,
    claim_id: str,
    evidence: tuple[ResearchPacketSourceFamilyEvidence, ...],
    config: ResearchPacketSourceFamilyIndependenceGateConfig,
) -> ResearchPacketSourceFamilyIndependenceGateRow:
    corroborating = tuple(item for item in evidence if item.corroborates_claim)
    source_family_count = _decimal_count(
        len({item.source_family for item in corroborating}),
    )
    corroborating_count = _decimal_count(len(corroborating))
    duplicate_family_count = _quantize(max(corroborating_count - source_family_count, _ZERO))
    independent_count = _quantize(max(source_family_count - _ONE, _ZERO))
    duplicate_penalty = _clamp_ratio(
        duplicate_family_count * config.duplicate_family_penalty_per_source,
    )
    independent_boost = _clamp_ratio(
        independent_count * config.independent_family_boost_per_family,
    )
    average_confidence = _average(
        tuple(item.confidence_score for item in corroborating),
    )
    independence_score = _clamp_ratio(
        average_confidence + independent_boost - duplicate_penalty,
    )
    reason_codes = _row_reason_codes(
        corroborating_count=corroborating_count,
        source_family_count=source_family_count,
        duplicate_family_count=duplicate_family_count,
        independence_score=independence_score,
        config=config,
    )
    return ResearchPacketSourceFamilyIndependenceGateRow(
        packet_id=packet_id,
        claim_id=claim_id,
        source_count=_decimal_count(len(evidence)),
        corroborating_source_count=corroborating_count,
        source_family_count=source_family_count,
        duplicate_source_family_count=duplicate_family_count,
        independent_corroboration_count=independent_count,
        duplicate_family_penalty=duplicate_penalty,
        independent_corroboration_boost=independent_boost,
        average_confidence_score=average_confidence,
        independence_score=independence_score,
        gate_status=_row_status(
            corroborating_count=corroborating_count,
            source_family_count=source_family_count,
            independence_score=independence_score,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    corroborating_count: Decimal,
    source_family_count: Decimal,
    duplicate_family_count: Decimal,
    independence_score: Decimal,
    config: ResearchPacketSourceFamilyIndependenceGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if corroborating_count == _ZERO:
        reason_codes.append("missing_corroboration")
    if source_family_count < config.min_independent_family_count:
        reason_codes.append("insufficient_source_family_independence")
    if duplicate_family_count > _ZERO:
        reason_codes.append("duplicate_source_family_penalty")
    if source_family_count > _ONE:
        reason_codes.append("independent_corroboration_boost")
    if (
        corroborating_count > _ZERO
        and source_family_count >= config.min_independent_family_count
        and independence_score < config.min_independence_score
    ):
        reason_codes.append("independence_score_watch")
    if (
        source_family_count >= config.min_independent_family_count
        and independence_score >= config.min_independence_score
    ):
        reason_codes.append("source_family_independence_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    corroborating_count: Decimal,
    source_family_count: Decimal,
    independence_score: Decimal,
    config: ResearchPacketSourceFamilyIndependenceGateConfig,
) -> str:
    if corroborating_count == _ZERO:
        return "blocked"
    if (
        source_family_count >= config.min_independent_family_count
        and independence_score >= config.min_independence_score
    ):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchPacketSourceFamilyIndependenceGateRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceFamilyIndependenceGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchPacketSourceFamilyIndependenceGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _validate_row_consistency(
    row: ResearchPacketSourceFamilyIndependenceGateRow,
) -> None:
    if row.corroborating_source_count > row.source_count:
        raise ValueError("corroborating_source_count must not exceed source_count")
    if row.source_family_count > row.corroborating_source_count:
        raise ValueError(
            "source_family_count must not exceed corroborating_source_count",
        )
    expected_duplicate_count = _quantize(
        row.corroborating_source_count - row.source_family_count,
    )
    if row.duplicate_source_family_count != expected_duplicate_count:
        raise ValueError(
            "duplicate_source_family_count must match repeated corroborating families",
        )
    expected_independent_count = _quantize(max(row.source_family_count - _ONE, _ZERO))
    if row.independent_corroboration_count != expected_independent_count:
        raise ValueError(
            "independent_corroboration_count must match source_family_count less one",
        )
    if row.gate_status == "pass" and "source_family_independence_pass" not in row.reason_codes:
        raise ValueError("pass rows must include source_family_independence_pass")
    if row.gate_status == "blocked" and row.corroborating_source_count > _ZERO:
        raise ValueError("blocked rows must have no corroborating sources")


def _validate_report_consistency(
    report: ResearchPacketSourceFamilyIndependenceGateReport,
) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_independence_score != _average(
        tuple(row.independence_score for row in report.rows),
    ):
        raise ValueError("average_independence_score must match rows")
    expected_max_penalty = max(
        (row.duplicate_family_penalty for row in report.rows),
        default=_ZERO,
    )
    if report.max_duplicate_family_penalty != expected_max_penalty:
        raise ValueError("max_duplicate_family_penalty must match rows")
    expected_status = _report_status(report.rows)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_evidence(
    evidence: Sequence[ResearchPacketSourceFamilyEvidence],
) -> tuple[ResearchPacketSourceFamilyEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchPacketSourceFamilyEvidence] = []
    for item in evidence:
        if type(item) is not ResearchPacketSourceFamilyEvidence:
            raise ValueError(
                "evidence items must be ResearchPacketSourceFamilyEvidence",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.packet_id,
                item.claim_id,
                item.observed_at,
                item.source_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchPacketSourceFamilyIndependenceGateRow],
) -> tuple[ResearchPacketSourceFamilyIndependenceGateRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchPacketSourceFamilyIndependenceGateRow] = []
    for row in rows:
        if type(row) is not ResearchPacketSourceFamilyIndependenceGateRow:
            raise ValueError(
                "rows must contain ResearchPacketSourceFamilyIndependenceGateRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.packet_id, row.claim_id)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchPacketSourceFamilyPublicPayloadItem],
) -> tuple[ResearchPacketSourceFamilyPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchPacketSourceFamilyPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchPacketSourceFamilyPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchPacketSourceFamilyPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_gate_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be a known gate status")
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
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


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


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
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
    report: ResearchPacketSourceFamilyIndependenceGateReport,
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
        return str(value)
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
    "DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_GATE_V2_CONFIG_VERSION",
    "ResearchPacketSourceFamilyEvidence",
    "ResearchPacketSourceFamilyIndependenceGateConfig",
    "ResearchPacketSourceFamilyIndependenceGateReport",
    "ResearchPacketSourceFamilyIndependenceGateRow",
    "ResearchPacketSourceFamilyPublicPayloadItem",
    "build_research_packet_source_family_independence_gate_v2_report",
)
