"""Pure report-only strategy edge decay monitor."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-strategy-edge-decay-monitor-report-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
AGE_WATCH_PRESSURE = Decimal("0.400000")
AGE_BLOCK_PRESSURE = Decimal("0.800000")
DECIMAL_CONTEXT = Context(prec=64)
PUBLIC_STATUSES = ("pass", "watch", "block")

REPORT_REASON_PRIORITY = (
    "strategy_edge_decay_monitor_clear",
    "strategy_edge_decay_block",
    "strategy_edge_decay_watch",
    "strategy_edge_decay_pass",
    "probability_delta_age_block",
    "probability_delta_age_watch",
    "evidence_freshness_block",
    "evidence_freshness_watch",
    "cost_drift_block",
    "cost_drift_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
)
ROW_REASON_PRIORITY = (
    "strategy_edge_decay_block",
    "strategy_edge_decay_watch",
    "strategy_edge_decay_pass",
    "probability_delta_age_block",
    "probability_delta_age_watch",
    "evidence_freshness_block",
    "evidence_freshness_watch",
    "cost_drift_block",
    "cost_drift_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
)
STATUS_SORT_PRIORITY = {"block": 0, "watch": 1, "pass": 2}
REASON_SORT_PRIORITY = {
    reason_code: index for index, reason_code in enumerate(ROW_REASON_PRIORITY)
}
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market_id",
    "slug",
    "question",
    "url",
    "http://",
    "https://",
    "://",
    "source_text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "recommend",
    "sizing",
    "size",
    "live",
    "auth",
    "private_key",
    "secret",
    "password",
    "bearer",
)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorObservation:
    monitor_bucket: str
    observed_at: datetime
    probability_delta_age_seconds: Decimal
    evidence_freshness_score: Decimal
    cost_drift_score: Decimal
    contradiction_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchStrategyEdgeDecayMonitorObservation",
            )
        _require_public_identifier("monitor_bucket", self.monitor_bucket)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_delta_age_seconds",
            _normalize_nonnegative_decimal(
                "probability_delta_age_seconds",
                self.probability_delta_age_seconds,
            ),
        )
        for field_name in (
            "evidence_freshness_score",
            "cost_drift_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_probability_delta_age_seconds: Decimal = Decimal("900.000000")
    block_probability_delta_age_seconds: Decimal = Decimal("1800.000000")
    watch_evidence_freshness_floor: Decimal = Decimal("0.650000")
    block_evidence_freshness_floor: Decimal = Decimal("0.350000")
    watch_cost_drift_score: Decimal = Decimal("0.250000")
    block_cost_drift_score: Decimal = Decimal("0.500000")
    watch_contradiction_pressure_score: Decimal = Decimal("0.300000")
    block_contradiction_pressure_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorReportConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyEdgeDecayMonitorReportConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "watch_probability_delta_age_seconds",
            "block_probability_delta_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.block_probability_delta_age_seconds
            <= self.watch_probability_delta_age_seconds
        ):
            raise ValueError(
                "block_probability_delta_age_seconds must exceed "
                "watch_probability_delta_age_seconds",
            )
        for field_name in (
            "watch_evidence_freshness_floor",
            "block_evidence_freshness_floor",
            "watch_cost_drift_score",
            "block_cost_drift_score",
            "watch_contradiction_pressure_score",
            "block_contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_evidence_freshness_floor >= self.watch_evidence_freshness_floor:
            raise ValueError(
                "block_evidence_freshness_floor must be below "
                "watch_evidence_freshness_floor",
            )
        if self.block_cost_drift_score <= self.watch_cost_drift_score:
            raise ValueError("block_cost_drift_score must exceed watch_cost_drift_score")
        if (
            self.block_contradiction_pressure_score
            <= self.watch_contradiction_pressure_score
        ):
            raise ValueError(
                "block_contradiction_pressure_score must exceed "
                "watch_contradiction_pressure_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorBucket:
    monitor_bucket: str
    observation_count: Decimal
    average_probability_delta_age_seconds: Decimal
    minimum_evidence_freshness_score: Decimal
    maximum_cost_drift_score: Decimal
    maximum_contradiction_pressure_score: Decimal
    edge_decay_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorBucket:
            raise ValueError("bucket must be exactly ResearchStrategyEdgeDecayMonitorBucket")
        _require_public_identifier("monitor_bucket", self.monitor_bucket)
        object.__setattr__(
            self,
            "observation_count",
            _normalize_count_decimal("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "average_probability_delta_age_seconds",
            _normalize_nonnegative_decimal(
                "average_probability_delta_age_seconds",
                self.average_probability_delta_age_seconds,
            ),
        )
        for field_name in (
            "minimum_evidence_freshness_score",
            "maximum_cost_drift_score",
            "maximum_contradiction_pressure_score",
            "edge_decay_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("bucket", self)
        _validate_bucket(self)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    bucket_count: Decimal
    watch_bucket_count: Decimal
    block_bucket_count: Decimal
    average_probability_delta_age_seconds: Decimal
    minimum_evidence_freshness_score: Decimal
    maximum_cost_drift_score: Decimal
    maximum_contradiction_pressure_score: Decimal
    maximum_edge_decay_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    bucket_rows: tuple[ResearchStrategyEdgeDecayMonitorBucket, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorReport:
            raise ValueError("report must be exactly ResearchStrategyEdgeDecayMonitorReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "bucket_count",
            "watch_bucket_count",
            "block_bucket_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_probability_delta_age_seconds",
            _normalize_nonnegative_decimal(
                "average_probability_delta_age_seconds",
                self.average_probability_delta_age_seconds,
            ),
        )
        for field_name in (
            "minimum_evidence_freshness_score",
            "maximum_cost_drift_score",
            "maximum_contradiction_pressure_score",
            "maximum_edge_decay_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "bucket_rows", _normalize_bucket_rows(self.bucket_rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_surface("report", self)


def build_research_strategy_edge_decay_monitor_report(
    observations: Iterable[object],
    *,
    config: ResearchStrategyEdgeDecayMonitorReportConfig,
    generated_at: datetime,
) -> ResearchStrategyEdgeDecayMonitorReport:
    if type(config) is not ResearchStrategyEdgeDecayMonitorReportConfig:
        raise ValueError("config must be a ResearchStrategyEdgeDecayMonitorReportConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations, generated_at)
    bucket_rows = _bucket_rows(normalized_observations, config)
    return ResearchStrategyEdgeDecayMonitorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count_decimal(len(normalized_observations)),
        bucket_count=_count_decimal(len(bucket_rows)),
        watch_bucket_count=_status_count(bucket_rows, "watch"),
        block_bucket_count=_status_count(bucket_rows, "block"),
        average_probability_delta_age_seconds=_average_decimal(
            tuple(
                observation.probability_delta_age_seconds
                for observation in normalized_observations
            ),
        ),
        minimum_evidence_freshness_score=_min_decimal(
            tuple(
                observation.evidence_freshness_score
                for observation in normalized_observations
            ),
        ),
        maximum_cost_drift_score=_max_decimal(
            tuple(observation.cost_drift_score for observation in normalized_observations),
        ),
        maximum_contradiction_pressure_score=_max_decimal(
            tuple(
                observation.contradiction_pressure_score
                for observation in normalized_observations
            ),
        ),
        maximum_edge_decay_pressure_score=_max_decimal(
            tuple(row.edge_decay_pressure_score for row in bucket_rows),
        ),
        status=_report_status(bucket_rows),
        reason_codes=_report_reason_codes(bucket_rows),
        bucket_rows=bucket_rows,
    )


def research_strategy_edge_decay_monitor_report_payload(
    report: ResearchStrategyEdgeDecayMonitorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyEdgeDecayMonitorReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _report_payload(report)
        validate_research_strategy_edge_decay_monitor_public_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_surface("public payload", report)
        _reject_public_numerics(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        validate_research_strategy_edge_decay_monitor_public_payload(payload)
        return payload
    raise ValueError("report must be a ResearchStrategyEdgeDecayMonitorReport")


def validate_research_strategy_edge_decay_monitor_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_exact_keys("public payload", payload, REPORT_PAYLOAD_KEYS)
    _require_iso_datetime_string("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    for field_name in REPORT_COUNT_FIELDS:
        _require_count_string(field_name, payload[field_name])
    _require_decimal_string(
        "average_probability_delta_age_seconds",
        payload["average_probability_delta_age_seconds"],
    )
    for field_name in REPORT_SCORE_FIELDS:
        _require_probability_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _require_reason_code_list("reason_codes", payload["reason_codes"])
    if type(payload["bucket_rows"]) is not list:
        raise ValueError("bucket_rows must be a list")
    for row in payload["bucket_rows"]:
        _validate_public_bucket_payload(row)
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


REPORT_COUNT_FIELDS = (
    "observation_count",
    "bucket_count",
    "watch_bucket_count",
    "block_bucket_count",
)
REPORT_SCORE_FIELDS = (
    "minimum_evidence_freshness_score",
    "maximum_cost_drift_score",
    "maximum_contradiction_pressure_score",
    "maximum_edge_decay_pressure_score",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *REPORT_COUNT_FIELDS,
    "average_probability_delta_age_seconds",
    *REPORT_SCORE_FIELDS,
    "status",
    "reason_codes",
    "bucket_rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
BUCKET_COUNT_FIELDS = ("observation_count",)
BUCKET_SCORE_FIELDS = (
    "minimum_evidence_freshness_score",
    "maximum_cost_drift_score",
    "maximum_contradiction_pressure_score",
    "edge_decay_pressure_score",
)
BUCKET_PAYLOAD_KEYS = (
    "monitor_bucket",
    *BUCKET_COUNT_FIELDS,
    "average_probability_delta_age_seconds",
    *BUCKET_SCORE_FIELDS,
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
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
    observations: Iterable[object],
    generated_at: datetime,
) -> tuple[ResearchStrategyEdgeDecayMonitorObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen: set[tuple[object, ...]] = set()
    for observation in normalized:
        if type(observation) is not ResearchStrategyEdgeDecayMonitorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyEdgeDecayMonitorObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        duplicate_key = (
            observation.monitor_bucket,
            observation.observed_at,
            observation.probability_delta_age_seconds,
            observation.evidence_freshness_score,
            observation.cost_drift_score,
            observation.contradiction_pressure_score,
        )
        if duplicate_key in seen:
            raise ValueError("duplicate monitor_bucket observation")
        seen.add(duplicate_key)
    return normalized


def _bucket_rows(
    observations: tuple[ResearchStrategyEdgeDecayMonitorObservation, ...],
    config: ResearchStrategyEdgeDecayMonitorReportConfig,
) -> tuple[ResearchStrategyEdgeDecayMonitorBucket, ...]:
    grouped: dict[str, list[ResearchStrategyEdgeDecayMonitorObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.monitor_bucket, []).append(observation)
    rows = tuple(
        _bucket_from_observations(monitor_bucket, tuple(group), config)
        for monitor_bucket, group in grouped.items()
    )
    return tuple(sorted(rows, key=_bucket_sort_key))


def _bucket_from_observations(
    monitor_bucket: str,
    observations: tuple[ResearchStrategyEdgeDecayMonitorObservation, ...],
    config: ResearchStrategyEdgeDecayMonitorReportConfig,
) -> ResearchStrategyEdgeDecayMonitorBucket:
    average_age = _average_decimal(
        tuple(observation.probability_delta_age_seconds for observation in observations),
    )
    minimum_freshness = _min_decimal(
        tuple(observation.evidence_freshness_score for observation in observations),
    )
    maximum_cost = _max_decimal(
        tuple(observation.cost_drift_score for observation in observations),
    )
    maximum_contradiction = _max_decimal(
        tuple(observation.contradiction_pressure_score for observation in observations),
    )
    status = _bucket_status(
        average_probability_delta_age_seconds=average_age,
        minimum_evidence_freshness_score=minimum_freshness,
        maximum_cost_drift_score=maximum_cost,
        maximum_contradiction_pressure_score=maximum_contradiction,
        config=config,
    )
    return ResearchStrategyEdgeDecayMonitorBucket(
        monitor_bucket=monitor_bucket,
        observation_count=_count_decimal(len(observations)),
        average_probability_delta_age_seconds=average_age,
        minimum_evidence_freshness_score=minimum_freshness,
        maximum_cost_drift_score=maximum_cost,
        maximum_contradiction_pressure_score=maximum_contradiction,
        edge_decay_pressure_score=_edge_decay_pressure_score(
            average_probability_delta_age_seconds=average_age,
            minimum_evidence_freshness_score=minimum_freshness,
            maximum_cost_drift_score=maximum_cost,
            maximum_contradiction_pressure_score=maximum_contradiction,
            config=config,
        ),
        status=status,
        reason_codes=_bucket_reason_codes(
            status=status,
            average_probability_delta_age_seconds=average_age,
            minimum_evidence_freshness_score=minimum_freshness,
            maximum_cost_drift_score=maximum_cost,
            maximum_contradiction_pressure_score=maximum_contradiction,
            config=config,
        ),
    )


def _bucket_status(
    *,
    average_probability_delta_age_seconds: Decimal,
    minimum_evidence_freshness_score: Decimal,
    maximum_cost_drift_score: Decimal,
    maximum_contradiction_pressure_score: Decimal,
    config: ResearchStrategyEdgeDecayMonitorReportConfig,
) -> str:
    if (
        average_probability_delta_age_seconds
        >= config.block_probability_delta_age_seconds
        or minimum_evidence_freshness_score <= config.block_evidence_freshness_floor
        or maximum_cost_drift_score >= config.block_cost_drift_score
        or maximum_contradiction_pressure_score
        >= config.block_contradiction_pressure_score
    ):
        return "block"
    if (
        average_probability_delta_age_seconds
        >= config.watch_probability_delta_age_seconds
        or minimum_evidence_freshness_score <= config.watch_evidence_freshness_floor
        or maximum_cost_drift_score >= config.watch_cost_drift_score
        or maximum_contradiction_pressure_score
        >= config.watch_contradiction_pressure_score
    ):
        return "watch"
    return "pass"


def _bucket_reason_codes(
    *,
    status: str,
    average_probability_delta_age_seconds: Decimal,
    minimum_evidence_freshness_score: Decimal,
    maximum_cost_drift_score: Decimal,
    maximum_contradiction_pressure_score: Decimal,
    config: ResearchStrategyEdgeDecayMonitorReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"strategy_edge_decay_{status}"]
    reason_codes.extend(
        _threshold_reason_codes(
            "probability_delta_age",
            average_probability_delta_age_seconds,
            watch_threshold=config.watch_probability_delta_age_seconds,
            block_threshold=config.block_probability_delta_age_seconds,
            lower_is_worse=False,
        ),
    )
    reason_codes.extend(
        _threshold_reason_codes(
            "evidence_freshness",
            minimum_evidence_freshness_score,
            watch_threshold=config.watch_evidence_freshness_floor,
            block_threshold=config.block_evidence_freshness_floor,
            lower_is_worse=True,
        ),
    )
    reason_codes.extend(
        _threshold_reason_codes(
            "cost_drift",
            maximum_cost_drift_score,
            watch_threshold=config.watch_cost_drift_score,
            block_threshold=config.block_cost_drift_score,
            lower_is_worse=False,
        ),
    )
    reason_codes.extend(
        _threshold_reason_codes(
            "contradiction_pressure",
            maximum_contradiction_pressure_score,
            watch_threshold=config.watch_contradiction_pressure_score,
            block_threshold=config.block_contradiction_pressure_score,
            lower_is_worse=False,
        ),
    )
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _threshold_reason_codes(
    label: str,
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    lower_is_worse: bool,
) -> tuple[str, ...]:
    if lower_is_worse:
        if value <= block_threshold:
            return (f"{label}_block",)
        if value <= watch_threshold:
            return (f"{label}_watch",)
        return ()
    if value >= block_threshold:
        return (f"{label}_block",)
    if value >= watch_threshold:
        return (f"{label}_watch",)
    return ()


def _edge_decay_pressure_score(
    *,
    average_probability_delta_age_seconds: Decimal,
    minimum_evidence_freshness_score: Decimal,
    maximum_cost_drift_score: Decimal,
    maximum_contradiction_pressure_score: Decimal,
    config: ResearchStrategyEdgeDecayMonitorReportConfig,
) -> Decimal:
    age_pressure = _probability_delta_age_pressure(
        average_probability_delta_age_seconds,
        config,
    )
    evidence_pressure = _subtract_decimal(ONE, minimum_evidence_freshness_score)
    return _max_decimal(
        (
            age_pressure,
            evidence_pressure,
            maximum_cost_drift_score,
            maximum_contradiction_pressure_score,
        ),
    )


def _probability_delta_age_pressure(
    value: Decimal,
    config: ResearchStrategyEdgeDecayMonitorReportConfig,
) -> Decimal:
    if value >= config.block_probability_delta_age_seconds:
        return AGE_BLOCK_PRESSURE
    if value >= config.watch_probability_delta_age_seconds:
        return AGE_WATCH_PRESSURE
    return ZERO


def _report_status(rows: tuple[ResearchStrategyEdgeDecayMonitorBucket, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEdgeDecayMonitorBucket, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_edge_decay_monitor_clear",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    if any(row.status != "pass" for row in rows):
        reason_codes = [
            reason_code
            for reason_code in reason_codes
            if reason_code != "strategy_edge_decay_pass"
        ]
    return _sort_report_reason_codes(tuple(reason_codes))


def _sort_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(reason_codes))
    priority = {reason_code: index for index, reason_code in enumerate(REPORT_REASON_PRIORITY)}
    return tuple(sorted(unique, key=lambda reason_code: (priority.get(reason_code, 999), reason_code)))


def _bucket_sort_key(
    row: ResearchStrategyEdgeDecayMonitorBucket,
) -> tuple[int, str]:
    return (STATUS_SORT_PRIORITY[row.status], row.monitor_bucket)


def _status_count(
    rows: tuple[ResearchStrategyEdgeDecayMonitorBucket, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _report_payload(report: ResearchStrategyEdgeDecayMonitorReport) -> dict[str, Any]:
    unsigned_payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "observation_count": _count_payload(report.observation_count),
        "bucket_count": _count_payload(report.bucket_count),
        "watch_bucket_count": _count_payload(report.watch_bucket_count),
        "block_bucket_count": _count_payload(report.block_bucket_count),
        "average_probability_delta_age_seconds": _decimal_payload(
            report.average_probability_delta_age_seconds,
        ),
        "minimum_evidence_freshness_score": _decimal_payload(
            report.minimum_evidence_freshness_score,
        ),
        "maximum_cost_drift_score": _decimal_payload(report.maximum_cost_drift_score),
        "maximum_contradiction_pressure_score": _decimal_payload(
            report.maximum_contradiction_pressure_score,
        ),
        "maximum_edge_decay_pressure_score": _decimal_payload(
            report.maximum_edge_decay_pressure_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "bucket_rows": [_bucket_payload(row) for row in report.bucket_rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    payload = dict(unsigned_payload)
    payload["derived_validation_digest"] = _digest_payload(unsigned_payload)
    return payload


def _bucket_payload(row: ResearchStrategyEdgeDecayMonitorBucket) -> dict[str, Any]:
    return {
        "monitor_bucket": row.monitor_bucket,
        "observation_count": _count_payload(row.observation_count),
        "average_probability_delta_age_seconds": _decimal_payload(
            row.average_probability_delta_age_seconds,
        ),
        "minimum_evidence_freshness_score": _decimal_payload(
            row.minimum_evidence_freshness_score,
        ),
        "maximum_cost_drift_score": _decimal_payload(row.maximum_cost_drift_score),
        "maximum_contradiction_pressure_score": _decimal_payload(
            row.maximum_contradiction_pressure_score,
        ),
        "edge_decay_pressure_score": _decimal_payload(row.edge_decay_pressure_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_public_bucket_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("bucket_rows must contain JSON objects")
    _require_exact_keys("bucket row", value, BUCKET_PAYLOAD_KEYS)
    _require_public_identifier("monitor_bucket", value["monitor_bucket"])
    for field_name in BUCKET_COUNT_FIELDS:
        _require_count_string(field_name, value[field_name])
    _require_decimal_string(
        "average_probability_delta_age_seconds",
        value["average_probability_delta_age_seconds"],
    )
    for field_name in BUCKET_SCORE_FIELDS:
        _require_probability_string(field_name, value[field_name])
    _require_status("status", value["status"])
    _require_reason_code_list("reason_codes", value["reason_codes"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_bucket(row: ResearchStrategyEdgeDecayMonitorBucket) -> None:
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive for bucket")
    if row.status == "pass" and row.reason_codes != ("strategy_edge_decay_pass",):
        raise ValueError("pass bucket reason_codes must be clear")
    if row.status != "pass" and f"strategy_edge_decay_{row.status}" not in row.reason_codes:
        raise ValueError("bucket reason_codes must include status reason")


def _validate_report(report: ResearchStrategyEdgeDecayMonitorReport) -> None:
    if report.bucket_count != _count_decimal(len(report.bucket_rows)):
        raise ValueError("bucket_count must equal bucket_rows length")
    if report.observation_count != _sum_decimal(
        row.observation_count for row in report.bucket_rows
    ):
        raise ValueError("observation_count must equal bucket row observations")
    if report.watch_bucket_count != _status_count(report.bucket_rows, "watch"):
        raise ValueError("watch_bucket_count must match bucket_rows")
    if report.block_bucket_count != _status_count(report.bucket_rows, "block"):
        raise ValueError("block_bucket_count must match bucket_rows")
    if report.maximum_edge_decay_pressure_score != _max_decimal(
        tuple(row.edge_decay_pressure_score for row in report.bucket_rows),
    ):
        raise ValueError("maximum_edge_decay_pressure_score must match bucket_rows")
    if report.status != _report_status(report.bucket_rows):
        raise ValueError("status must match bucket_rows")
    if tuple(report.bucket_rows) != tuple(sorted(report.bucket_rows, key=_bucket_sort_key)):
        raise ValueError("bucket_rows must be sorted deterministically")
    if report.bucket_rows:
        if report.reason_codes != _report_reason_codes(report.bucket_rows):
            raise ValueError("reason_codes must match bucket_rows")
    elif report.reason_codes != ("strategy_edge_decay_monitor_clear",):
        raise ValueError("empty report reason_codes must be clear")


def _normalize_bucket_rows(
    rows: tuple[ResearchStrategyEdgeDecayMonitorBucket, ...],
) -> tuple[ResearchStrategyEdgeDecayMonitorBucket, ...]:
    if type(rows) is not tuple:
        raise ValueError("bucket_rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyEdgeDecayMonitorBucket:
            raise ValueError("bucket_rows must contain ResearchStrategyEdgeDecayMonitorBucket")
        _require_hard_flags("bucket row", row)
        if row.monitor_bucket in seen:
            raise ValueError("duplicate monitor_bucket")
        seen.add(row.monitor_bucket)
    return rows


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                REASON_SORT_PRIORITY.get(reason_code, 999),
                reason_code,
            ),
        ),
    )


def _require_reason_code_list(field_name: str, value: object) -> None:
    if type(value) is not list or not value:
        raise ValueError(f"{field_name} must be a non-empty list")
    for item in value:
        _require_reason_code(field_name, item)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    _require_public_identifier(field_name, value)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {field_name}")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in value):
        raise ValueError(f"{field_name} must be a public canonical identifier")
    return value


def _require_status(field_name: str, value: object) -> str:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio_decimal(_sum_decimal(values), _count_decimal(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left + right).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _ratio_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (left / right).quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    normalized = _normalize_count_decimal("payload count", value)
    return str(int(normalized))


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    return _normalize_nonnegative_decimal(field_name, parsed)


def _require_probability_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    return _normalize_probability_decimal(field_name, parsed)


def _require_count_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    return _normalize_count_decimal(field_name, parsed)


def _require_iso_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    if "T" not in value or not value.endswith("+00:00"):
        raise ValueError(f"{field_name} must be a UTC ISO datetime string")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_exact_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    keys = tuple(value.keys())
    if set(keys) != set(expected_keys):
        raise ValueError(f"{label} must use the public readonly schema")


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
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


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("public payload must not contain float")
    if type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


__all__ = (
    "ResearchStrategyEdgeDecayMonitorObservation",
    "ResearchStrategyEdgeDecayMonitorReportConfig",
    "ResearchStrategyEdgeDecayMonitorReport",
    "ResearchStrategyEdgeDecayMonitorBucket",
    "build_research_strategy_edge_decay_monitor_report",
    "research_strategy_edge_decay_monitor_report_payload",
    "validate_research_strategy_edge_decay_monitor_public_payload",
)
