"""Report-only event claim memory-authority quorum research snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_CLAIM_MEMORY_AUTHORITY_QUORUM_CONFIG_VERSION = (
    "research-event-claim-memory-authority-quorum-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "missing_support",
    "insufficient_memory_quorum",
    "insufficient_authority_quorum",
    "quorum_score_watch",
    "memory_authority_quorum_pass",
)
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "db",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
        "candidate",
        "market",
        "id",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "trade",
    ),
)


@dataclass(frozen=True)
class ResearchEventClaimMemoryAuthorityQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CLAIM_MEMORY_AUTHORITY_QUORUM_CONFIG_VERSION
    )
    min_memory_count: Decimal = _TWO
    min_authority_count: Decimal = _TWO
    min_quorum_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMemoryAuthorityQuorumConfig:
            raise TypeError(
                "ResearchEventClaimMemoryAuthorityQuorumConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMemoryAuthorityQuorumConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventClaimMemoryAuthorityQuorumConfig",
            )
        _require_supported_config_version(self.config_version)
        object.__setattr__(
            self,
            "min_memory_count",
            _require_positive_count_decimal("min_memory_count", self.min_memory_count),
        )
        object.__setattr__(
            self,
            "min_authority_count",
            _require_positive_count_decimal(
                "min_authority_count",
                self.min_authority_count,
            ),
        )
        object.__setattr__(
            self,
            "min_quorum_score",
            _require_ratio_decimal("min_quorum_score", self.min_quorum_score),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventClaimMemoryAuthorityObservation:
    event_id: str
    claim_id: str
    memory_ref: str
    authority_ref: str
    recorded_at: datetime
    memory_score: Decimal
    authority_score: Decimal
    supports_claim: bool = True
    private_material: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMemoryAuthorityObservation:
            raise TypeError(
                "ResearchEventClaimMemoryAuthorityObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMemoryAuthorityObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchEventClaimMemoryAuthorityObservation",
            )
        for field_name in ("event_id", "claim_id", "memory_ref", "authority_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "recorded_at", _as_utc("recorded_at", self.recorded_at))
        object.__setattr__(
            self,
            "memory_score",
            _require_ratio_decimal("memory_score", self.memory_score),
        )
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        _require_bool("supports_claim", self.supports_claim)
        object.__setattr__(
            self,
            "private_material",
            _normalize_private_material(self.private_material),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem:
            raise TypeError(
                "ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventClaimMemoryAuthorityQuorumRow:
    event_claim_digest: str
    observation_count: Decimal
    supporting_memory_count: Decimal
    supporting_authority_count: Decimal
    supporting_pair_count: Decimal
    average_memory_score: Decimal
    average_authority_score: Decimal
    quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMemoryAuthorityQuorumRow:
            raise TypeError(
                "ResearchEventClaimMemoryAuthorityQuorumRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMemoryAuthorityQuorumRow:
            raise ValueError("row must be exactly ResearchEventClaimMemoryAuthorityQuorumRow")
        _require_sha256_digest("event_claim_digest", self.event_claim_digest)
        for field_name in (
            "observation_count",
            "supporting_memory_count",
            "supporting_authority_count",
            "supporting_pair_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_score",
            "average_authority_score",
            "quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventClaimMemoryAuthorityQuorumReport:
    generated_at: datetime
    config_version: str
    status: str
    event_claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quorum_score: Decimal
    rows: tuple[ResearchEventClaimMemoryAuthorityQuorumRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMemoryAuthorityQuorumReport:
            raise TypeError(
                "ResearchEventClaimMemoryAuthorityQuorumReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMemoryAuthorityQuorumReport:
            raise ValueError(
                "report must be exactly ResearchEventClaimMemoryAuthorityQuorumReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status("status", self.status)
        for field_name in ("event_claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quorum_score",
            _require_ratio_decimal("average_quorum_score", self.average_quorum_score),
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
            "ResearchEventClaimMemoryAuthorityQuorumReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_claim_memory_authority_quorum_report(
    observations: Sequence[ResearchEventClaimMemoryAuthorityObservation],
    *,
    generated_at: datetime,
    config: ResearchEventClaimMemoryAuthorityQuorumConfig | None = None,
    public_payload: Sequence[ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem] = (),
) -> ResearchEventClaimMemoryAuthorityQuorumReport:
    """Build a deterministic local report-only memory-authority quorum snapshot."""

    if config is None:
        config = ResearchEventClaimMemoryAuthorityQuorumConfig()
    if type(config) is not ResearchEventClaimMemoryAuthorityQuorumConfig:
        raise ValueError(
            "config must be a ResearchEventClaimMemoryAuthorityQuorumConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.recorded_at > generated_at:
            raise ValueError("observation recorded_at must not be after generated_at")
    rows = _build_rows(normalized_observations, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "event_claim_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventClaimMemoryAuthorityQuorumReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[ResearchEventClaimMemoryAuthorityObservation, ...],
    config: ResearchEventClaimMemoryAuthorityQuorumConfig,
) -> tuple[ResearchEventClaimMemoryAuthorityQuorumRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchEventClaimMemoryAuthorityObservation]] = {}
    for item in observations:
        grouped.setdefault((item.event_id, item.claim_id), []).append(item)
    return tuple(
        _row_for_group(event_id, claim_id, tuple(items), config)
        for (event_id, claim_id), items in sorted(grouped.items())
    )


def _row_for_group(
    event_id: str,
    claim_id: str,
    observations: tuple[ResearchEventClaimMemoryAuthorityObservation, ...],
    config: ResearchEventClaimMemoryAuthorityQuorumConfig,
) -> ResearchEventClaimMemoryAuthorityQuorumRow:
    supporting = tuple(item for item in observations if item.supports_claim)
    memory_count = _decimal_count(len({item.memory_ref for item in supporting}))
    authority_count = _decimal_count(len({item.authority_ref for item in supporting}))
    pair_count = min(memory_count, authority_count)
    average_memory_score = _average(tuple(item.memory_score for item in supporting))
    average_authority_score = _average(tuple(item.authority_score for item in supporting))
    quorum_score = _average((average_memory_score, average_authority_score))
    status = _row_status(
        memory_count=memory_count,
        authority_count=authority_count,
        quorum_score=quorum_score,
        config=config,
    )
    return ResearchEventClaimMemoryAuthorityQuorumRow(
        event_claim_digest=_event_claim_digest(event_id, claim_id),
        observation_count=_decimal_count(len(observations)),
        supporting_memory_count=memory_count,
        supporting_authority_count=authority_count,
        supporting_pair_count=pair_count,
        average_memory_score=average_memory_score,
        average_authority_score=average_authority_score,
        quorum_score=quorum_score,
        status=status,
        reason_codes=_row_reason_codes(
            memory_count=memory_count,
            authority_count=authority_count,
            quorum_score=quorum_score,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    memory_count: Decimal,
    authority_count: Decimal,
    quorum_score: Decimal,
    config: ResearchEventClaimMemoryAuthorityQuorumConfig,
) -> str:
    if (
        memory_count < config.min_memory_count
        or authority_count < config.min_authority_count
    ):
        return "block"
    if quorum_score < config.min_quorum_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    memory_count: Decimal,
    authority_count: Decimal,
    quorum_score: Decimal,
    status: str,
    config: ResearchEventClaimMemoryAuthorityQuorumConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_count == _ZERO and authority_count == _ZERO:
        reason_codes.append("missing_support")
    if memory_count < config.min_memory_count:
        reason_codes.append("insufficient_memory_quorum")
    if authority_count < config.min_authority_count:
        reason_codes.append("insufficient_authority_quorum")
    if status == "watch" and quorum_score < config.min_quorum_score:
        reason_codes.append("quorum_score_watch")
    if status == "pass":
        reason_codes.append("memory_authority_quorum_pass")
    return _normalize_reason_codes(reason_codes)


def _report_status(rows: tuple[ResearchEventClaimMemoryAuthorityQuorumRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventClaimMemoryAuthorityQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    codes: list[str] = []
    for row in rows:
        codes.extend(row.reason_codes)
    return _normalize_reason_codes(codes)


def _status_count(
    rows: tuple[ResearchEventClaimMemoryAuthorityQuorumRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_observations(
    observations: Sequence[ResearchEventClaimMemoryAuthorityObservation],
) -> tuple[ResearchEventClaimMemoryAuthorityObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchEventClaimMemoryAuthorityObservation] = []
    for item in observations:
        if type(item) is not ResearchEventClaimMemoryAuthorityObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventClaimMemoryAuthorityObservation items",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_id,
                item.claim_id,
                item.recorded_at.isoformat(),
                item.memory_ref,
                item.authority_ref,
                item.memory_score,
                item.authority_score,
                item.supports_claim,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEventClaimMemoryAuthorityQuorumRow],
) -> tuple[ResearchEventClaimMemoryAuthorityQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventClaimMemoryAuthorityQuorumRow] = []
    for row in rows:
        if type(row) is not ResearchEventClaimMemoryAuthorityQuorumRow:
            raise ValueError(
                "rows must contain ResearchEventClaimMemoryAuthorityQuorumRow items",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.event_claim_digest))


def _normalize_public_payload(
    public_payload: Sequence[ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem],
) -> tuple[ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem items",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_private_material(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("private_material must be a sequence")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError("private_material items must be strings")
        normalized.append(item)
    return tuple(normalized)


def _validate_row_consistency(row: ResearchEventClaimMemoryAuthorityQuorumRow) -> None:
    if row.supporting_pair_count > row.supporting_memory_count:
        raise ValueError("supporting_pair_count cannot exceed supporting_memory_count")
    if row.supporting_pair_count > row.supporting_authority_count:
        raise ValueError("supporting_pair_count cannot exceed supporting_authority_count")
    if row.supporting_memory_count > row.observation_count:
        raise ValueError("supporting_memory_count cannot exceed observation_count")
    if row.supporting_authority_count > row.observation_count:
        raise ValueError("supporting_authority_count cannot exceed observation_count")


def _validate_report_consistency(
    report: ResearchEventClaimMemoryAuthorityQuorumReport,
) -> None:
    rows = report.rows
    if report.event_claim_count != _decimal_count(len(rows)):
        raise ValueError("event_claim_count does not match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count does not match rows")
    if report.average_quorum_score != _average(tuple(row.quorum_score for row in rows)):
        raise ValueError("average_quorum_score does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")


def _require_supported_config_version(value: object) -> None:
    _require_public_identifier("config_version", value)
    if value != DEFAULT_RESEARCH_EVENT_CLAIM_MEMORY_AUTHORITY_QUORUM_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 256:
        raise ValueError(f"{field_name} must be nonempty public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


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


def _event_claim_digest(event_id: str, claim_id: str) -> str:
    canonical = json.dumps(
        {
            "claim_ref": claim_id,
            "event_ref": event_id,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


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


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _report_values_without_digest(
    report: ResearchEventClaimMemoryAuthorityQuorumReport,
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
    if _has_unsafe_public_token(key):
        raise ValueError(f"{path}.{key} has unsafe public payload field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    if _has_unsafe_public_token(value):
        raise ValueError(f"{path} has unsafe public payload value")


def _has_unsafe_public_token(value: str) -> bool:
    return any(token in _UNSAFE_PUBLIC_TOKENS for token in _public_tokens(value))


def _public_tokens(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", value.lower()))


__all__ = (
    "DEFAULT_RESEARCH_EVENT_CLAIM_MEMORY_AUTHORITY_QUORUM_CONFIG_VERSION",
    "ResearchEventClaimMemoryAuthorityObservation",
    "ResearchEventClaimMemoryAuthorityQuorumConfig",
    "ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem",
    "ResearchEventClaimMemoryAuthorityQuorumReport",
    "ResearchEventClaimMemoryAuthorityQuorumRow",
    "build_research_event_claim_memory_authority_quorum_report",
)
