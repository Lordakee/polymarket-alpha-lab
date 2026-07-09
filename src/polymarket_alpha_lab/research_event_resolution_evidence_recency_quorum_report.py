"""Report-only event resolution evidence recency quorum reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_CONFIG_VERSION = (
    "research-event-resolution-evidence-recency-quorum-report-v1"
)
RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_STATUSES = (
    "pass",
    "watch",
    "block",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_STATUSES = frozenset(RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_STATUSES)
_BLOCK_REASON_CODES = frozenset(
    (
        "insufficient_recent_evidence_quorum_block",
        "insufficient_independent_evidence_quorum_block",
        "evidence_recency_block",
        "conflict_pressure_block",
        "update_latency_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "insufficient_recent_evidence_quorum_block",
    "recent_evidence_quorum_watch",
    "insufficient_independent_evidence_quorum_block",
    "independent_evidence_quorum_watch",
    "evidence_recency_block",
    "evidence_recency_watch",
    "conflict_pressure_block",
    "conflict_pressure_watch",
    "update_latency_block",
    "update_latency_watch",
    "recency_quorum_score_watch",
    "evidence_recency_quorum_pass",
    "empty_evidence_recency_quorum_set",
)
_UNSAFE_PUBLIC_KEY_TOKENS = frozenset(
    (
        "auth",
        "buy",
        "candidate",
        "database",
        "db",
        "dsn",
        "live",
        "market",
        "network",
        "order",
        "question",
        "recommendation",
        "sell",
        "sizing",
        "slug",
        "source",
        "table",
        "text",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)
_UNSAFE_PUBLIC_VALUE_PATTERNS = (
    "://",
    "auth",
    "buy ",
    "candidate",
    "credential",
    "database",
    "dsn",
    "live trading",
    "market",
    "order",
    "password",
    "postgres",
    "private",
    "question",
    "recommendation",
    "secret",
    "sell ",
    "sizing",
    "slug",
    "source text",
    "source_text",
    "source url",
    "source_url",
    "table",
    "token",
    "trade",
    "wallet",
)
_STATUS_SORT_WEIGHT = {
    "pass": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "block": Decimal("2.000000"),
}


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceRecencyQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_CONFIG_VERSION
    )
    pass_recent_evidence_count: Decimal = Decimal("3.000000")
    watch_recent_evidence_count: Decimal = Decimal("2.000000")
    pass_independent_evidence_count: Decimal = Decimal("2.000000")
    watch_independent_evidence_count: Decimal = Decimal("1.000000")
    fresh_evidence_age_seconds: Decimal = Decimal("86400.000000")
    stale_evidence_age_seconds: Decimal = Decimal("259200.000000")
    conflict_watch_pressure: Decimal = Decimal("0.250000")
    conflict_block_pressure: Decimal = Decimal("0.500000")
    update_latency_watch_seconds: Decimal = Decimal("7200.000000")
    update_latency_block_seconds: Decimal = Decimal("21600.000000")
    min_recency_quorum_score: Decimal = Decimal("0.750000")
    quorum_weight: Decimal = Decimal("0.450000")
    recency_weight: Decimal = Decimal("0.350000")
    conflict_weight: Decimal = Decimal("0.150000")
    latency_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceRecencyQuorumConfig:
            raise TypeError(
                "ResearchEventResolutionEvidenceRecencyQuorumConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionEvidenceRecencyQuorumConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_recent_evidence_count",
            "watch_recent_evidence_count",
            "pass_independent_evidence_count",
            "watch_independent_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_recent_evidence_count > self.pass_recent_evidence_count:
            raise ValueError(
                "watch_recent_evidence_count must not exceed "
                "pass_recent_evidence_count",
            )
        if self.watch_independent_evidence_count > self.pass_independent_evidence_count:
            raise ValueError(
                "watch_independent_evidence_count must not exceed "
                "pass_independent_evidence_count",
            )
        for field_name in (
            "fresh_evidence_age_seconds",
            "stale_evidence_age_seconds",
            "update_latency_watch_seconds",
            "update_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_evidence_age_seconds > self.stale_evidence_age_seconds:
            raise ValueError(
                "fresh_evidence_age_seconds must not exceed stale_evidence_age_seconds",
            )
        if self.update_latency_watch_seconds > self.update_latency_block_seconds:
            raise ValueError(
                "update_latency_watch_seconds must not exceed "
                "update_latency_block_seconds",
            )
        for field_name in (
            "conflict_watch_pressure",
            "conflict_block_pressure",
            "min_recency_quorum_score",
            "quorum_weight",
            "recency_weight",
            "conflict_weight",
            "latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflict_watch_pressure > self.conflict_block_pressure:
            raise ValueError(
                "conflict_watch_pressure must not exceed conflict_block_pressure",
            )
        if (
            self.quorum_weight
            + self.recency_weight
            + self.conflict_weight
            + self.latency_weight
            != _ONE
        ):
            raise ValueError("recency quorum weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceRecencyQuorumInput:
    event_digest: str
    resolution_digest: str
    evidence_packet_digest: str
    recent_evidence_count: Decimal
    independent_evidence_count: Decimal
    newest_evidence_age_seconds: Decimal
    oldest_evidence_age_seconds: Decimal
    conflict_pressure: Decimal
    resolution_update_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceRecencyQuorumInput:
            raise TypeError(
                "ResearchEventResolutionEvidenceRecencyQuorumInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionEvidenceRecencyQuorumInput,
            "input",
        )
        for field_name in (
            "event_digest",
            "resolution_digest",
            "evidence_packet_digest",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        for field_name in ("recent_evidence_count", "independent_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_evidence_age_seconds",
            "oldest_evidence_age_seconds",
            "resolution_update_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_evidence_age_seconds < self.newest_evidence_age_seconds:
            raise ValueError(
                "oldest_evidence_age_seconds must be greater than or equal to "
                "newest_evidence_age_seconds",
            )
        object.__setattr__(
            self,
            "conflict_pressure",
            _require_ratio_decimal("conflict_pressure", self.conflict_pressure),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem:
            raise TypeError(
                "ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem,
            "public payload item",
        )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceRecencyQuorumRow:
    event_digest: str
    resolution_digest: str
    evidence_packet_digest: str
    recent_evidence_count: Decimal
    independent_evidence_count: Decimal
    quorum_score: Decimal
    recency_score: Decimal
    conflict_pressure: Decimal
    conflict_score: Decimal
    latency_score: Decimal
    recency_quorum_score: Decimal
    newest_evidence_age_seconds: Decimal
    oldest_evidence_age_seconds: Decimal
    resolution_update_latency_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceRecencyQuorumRow:
            raise TypeError(
                "ResearchEventResolutionEvidenceRecencyQuorumRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionEvidenceRecencyQuorumRow, "row")
        for field_name in (
            "event_digest",
            "resolution_digest",
            "evidence_packet_digest",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        for field_name in ("recent_evidence_count", "independent_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quorum_score",
            "recency_score",
            "conflict_pressure",
            "conflict_score",
            "latency_score",
            "recency_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_evidence_age_seconds",
            "oldest_evidence_age_seconds",
            "resolution_update_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_evidence_age_seconds < self.newest_evidence_age_seconds:
            raise ValueError(
                "oldest_evidence_age_seconds must be greater than or equal to "
                "newest_evidence_age_seconds",
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceRecencyQuorumReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_recency_quorum_score: Decimal
    average_quorum_score: Decimal
    average_recency_score: Decimal
    average_conflict_pressure: Decimal
    average_latency_score: Decimal
    insufficient_quorum_count: Decimal
    stale_evidence_count: Decimal
    conflict_pressure_count: Decimal
    update_latency_count: Decimal
    rows: tuple[ResearchEventResolutionEvidenceRecencyQuorumRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceRecencyQuorumReport:
            raise TypeError(
                "ResearchEventResolutionEvidenceRecencyQuorumReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionEvidenceRecencyQuorumReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "insufficient_quorum_count",
            "stale_evidence_count",
            "conflict_pressure_count",
            "update_latency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_recency_quorum_score",
            "average_quorum_score",
            "average_recency_score",
            "average_conflict_pressure",
            "average_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_event_resolution_evidence_recency_quorum_public_payload(self)


def build_research_event_resolution_evidence_recency_quorum_report(
    inputs: Sequence[ResearchEventResolutionEvidenceRecencyQuorumInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig | None = None,
    public_payload: Sequence[
        ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem
    ] = (),
) -> ResearchEventResolutionEvidenceRecencyQuorumReport:
    """Build a deterministic report-only evidence recency quorum snapshot."""

    if config is None:
        config = ResearchEventResolutionEvidenceRecencyQuorumConfig()
    if type(config) is not ResearchEventResolutionEvidenceRecencyQuorumConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionEvidenceRecencyQuorumConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_recency_quorum_score": _average(
            tuple(row.recency_quorum_score for row in rows),
        ),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "average_recency_score": _average(tuple(row.recency_score for row in rows)),
        "average_conflict_pressure": _average(
            tuple(row.conflict_pressure for row in rows),
        ),
        "average_latency_score": _average(tuple(row.latency_score for row in rows)),
        "insufficient_quorum_count": _quorum_penalty_count(rows),
        "stale_evidence_count": _reason_prefix_count(rows, "evidence_recency_"),
        "conflict_pressure_count": _reason_prefix_count(rows, "conflict_pressure_"),
        "update_latency_count": _reason_prefix_count(rows, "update_latency_"),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionEvidenceRecencyQuorumReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_evidence_recency_quorum_public_payload(
    report: ResearchEventResolutionEvidenceRecencyQuorumReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventResolutionEvidenceRecencyQuorumReport:
        raise ValueError(
            "report must be a ResearchEventResolutionEvidenceRecencyQuorumReport",
        )
    _rebuild_report_for_payload(report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(
        "ResearchEventResolutionEvidenceRecencyQuorumReport.payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_event_resolution_evidence_recency_quorum_report_digest(
    report: ResearchEventResolutionEvidenceRecencyQuorumReport,
) -> str:
    if type(report) is not ResearchEventResolutionEvidenceRecencyQuorumReport:
        raise ValueError(
            "report must be a ResearchEventResolutionEvidenceRecencyQuorumReport",
        )
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_event_resolution_evidence_recency_quorum_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    payload_copy = dict(payload)
    _reject_unsafe_public_payload(
        "research_event_resolution_evidence_recency_quorum_public_payload",
        payload_copy,
        allow_json_containers=True,
    )
    digest = payload_copy.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload_copy)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = _public_payload_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    _require_hard_flags("payload", _DictFlags(payload_copy))
    return payload_copy


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

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
    item: ResearchEventResolutionEvidenceRecencyQuorumInput,
    *,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig,
) -> ResearchEventResolutionEvidenceRecencyQuorumRow:
    recent_quorum_score = _clamp_ratio(
        item.recent_evidence_count / config.pass_recent_evidence_count,
    )
    independent_quorum_score = _clamp_ratio(
        item.independent_evidence_count / config.pass_independent_evidence_count,
    )
    quorum_score = _average((recent_quorum_score, independent_quorum_score))
    recency_score = _recency_score(item.newest_evidence_age_seconds, config)
    conflict_score = _conflict_score(item.conflict_pressure, config)
    latency_score = _latency_score(item.resolution_update_latency_seconds, config)
    recency_quorum_score = _recency_quorum_score(
        quorum_score=quorum_score,
        recency_score=recency_score,
        conflict_score=conflict_score,
        latency_score=latency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        recency_quorum_score=recency_quorum_score,
        config=config,
    )
    return ResearchEventResolutionEvidenceRecencyQuorumRow(
        event_digest=item.event_digest,
        resolution_digest=item.resolution_digest,
        evidence_packet_digest=item.evidence_packet_digest,
        recent_evidence_count=item.recent_evidence_count,
        independent_evidence_count=item.independent_evidence_count,
        quorum_score=quorum_score,
        recency_score=recency_score,
        conflict_pressure=item.conflict_pressure,
        conflict_score=conflict_score,
        latency_score=latency_score,
        recency_quorum_score=recency_quorum_score,
        newest_evidence_age_seconds=item.newest_evidence_age_seconds,
        oldest_evidence_age_seconds=item.oldest_evidence_age_seconds,
        resolution_update_latency_seconds=item.resolution_update_latency_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchEventResolutionEvidenceRecencyQuorumInput,
    *,
    recency_quorum_score: Decimal,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.recent_evidence_count < config.watch_recent_evidence_count:
        reason_codes.append("insufficient_recent_evidence_quorum_block")
    elif item.recent_evidence_count < config.pass_recent_evidence_count:
        reason_codes.append("recent_evidence_quorum_watch")
    if item.independent_evidence_count < config.watch_independent_evidence_count:
        reason_codes.append("insufficient_independent_evidence_quorum_block")
    elif item.independent_evidence_count < config.pass_independent_evidence_count:
        reason_codes.append("independent_evidence_quorum_watch")
    if item.newest_evidence_age_seconds > config.stale_evidence_age_seconds:
        reason_codes.append("evidence_recency_block")
    elif item.oldest_evidence_age_seconds > config.fresh_evidence_age_seconds:
        reason_codes.append("evidence_recency_watch")
    if item.conflict_pressure >= config.conflict_block_pressure:
        reason_codes.append("conflict_pressure_block")
    elif item.conflict_pressure >= config.conflict_watch_pressure:
        reason_codes.append("conflict_pressure_watch")
    if item.resolution_update_latency_seconds >= config.update_latency_block_seconds:
        reason_codes.append("update_latency_block")
    elif item.resolution_update_latency_seconds >= config.update_latency_watch_seconds:
        reason_codes.append("update_latency_watch")
    if (
        not _has_block_reason(reason_codes)
        and recency_quorum_score < config.min_recency_quorum_score
    ):
        reason_codes.append("recency_quorum_score_watch")
    if not reason_codes:
        reason_codes.append("evidence_recency_quorum_pass")
    return _normalize_reason_codes(reason_codes)


def _recency_score(
    newest_evidence_age_seconds: Decimal,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig,
) -> Decimal:
    if newest_evidence_age_seconds <= config.fresh_evidence_age_seconds:
        return _ONE
    if newest_evidence_age_seconds >= config.stale_evidence_age_seconds:
        return _ZERO
    window = config.stale_evidence_age_seconds - config.fresh_evidence_age_seconds
    if window == _ZERO:
        return _ZERO
    return _clamp_ratio(
        (config.stale_evidence_age_seconds - newest_evidence_age_seconds) / window,
    )


def _conflict_score(
    conflict_pressure: Decimal,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig,
) -> Decimal:
    if config.conflict_block_pressure == _ZERO:
        return _ZERO if conflict_pressure > _ZERO else _ONE
    return _clamp_ratio(_ONE - conflict_pressure / config.conflict_block_pressure)


def _latency_score(
    resolution_update_latency_seconds: Decimal,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig,
) -> Decimal:
    if resolution_update_latency_seconds <= config.update_latency_watch_seconds:
        return _ONE
    if resolution_update_latency_seconds >= config.update_latency_block_seconds:
        return _ZERO
    window = config.update_latency_block_seconds - config.update_latency_watch_seconds
    if window == _ZERO:
        return _ZERO
    return _clamp_ratio(
        (config.update_latency_block_seconds - resolution_update_latency_seconds)
        / window,
    )


def _recency_quorum_score(
    *,
    quorum_score: Decimal,
    recency_score: Decimal,
    conflict_score: Decimal,
    latency_score: Decimal,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig,
) -> Decimal:
    return _clamp_ratio(
        quorum_score * config.quorum_weight
        + recency_score * config.recency_weight
        + conflict_score * config.conflict_weight
        + latency_score * config.latency_weight,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchEventResolutionEvidenceRecencyQuorumInput],
) -> tuple[ResearchEventResolutionEvidenceRecencyQuorumInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchEventResolutionEvidenceRecencyQuorumInput] = []
    seen: set[tuple[str, str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchEventResolutionEvidenceRecencyQuorumInput:
            raise ValueError(
                "inputs must contain ResearchEventResolutionEvidenceRecencyQuorumInput",
            )
        _require_hard_flags("input", item)
        key = (item.event_digest, item.resolution_digest, item.evidence_packet_digest)
        if key in seen:
            raise ValueError("input digests must be unique")
        seen.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_digest,
                item.resolution_digest,
                item.evidence_packet_digest,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEventResolutionEvidenceRecencyQuorumRow],
) -> tuple[ResearchEventResolutionEvidenceRecencyQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionEvidenceRecencyQuorumRow] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionEvidenceRecencyQuorumRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionEvidenceRecencyQuorumRow",
            )
        _require_hard_flags("row", row)
        key = (row.event_digest, row.resolution_digest, row.evidence_packet_digest)
        if key in seen:
            raise ValueError("row digests must be unique")
        seen.add(key)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must use canonical sequence")
    return sorted_rows


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem
    ],
) -> tuple[ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_report_consistency(
    report: ResearchEventResolutionEvidenceRecencyQuorumReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count does not match rows")
    for status in _STATUSES:
        if getattr(report, f"{status}_count") != _status_count(rows, status):
            raise ValueError(f"{status}_count does not match rows")
    if report.insufficient_quorum_count != _quorum_penalty_count(rows):
        raise ValueError("insufficient_quorum_count does not match rows")
    if report.stale_evidence_count != _reason_prefix_count(rows, "evidence_recency_"):
        raise ValueError("stale_evidence_count does not match rows")
    if report.conflict_pressure_count != _reason_prefix_count(
        rows,
        "conflict_pressure_",
    ):
        raise ValueError("conflict_pressure_count does not match rows")
    if report.update_latency_count != _reason_prefix_count(rows, "update_latency_"):
        raise ValueError("update_latency_count does not match rows")
    expected_averages = {
        "average_recency_quorum_score": _average(
            tuple(row.recency_quorum_score for row in rows),
        ),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "average_recency_score": _average(tuple(row.recency_score for row in rows)),
        "average_conflict_pressure": _average(
            tuple(row.conflict_pressure for row in rows),
        ),
        "average_latency_score": _average(tuple(row.latency_score for row in rows)),
    }
    for field_name, expected in expected_averages.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")


def _row_status(reason_codes: Sequence[str]) -> str:
    if _has_block_reason(reason_codes):
        return "block"
    if tuple(reason_codes) == ("evidence_recency_quorum_pass",):
        return "pass"
    return "watch"


def _has_block_reason(reason_codes: Sequence[str]) -> bool:
    return any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes)


def _report_status(
    rows: tuple[ResearchEventResolutionEvidenceRecencyQuorumRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionEvidenceRecencyQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence_recency_quorum_set",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _status_count(
    rows: tuple[ResearchEventResolutionEvidenceRecencyQuorumRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_prefix_count(
    rows: tuple[ResearchEventResolutionEvidenceRecencyQuorumRow, ...],
    prefix: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code.startswith(prefix) for code in row.reason_codes)),
    )


def _quorum_penalty_count(
    rows: tuple[ResearchEventResolutionEvidenceRecencyQuorumRow, ...],
) -> Decimal:
    quorum_penalty_reasons = (
        "insufficient_recent_evidence_quorum_block",
        "recent_evidence_quorum_watch",
        "insufficient_independent_evidence_quorum_block",
        "independent_evidence_quorum_watch",
    )
    return _decimal_count(
        sum(
            1
            for row in rows
            if any(code in quorum_penalty_reasons for code in row.reason_codes)
        ),
    )


def _row_sort_key(
    row: ResearchEventResolutionEvidenceRecencyQuorumRow,
) -> tuple[Decimal, str, str, str]:
    return (
        _STATUS_SORT_WEIGHT[row.status],
        row.event_digest,
        row.resolution_digest,
        row.evidence_packet_digest,
    )


def _rebuild_report_for_payload(
    report: ResearchEventResolutionEvidenceRecencyQuorumReport,
) -> None:
    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}
    try:
        ResearchEventResolutionEvidenceRecencyQuorumReport(**kwargs)
    except Exception as exc:
        raise ValueError(
            "ResearchEventResolutionEvidenceRecencyQuorumReport failed payload "
            "revalidation",
        ) from exc


def _report_values_without_digest(
    report: ResearchEventResolutionEvidenceRecencyQuorumReport,
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


def _public_payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload(
        "public payload digest",
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
        _require_six_decimal_decimal("Decimal payload value", value)
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
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    if any(token in _UNSAFE_PUBLIC_KEY_TOKENS for token in tokens):
        raise ValueError(f"{path}.{key} has unsafe public field")
    if any(
        term in lowered
        for term in (
            "candidate_id",
            "market_id",
            "market_slug",
            "source_url",
            "source_text",
            "table_name",
        )
    ):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(pattern in lowered for pattern in _UNSAFE_PUBLIC_VALUE_PATTERNS):
        raise ValueError(f"{path} has unsafe public value")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must have hard {field_name}=True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


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
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    _reject_unsafe_public_string(field_name, normalized)
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
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


def _require_six_decimal_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


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


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_STATUSES",
    "ResearchEventResolutionEvidenceRecencyQuorumConfig",
    "ResearchEventResolutionEvidenceRecencyQuorumInput",
    "ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem",
    "ResearchEventResolutionEvidenceRecencyQuorumReport",
    "ResearchEventResolutionEvidenceRecencyQuorumRow",
    "build_research_event_resolution_evidence_recency_quorum_report",
    "research_event_resolution_evidence_recency_quorum_public_payload",
    "research_event_resolution_evidence_recency_quorum_report_digest",
    "validate_research_event_resolution_evidence_recency_quorum_public_payload",
)
