"""Report-only event-cluster signal memory score snapshot.

The module is deterministic and side-effect free. Callers provide already
redacted cluster and signal fingerprints; the builder returns local report-only
scores, statuses, reason codes, and a digest-validated JSON public payload.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_SIGNAL_MEMORY_SCORE_CONFIG_VERSION = (
    "research-strategy-event-cluster-signal-memory-score-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "sizing",
    "recommendation",
    "auth",
    "network",
    "database",
    "live",
    "buy",
    "sell",
)
_REASON_CODE_SEQUENCE = (
    "empty_signal_memory",
    "stale_signal_memory",
    "fresh_signal_memory",
    "insufficient_signal_count",
    "insufficient_unique_signals",
    "duplicate_signal_memory",
    "unsupported_signal_memory",
    "low_signal_memory_score",
    "unique_signal_memory",
    "signal_memory_block",
    "signal_memory_watch",
    "signal_memory_pass",
)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventClusterSignalMemoryScoreConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_SIGNAL_MEMORY_SCORE_CONFIG_VERSION
    )
    stale_signal_age_seconds: Decimal = Decimal("86400.000000")
    min_signal_count: Decimal = Decimal("2.000000")
    min_unique_signal_count: Decimal = Decimal("2.000000")
    pass_memory_score: Decimal = Decimal("0.700000")
    watch_memory_score: Decimal = Decimal("0.400000")
    signal_strength_weight: Decimal = Decimal("0.400000")
    recency_memory_weight: Decimal = Decimal("0.400000")
    unique_signal_weight: Decimal = Decimal("0.200000")
    duplicate_signal_penalty_per_signal: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventClusterSignalMemoryScoreConfig:
            raise TypeError(
                "ResearchStrategyEventClusterSignalMemoryScoreConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventClusterSignalMemoryScoreConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategyEventClusterSignalMemoryScoreConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_SIGNAL_MEMORY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "stale_signal_age_seconds",
            _require_positive_decimal(
                "stale_signal_age_seconds",
                self.stale_signal_age_seconds,
            ),
        )
        for field_name in ("min_signal_count", "min_unique_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_memory_score",
            "watch_memory_score",
            "signal_strength_weight",
            "recency_memory_weight",
            "unique_signal_weight",
            "duplicate_signal_penalty_per_signal",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_memory_score <= self.watch_memory_score:
            raise ValueError("pass_memory_score must exceed watch_memory_score")
        weight_sum = _sum_decimals(
            (
                self.signal_strength_weight,
                self.recency_memory_weight,
                self.unique_signal_weight,
            ),
        )
        if weight_sum != _ONE:
            raise ValueError(
                "signal_strength_weight, recency_memory_weight, and "
                "unique_signal_weight must sum to 1",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventClusterSignalMemoryObservation:
    cluster_fingerprint: str
    signal_fingerprint: str
    observed_at: datetime
    signal_strength: Decimal
    supports_memory: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventClusterSignalMemoryObservation:
            raise TypeError(
                "ResearchStrategyEventClusterSignalMemoryObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventClusterSignalMemoryObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchStrategyEventClusterSignalMemoryObservation",
            )
        _require_fingerprint("cluster_fingerprint", self.cluster_fingerprint)
        _require_fingerprint("signal_fingerprint", self.signal_fingerprint)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signal_strength",
            _require_ratio_decimal("signal_strength", self.signal_strength),
        )
        _require_bool("supports_memory", self.supports_memory)
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventClusterSignalMemoryPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventClusterSignalMemoryPublicPayloadItem:
            raise TypeError(
                "ResearchStrategyEventClusterSignalMemoryPublicPayloadItem does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventClusterSignalMemoryPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchStrategyEventClusterSignalMemoryPublicPayloadItem",
            )
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventClusterSignalMemoryScoreRow:
    cluster_fingerprint: str
    signal_count: Decimal
    unique_signal_count: Decimal
    duplicate_signal_count: Decimal
    latest_observed_at: datetime
    latest_signal_age_seconds: Decimal
    recency_memory_score: Decimal
    average_signal_strength: Decimal
    unique_signal_ratio: Decimal
    duplicate_signal_penalty: Decimal
    memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventClusterSignalMemoryScoreRow:
            raise TypeError(
                "ResearchStrategyEventClusterSignalMemoryScoreRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventClusterSignalMemoryScoreRow:
            raise ValueError(
                "row must be exactly ResearchStrategyEventClusterSignalMemoryScoreRow",
            )
        _require_fingerprint("cluster_fingerprint", self.cluster_fingerprint)
        for field_name in (
            "signal_count",
            "unique_signal_count",
            "duplicate_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_signal_age_seconds",
            _require_nonnegative_decimal(
                "latest_signal_age_seconds",
                self.latest_signal_age_seconds,
            ),
        )
        for field_name in (
            "recency_memory_score",
            "average_signal_strength",
            "unique_signal_ratio",
            "duplicate_signal_penalty",
            "memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventClusterSignalMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventClusterSignalMemoryReasonCodeCount:
            raise TypeError(
                "ResearchStrategyEventClusterSignalMemoryReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventClusterSignalMemoryReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchStrategyEventClusterSignalMemoryReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventClusterSignalMemoryScoreReport:
    generated_at: datetime
    config_version: str
    status: str
    cluster_count: Decimal
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_score: Decimal
    rows: tuple[ResearchStrategyEventClusterSignalMemoryScoreRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyEventClusterSignalMemoryReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchStrategyEventClusterSignalMemoryPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventClusterSignalMemoryScoreReport:
            raise TypeError(
                "ResearchStrategyEventClusterSignalMemoryScoreReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventClusterSignalMemoryScoreReport:
            raise ValueError(
                "report must be exactly "
                "ResearchStrategyEventClusterSignalMemoryScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_SIGNAL_MEMORY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "cluster_count",
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_score",
            _require_ratio_decimal("average_memory_score", self.average_memory_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload, canonical=True),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _validate_report_for_payload(self)
        _reject_unsafe_public_payload(
            "ResearchStrategyEventClusterSignalMemoryScoreReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_event_cluster_signal_memory_score_report(
    observations: Sequence[ResearchStrategyEventClusterSignalMemoryObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategyEventClusterSignalMemoryScoreConfig | None = None,
    public_payload: Sequence[
        ResearchStrategyEventClusterSignalMemoryPublicPayloadItem
    ] = (),
) -> ResearchStrategyEventClusterSignalMemoryScoreReport:
    if config is None:
        config = ResearchStrategyEventClusterSignalMemoryScoreConfig()
    if type(config) is not ResearchStrategyEventClusterSignalMemoryScoreConfig:
        raise ValueError(
            "config must be a ResearchStrategyEventClusterSignalMemoryScoreConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_observations, generated_at, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "cluster_count": _decimal_count(len(rows)),
        "signal_count": _sum_decimals(tuple(row.signal_count for row in rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_memory_score": _average(tuple(row.memory_score for row in rows)),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEventClusterSignalMemoryScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_event_cluster_signal_memory_score_report_payload(
    report: ResearchStrategyEventClusterSignalMemoryScoreReport
    | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchStrategyEventClusterSignalMemoryScoreReport:
        _validate_report_for_payload(report)
        return report.payload
    if type(report) is dict:
        return _payload_from_mapping(report)
    raise ValueError(
        "report must be a ResearchStrategyEventClusterSignalMemoryScoreReport "
        "or a JSON payload mapping",
    )


def _build_rows(
    observations: tuple[ResearchStrategyEventClusterSignalMemoryObservation, ...],
    generated_at: datetime,
    config: ResearchStrategyEventClusterSignalMemoryScoreConfig,
) -> tuple[ResearchStrategyEventClusterSignalMemoryScoreRow, ...]:
    grouped: dict[str, list[ResearchStrategyEventClusterSignalMemoryObservation]] = {}
    for item in observations:
        grouped.setdefault(item.cluster_fingerprint, []).append(item)
    return tuple(
        _row_for_cluster(cluster_fingerprint, tuple(grouped[cluster_fingerprint]), generated_at, config)
        for cluster_fingerprint in sorted(grouped)
    )


def _row_for_cluster(
    cluster_fingerprint: str,
    observations: tuple[ResearchStrategyEventClusterSignalMemoryObservation, ...],
    generated_at: datetime,
    config: ResearchStrategyEventClusterSignalMemoryScoreConfig,
) -> ResearchStrategyEventClusterSignalMemoryScoreRow:
    with localcontext(_DECIMAL_CONTEXT):
        signal_count = _decimal_count(len(observations))
        supportive = tuple(item for item in observations if item.supports_memory)
        unique_count = _decimal_count(
            len({item.signal_fingerprint for item in supportive}),
        )
        duplicate_count = _quantize(max(signal_count - unique_count, _ZERO))
        latest_observed_at = max(item.observed_at for item in observations)
        latest_age = _age_seconds(generated_at, latest_observed_at)
        recency_score = _recency_score(latest_age, config.stale_signal_age_seconds)
        average_strength = _average(tuple(item.signal_strength for item in supportive))
        unique_ratio = _clamp_ratio(
            unique_count / signal_count if signal_count > _ZERO else _ZERO,
        )
        duplicate_penalty = _clamp_ratio(
            duplicate_count * config.duplicate_signal_penalty_per_signal,
        )
        memory_score = _clamp_ratio(
            (average_strength * config.signal_strength_weight)
            + (recency_score * config.recency_memory_weight)
            + (unique_ratio * config.unique_signal_weight)
            - duplicate_penalty,
        )
    status = _row_status(
        signal_count=signal_count,
        unique_signal_count=unique_count,
        memory_score=memory_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        signal_count=signal_count,
        unique_signal_count=unique_count,
        duplicate_signal_count=duplicate_count,
        latest_signal_age_seconds=latest_age,
        memory_score=memory_score,
        has_unsupported_signal=len(supportive) != len(observations),
        status=status,
        config=config,
    )
    return ResearchStrategyEventClusterSignalMemoryScoreRow(
        cluster_fingerprint=cluster_fingerprint,
        signal_count=signal_count,
        unique_signal_count=unique_count,
        duplicate_signal_count=duplicate_count,
        latest_observed_at=latest_observed_at,
        latest_signal_age_seconds=latest_age,
        recency_memory_score=recency_score,
        average_signal_strength=average_strength,
        unique_signal_ratio=unique_ratio,
        duplicate_signal_penalty=duplicate_penalty,
        memory_score=memory_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    signal_count: Decimal,
    unique_signal_count: Decimal,
    memory_score: Decimal,
    config: ResearchStrategyEventClusterSignalMemoryScoreConfig,
) -> str:
    if memory_score < config.watch_memory_score:
        return "block"
    if (
        signal_count >= config.min_signal_count
        and unique_signal_count >= config.min_unique_signal_count
        and memory_score >= config.pass_memory_score
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    signal_count: Decimal,
    unique_signal_count: Decimal,
    duplicate_signal_count: Decimal,
    latest_signal_age_seconds: Decimal,
    memory_score: Decimal,
    has_unsupported_signal: bool,
    status: str,
    config: ResearchStrategyEventClusterSignalMemoryScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if latest_signal_age_seconds >= config.stale_signal_age_seconds:
        reason_codes.append("stale_signal_memory")
    else:
        reason_codes.append("fresh_signal_memory")
    if signal_count < config.min_signal_count:
        reason_codes.append("insufficient_signal_count")
    if unique_signal_count < config.min_unique_signal_count:
        reason_codes.append("insufficient_unique_signals")
    else:
        reason_codes.append("unique_signal_memory")
    if duplicate_signal_count > _ZERO:
        reason_codes.append("duplicate_signal_memory")
    if has_unsupported_signal:
        reason_codes.append("unsupported_signal_memory")
    if memory_score < config.watch_memory_score:
        reason_codes.append("low_signal_memory_score")
    reason_codes.append(f"signal_memory_{status}")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _report_status(
    rows: tuple[ResearchStrategyEventClusterSignalMemoryScoreRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventClusterSignalMemoryScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_signal_memory",)
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyEventClusterSignalMemoryScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyEventClusterSignalMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyEventClusterSignalMemoryReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyEventClusterSignalMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchStrategyEventClusterSignalMemoryScoreRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_observations(
    observations: Sequence[ResearchStrategyEventClusterSignalMemoryObservation],
) -> tuple[ResearchStrategyEventClusterSignalMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchStrategyEventClusterSignalMemoryObservation] = []
    for item in observations:
        if type(item) is not ResearchStrategyEventClusterSignalMemoryObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyEventClusterSignalMemoryObservation values",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.cluster_fingerprint,
                item.observed_at,
                item.signal_fingerprint,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyEventClusterSignalMemoryScoreRow],
) -> tuple[ResearchStrategyEventClusterSignalMemoryScoreRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyEventClusterSignalMemoryScoreRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyEventClusterSignalMemoryScoreRow:
            raise ValueError(
                "rows must contain ResearchStrategyEventClusterSignalMemoryScoreRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    normalized_tuple = tuple(normalized)
    if len({row.cluster_fingerprint for row in normalized_tuple}) != len(normalized_tuple):
        raise ValueError("rows must have unique cluster_fingerprint values")
    if normalized_tuple != tuple(
        sorted(normalized_tuple, key=lambda row: row.cluster_fingerprint),
    ):
        raise ValueError("rows must use deterministic ordering")
    return normalized_tuple


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyEventClusterSignalMemoryReasonCodeCount],
) -> tuple[ResearchStrategyEventClusterSignalMemoryReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchStrategyEventClusterSignalMemoryReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchStrategyEventClusterSignalMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEventClusterSignalMemoryReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        normalized.append(count)
    normalized_tuple = tuple(normalized)
    if len({item.reason_code for item in normalized_tuple}) != len(normalized_tuple):
        raise ValueError("reason_code_counts must have unique reason codes")
    order = {reason_code: index for index, reason_code in enumerate(_REASON_CODE_SEQUENCE)}
    if normalized_tuple != tuple(sorted(normalized_tuple, key=lambda count: order[count.reason_code])):
        raise ValueError("reason_code_counts must use deterministic ordering")
    return normalized_tuple


def _normalize_public_payload(
    public_payload: Sequence[ResearchStrategyEventClusterSignalMemoryPublicPayloadItem],
    *,
    canonical: bool = False,
) -> tuple[ResearchStrategyEventClusterSignalMemoryPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchStrategyEventClusterSignalMemoryPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchStrategyEventClusterSignalMemoryPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchStrategyEventClusterSignalMemoryPublicPayloadItem values",
            )
        _require_hard_flags("public payload item", item)
        normalized.append(item)
    normalized_tuple = tuple(normalized)
    if len({item.key for item in normalized_tuple}) != len(normalized_tuple):
        raise ValueError("public_payload must have unique keys")
    sorted_tuple = tuple(sorted(normalized_tuple, key=lambda item: item.key))
    if canonical and normalized_tuple != sorted_tuple:
        raise ValueError("public_payload must use deterministic ordering")
    return sorted_tuple


def _validate_row_consistency(
    row: ResearchStrategyEventClusterSignalMemoryScoreRow,
) -> None:
    if row.unique_signal_count > row.signal_count:
        raise ValueError("unique_signal_count must not exceed signal_count")
    with localcontext(_DECIMAL_CONTEXT):
        expected_duplicate = _quantize(row.signal_count - row.unique_signal_count)
    if row.duplicate_signal_count != expected_duplicate:
        raise ValueError("duplicate_signal_count must match signal_count less unique")
    if row.status == "pass" and "signal_memory_pass" not in row.reason_codes:
        raise ValueError("pass rows must include signal_memory_pass")
    if row.status == "block" and "signal_memory_block" not in row.reason_codes:
        raise ValueError("block rows must include signal_memory_block")


def _validate_report_consistency(
    report: ResearchStrategyEventClusterSignalMemoryScoreReport,
) -> None:
    if report.cluster_count != _decimal_count(len(report.rows)):
        raise ValueError("cluster_count must match rows")
    if report.signal_count != _sum_decimals(tuple(row.signal_count for row in report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_memory_score != _average(
        tuple(row.memory_score for row in report.rows),
    ):
        raise ValueError("average_memory_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_for_payload(
    report: ResearchStrategyEventClusterSignalMemoryScoreReport,
) -> None:
    if type(report) is not ResearchStrategyEventClusterSignalMemoryScoreReport:
        raise ValueError(
            "report must be a ResearchStrategyEventClusterSignalMemoryScoreReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    _reject_unsafe_public_payload("report", report)
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _payload_from_mapping(payload: dict[str, object]) -> dict[str, object]:
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _require_exact_payload_keys(
        "payload",
        payload,
        {
            "generated_at",
            "config_version",
            "status",
            "cluster_count",
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_memory_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "public_payload",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    )

    rows_value = _require_payload_list("rows", payload["rows"])
    row_fields = {
        "cluster_fingerprint",
        "signal_count",
        "unique_signal_count",
        "duplicate_signal_count",
        "latest_observed_at",
        "latest_signal_age_seconds",
        "recency_memory_score",
        "average_signal_strength",
        "unique_signal_ratio",
        "duplicate_signal_penalty",
        "memory_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    rows: list[ResearchStrategyEventClusterSignalMemoryScoreRow] = []
    for index, item in enumerate(rows_value):
        row_payload = _require_payload_mapping(f"rows[{index}]", item)
        _require_exact_payload_keys(f"rows[{index}]", row_payload, row_fields)
        rows.append(
            ResearchStrategyEventClusterSignalMemoryScoreRow(
                cluster_fingerprint=_require_payload_string(
                    f"rows[{index}].cluster_fingerprint",
                    row_payload["cluster_fingerprint"],
                ),
                signal_count=_payload_decimal(
                    f"rows[{index}].signal_count", row_payload["signal_count"]
                ),
                unique_signal_count=_payload_decimal(
                    f"rows[{index}].unique_signal_count",
                    row_payload["unique_signal_count"],
                ),
                duplicate_signal_count=_payload_decimal(
                    f"rows[{index}].duplicate_signal_count",
                    row_payload["duplicate_signal_count"],
                ),
                latest_observed_at=_payload_datetime(
                    f"rows[{index}].latest_observed_at",
                    row_payload["latest_observed_at"],
                ),
                latest_signal_age_seconds=_payload_decimal(
                    f"rows[{index}].latest_signal_age_seconds",
                    row_payload["latest_signal_age_seconds"],
                ),
                recency_memory_score=_payload_decimal(
                    f"rows[{index}].recency_memory_score",
                    row_payload["recency_memory_score"],
                ),
                average_signal_strength=_payload_decimal(
                    f"rows[{index}].average_signal_strength",
                    row_payload["average_signal_strength"],
                ),
                unique_signal_ratio=_payload_decimal(
                    f"rows[{index}].unique_signal_ratio",
                    row_payload["unique_signal_ratio"],
                ),
                duplicate_signal_penalty=_payload_decimal(
                    f"rows[{index}].duplicate_signal_penalty",
                    row_payload["duplicate_signal_penalty"],
                ),
                memory_score=_payload_decimal(
                    f"rows[{index}].memory_score", row_payload["memory_score"]
                ),
                status=_require_payload_string(
                    f"rows[{index}].status", row_payload["status"]
                ),
                reason_codes=tuple(
                    _require_payload_string_list(
                        f"rows[{index}].reason_codes", row_payload["reason_codes"]
                    ),
                ),
                paper_only=row_payload["paper_only"],  # type: ignore[arg-type]
                report_only=row_payload["report_only"],  # type: ignore[arg-type]
                readonly=row_payload["readonly"],  # type: ignore[arg-type]
            ),
        )
    if tuple(row.cluster_fingerprint for row in rows) != tuple(
        sorted(row.cluster_fingerprint for row in rows)
    ):
        raise ValueError("payload schema rows must use deterministic ordering")

    count_fields = {"reason_code", "count", "paper_only", "report_only", "readonly"}
    counts_value = _require_payload_list("reason_code_counts", payload["reason_code_counts"])
    counts: list[ResearchStrategyEventClusterSignalMemoryReasonCodeCount] = []
    for index, item in enumerate(counts_value):
        count_payload = _require_payload_mapping(f"reason_code_counts[{index}]", item)
        _require_exact_payload_keys(
            f"reason_code_counts[{index}]",
            count_payload,
            count_fields,
        )
        counts.append(
            ResearchStrategyEventClusterSignalMemoryReasonCodeCount(
                reason_code=_require_payload_string(
                    f"reason_code_counts[{index}].reason_code",
                    count_payload["reason_code"],
                ),
                count=_payload_decimal(
                    f"reason_code_counts[{index}].count", count_payload["count"]
                ),
                paper_only=count_payload["paper_only"],  # type: ignore[arg-type]
                report_only=count_payload["report_only"],  # type: ignore[arg-type]
                readonly=count_payload["readonly"],  # type: ignore[arg-type]
            ),
        )

    public_fields = {"key", "value", "paper_only", "report_only", "readonly"}
    public_value = _require_payload_list("public_payload", payload["public_payload"])
    public_items: list[ResearchStrategyEventClusterSignalMemoryPublicPayloadItem] = []
    for index, item in enumerate(public_value):
        item_payload = _require_payload_mapping(f"public_payload[{index}]", item)
        _require_exact_payload_keys(f"public_payload[{index}]", item_payload, public_fields)
        public_items.append(
            ResearchStrategyEventClusterSignalMemoryPublicPayloadItem(
                key=_require_payload_string(
                    f"public_payload[{index}].key", item_payload["key"]
                ),
                value=_require_payload_string(
                    f"public_payload[{index}].value", item_payload["value"]
                ),
                paper_only=item_payload["paper_only"],  # type: ignore[arg-type]
                report_only=item_payload["report_only"],  # type: ignore[arg-type]
                readonly=item_payload["readonly"],  # type: ignore[arg-type]
            ),
        )
    if tuple(item.key for item in public_items) != tuple(
        sorted(item.key for item in public_items)
    ):
        raise ValueError("payload schema public_payload must use deterministic ordering")

    validated = ResearchStrategyEventClusterSignalMemoryScoreReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_require_payload_string("config_version", payload["config_version"]),
        status=_require_payload_string("status", payload["status"]),
        cluster_count=_payload_decimal("cluster_count", payload["cluster_count"]),
        signal_count=_payload_decimal("signal_count", payload["signal_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_memory_score=_payload_decimal(
            "average_memory_score", payload["average_memory_score"]
        ),
        rows=tuple(rows),
        reason_code_counts=tuple(counts),
        reason_codes=tuple(
            _require_payload_string_list("reason_codes", payload["reason_codes"])
        ),
        public_payload=tuple(public_items),
        derived_validation_digest=_require_payload_string(
            "derived_validation_digest", payload["derived_validation_digest"]
        ),
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )
    _validate_report_for_payload(validated)
    return _json_ready(asdict(validated))


def _require_exact_payload_keys(
    label: str,
    value: dict[str, object],
    expected: set[str],
) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} payload schema must match exactly")


def _require_payload_mapping(label: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} payload schema must be an object")
    return value


def _require_payload_list(label: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label} payload schema must be an array")
    return value


def _require_payload_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} payload schema must be a string")
    return value


def _require_payload_string_list(label: str, value: object) -> list[str]:
    values = _require_payload_list(label, value)
    if any(type(item) is not str for item in values):
        raise ValueError(f"{label} payload schema must contain strings")
    return values  # type: ignore[return-value]


def _payload_decimal(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{label} payload schema must be a Decimal string") from exc
    if not parsed.is_finite() or str(_quantize(parsed)) != text:
        raise ValueError(f"{label} payload schema must use a canonical Decimal string")
    return parsed


def _payload_datetime(label: str, value: object) -> datetime:
    text = _require_payload_string(label, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} payload schema must be an ISO datetime") from exc
    normalized = _as_utc(label, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{label} payload schema must use canonical UTC")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_fingerprint(field_name: str, value: object) -> str:
    if type(value) is not str or not _FINGERPRINT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 fingerprint")
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


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
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


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
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


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            normalized = value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value exceeds the fixed numeric context") from exc
    return _ZERO if normalized.is_zero() else normalized


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86_400)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000")),
        )


def _recency_score(age_seconds: Decimal, stale_signal_age_seconds: Decimal) -> Decimal:
    if age_seconds >= stale_signal_age_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(_ONE - (age_seconds / stale_signal_age_seconds))


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must be nonempty")
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
    report: ResearchStrategyEventClusterSignalMemoryScoreReport,
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
    "DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_SIGNAL_MEMORY_SCORE_CONFIG_VERSION",
    "ResearchStrategyEventClusterSignalMemoryObservation",
    "ResearchStrategyEventClusterSignalMemoryPublicPayloadItem",
    "ResearchStrategyEventClusterSignalMemoryReasonCodeCount",
    "ResearchStrategyEventClusterSignalMemoryScoreConfig",
    "ResearchStrategyEventClusterSignalMemoryScoreReport",
    "ResearchStrategyEventClusterSignalMemoryScoreRow",
    "build_research_strategy_event_cluster_signal_memory_score_report",
    "research_strategy_event_cluster_signal_memory_score_report_payload",
)
