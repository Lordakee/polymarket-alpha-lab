"""Report-only team memory-source-authority quorum snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_TEAM_MEMORY_SOURCE_AUTHORITY_QUORUM_CONFIG_VERSION = (
    "research-team-memory-source-authority-quorum-report-v1"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_OBSERVATIONS = "empty_observations"
REASON_MISSING_SUPPORT = "missing_support"
REASON_INSUFFICIENT_MEMORY_QUORUM = "insufficient_memory_quorum"
REASON_INSUFFICIENT_SOURCE_FAMILY_QUORUM = "insufficient_source_family_quorum"
REASON_INSUFFICIENT_AUTHORITY_QUORUM = "insufficient_authority_quorum"
REASON_QUORUM_SCORE_WATCH = "quorum_score_watch"
REASON_QUORUM_SCORE_BLOCK = "quorum_score_block"
REASON_MEMORY_SOURCE_AUTHORITY_QUORUM_PASS = (
    "memory_source_authority_quorum_pass"
)

_REASON_CODE_SEQUENCE = (
    REASON_EMPTY_OBSERVATIONS,
    REASON_MISSING_SUPPORT,
    REASON_INSUFFICIENT_MEMORY_QUORUM,
    REASON_INSUFFICIENT_SOURCE_FAMILY_QUORUM,
    REASON_INSUFFICIENT_AUTHORITY_QUORUM,
    REASON_QUORUM_SCORE_BLOCK,
    REASON_QUORUM_SCORE_WATCH,
    REASON_MEMORY_SOURCE_AUTHORITY_QUORUM_PASS,
)
_Q = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _term(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "raw_text",
    "raw text",
    "dsn",
    "table",
    _term("to", "ken"),
    _term("wa", "llet"),
    _term("au", "th"),
    _term("or", "der"),
    _term("li", "ve"),
    _term("tra", "ding"),
    _term("siz", "ing"),
    _term("recom", "mendation"),
    _term("d", "b"),
    _term("data", "base"),
    _term("net", "work"),
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class ResearchTeamMemorySourceAuthorityQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_MEMORY_SOURCE_AUTHORITY_QUORUM_CONFIG_VERSION
    )
    min_memory_count: Decimal = _TWO
    min_source_family_count: Decimal = _TWO
    min_authority_count: Decimal = _TWO
    min_pass_quorum_score: Decimal = Decimal("0.750000")
    min_watch_quorum_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemorySourceAuthorityQuorumConfig:
            raise TypeError(
                "ResearchTeamMemorySourceAuthorityQuorumConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySourceAuthorityQuorumConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_MEMORY_SOURCE_AUTHORITY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_memory_count",
            "min_source_family_count",
            "min_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_pass_quorum_score",
            _require_ratio_decimal(
                "min_pass_quorum_score",
                self.min_pass_quorum_score,
            ),
        )
        object.__setattr__(
            self,
            "min_watch_quorum_score",
            _require_ratio_decimal(
                "min_watch_quorum_score",
                self.min_watch_quorum_score,
            ),
        )
        if self.min_pass_quorum_score < self.min_watch_quorum_score:
            raise ValueError(
                "min_pass_quorum_score must be at least min_watch_quorum_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamMemorySourceAuthorityObservation:
    item_ref: str
    memory_ref: str
    source_family_ref: str
    authority_ref: str
    observed_at: datetime
    memory_confidence_score: Decimal
    source_authority_score: Decimal
    supports_quorum: bool = True
    private_material: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemorySourceAuthorityObservation:
            raise TypeError(
                "ResearchTeamMemorySourceAuthorityObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySourceAuthorityObservation, "observation")
        object.__setattr__(self, "item_ref", _require_private_ref("item_ref", self.item_ref))
        object.__setattr__(
            self,
            "memory_ref",
            _require_private_ref("memory_ref", self.memory_ref),
        )
        object.__setattr__(
            self,
            "source_family_ref",
            _require_private_ref("source_family_ref", self.source_family_ref),
        )
        object.__setattr__(
            self,
            "authority_ref",
            _require_private_ref("authority_ref", self.authority_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_confidence_score",
            _require_ratio_decimal(
                "memory_confidence_score",
                self.memory_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "source_authority_score",
            _require_ratio_decimal(
                "source_authority_score",
                self.source_authority_score,
            ),
        )
        _require_bool("supports_quorum", self.supports_quorum)
        object.__setattr__(
            self,
            "private_material",
            _normalize_private_material(self.private_material),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem:
            raise TypeError(
                "ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem,
            "public payload item",
        )
        object.__setattr__(
            self,
            "key",
            _require_public_identifier("key", self.key),
        )
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchTeamMemorySourceAuthorityQuorumRow:
    item_digest: str
    observation_count: Decimal
    supporting_memory_count: Decimal
    supporting_source_family_count: Decimal
    supporting_authority_count: Decimal
    average_memory_confidence_score: Decimal
    average_source_authority_score: Decimal
    source_family_quorum_score: Decimal
    quorum_score: Decimal
    latest_observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemorySourceAuthorityQuorumRow:
            raise TypeError(
                "ResearchTeamMemorySourceAuthorityQuorumRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySourceAuthorityQuorumRow, "row")
        object.__setattr__(
            self,
            "item_digest",
            _require_private_digest("item_digest", self.item_digest),
        )
        for field_name in (
            "observation_count",
            "supporting_memory_count",
            "supporting_source_family_count",
            "supporting_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_confidence_score",
            "average_source_authority_score",
            "source_family_quorum_score",
            "quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamMemorySourceAuthorityQuorumReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quorum_score: Decimal
    rows: tuple[ResearchTeamMemorySourceAuthorityQuorumRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemorySourceAuthorityQuorumReport:
            raise TypeError(
                "ResearchTeamMemorySourceAuthorityQuorumReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySourceAuthorityQuorumReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_MEMORY_SOURCE_AUTHORITY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quorum_score",
            _require_ratio_decimal("average_quorum_score", self.average_quorum_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_memory_source_authority_quorum_report(
    observations: Sequence[ResearchTeamMemorySourceAuthorityObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamMemorySourceAuthorityQuorumConfig | None = None,
    public_payload: Sequence[
        ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem
    ] = (),
) -> ResearchTeamMemorySourceAuthorityQuorumReport:
    if config is None:
        config = ResearchTeamMemorySourceAuthorityQuorumConfig()
    if type(config) is not ResearchTeamMemorySourceAuthorityQuorumConfig:
        raise ValueError(
            "config must be a ResearchTeamMemorySourceAuthorityQuorumConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_observations, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamMemorySourceAuthorityQuorumReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_memory_source_authority_quorum_report_public_payload(
    report: ResearchTeamMemorySourceAuthorityQuorumReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemorySourceAuthorityQuorumReport:
        raise ValueError(
            "report must be a ResearchTeamMemorySourceAuthorityQuorumReport",
        )
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _require_payload_hard_flags(payload)
    return payload


def research_team_memory_source_authority_quorum_report_digest(
    report: ResearchTeamMemorySourceAuthorityQuorumReport,
) -> str:
    if type(report) is not ResearchTeamMemorySourceAuthorityQuorumReport:
        raise ValueError(
            "report must be a ResearchTeamMemorySourceAuthorityQuorumReport",
        )
    return _digest_from_values(_report_values_without_digest(report))


def validate_research_team_memory_source_authority_quorum_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(payload, (str, bytes)) or not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    normalized = dict(payload)
    _reject_unsafe_public_payload(
        "public payload",
        normalized,
        allow_json_containers=True,
    )
    _require_payload_hard_flags(normalized)
    digest = normalized.get(_DIGEST_FIELD)
    _require_sha256_digest(_DIGEST_FIELD, digest)
    if _digest_from_payload(normalized) != digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return normalized


def _build_rows(
    observations: tuple[ResearchTeamMemorySourceAuthorityObservation, ...],
    config: ResearchTeamMemorySourceAuthorityQuorumConfig,
) -> tuple[ResearchTeamMemorySourceAuthorityQuorumRow, ...]:
    grouped: dict[str, list[ResearchTeamMemorySourceAuthorityObservation]] = {}
    for item in observations:
        grouped.setdefault(item.item_ref, []).append(item)
    rows = tuple(
        _row_for_group(item_ref, tuple(items), config)
        for item_ref, items in grouped.items()
    )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.status),
                row.quorum_score,
                row.item_digest,
            ),
        ),
    )


def _row_for_group(
    item_ref: str,
    observations: tuple[ResearchTeamMemorySourceAuthorityObservation, ...],
    config: ResearchTeamMemorySourceAuthorityQuorumConfig,
) -> ResearchTeamMemorySourceAuthorityQuorumRow:
    supporting = tuple(item for item in observations if item.supports_quorum)
    memory_count = _decimal_count(len({item.memory_ref for item in supporting}))
    source_family_count = _decimal_count(
        len({item.source_family_ref for item in supporting}),
    )
    authority_count = _decimal_count(len({item.authority_ref for item in supporting}))
    average_memory_confidence_score = _average(
        tuple(item.memory_confidence_score for item in supporting),
    )
    average_source_authority_score = _average(
        tuple(item.source_authority_score for item in supporting),
    )
    source_family_quorum_score = _ratio_cap(
        source_family_count,
        config.min_source_family_count,
    )
    quorum_score = _average(
        (
            average_memory_confidence_score,
            average_source_authority_score,
            source_family_quorum_score,
        ),
    )
    status = _row_status(
        memory_count=memory_count,
        source_family_count=source_family_count,
        authority_count=authority_count,
        quorum_score=quorum_score,
        config=config,
    )
    return ResearchTeamMemorySourceAuthorityQuorumRow(
        item_digest=_private_digest(item_ref),
        observation_count=_decimal_count(len(observations)),
        supporting_memory_count=memory_count,
        supporting_source_family_count=source_family_count,
        supporting_authority_count=authority_count,
        average_memory_confidence_score=average_memory_confidence_score,
        average_source_authority_score=average_source_authority_score,
        source_family_quorum_score=source_family_quorum_score,
        quorum_score=quorum_score,
        latest_observed_at=max(item.observed_at for item in observations),
        status=status,
        reason_codes=_row_reason_codes(
            memory_count=memory_count,
            source_family_count=source_family_count,
            authority_count=authority_count,
            quorum_score=quorum_score,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    memory_count: Decimal,
    source_family_count: Decimal,
    authority_count: Decimal,
    quorum_score: Decimal,
    config: ResearchTeamMemorySourceAuthorityQuorumConfig,
) -> str:
    if (
        memory_count < config.min_memory_count
        or source_family_count < config.min_source_family_count
        or authority_count < config.min_authority_count
    ):
        return STATUS_BLOCK
    if quorum_score < config.min_watch_quorum_score:
        return STATUS_BLOCK
    if quorum_score < config.min_pass_quorum_score:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    memory_count: Decimal,
    source_family_count: Decimal,
    authority_count: Decimal,
    quorum_score: Decimal,
    status: str,
    config: ResearchTeamMemorySourceAuthorityQuorumConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if (
        memory_count == _ZERO
        and source_family_count == _ZERO
        and authority_count == _ZERO
    ):
        codes.append(REASON_MISSING_SUPPORT)
    if memory_count < config.min_memory_count:
        codes.append(REASON_INSUFFICIENT_MEMORY_QUORUM)
    if source_family_count < config.min_source_family_count:
        codes.append(REASON_INSUFFICIENT_SOURCE_FAMILY_QUORUM)
    if authority_count < config.min_authority_count:
        codes.append(REASON_INSUFFICIENT_AUTHORITY_QUORUM)
    if (
        status == STATUS_BLOCK
        and not codes
        and quorum_score < config.min_watch_quorum_score
    ):
        codes.append(REASON_QUORUM_SCORE_BLOCK)
    if status == STATUS_WATCH:
        codes.append(REASON_QUORUM_SCORE_WATCH)
    if status == STATUS_PASS:
        codes.append(REASON_MEMORY_SOURCE_AUTHORITY_QUORUM_PASS)
    return _normalize_reason_codes(codes)


def _report_status(rows: tuple[ResearchTeamMemorySourceAuthorityQuorumRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamMemorySourceAuthorityQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_EMPTY_OBSERVATIONS,)
    codes: list[str] = []
    for row in rows:
        codes.extend(row.reason_codes)
    return _normalize_reason_codes(codes)


def _status_count(
    rows: tuple[ResearchTeamMemorySourceAuthorityQuorumRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_rank(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return Decimal("0.000000")
    if status == STATUS_WATCH:
        return Decimal("1.000000")
    return Decimal("2.000000")


def _normalize_observations(
    observations: Sequence[ResearchTeamMemorySourceAuthorityObservation],
) -> tuple[ResearchTeamMemorySourceAuthorityObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchTeamMemorySourceAuthorityObservation] = []
    for item in observations:
        if type(item) is not ResearchTeamMemorySourceAuthorityObservation:
            raise ValueError(
                "observations must contain ResearchTeamMemorySourceAuthorityObservation",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.item_ref,
                item.observed_at.isoformat(),
                item.memory_ref,
                item.source_family_ref,
                item.authority_ref,
                item.memory_confidence_score,
                item.source_authority_score,
                item.supports_quorum,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchTeamMemorySourceAuthorityQuorumRow],
) -> tuple[ResearchTeamMemorySourceAuthorityQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamMemorySourceAuthorityQuorumRow] = []
    for row in rows:
        if type(row) is not ResearchTeamMemorySourceAuthorityQuorumRow:
            raise ValueError(
                "rows must contain ResearchTeamMemorySourceAuthorityQuorumRow items",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                _status_rank(row.status),
                row.quorum_score,
                row.item_digest,
            ),
        ),
    )


def _normalize_public_payload(
    public_payload: Sequence[ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem],
) -> tuple[ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem items",
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


def _validate_row_consistency(
    row: ResearchTeamMemorySourceAuthorityQuorumRow,
) -> None:
    if row.supporting_memory_count > row.observation_count:
        raise ValueError("supporting_memory_count cannot exceed observation_count")
    if row.supporting_source_family_count > row.observation_count:
        raise ValueError(
            "supporting_source_family_count cannot exceed observation_count",
        )
    if row.supporting_authority_count > row.observation_count:
        raise ValueError("supporting_authority_count cannot exceed observation_count")


def _validate_report_consistency(
    report: ResearchTeamMemorySourceAuthorityQuorumReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count does not match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count does not match rows")
    if report.average_quorum_score != _average(tuple(row.quorum_score for row in rows)):
        raise ValueError("average_quorum_score does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 256:
        raise ValueError(f"{field_name} must be nonempty public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 512:
        raise ValueError(f"{field_name} must be a nonempty private reference")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a private sha256 digest")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True in public payload")
        for item in value.values():
            _require_payload_hard_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_hard_flags(item)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_Q, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_reason_codes(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        if item not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains an unsupported reason code")
        if item not in seen:
            seen.add(item)
            normalized.append(item)
    rank = {item: index for index, item in enumerate(_REASON_CODE_SEQUENCE)}
    return tuple(sorted(normalized, key=lambda item: rank[item]))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(_Q, rounding=ROUND_HALF_UP)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _ratio_cap(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    return min(_ONE, _quantize(numerator / denominator))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_Q, rounding=ROUND_HALF_UP)


def _private_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchTeamMemorySourceAuthorityQuorumReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop(_DIGEST_FIELD)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return f"{value.quantize(_Q, rounding=ROUND_HALF_UP):f}"
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if isinstance(value, str):
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, Decimal):
        return
    if type(value) is datetime:
        return
    if type(value) is bool or value is None:
        return
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError("public payload container must be explicitly allowed")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list) and allow_json_containers:
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    raise ValueError(f"unsupported public payload value for {label}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.strip().lower()
    tokenized = re.sub(r"[^a-z0-9]+", " ", normalized)
    padded = f" {tokenized.strip()} "
    tokens = frozenset(tokenized.split())
    for fragment in _UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in ("http://", "https://", "://"):
            if fragment in normalized:
                raise ValueError(f"unsafe public payload field: {field_name}")
            continue
        fragment_tokens = tuple(
            item
            for item in re.sub(r"[^a-z0-9]+", " ", fragment).split()
            if item
        )
        if len(fragment_tokens) == 1 and fragment_tokens[0] in tokens:
            raise ValueError(f"unsafe public payload field: {field_name}")
        if len(fragment_tokens) > 1:
            phrase = " ".join(fragment_tokens)
            if f" {phrase} " in padded:
                raise ValueError(f"unsafe public payload field: {field_name}")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_SOURCE_AUTHORITY_QUORUM_CONFIG_VERSION",
    "STATUS_PASS",
    "STATUS_WATCH",
    "STATUS_BLOCK",
    "REASON_EMPTY_OBSERVATIONS",
    "REASON_MISSING_SUPPORT",
    "REASON_INSUFFICIENT_MEMORY_QUORUM",
    "REASON_INSUFFICIENT_SOURCE_FAMILY_QUORUM",
    "REASON_INSUFFICIENT_AUTHORITY_QUORUM",
    "REASON_QUORUM_SCORE_WATCH",
    "REASON_QUORUM_SCORE_BLOCK",
    "REASON_MEMORY_SOURCE_AUTHORITY_QUORUM_PASS",
    "ResearchTeamMemorySourceAuthorityQuorumConfig",
    "ResearchTeamMemorySourceAuthorityObservation",
    "ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem",
    "ResearchTeamMemorySourceAuthorityQuorumRow",
    "ResearchTeamMemorySourceAuthorityQuorumReport",
    "build_research_team_memory_source_authority_quorum_report",
    "research_team_memory_source_authority_quorum_report_public_payload",
    "research_team_memory_source_authority_quorum_report_digest",
    "validate_research_team_memory_source_authority_quorum_public_payload",
)
