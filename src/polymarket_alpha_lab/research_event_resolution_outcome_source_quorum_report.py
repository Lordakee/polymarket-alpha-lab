"""Report-only outcome resolution quorum readiness reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_OUTCOME_SOURCE_QUORUM_CONFIG_VERSION = (
    "research-event-resolution-outcome-source-quorum-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_BLOCK_REASON_CODES = frozenset(
    (
        "insufficient_authoritative_quorum_block",
        "source_freshness_block",
        "contradiction_pressure_block",
        "deadline_proximity_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "insufficient_authoritative_quorum_block",
    "authoritative_quorum_watch",
    "source_freshness_block",
    "source_freshness_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "deadline_proximity_block",
    "deadline_proximity_watch",
    "readiness_score_watch",
    "resolution_outcome_source_quorum_pass",
    "empty_resolution_outcome_source_quorum_set",
)
_UNSAFE_PUBLIC_KEY_TOKENS = frozenset(
    (
        "candidate",
        "auth",
        "credential",
        "market",
        "password",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "database",
        "live",
        "network",
        "buy",
        "sell",
        "sizing",
        "recommendation",
    ),
)
_UNSAFE_PUBLIC_VALUE_TOKENS = frozenset(
    (
        "auth",
        "authentication",
        "authorization",
        "buy",
        "candidate",
        "credential",
        "dsn",
        "live",
        "market",
        "order",
        "password",
        "question",
        "recommendation",
        "sell",
        "sizing",
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
    "candidate",
    "credential",
    "dsn",
    "live trading",
    "market id",
    "market_id",
    "market slug",
    "market_slug",
    "order",
    "password",
    "postgres",
    "question",
    "recommendation",
    "sizing",
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
class ResearchEventResolutionOutcomeSourceQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_OUTCOME_SOURCE_QUORUM_CONFIG_VERSION
    )
    pass_authoritative_source_count: Decimal = Decimal("3.000000")
    watch_authoritative_source_count: Decimal = Decimal("2.000000")
    max_fresh_source_age_seconds: Decimal = Decimal("86400.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.250000")
    contradiction_block_pressure: Decimal = Decimal("0.500000")
    deadline_watch_seconds: Decimal = Decimal("7200.000000")
    deadline_block_seconds: Decimal = Decimal("0.000000")
    min_readiness_score: Decimal = Decimal("0.750000")
    quorum_weight: Decimal = Decimal("0.140000")
    freshness_weight: Decimal = Decimal("0.020000")
    contradiction_weight: Decimal = Decimal("0.750000")
    deadline_weight: Decimal = Decimal("0.090000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionOutcomeSourceQuorumConfig:
            raise TypeError(
                "ResearchEventResolutionOutcomeSourceQuorumConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionOutcomeSourceQuorumConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventResolutionOutcomeSourceQuorumConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_OUTCOME_SOURCE_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_authoritative_source_count",
            "watch_authoritative_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_authoritative_source_count > self.pass_authoritative_source_count:
            raise ValueError(
                "watch_authoritative_source_count must not exceed "
                "pass_authoritative_source_count",
            )
        object.__setattr__(
            self,
            "max_fresh_source_age_seconds",
            _require_positive_decimal(
                "max_fresh_source_age_seconds",
                self.max_fresh_source_age_seconds,
            ),
        )
        for field_name in (
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "min_readiness_score",
            "quorum_weight",
            "freshness_weight",
            "contradiction_weight",
            "deadline_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.contradiction_watch_pressure > self.contradiction_block_pressure:
            raise ValueError(
                "contradiction_watch_pressure must not exceed "
                "contradiction_block_pressure",
            )
        for field_name in ("deadline_watch_seconds", "deadline_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.deadline_block_seconds > self.deadline_watch_seconds:
            raise ValueError(
                "deadline_block_seconds must not exceed deadline_watch_seconds",
            )
        if (
            self.quorum_weight
            + self.freshness_weight
            + self.contradiction_weight
            + self.deadline_weight
            != _ONE
        ):
            raise ValueError("readiness weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionOutcomeSourceQuorumInput:
    event_digest: str
    outcome_digest: str
    authoritative_source_count: Decimal
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    contradiction_pressure: Decimal
    seconds_until_deadline: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionOutcomeSourceQuorumInput:
            raise TypeError(
                "ResearchEventResolutionOutcomeSourceQuorumInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionOutcomeSourceQuorumInput:
            raise ValueError(
                "input must be exactly "
                "ResearchEventResolutionOutcomeSourceQuorumInput",
            )
        _require_sha256_digest("event_digest", self.event_digest)
        _require_sha256_digest("outcome_digest", self.outcome_digest)
        object.__setattr__(
            self,
            "authoritative_source_count",
            _require_nonnegative_count_decimal(
                "authoritative_source_count",
                self.authoritative_source_count,
            ),
        )
        for field_name in (
            "newest_source_age_seconds",
            "oldest_source_age_seconds",
            "seconds_until_deadline",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_source_age_seconds < self.newest_source_age_seconds:
            raise ValueError(
                "oldest_source_age_seconds must be greater than or equal to "
                "newest_source_age_seconds",
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal(
                "contradiction_pressure",
                self.contradiction_pressure,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem:
            raise TypeError(
                "ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem",
            )
        object.__setattr__(self, "key", _require_public_payload_key("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventResolutionOutcomeSourceQuorumRow:
    event_digest: str
    outcome_digest: str
    authoritative_source_count: Decimal
    quorum_score: Decimal
    freshness_score: Decimal
    contradiction_pressure: Decimal
    contradiction_score: Decimal
    deadline_proximity_score: Decimal
    readiness_score: Decimal
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    seconds_until_deadline: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionOutcomeSourceQuorumRow:
            raise TypeError(
                "ResearchEventResolutionOutcomeSourceQuorumRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionOutcomeSourceQuorumRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionOutcomeSourceQuorumRow",
            )
        _require_sha256_digest("event_digest", self.event_digest)
        _require_sha256_digest("outcome_digest", self.outcome_digest)
        object.__setattr__(
            self,
            "authoritative_source_count",
            _require_nonnegative_count_decimal(
                "authoritative_source_count",
                self.authoritative_source_count,
            ),
        )
        for field_name in (
            "quorum_score",
            "freshness_score",
            "contradiction_pressure",
            "contradiction_score",
            "deadline_proximity_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_source_age_seconds",
            "oldest_source_age_seconds",
            "seconds_until_deadline",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_source_age_seconds < self.newest_source_age_seconds:
            raise ValueError(
                "oldest_source_age_seconds must be greater than or equal to "
                "newest_source_age_seconds",
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
class ResearchEventResolutionOutcomeSourceQuorumReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    average_quorum_score: Decimal
    average_freshness_score: Decimal
    average_contradiction_pressure: Decimal
    average_deadline_proximity_score: Decimal
    source_freshness_penalty_count: Decimal
    contradiction_pressure_count: Decimal
    deadline_proximity_count: Decimal
    rows: tuple[ResearchEventResolutionOutcomeSourceQuorumRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionOutcomeSourceQuorumReport:
            raise TypeError(
                "ResearchEventResolutionOutcomeSourceQuorumReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionOutcomeSourceQuorumReport:
            raise ValueError(
                "report must be exactly ResearchEventResolutionOutcomeSourceQuorumReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_OUTCOME_SOURCE_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "source_freshness_penalty_count",
            "contradiction_pressure_count",
            "deadline_proximity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "average_quorum_score",
            "average_freshness_score",
            "average_contradiction_pressure",
            "average_deadline_proximity_score",
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
        return research_event_resolution_outcome_source_quorum_public_payload(self)


def build_research_event_resolution_outcome_source_quorum_report(
    inputs: Sequence[ResearchEventResolutionOutcomeSourceQuorumInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig | None = None,
    public_payload: Sequence[
        ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem
    ] = (),
) -> ResearchEventResolutionOutcomeSourceQuorumReport:
    """Build a deterministic report-only quorum readiness snapshot."""

    if config is None:
        config = ResearchEventResolutionOutcomeSourceQuorumConfig()
    if type(config) is not ResearchEventResolutionOutcomeSourceQuorumConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionOutcomeSourceQuorumConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    payload_items = _normalize_public_payload(public_payload)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_readiness_score": _average(tuple(row.readiness_score for row in rows)),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "average_freshness_score": _average(tuple(row.freshness_score for row in rows)),
        "average_contradiction_pressure": _average(
            tuple(row.contradiction_pressure for row in rows),
        ),
        "average_deadline_proximity_score": _average(
            tuple(row.deadline_proximity_score for row in rows),
        ),
        "source_freshness_penalty_count": _reason_prefix_count(rows, "source_freshness_"),
        "contradiction_pressure_count": _reason_prefix_count(
            rows,
            "contradiction_pressure_",
        ),
        "deadline_proximity_count": _reason_prefix_count(rows, "deadline_proximity_"),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionOutcomeSourceQuorumReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_outcome_source_quorum_public_payload(
    report: ResearchEventResolutionOutcomeSourceQuorumReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventResolutionOutcomeSourceQuorumReport:
        raise ValueError(
            "report must be a ResearchEventResolutionOutcomeSourceQuorumReport",
        )
    _rebuild_report_for_payload(report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(
        "ResearchEventResolutionOutcomeSourceQuorumReport.payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


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
    item: ResearchEventResolutionOutcomeSourceQuorumInput,
    *,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig,
) -> ResearchEventResolutionOutcomeSourceQuorumRow:
    quorum_score = _clamp_ratio(
        item.authoritative_source_count / config.pass_authoritative_source_count,
    )
    freshness_score = _freshness_score(item.newest_source_age_seconds, config)
    contradiction_score = _contradiction_score(item.contradiction_pressure, config)
    deadline_score = _deadline_proximity_score(item.seconds_until_deadline, config)
    readiness_score = _readiness_score(
        quorum_score=quorum_score,
        freshness_score=freshness_score,
        contradiction_score=contradiction_score,
        deadline_proximity_score=deadline_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        readiness_score=readiness_score,
        config=config,
    )
    return ResearchEventResolutionOutcomeSourceQuorumRow(
        event_digest=item.event_digest,
        outcome_digest=item.outcome_digest,
        authoritative_source_count=item.authoritative_source_count,
        quorum_score=quorum_score,
        freshness_score=freshness_score,
        contradiction_pressure=item.contradiction_pressure,
        contradiction_score=contradiction_score,
        deadline_proximity_score=deadline_score,
        readiness_score=readiness_score,
        newest_source_age_seconds=item.newest_source_age_seconds,
        oldest_source_age_seconds=item.oldest_source_age_seconds,
        seconds_until_deadline=item.seconds_until_deadline,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchEventResolutionOutcomeSourceQuorumInput,
    *,
    readiness_score: Decimal,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.authoritative_source_count < config.watch_authoritative_source_count:
        reason_codes.append("insufficient_authoritative_quorum_block")
    elif item.authoritative_source_count < config.pass_authoritative_source_count:
        reason_codes.append("authoritative_quorum_watch")
    if item.newest_source_age_seconds > config.max_fresh_source_age_seconds:
        reason_codes.append("source_freshness_block")
    elif item.oldest_source_age_seconds > config.max_fresh_source_age_seconds:
        reason_codes.append("source_freshness_watch")
    if item.contradiction_pressure >= config.contradiction_block_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif item.contradiction_pressure >= config.contradiction_watch_pressure:
        reason_codes.append("contradiction_pressure_watch")
    if item.seconds_until_deadline <= config.deadline_block_seconds:
        reason_codes.append("deadline_proximity_block")
    elif item.seconds_until_deadline <= config.deadline_watch_seconds:
        reason_codes.append("deadline_proximity_watch")
    if (
        not _has_block_reason(reason_codes)
        and readiness_score < config.min_readiness_score
    ):
        reason_codes.append("readiness_score_watch")
    if not reason_codes:
        reason_codes.append("resolution_outcome_source_quorum_pass")
    return _normalize_reason_codes(reason_codes)


def _freshness_score(
    newest_source_age_seconds: Decimal,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig,
) -> Decimal:
    return _clamp_ratio(
        _ONE - newest_source_age_seconds / config.max_fresh_source_age_seconds,
    )


def _contradiction_score(
    contradiction_pressure: Decimal,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig,
) -> Decimal:
    if config.contradiction_block_pressure == _ZERO:
        return _ZERO if contradiction_pressure > _ZERO else _ONE
    return _clamp_ratio(_ONE - contradiction_pressure / config.contradiction_block_pressure)


def _deadline_proximity_score(
    seconds_until_deadline: Decimal,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig,
) -> Decimal:
    if seconds_until_deadline >= config.deadline_watch_seconds:
        return _ONE
    if seconds_until_deadline <= config.deadline_block_seconds:
        return _ZERO
    window = config.deadline_watch_seconds - config.deadline_block_seconds
    if window == _ZERO:
        return _ZERO
    return _clamp_ratio((seconds_until_deadline - config.deadline_block_seconds) / window)


def _readiness_score(
    *,
    quorum_score: Decimal,
    freshness_score: Decimal,
    contradiction_score: Decimal,
    deadline_proximity_score: Decimal,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig,
) -> Decimal:
    return _clamp_ratio(
        quorum_score * config.quorum_weight
        + freshness_score * config.freshness_weight
        + contradiction_score * config.contradiction_weight
        + deadline_proximity_score * config.deadline_weight,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchEventResolutionOutcomeSourceQuorumInput],
) -> tuple[ResearchEventResolutionOutcomeSourceQuorumInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchEventResolutionOutcomeSourceQuorumInput] = []
    seen: set[tuple[str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchEventResolutionOutcomeSourceQuorumInput:
            raise ValueError(
                "inputs must contain ResearchEventResolutionOutcomeSourceQuorumInput",
            )
        _require_hard_flags("input", item)
        key = (item.event_digest, item.outcome_digest)
        if key in seen:
            raise ValueError("event and outcome digests must be unique")
        seen.add(key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.event_digest, item.outcome_digest)))


def _normalize_rows(
    rows: Sequence[ResearchEventResolutionOutcomeSourceQuorumRow],
) -> tuple[ResearchEventResolutionOutcomeSourceQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionOutcomeSourceQuorumRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionOutcomeSourceQuorumRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionOutcomeSourceQuorumRow",
            )
        _require_hard_flags("row", row)
        key = (row.event_digest, row.outcome_digest)
        if key in seen:
            raise ValueError("row digests must be unique")
        seen.add(key)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must use canonical sequence")
    return sorted_rows


def _normalize_public_payload(
    public_payload: Sequence[ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem],
) -> tuple[ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    sorted_items = tuple(sorted(normalized, key=lambda item: item.key))
    if tuple(normalized) != sorted_items:
        raise ValueError("public_payload must use canonical sequence")
    return sorted_items


def _validate_report_consistency(
    report: ResearchEventResolutionOutcomeSourceQuorumReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count does not match rows")
    for status in _STATUSES:
        if getattr(report, f"{status}_count") != _status_count(rows, status):
            raise ValueError(f"{status}_count does not match rows")
    if report.source_freshness_penalty_count != _reason_prefix_count(
        rows,
        "source_freshness_",
    ):
        raise ValueError("source_freshness_penalty_count does not match rows")
    if report.contradiction_pressure_count != _reason_prefix_count(
        rows,
        "contradiction_pressure_",
    ):
        raise ValueError("contradiction_pressure_count does not match rows")
    if report.deadline_proximity_count != _reason_prefix_count(
        rows,
        "deadline_proximity_",
    ):
        raise ValueError("deadline_proximity_count does not match rows")
    expected_averages = {
        "average_readiness_score": _average(tuple(row.readiness_score for row in rows)),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "average_freshness_score": _average(tuple(row.freshness_score for row in rows)),
        "average_contradiction_pressure": _average(
            tuple(row.contradiction_pressure for row in rows),
        ),
        "average_deadline_proximity_score": _average(
            tuple(row.deadline_proximity_score for row in rows),
        ),
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
    if tuple(reason_codes) == ("resolution_outcome_source_quorum_pass",):
        return "pass"
    return "watch"


def _has_block_reason(reason_codes: Sequence[str]) -> bool:
    return any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes)


def _report_status(
    rows: tuple[ResearchEventResolutionOutcomeSourceQuorumRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionOutcomeSourceQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_resolution_outcome_source_quorum_set",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _status_count(
    rows: tuple[ResearchEventResolutionOutcomeSourceQuorumRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_prefix_count(
    rows: tuple[ResearchEventResolutionOutcomeSourceQuorumRow, ...],
    prefix: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code.startswith(prefix) for code in row.reason_codes)),
    )


def _row_sort_key(
    row: ResearchEventResolutionOutcomeSourceQuorumRow,
) -> tuple[Decimal, str, str]:
    return (_STATUS_SORT_WEIGHT[row.status], row.event_digest, row.outcome_digest)


def _rebuild_report_for_payload(
    report: ResearchEventResolutionOutcomeSourceQuorumReport,
) -> None:
    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}
    try:
        ResearchEventResolutionOutcomeSourceQuorumReport(**kwargs)
    except Exception as exc:
        raise ValueError(
            "ResearchEventResolutionOutcomeSourceQuorumReport failed payload "
            "revalidation",
        ) from exc


def _report_values_without_digest(
    report: ResearchEventResolutionOutcomeSourceQuorumReport,
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
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    if any(pattern in lowered for pattern in _UNSAFE_PUBLIC_VALUE_PATTERNS) or any(
        token in _UNSAFE_PUBLIC_VALUE_TOKENS for token in tokens
    ):
        raise ValueError(f"{path} has unsafe public value")


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
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_payload_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_key(value, field_name)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
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
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_OUTCOME_SOURCE_QUORUM_CONFIG_VERSION",
    "ResearchEventResolutionOutcomeSourceQuorumConfig",
    "ResearchEventResolutionOutcomeSourceQuorumInput",
    "ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem",
    "ResearchEventResolutionOutcomeSourceQuorumReport",
    "ResearchEventResolutionOutcomeSourceQuorumRow",
    "build_research_event_resolution_outcome_source_quorum_report",
    "research_event_resolution_outcome_source_quorum_public_payload",
)
