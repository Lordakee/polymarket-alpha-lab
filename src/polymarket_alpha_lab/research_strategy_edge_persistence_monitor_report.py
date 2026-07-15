"""Read-only monitor for probability edge persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EDGE_PERSISTENCE_MONITOR_REPORT_CONFIG_VERSION = (
    "research-strategy-edge-persistence-monitor-report-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "edge_persistent",
    "edge_not_persistent",
    "evidence_aging_watch",
    "edge_movement_watch",
    "cost_drag_watch",
    "liquidity_quality_watch",
    "liquidity_quality_block",
    "confidence_haircut_watch",
    "resolution_ambiguity_watch",
    "resolution_ambiguity_block",
)
REPORT_REASON_CODES = (
    "edge_persistence_clear",
    "edge_persistence_watch",
    "edge_persistence_block",
    "evidence_aging_watch",
    "edge_movement_watch",
    "cost_drag_watch",
    "liquidity_quality_watch",
    "liquidity_quality_block",
    "confidence_haircut_watch",
    "resolution_ambiguity_watch",
    "resolution_ambiguity_block",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
REDACTED_SOURCE_REF_PREFIX = "source_ref_"
REDACTED_DIGEST_LENGTH = 16

UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate",
    "condition",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "text",
    "d" + "sn",
    "table",
    "token",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "candidate",
    "condition",
    "market_id",
    "market_slug",
    "question",
    "url",
    "raw-",
    "token",
    "secret",
    "private",
    "d" + "sn",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
)

REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "source_row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "persisted_edge_count",
    "mean_adjusted_edge_probability",
    "min_adjusted_edge_probability",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "payload_sha256",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "redacted_source_ref",
    "observed_at",
    "baseline_edge_probability",
    "current_edge_probability",
    "edge_movement_probability",
    "evidence_age_hours",
    "evidence_age_drag_probability",
    "cost_drag_probability",
    "liquidity_quality_score",
    "liquidity_drag_probability",
    "confidence_haircut_probability",
    "resolution_ambiguity_score",
    "resolution_ambiguity_drag_probability",
    "adjusted_edge_probability",
    "persistence_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True, slots=True)
class ResearchStrategyEdgePersistenceMonitorConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EDGE_PERSISTENCE_MONITOR_REPORT_CONFIG_VERSION
    )
    persisted_edge_floor: Decimal = Decimal("0.050000")
    watch_edge_floor: Decimal = Decimal("0.015000")
    max_evidence_age_hours: Decimal = Decimal("24.000000")
    evidence_age_drag_cap: Decimal = Decimal("0.040000")
    market_movement_watch_probability: Decimal = Decimal("0.040000")
    cost_drag_watch_probability: Decimal = Decimal("0.020000")
    liquidity_watch_floor: Decimal = Decimal("0.500000")
    liquidity_block_floor: Decimal = Decimal("0.200000")
    liquidity_drag_cap: Decimal = Decimal("0.020000")
    confidence_haircut_watch_probability: Decimal = Decimal("0.030000")
    resolution_ambiguity_watch_score: Decimal = Decimal("0.500000")
    resolution_ambiguity_block_score: Decimal = Decimal("0.750000")
    resolution_ambiguity_drag_cap: Decimal = Decimal("0.030000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEdgePersistenceMonitorConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EDGE_PERSISTENCE_MONITOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "persisted_edge_floor",
            "watch_edge_floor",
            "evidence_age_drag_cap",
            "market_movement_watch_probability",
            "cost_drag_watch_probability",
            "liquidity_watch_floor",
            "liquidity_block_floor",
            "liquidity_drag_cap",
            "confidence_haircut_watch_probability",
            "resolution_ambiguity_watch_score",
            "resolution_ambiguity_block_score",
            "resolution_ambiguity_drag_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_hours",
            _normalize_nonnegative_value(
                "max_evidence_age_hours",
                self.max_evidence_age_hours,
            ),
        )
        if self.max_evidence_age_hours == ZERO_RATIO:
            raise ValueError("max_evidence_age_hours must be positive")
        if self.watch_edge_floor > self.persisted_edge_floor:
            raise ValueError("watch_edge_floor must not exceed persisted_edge_floor")
        if self.liquidity_block_floor > self.liquidity_watch_floor:
            raise ValueError("liquidity_block_floor must not exceed liquidity_watch_floor")
        if self.resolution_ambiguity_watch_score > self.resolution_ambiguity_block_score:
            raise ValueError(
                "resolution_ambiguity_watch_score must not exceed "
                "resolution_ambiguity_block_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEdgePersistenceObservation(_FinalPublicDataclass):
    source_ref: str
    observed_at: datetime
    baseline_edge_probability: Decimal
    current_edge_probability: Decimal
    evidence_age_hours: Decimal
    cost_drag_probability: Decimal
    liquidity_quality_score: Decimal
    confidence_haircut_probability: Decimal
    resolution_ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEdgePersistenceObservation, "observation")
        _require_canonical_string("source_ref", self.source_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("baseline_edge_probability", "current_edge_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _normalize_nonnegative_value("evidence_age_hours", self.evidence_age_hours),
        )
        for field_name in (
            "cost_drag_probability",
            "liquidity_quality_score",
            "confidence_haircut_probability",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEdgePersistenceMonitorRow(_FinalPublicDataclass):
    redacted_source_ref: str
    observed_at: datetime
    baseline_edge_probability: Decimal
    current_edge_probability: Decimal
    edge_movement_probability: Decimal
    evidence_age_hours: Decimal
    evidence_age_drag_probability: Decimal
    cost_drag_probability: Decimal
    liquidity_quality_score: Decimal
    liquidity_drag_probability: Decimal
    confidence_haircut_probability: Decimal
    resolution_ambiguity_score: Decimal
    resolution_ambiguity_drag_probability: Decimal
    adjusted_edge_probability: Decimal
    persistence_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEdgePersistenceMonitorRow, "row")
        _require_redacted_source_ref(self.redacted_source_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "baseline_edge_probability",
            "current_edge_probability",
            "edge_movement_probability",
            "evidence_age_hours",
            "evidence_age_drag_probability",
            "cost_drag_probability",
            "liquidity_quality_score",
            "liquidity_drag_probability",
            "confidence_haircut_probability",
            "resolution_ambiguity_score",
            "resolution_ambiguity_drag_probability",
            "adjusted_edge_probability",
        ):
            if field_name in (
                "baseline_edge_probability",
                "current_edge_probability",
                "adjusted_edge_probability",
            ):
                normalized = _normalize_value(field_name, getattr(self, field_name))
            elif field_name == "evidence_age_hours":
                normalized = _normalize_nonnegative_value(
                    field_name,
                    getattr(self, field_name),
                )
            else:
                normalized = _normalize_probability(field_name, getattr(self, field_name))
            object.__setattr__(self, field_name, normalized)
        _require_member("persistence_status", self.persistence_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEdgePersistenceMonitorReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    persisted_edge_count: Decimal
    mean_adjusted_edge_probability: Decimal
    min_adjusted_edge_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyEdgePersistenceMonitorRow, ...]
    payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEdgePersistenceMonitorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EDGE_PERSISTENCE_MONITOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "persisted_edge_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_adjusted_edge_probability",
            "min_adjusted_edge_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _payload_digest_without_digest(_json_ready(self))
        if self.payload_sha256:
            _require_sha256("payload_sha256", self.payload_sha256)
            if self.payload_sha256 != expected_digest:
                raise ValueError("payload_sha256 does not match report payload")
        else:
            object.__setattr__(self, "payload_sha256", expected_digest)


def build_research_strategy_edge_persistence_monitor_report(
    observations: list[ResearchStrategyEdgePersistenceObservation]
    | tuple[ResearchStrategyEdgePersistenceObservation, ...],
    *,
    config: ResearchStrategyEdgePersistenceMonitorConfig,
    generated_at: datetime,
) -> ResearchStrategyEdgePersistenceMonitorReport:
    if type(config) is not ResearchStrategyEdgePersistenceMonitorConfig:
        raise ValueError(
            "config must be a ResearchStrategyEdgePersistenceMonitorConfig",
        )
    config = _revalidate_config(config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (_row_from_observation(row, config) for row in source_rows),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyEdgePersistenceMonitorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(source_rows)),
        pass_count=_count(sum(1 for row in rows if row.persistence_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.persistence_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.persistence_status == "block")),
        persisted_edge_count=_count(
            sum(
                1
                for row in rows
                if row.adjusted_edge_probability >= config.persisted_edge_floor
            ),
        ),
        mean_adjusted_edge_probability=_mean(
            tuple(row.adjusted_edge_probability for row in rows),
        ),
        min_adjusted_edge_probability=_min_or_zero(
            tuple(row.adjusted_edge_probability for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_edge_persistence_monitor_report_payload(
    report: ResearchStrategyEdgePersistenceMonitorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyEdgePersistenceMonitorReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_keys("payload", report)
        _reject_unsafe_public_values("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyEdgePersistenceMonitorReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_keys("payload", payload)
    _reject_unsafe_public_values("payload", payload)
    validate_research_strategy_edge_persistence_monitor_report_payload(payload)
    return payload


def research_strategy_edge_persistence_monitor_report_json(
    report: ResearchStrategyEdgePersistenceMonitorReport | dict[str, Any],
) -> str:
    payload = research_strategy_edge_persistence_monitor_report_payload(report)
    return _canonical_json(payload)


def validate_research_strategy_edge_persistence_monitor_report_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_keys("payload", payload)
    _reject_unsafe_public_values("payload", payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    digest = ready.get("payload_sha256")
    if type(digest) is not str:
        raise ValueError("payload_sha256 must be present")
    _require_sha256("payload_sha256", digest)
    expected_digest = _payload_digest_without_digest(ready)
    if digest != expected_digest:
        raise ValueError("payload_sha256 does not match report payload")
    _validate_payload_schema(ready)


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    rows = tuple(
        _payload_row(row_payload)
        for row_payload in _payload_object_list("rows", payload["rows"])
    )
    reason_code_counts = tuple(
        _payload_reason_code_count(item)
        for item in _payload_pair_list(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    report = ResearchStrategyEdgePersistenceMonitorReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        source_row_count=_payload_decimal(
            "source_row_count",
            payload["source_row_count"],
            _normalize_nonnegative_count,
        ),
        pass_count=_payload_decimal(
            "pass_count",
            payload["pass_count"],
            _normalize_nonnegative_count,
        ),
        watch_count=_payload_decimal(
            "watch_count",
            payload["watch_count"],
            _normalize_nonnegative_count,
        ),
        block_count=_payload_decimal(
            "block_count",
            payload["block_count"],
            _normalize_nonnegative_count,
        ),
        persisted_edge_count=_payload_decimal(
            "persisted_edge_count",
            payload["persisted_edge_count"],
            _normalize_nonnegative_count,
        ),
        mean_adjusted_edge_probability=_payload_decimal(
            "mean_adjusted_edge_probability",
            payload["mean_adjusted_edge_probability"],
            _normalize_value,
        ),
        min_adjusted_edge_probability=_payload_decimal(
            "min_adjusted_edge_probability",
            payload["min_adjusted_edge_probability"],
            _normalize_value,
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        payload_sha256=_payload_string("payload_sha256", payload["payload_sha256"]),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    if _json_ready(report) != payload:
        raise ValueError("report payload must use canonical report payload schema")


def _payload_row(
    payload: dict[str, Any],
) -> ResearchStrategyEdgePersistenceMonitorRow:
    _require_payload_keys("row payload", payload, ROW_PAYLOAD_KEYS)
    return ResearchStrategyEdgePersistenceMonitorRow(
        redacted_source_ref=_payload_string(
            "redacted_source_ref",
            payload["redacted_source_ref"],
        ),
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        baseline_edge_probability=_payload_decimal(
            "baseline_edge_probability",
            payload["baseline_edge_probability"],
            _normalize_value,
        ),
        current_edge_probability=_payload_decimal(
            "current_edge_probability",
            payload["current_edge_probability"],
            _normalize_value,
        ),
        edge_movement_probability=_payload_decimal(
            "edge_movement_probability",
            payload["edge_movement_probability"],
            _normalize_probability,
        ),
        evidence_age_hours=_payload_decimal(
            "evidence_age_hours",
            payload["evidence_age_hours"],
            _normalize_nonnegative_value,
        ),
        evidence_age_drag_probability=_payload_decimal(
            "evidence_age_drag_probability",
            payload["evidence_age_drag_probability"],
            _normalize_probability,
        ),
        cost_drag_probability=_payload_decimal(
            "cost_drag_probability",
            payload["cost_drag_probability"],
            _normalize_probability,
        ),
        liquidity_quality_score=_payload_decimal(
            "liquidity_quality_score",
            payload["liquidity_quality_score"],
            _normalize_probability,
        ),
        liquidity_drag_probability=_payload_decimal(
            "liquidity_drag_probability",
            payload["liquidity_drag_probability"],
            _normalize_probability,
        ),
        confidence_haircut_probability=_payload_decimal(
            "confidence_haircut_probability",
            payload["confidence_haircut_probability"],
            _normalize_probability,
        ),
        resolution_ambiguity_score=_payload_decimal(
            "resolution_ambiguity_score",
            payload["resolution_ambiguity_score"],
            _normalize_probability,
        ),
        resolution_ambiguity_drag_probability=_payload_decimal(
            "resolution_ambiguity_drag_probability",
            payload["resolution_ambiguity_drag_probability"],
            _normalize_probability,
        ),
        adjusted_edge_probability=_payload_decimal(
            "adjusted_edge_probability",
            payload["adjusted_edge_probability"],
            _normalize_value,
        ),
        persistence_status=_payload_string(
            "persistence_status",
            payload["persistence_status"],
        ),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _payload_reason_code_count(item: object) -> tuple[str, Decimal]:
    if type(item) is not list or len(item) != 2:
        raise ValueError("reason_code_counts must use canonical report payload schema")
    return (
        _payload_string("reason_code_counts reason code", item[0]),
        _payload_decimal(
            "reason_code_counts count",
            item[1],
            _normalize_nonnegative_count,
        ),
    )


def _require_payload_keys(
    label: str,
    payload: object,
    expected_keys: tuple[str, ...],
) -> None:
    if type(payload) is not dict or tuple(payload) != expected_keys:
        raise ValueError(f"{label} must use canonical report payload schema")


def _payload_object_list(field_name: str, value: object) -> tuple[dict[str, Any], ...]:
    if type(value) is not list or any(type(item) is not dict for item in value):
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return tuple(value)


def _payload_pair_list(field_name: str, value: object) -> tuple[list[Any], ...]:
    if type(value) is not list or any(type(item) is not list for item in value):
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return tuple(value)


def _payload_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _payload_flag(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return value


def _payload_reason_codes(
    field_name: str,
    value: object,
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        return _normalize_reason_codes(field_name, tuple(value), supported)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use canonical report payload schema") from exc


def _payload_decimal(
    field_name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use canonical report payload schema") from exc
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    try:
        normalized = normalizer(field_name, decimal_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use canonical report payload schema") from exc
    if str(normalized) != value:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return normalized


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        normalized = _as_utc(field_name, datetime.fromisoformat(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must use canonical report payload schema") from exc
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return normalized


@dataclass(frozen=True, slots=True)
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


def _normalize_observations(
    observations: list[ResearchStrategyEdgePersistenceObservation]
    | tuple[ResearchStrategyEdgePersistenceObservation, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyEdgePersistenceObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(observations)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyEdgePersistenceObservation:
            raise ValueError(
                "observations must contain ResearchStrategyEdgePersistenceObservation "
                "values",
            )
        _require_hard_flags("observation", row)
        if row.source_ref in seen:
            raise ValueError("observations must not contain duplicate source_ref values")
        seen.add(row.source_ref)
    normalized = tuple(_revalidate_observation(row) for row in rows)
    for row in normalized:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return normalized


def _revalidate_config(
    config: ResearchStrategyEdgePersistenceMonitorConfig,
) -> ResearchStrategyEdgePersistenceMonitorConfig:
    return ResearchStrategyEdgePersistenceMonitorConfig(
        **{field.name: getattr(config, field.name) for field in fields(config)},
    )


def _revalidate_observation(
    observation: ResearchStrategyEdgePersistenceObservation,
) -> ResearchStrategyEdgePersistenceObservation:
    return ResearchStrategyEdgePersistenceObservation(
        **{field.name: getattr(observation, field.name) for field in fields(observation)},
    )


def _revalidate_row(
    row: ResearchStrategyEdgePersistenceMonitorRow,
) -> ResearchStrategyEdgePersistenceMonitorRow:
    return ResearchStrategyEdgePersistenceMonitorRow(
        **{field.name: getattr(row, field.name) for field in fields(row)},
    )


def _row_from_observation(
    row: ResearchStrategyEdgePersistenceObservation,
    config: ResearchStrategyEdgePersistenceMonitorConfig,
) -> ResearchStrategyEdgePersistenceMonitorRow:
    edge_movement = _edge_movement(
        row.current_edge_probability,
        row.baseline_edge_probability,
    )
    evidence_drag = _evidence_age_drag(row.evidence_age_hours, config)
    liquidity_drag = _liquidity_drag(row.liquidity_quality_score, config)
    ambiguity_drag = _resolution_ambiguity_drag(row.resolution_ambiguity_score, config)
    with localcontext(DECIMAL_CONTEXT):
        adjusted_edge = _quantize_ratio(
            row.current_edge_probability
            - evidence_drag
            - row.cost_drag_probability
            - liquidity_drag
            - row.confidence_haircut_probability
            - ambiguity_drag,
        )
    return ResearchStrategyEdgePersistenceMonitorRow(
        redacted_source_ref=_redacted_source_ref(row.source_ref),
        observed_at=row.observed_at,
        baseline_edge_probability=row.baseline_edge_probability,
        current_edge_probability=row.current_edge_probability,
        edge_movement_probability=edge_movement,
        evidence_age_hours=row.evidence_age_hours,
        evidence_age_drag_probability=evidence_drag,
        cost_drag_probability=row.cost_drag_probability,
        liquidity_quality_score=row.liquidity_quality_score,
        liquidity_drag_probability=liquidity_drag,
        confidence_haircut_probability=row.confidence_haircut_probability,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        resolution_ambiguity_drag_probability=ambiguity_drag,
        adjusted_edge_probability=adjusted_edge,
        persistence_status=_row_status(
            adjusted_edge,
            row,
            config,
        ),
        reason_codes=_row_reason_codes(adjusted_edge, row, config),
    )


def _row_status(
    adjusted_edge: Decimal,
    row: ResearchStrategyEdgePersistenceObservation,
    config: ResearchStrategyEdgePersistenceMonitorConfig,
) -> str:
    if adjusted_edge < config.watch_edge_floor:
        return "block"
    if row.liquidity_quality_score <= config.liquidity_block_floor:
        return "block"
    if row.resolution_ambiguity_score >= config.resolution_ambiguity_block_score:
        return "block"
    if adjusted_edge < config.persisted_edge_floor:
        return "watch"
    if row.evidence_age_hours > config.max_evidence_age_hours:
        return "watch"
    if (
        _edge_movement(row.current_edge_probability, row.baseline_edge_probability)
        >= config.market_movement_watch_probability
    ):
        return "watch"
    if row.cost_drag_probability >= config.cost_drag_watch_probability:
        return "watch"
    if row.liquidity_quality_score < config.liquidity_watch_floor:
        return "watch"
    if row.confidence_haircut_probability >= config.confidence_haircut_watch_probability:
        return "watch"
    if row.resolution_ambiguity_score >= config.resolution_ambiguity_watch_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    adjusted_edge: Decimal,
    row: ResearchStrategyEdgePersistenceObservation,
    config: ResearchStrategyEdgePersistenceMonitorConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if adjusted_edge >= config.persisted_edge_floor:
        codes.append("edge_persistent")
    else:
        codes.append("edge_not_persistent")
    if row.evidence_age_hours > config.max_evidence_age_hours:
        codes.append("evidence_aging_watch")
    if (
        _edge_movement(row.current_edge_probability, row.baseline_edge_probability)
        >= config.market_movement_watch_probability
    ):
        codes.append("edge_movement_watch")
    if row.cost_drag_probability >= config.cost_drag_watch_probability:
        codes.append("cost_drag_watch")
    if row.liquidity_quality_score <= config.liquidity_block_floor:
        codes.append("liquidity_quality_block")
    elif row.liquidity_quality_score < config.liquidity_watch_floor:
        codes.append("liquidity_quality_watch")
    if row.confidence_haircut_probability >= config.confidence_haircut_watch_probability:
        codes.append("confidence_haircut_watch")
    if row.resolution_ambiguity_score >= config.resolution_ambiguity_block_score:
        codes.append("resolution_ambiguity_block")
    elif row.resolution_ambiguity_score >= config.resolution_ambiguity_watch_score:
        codes.append("resolution_ambiguity_watch")
    return tuple(codes)


def _report_status(rows: tuple[ResearchStrategyEdgePersistenceMonitorRow, ...]) -> str:
    if any(row.persistence_status == "block" for row in rows):
        return "block"
    if any(row.persistence_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEdgePersistenceMonitorRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.persistence_status == "pass" for row in rows):
        return ("edge_persistence_clear",)
    codes: list[str] = []
    if any(row.persistence_status == "block" for row in rows):
        codes.append("edge_persistence_block")
    if any(row.persistence_status == "watch" for row in rows):
        codes.append("edge_persistence_watch")
    for code in ROW_REASON_CODES:
        if code in ("edge_persistent", "edge_not_persistent"):
            continue
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyEdgePersistenceMonitorRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _evidence_age_drag(
    evidence_age_hours: Decimal,
    config: ResearchStrategyEdgePersistenceMonitorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_ratio = evidence_age_hours / config.max_evidence_age_hours
        if age_ratio > ONE_RATIO:
            age_ratio = ONE_RATIO
        return _quantize_ratio(config.evidence_age_drag_cap * age_ratio)


def _liquidity_drag(
    liquidity_quality_score: Decimal,
    config: ResearchStrategyEdgePersistenceMonitorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(config.liquidity_drag_cap * (ONE_RATIO - liquidity_quality_score))


def _resolution_ambiguity_drag(
    resolution_ambiguity_score: Decimal,
    config: ResearchStrategyEdgePersistenceMonitorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            config.resolution_ambiguity_drag_cap * resolution_ambiguity_score,
        )


def _row_sort_key(
    row: ResearchStrategyEdgePersistenceMonitorRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        _status_rank(row.persistence_status),
        row.adjusted_edge_probability,
        -row.edge_movement_probability,
        row.redacted_source_ref,
    )


def _status_rank(status: str) -> Decimal:
    if status == "block":
        return Decimal("0")
    if status == "watch":
        return Decimal("1")
    return Decimal("2")


def _validate_row(row: ResearchStrategyEdgePersistenceMonitorRow) -> None:
    canonical_reason_codes = tuple(
        code for code in ROW_REASON_CODES if code in row.reason_codes
    )
    if row.reason_codes != canonical_reason_codes:
        raise ValueError("reason_codes must use canonical reason code sequence")
    block_reason_codes = {
        "liquidity_quality_block",
        "resolution_ambiguity_block",
    }
    if row.persistence_status == "pass" and row.reason_codes != ("edge_persistent",):
        raise ValueError("persistence_status must match reason_codes")
    if row.persistence_status == "watch" and (
        row.reason_codes == ("edge_persistent",)
        or any(code in block_reason_codes for code in row.reason_codes)
    ):
        raise ValueError("persistence_status must match reason_codes")
    if row.persistence_status == "block" and (
        "edge_not_persistent" not in row.reason_codes
        and not any(code in block_reason_codes for code in row.reason_codes)
    ):
        raise ValueError("persistence_status must match reason_codes")
    with localcontext(DECIMAL_CONTEXT):
        expected_adjusted = _quantize_ratio(
            row.current_edge_probability
            - row.evidence_age_drag_probability
            - row.cost_drag_probability
            - row.liquidity_drag_probability
            - row.confidence_haircut_probability
            - row.resolution_ambiguity_drag_probability,
        )
    if row.adjusted_edge_probability != expected_adjusted:
        raise ValueError("adjusted_edge_probability must match persistence reducer")
    expected_movement = _edge_movement(
        row.current_edge_probability,
        row.baseline_edge_probability,
    )
    if row.edge_movement_probability != expected_movement:
        raise ValueError("edge_movement_probability must match edge change")


def _validate_report(report: ResearchStrategyEdgePersistenceMonitorReport) -> None:
    rows = report.rows
    if any(row.observed_at > report.generated_at for row in rows):
        raise ValueError("observed_at must not be after generated_at")
    if report.source_row_count != _count(len(rows)):
        raise ValueError("source_row_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in rows if row.persistence_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in rows if row.persistence_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in rows if row.persistence_status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.persisted_edge_count != _count(
        sum(1 for row in rows if "edge_persistent" in row.reason_codes),
    ):
        raise ValueError("persisted_edge_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")
    adjusted_edges = tuple(row.adjusted_edge_probability for row in rows)
    if report.mean_adjusted_edge_probability != _mean(adjusted_edges):
        raise ValueError("mean_adjusted_edge_probability must match rows")
    if report.min_adjusted_edge_probability != _min_or_zero(adjusted_edges):
        raise ValueError("min_adjusted_edge_probability must match rows")


def _normalize_rows(
    rows: list[ResearchStrategyEdgePersistenceMonitorRow]
    | tuple[ResearchStrategyEdgePersistenceMonitorRow, ...],
) -> tuple[ResearchStrategyEdgePersistenceMonitorRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyEdgePersistenceMonitorRow:
            raise ValueError(
                "rows must contain ResearchStrategyEdgePersistenceMonitorRow values",
            )
        _require_hard_flags("row", row)
    revalidated = tuple(_revalidate_row(row) for row in normalized)
    ordered = tuple(sorted(revalidated, key=_row_sort_key))
    if revalidated != ordered:
        raise ValueError("rows must use deterministic ordering")
    return ordered


def _normalize_reason_code_counts(
    reason_code_counts: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in reason_code_counts:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        reason_code, count = item
        if type(reason_code) is not str:
            raise ValueError("reason_code_counts reason code must be a string")
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code_counts reason code is not supported")
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    expected = tuple(
        sorted(normalized, key=lambda item: (-item[1], item[0])),
    )
    if tuple(normalized) != expected:
        raise ValueError("reason_code_counts must be sorted")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in normalized:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} values must be strings")
        if reason_code not in supported:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return normalized


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("JSON Decimal value must not use signed zero")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_digest_without_digest(payload: dict[str, Any]) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    return sha256(_canonical_json(payload_without_digest).encode("utf-8")).hexdigest()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _reject_unsafe_public_keys(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_keys(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key, UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_keys(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_keys(label, item)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value, UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(label, item)


def _has_unsafe_fragment(value: str, fragments: tuple[str, ...]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_member(field_name: str, value: str, members: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")


def _require_redacted_source_ref(value: object) -> None:
    if type(value) is not str:
        raise ValueError("redacted_source_ref must be a string")
    if not value.startswith(REDACTED_SOURCE_REF_PREFIX):
        raise ValueError("redacted_source_ref must be redacted")
    suffix = value.removeprefix(REDACTED_SOURCE_REF_PREFIX)
    if len(suffix) != REDACTED_DIGEST_LENGTH:
        raise ValueError("redacted_source_ref must have a digest suffix")
    if any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError("redacted_source_ref digest suffix must be hex")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_value(field_name: str, value: object) -> Decimal:
    return _quantize_ratio(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(RATIO_QUANTUM)
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError("Decimal must not quantize to signed zero")
    if normalized == ZERO_COUNT:
        return ZERO_RATIO
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / Decimal(len(values)))


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _quantize_ratio(min(values))


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(RATIO_QUANTUM)


def _edge_movement(current: Decimal, baseline: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(abs(current - baseline))


def _redacted_source_ref(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:REDACTED_DIGEST_LENGTH]
    return f"{REDACTED_SOURCE_REF_PREFIX}{digest}"


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EDGE_PERSISTENCE_MONITOR_REPORT_CONFIG_VERSION",
    "ResearchStrategyEdgePersistenceMonitorConfig",
    "ResearchStrategyEdgePersistenceObservation",
    "ResearchStrategyEdgePersistenceMonitorRow",
    "ResearchStrategyEdgePersistenceMonitorReport",
    "build_research_strategy_edge_persistence_monitor_report",
    "research_strategy_edge_persistence_monitor_report_payload",
    "research_strategy_edge_persistence_monitor_report_json",
    "validate_research_strategy_edge_persistence_monitor_report_payload",
)
