"""Pure report-only correlation checks for research event clusters."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping


DEFAULT_RESEARCH_MARKET_CLUSTER_CORRELATION_CONFIG_VERSION = (
    "research-market-cluster-correlation-report-v0"
)

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_FOUR = Decimal("4.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "cluster_pass",
    "correlation_watch",
    "correlation_block",
    "risk_overlap_watch",
    "risk_overlap_block",
    "cluster_size_watch",
    "cluster_size_block",
    "confidence_watch",
    "confidence_block",
)
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("raw", "_", "candidate", "_", "id"),
        ("candidate", "_", "id"),
        ("market", "_", "id"),
        ("market", "_", "slug"),
        ("market", "_", "question"),
        ("quest", "ion"),
        ("sou", "rce", "_", "ref"),
        ("sou", "rce", "_", "url"),
        ("sou", "rce", "_", "text"),
        ("http", "://"),
        ("https", "://"),
        ("ur", "l"),
        ("d", "sn"),
        ("ta", "ble"),
        ("to", "ken"),
        ("wa", "llet"),
        ("au", "th"),
        ("or", "der"),
        ("tr", "ade"),
        ("po", "sition"),
        ("b", "uy"),
        ("se", "ll"),
        ("reco", "mmend"),
    )
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_CLUSTER_CORRELATION_CONFIG_VERSION",
    "ResearchMarketClusterCorrelationConfig",
    "ResearchMarketClusterCorrelationDigest",
    "ResearchMarketClusterCorrelationObservation",
    "ResearchMarketClusterCorrelationReport",
    "ResearchMarketClusterCorrelationRow",
    "build_research_market_cluster_correlation_report",
    "research_market_cluster_correlation_digest",
    "research_market_cluster_correlation_digest_payload",
    "research_market_cluster_correlation_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketClusterCorrelationConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_CLUSTER_CORRELATION_CONFIG_VERSION
    watch_correlation_score: Decimal = Decimal("0.450000")
    block_correlation_score: Decimal = Decimal("0.700000")
    watch_risk_overlap_score: Decimal = Decimal("0.450000")
    block_risk_overlap_score: Decimal = Decimal("0.700000")
    watch_cluster_event_count: Decimal = Decimal("2.000000")
    block_cluster_event_count: Decimal = Decimal("3.000000")
    watch_confidence_floor: Decimal = Decimal("0.500000")
    block_confidence_floor: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClusterCorrelationConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_CLUSTER_CORRELATION_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_correlation_score",
            "block_correlation_score",
            "watch_risk_overlap_score",
            "block_risk_overlap_score",
            "watch_confidence_floor",
            "block_confidence_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_cluster_event_count",
            "block_cluster_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_threshold_not_above_block(
            "correlation_score",
            self.watch_correlation_score,
            self.block_correlation_score,
        )
        _require_watch_threshold_not_above_block(
            "risk_overlap_score",
            self.watch_risk_overlap_score,
            self.block_risk_overlap_score,
        )
        _require_watch_threshold_not_above_block(
            "cluster_event_count",
            self.watch_cluster_event_count,
            self.block_cluster_event_count,
        )
        if self.block_confidence_floor > self.watch_confidence_floor:
            raise ValueError("block_confidence_floor must not exceed watch_confidence_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketClusterCorrelationObservation(_FinalPublicDataclass):
    candidate_label: str
    theme_label: str
    risk_label: str
    resolution_window: str
    observed_at: datetime
    theme_similarity_score: Decimal
    risk_correlation_score: Decimal
    shared_driver_score: Decimal
    evidence_overlap_score: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketClusterCorrelationObservation,
            "observation",
        )
        for field_name in (
            "candidate_label",
            "theme_label",
            "risk_label",
            "resolution_window",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "theme_similarity_score",
            "risk_correlation_score",
            "shared_driver_score",
            "evidence_overlap_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketClusterCorrelationRow(_FinalPublicDataclass):
    theme_label: str
    risk_label: str
    resolution_window: str
    event_count: Decimal
    average_theme_similarity_score: Decimal
    average_risk_correlation_score: Decimal
    average_shared_driver_score: Decimal
    average_evidence_overlap_score: Decimal
    average_confidence_score: Decimal
    correlation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClusterCorrelationRow, "row")
        for field_name in ("theme_label", "risk_label", "resolution_window"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "event_count",
            _require_positive_count_decimal("event_count", self.event_count),
        )
        for field_name in (
            "average_theme_similarity_score",
            "average_risk_correlation_score",
            "average_shared_driver_score",
            "average_evidence_overlap_score",
            "average_confidence_score",
            "correlation_score",
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
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketClusterCorrelationDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    cluster_count: Decimal
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_correlation_score: Decimal
    average_correlation_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClusterCorrelationDigest, "digest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_CLUSTER_CORRELATION_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "cluster_count",
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_correlation_score", "average_correlation_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_digest_consistency(self)
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)
        expected_digest = _digest_from_values(_digest_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match digest fields")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cluster_correlation_digest_payload(self)


@dataclass(frozen=True)
class ResearchMarketClusterCorrelationReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    digest: ResearchMarketClusterCorrelationDigest
    cluster_count: Decimal
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_correlation_score: Decimal
    average_correlation_score: Decimal
    rows: tuple[ResearchMarketClusterCorrelationRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClusterCorrelationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_CLUSTER_CORRELATION_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        if type(self.digest) is not ResearchMarketClusterCorrelationDigest:
            raise ValueError("digest must be a ResearchMarketClusterCorrelationDigest")
        _require_hard_flags("digest", self.digest)
        for field_name in (
            "cluster_count",
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_correlation_score", "average_correlation_score"):
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
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cluster_correlation_report_payload(self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketClusterCorrelationConfig,
    ResearchMarketClusterCorrelationDigest,
    ResearchMarketClusterCorrelationObservation,
    ResearchMarketClusterCorrelationReport,
    ResearchMarketClusterCorrelationRow,
)


def build_research_market_cluster_correlation_report(
    observations: Sequence[ResearchMarketClusterCorrelationObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketClusterCorrelationConfig | None = None,
) -> ResearchMarketClusterCorrelationReport:
    """Build a deterministic paper-only review report from caller-supplied inputs."""

    if config is None:
        config = ResearchMarketClusterCorrelationConfig()
    if type(config) is not ResearchMarketClusterCorrelationConfig:
        raise ValueError("config must be a ResearchMarketClusterCorrelationConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_observations, config=config)
    reason_codes = _report_reason_codes(rows)
    digest_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "cluster_count": _decimal_count(len(rows)),
        "event_count": _sum_decimals(tuple(row.event_count for row in rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "max_correlation_score": _max_correlation_score(rows),
        "average_correlation_score": _weighted_row_average(rows, "correlation_score"),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = ResearchMarketClusterCorrelationDigest(
        **digest_values,
        derived_validation_digest=_digest_from_values(digest_values),
    )
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": digest.status,
        "digest": digest,
        "cluster_count": digest.cluster_count,
        "event_count": digest.event_count,
        "pass_count": digest.pass_count,
        "watch_count": digest.watch_count,
        "block_count": digest.block_count,
        "max_correlation_score": digest.max_correlation_score,
        "average_correlation_score": digest.average_correlation_score,
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketClusterCorrelationReport(
        **report_values,
        derived_validation_digest=_digest_from_values(report_values),
    )


def research_market_cluster_correlation_digest(
    report: ResearchMarketClusterCorrelationReport,
) -> ResearchMarketClusterCorrelationDigest:
    if type(report) is not ResearchMarketClusterCorrelationReport:
        raise ValueError("report must be a ResearchMarketClusterCorrelationReport")
    _require_payload_safe_value("report", report)
    return report.digest


def research_market_cluster_correlation_digest_payload(
    digest: ResearchMarketClusterCorrelationDigest,
) -> dict[str, Any]:
    if type(digest) is not ResearchMarketClusterCorrelationDigest:
        raise ValueError("digest payload must be a ResearchMarketClusterCorrelationDigest")
    _require_payload_safe_value("digest", digest)
    payload = _payload_value(digest)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    _reject_unsafe_public_payload("digest payload", payload)
    return payload


def research_market_cluster_correlation_report_payload(
    report: ResearchMarketClusterCorrelationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketClusterCorrelationReport:
        raise ValueError("report payload must be a ResearchMarketClusterCorrelationReport")
    _require_payload_safe_value("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _build_rows(
    observations: tuple[ResearchMarketClusterCorrelationObservation, ...],
    *,
    config: ResearchMarketClusterCorrelationConfig,
) -> tuple[ResearchMarketClusterCorrelationRow, ...]:
    grouped: dict[tuple[str, str, str], list[ResearchMarketClusterCorrelationObservation]]
    grouped = {}
    for observation in observations:
        key = (
            observation.theme_label,
            observation.risk_label,
            observation.resolution_window,
        )
        grouped.setdefault(key, []).append(observation)
    return _sorted_rows(
        tuple(
            _row_from_cluster(key, tuple(cluster_observations), config=config)
            for key, cluster_observations in grouped.items()
        ),
    )


def _row_from_cluster(
    key: tuple[str, str, str],
    observations: tuple[ResearchMarketClusterCorrelationObservation, ...],
    *,
    config: ResearchMarketClusterCorrelationConfig,
) -> ResearchMarketClusterCorrelationRow:
    theme_label, risk_label, resolution_window = key
    event_count = _decimal_count(len(observations))
    average_theme_similarity_score = _average_decimal(
        tuple(observation.theme_similarity_score for observation in observations),
    )
    average_risk_correlation_score = _average_decimal(
        tuple(observation.risk_correlation_score for observation in observations),
    )
    average_shared_driver_score = _average_decimal(
        tuple(observation.shared_driver_score for observation in observations),
    )
    average_evidence_overlap_score = _average_decimal(
        tuple(observation.evidence_overlap_score for observation in observations),
    )
    average_confidence_score = _average_decimal(
        tuple(observation.confidence_score for observation in observations),
    )
    correlation_score = _cluster_correlation_score(
        average_theme_similarity_score=average_theme_similarity_score,
        average_risk_correlation_score=average_risk_correlation_score,
        average_shared_driver_score=average_shared_driver_score,
        average_evidence_overlap_score=average_evidence_overlap_score,
    )
    status = _row_status(
        event_count=event_count,
        correlation_score=correlation_score,
        average_risk_correlation_score=average_risk_correlation_score,
        average_confidence_score=average_confidence_score,
        config=config,
    )
    return ResearchMarketClusterCorrelationRow(
        theme_label=theme_label,
        risk_label=risk_label,
        resolution_window=resolution_window,
        event_count=event_count,
        average_theme_similarity_score=average_theme_similarity_score,
        average_risk_correlation_score=average_risk_correlation_score,
        average_shared_driver_score=average_shared_driver_score,
        average_evidence_overlap_score=average_evidence_overlap_score,
        average_confidence_score=average_confidence_score,
        correlation_score=correlation_score,
        status=status,
        reason_codes=_row_reason_codes(
            event_count=event_count,
            correlation_score=correlation_score,
            average_risk_correlation_score=average_risk_correlation_score,
            average_confidence_score=average_confidence_score,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    event_count: Decimal,
    correlation_score: Decimal,
    average_risk_correlation_score: Decimal,
    average_confidence_score: Decimal,
    config: ResearchMarketClusterCorrelationConfig,
) -> str:
    if (
        correlation_score >= config.block_correlation_score
        or average_risk_correlation_score >= config.block_risk_overlap_score
        or event_count >= config.block_cluster_event_count
        or average_confidence_score <= config.block_confidence_floor
    ):
        return "block"
    if (
        correlation_score >= config.watch_correlation_score
        or average_risk_correlation_score >= config.watch_risk_overlap_score
        or event_count >= config.watch_cluster_event_count
        or average_confidence_score <= config.watch_confidence_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    event_count: Decimal,
    correlation_score: Decimal,
    average_risk_correlation_score: Decimal,
    average_confidence_score: Decimal,
    status: str,
    config: ResearchMarketClusterCorrelationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if correlation_score >= config.block_correlation_score:
        reason_codes.append("correlation_block")
    elif correlation_score >= config.watch_correlation_score:
        reason_codes.append("correlation_watch")
    if average_risk_correlation_score >= config.block_risk_overlap_score:
        reason_codes.append("risk_overlap_block")
    elif average_risk_correlation_score >= config.watch_risk_overlap_score:
        reason_codes.append("risk_overlap_watch")
    if event_count >= config.block_cluster_event_count:
        reason_codes.append("cluster_size_block")
    elif event_count >= config.watch_cluster_event_count:
        reason_codes.append("cluster_size_watch")
    if average_confidence_score <= config.block_confidence_floor:
        reason_codes.append("confidence_block")
    elif average_confidence_score <= config.watch_confidence_floor:
        reason_codes.append("confidence_watch")
    if status == "pass":
        reason_codes.append("cluster_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchMarketClusterCorrelationRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketClusterCorrelationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _status_count(
    rows: tuple[ResearchMarketClusterCorrelationRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _max_correlation_score(
    rows: tuple[ResearchMarketClusterCorrelationRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.correlation_score for row in rows)


def _weighted_row_average(
    rows: tuple[ResearchMarketClusterCorrelationRow, ...],
    field_name: str,
) -> Decimal:
    event_count = _sum_decimals(tuple(row.event_count for row in rows))
    if event_count == _ZERO:
        return _ZERO
    total = _sum_decimals(
        tuple(getattr(row, field_name) * row.event_count for row in rows),
    )
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(total / event_count)


def _cluster_correlation_score(
    *,
    average_theme_similarity_score: Decimal,
    average_risk_correlation_score: Decimal,
    average_shared_driver_score: Decimal,
    average_evidence_overlap_score: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            (
                average_theme_similarity_score
                + average_risk_correlation_score
                + average_shared_driver_score
                + average_evidence_overlap_score
            )
            / _DECIMAL_FOUR,
        )


def _validate_row_consistency(row: ResearchMarketClusterCorrelationRow) -> None:
    expected_score = _cluster_correlation_score(
        average_theme_similarity_score=row.average_theme_similarity_score,
        average_risk_correlation_score=row.average_risk_correlation_score,
        average_shared_driver_score=row.average_shared_driver_score,
        average_evidence_overlap_score=row.average_evidence_overlap_score,
    )
    if row.correlation_score != expected_score:
        raise ValueError("correlation_score must match row averages")
    if row.status == "pass" and row.reason_codes != ("cluster_pass",):
        raise ValueError("pass rows must only include cluster_pass")
    if row.status == "watch" and not any(
        reason_code.endswith("_watch") for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must include a watch reason code")
    if row.status == "block" and not any(
        reason_code.endswith("_block") for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must include a block reason code")


def _validate_digest_consistency(digest: ResearchMarketClusterCorrelationDigest) -> None:
    if digest.pass_count + digest.watch_count + digest.block_count != digest.cluster_count:
        raise ValueError("status counts must match cluster_count")
    if digest.event_count < digest.cluster_count:
        raise ValueError("event_count must cover cluster_count")
    if digest.cluster_count == _ZERO:
        if digest.status != "block":
            raise ValueError("empty digest status must be block")
        if digest.reason_codes != ("empty_observations",):
            raise ValueError("empty digest reason_codes must match")
    else:
        if digest.reason_codes == ("empty_observations",):
            raise ValueError("non-empty digest reason_codes must match")
    if digest.status != _status_from_counts(digest):
        raise ValueError("status must match counts")


def _validate_report_consistency(report: ResearchMarketClusterCorrelationReport) -> None:
    rows = report.rows
    if report.cluster_count != _decimal_count(len(rows)):
        raise ValueError("cluster_count must match rows")
    if report.event_count != _sum_decimals(tuple(row.event_count for row in rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_correlation_score != _max_correlation_score(rows):
        raise ValueError("max_correlation_score must match rows")
    if report.average_correlation_score != _weighted_row_average(rows, "correlation_score"):
        raise ValueError("average_correlation_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    expected_digest = _digest_for_report(report)
    if report.digest != expected_digest:
        raise ValueError("digest must match report")


def _status_from_counts(digest: ResearchMarketClusterCorrelationDigest) -> str:
    if digest.cluster_count == _ZERO:
        return "block"
    if digest.block_count > _ZERO:
        return "block"
    if digest.watch_count > _ZERO:
        return "watch"
    return "pass"


def _digest_for_report(
    report: ResearchMarketClusterCorrelationReport,
) -> ResearchMarketClusterCorrelationDigest:
    values: dict[str, object] = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "status": report.status,
        "cluster_count": report.cluster_count,
        "event_count": report.event_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "max_correlation_score": report.max_correlation_score,
        "average_correlation_score": report.average_correlation_score,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    return ResearchMarketClusterCorrelationDigest(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def _normalize_observations(
    observations: Sequence[ResearchMarketClusterCorrelationObservation],
) -> tuple[ResearchMarketClusterCorrelationObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    seen_candidate_labels: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchMarketClusterCorrelationObservation:
            raise ValueError(
                "observations must contain ResearchMarketClusterCorrelationObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.candidate_label in seen_candidate_labels:
            raise ValueError("candidate_label values must be unique")
        seen_candidate_labels.add(observation.candidate_label)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.theme_label,
                observation.risk_label,
                observation.resolution_window,
                observation.observed_at,
                observation.candidate_label,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchMarketClusterCorrelationRow],
) -> tuple[ResearchMarketClusterCorrelationRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchMarketClusterCorrelationRow:
            raise ValueError("rows must contain ResearchMarketClusterCorrelationRow")
        _require_hard_flags("row", row)
        key = (row.theme_label, row.risk_label, row.resolution_window)
        if key in seen_keys:
            raise ValueError("rows must contain unique cluster keys")
        seen_keys.add(key)
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _sorted_rows(
    rows: Sequence[ResearchMarketClusterCorrelationRow],
) -> tuple[ResearchMarketClusterCorrelationRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_WEIGHT[row.status],
                -row.correlation_score,
                -row.event_count,
                row.theme_label,
                row.risk_label,
                row.resolution_window,
            ),
        ),
    )


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        seen.add(reason_code)
    if not seen:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in seen)


def _require_exact_type(value: object, type_: type[object], field_name: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{field_name} must be exactly {type_.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_watch_threshold_not_above_block(
    label: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if block_threshold < watch_threshold:
        raise ValueError(f"block {label} threshold must not be below watch threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        _require_decimal(field_name, value)
        if value != _quantize(value):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a known public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (bool, str):
        return
    if type(value) in (dict, list, set, int, float) or value is None:
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be a public value")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    return value


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _digest_values_without_digest(
    digest: ResearchMarketClusterCorrelationDigest,
) -> dict[str, object]:
    values = {field.name: getattr(digest, field.name) for field in fields(digest)}
    values.pop("derived_validation_digest", None)
    return values


def _report_values_without_digest(
    report: ResearchMarketClusterCorrelationReport,
) -> dict[str, object]:
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values.pop("derived_validation_digest", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    _reject_unsafe_public_payload("digest input", values)
    encoded = json.dumps(
        _json_ready(dict(values)),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if type(value) in (Decimal, datetime, bool):
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_string("field", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_string("field", key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) in (int, float, set) or value is None:
        raise ValueError(f"{label} has unsafe public value")
