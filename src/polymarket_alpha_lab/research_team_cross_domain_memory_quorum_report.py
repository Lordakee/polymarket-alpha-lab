"""Public-safe report-only cross-domain memory quorum scoring."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_QUORUM_CONFIG_VERSION = (
    "research-team-cross-domain-memory-quorum-report-v0"
)
PUBLIC_STATUSES = ("pass", "watch", "block")

QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT_PREC = 64
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FLAG_NAMES = ("paper_only", "report_only", "readonly")

ROW_STATUS_REASON_CODES = (
    "cross_domain_memory_quorum_pass",
    "cross_domain_memory_quorum_watch",
    "cross_domain_memory_quorum_block",
)
BLOCK_REASON_CODES = (
    "insufficient_independent_domain_memory_block",
    "memory_freshness_block",
    "calibration_recency_block",
    "contradiction_pressure_block",
    "evidence_reuse_quality_block",
    "open_review_load_block",
)
WATCH_REASON_CODES = (
    "insufficient_independent_domain_memory_watch",
    "memory_freshness_watch",
    "calibration_recency_watch",
    "contradiction_pressure_watch",
    "evidence_reuse_quality_watch",
    "open_review_load_watch",
)
ROW_REASON_CODES = ROW_STATUS_REASON_CODES + BLOCK_REASON_CODES + WATCH_REASON_CODES
REPORT_REASON_CODES = (
    "cross_domain_memory_quorum_report_pass",
    "cross_domain_memory_quorum_report_watch",
    "cross_domain_memory_quorum_report_block",
    "cross_domain_memory_quorum_report_empty",
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "candidate_id",
    "candidateid",
    "event_id",
    "eventid",
    "market",
    "market_id",
    "marketid",
    "market_slug",
    "marketslug",
    "market_question",
    "slug",
    "question",
    "source",
    "source_id",
    "sourceid",
    "source_ref",
    "source_reference",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "database_url",
    "dsn",
    "table_name",
    "table",
    "token",
    "secret",
    "credential",
    "password",
    "private_key",
    "api_key",
    "auth",
    "wallet",
    "order",
    "trade",
    "trading",
    "live",
    "execution",
    "position",
    "buy",
    "sell",
    "recommendation",
    "sizing",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_QUORUM_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamCrossDomainMemoryQuorumConfig",
    "ResearchTeamCrossDomainMemoryQuorumObservation",
    "ResearchTeamCrossDomainMemoryQuorumReport",
    "ResearchTeamCrossDomainMemoryQuorumRow",
    "build_research_team_cross_domain_memory_quorum_report",
    "research_team_cross_domain_memory_quorum_public_payload",
)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryQuorumConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_QUORUM_CONFIG_VERSION
    pass_quorum_score_threshold: Decimal = Decimal("0.750000")
    block_quorum_score_threshold: Decimal = Decimal("0.450000")
    min_pass_independent_domain_memory_count: Decimal = Decimal("3")
    min_watch_independent_domain_memory_count: Decimal = Decimal("2")
    stale_memory_age_seconds: Decimal = Decimal("86400.000000")
    stale_calibration_age_seconds: Decimal = Decimal("604800.000000")
    pass_component_score_threshold: Decimal = Decimal("0.750000")
    block_component_score_threshold: Decimal = Decimal("0.350000")
    pass_contradiction_pressure_score: Decimal = Decimal("0.250000")
    block_contradiction_pressure_score: Decimal = Decimal("0.700000")
    pass_evidence_reuse_quality_score: Decimal = Decimal("0.700000")
    block_evidence_reuse_quality_score: Decimal = Decimal("0.400000")
    pass_open_review_load_pressure_score: Decimal = Decimal("0.300000")
    block_open_review_load_pressure_score: Decimal = Decimal("0.800000")
    max_open_review_count: Decimal = Decimal("10")
    independent_domain_memory_weight: Decimal = Decimal("0.250000")
    memory_freshness_weight: Decimal = Decimal("0.150000")
    calibration_recency_weight: Decimal = Decimal("0.150000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    evidence_reuse_quality_weight: Decimal = Decimal("0.150000")
    open_review_load_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainMemoryQuorumConfig:
            raise TypeError(
                "ResearchTeamCrossDomainMemoryQuorumConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainMemoryQuorumConfig:
            raise ValueError(
                "config must be exactly ResearchTeamCrossDomainMemoryQuorumConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_quorum_score_threshold",
            "block_quorum_score_threshold",
            "pass_component_score_threshold",
            "block_component_score_threshold",
            "pass_contradiction_pressure_score",
            "block_contradiction_pressure_score",
            "pass_evidence_reuse_quality_score",
            "block_evidence_reuse_quality_score",
            "pass_open_review_load_pressure_score",
            "block_open_review_load_pressure_score",
            "independent_domain_memory_weight",
            "memory_freshness_weight",
            "calibration_recency_weight",
            "contradiction_pressure_weight",
            "evidence_reuse_quality_weight",
            "open_review_load_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_independent_domain_memory_count",
            "min_watch_independent_domain_memory_count",
            "max_open_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_memory_age_seconds", "stale_calibration_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryQuorumObservation:
    quorum_key: str
    domain_key: str
    captured_at: datetime
    calibrated_at: datetime
    contradiction_pressure_score: Decimal
    evidence_reuse_quality_score: Decimal
    open_review_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainMemoryQuorumObservation:
            raise TypeError(
                "ResearchTeamCrossDomainMemoryQuorumObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainMemoryQuorumObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchTeamCrossDomainMemoryQuorumObservation",
            )
        object.__setattr__(
            self,
            "quorum_key",
            _require_public_identifier("quorum_key", self.quorum_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_identifier("domain_key", self.domain_key),
        )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "calibrated_at",
            _as_utc("calibrated_at", self.calibrated_at),
        )
        object.__setattr__(
            self,
            "contradiction_pressure_score",
            _require_ratio_decimal(
                "contradiction_pressure_score",
                self.contradiction_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "evidence_reuse_quality_score",
            _require_ratio_decimal(
                "evidence_reuse_quality_score",
                self.evidence_reuse_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "open_review_count",
            _require_nonnegative_count_decimal("open_review_count", self.open_review_count),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryQuorumRow:
    quorum_key: str
    status: str
    independent_domain_memory_count: Decimal
    domain_memory_count: Decimal
    independent_domain_memory_score: Decimal
    max_memory_age_seconds: Decimal
    memory_freshness_score: Decimal
    max_calibration_age_seconds: Decimal
    calibration_recency_score: Decimal
    average_contradiction_pressure_score: Decimal
    average_evidence_reuse_quality_score: Decimal
    total_open_review_count: Decimal
    open_review_load_pressure_score: Decimal
    quorum_score: Decimal
    latest_memory_captured_at: datetime
    latest_calibrated_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainMemoryQuorumRow:
            raise TypeError(
                "ResearchTeamCrossDomainMemoryQuorumRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainMemoryQuorumRow:
            raise ValueError("row must be exactly ResearchTeamCrossDomainMemoryQuorumRow")
        object.__setattr__(
            self,
            "quorum_key",
            _require_public_identifier("quorum_key", self.quorum_key),
        )
        _require_status("status", self.status)
        for field_name in (
            "independent_domain_memory_count",
            "domain_memory_count",
            "total_open_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_memory_age_seconds",
            "max_calibration_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_domain_memory_score",
            "memory_freshness_score",
            "calibration_recency_score",
            "average_contradiction_pressure_score",
            "average_evidence_reuse_quality_score",
            "open_review_load_pressure_score",
            "quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_memory_captured_at",
            _as_utc("latest_memory_captured_at", self.latest_memory_captured_at),
        )
        object.__setattr__(
            self,
            "latest_calibrated_at",
            _as_utc("latest_calibrated_at", self.latest_calibrated_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryQuorumReport:
    generated_at: datetime
    config_version: str
    report_status: str
    quorum_count: Decimal
    observation_count: Decimal
    domain_memory_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quorum_score: Decimal
    min_quorum_score: Decimal
    max_open_review_load_pressure_score: Decimal
    rows: tuple[ResearchTeamCrossDomainMemoryQuorumRow, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainMemoryQuorumReport:
            raise TypeError(
                "ResearchTeamCrossDomainMemoryQuorumReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainMemoryQuorumReport:
            raise ValueError(
                "report must be exactly ResearchTeamCrossDomainMemoryQuorumReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in (
            "quorum_count",
            "observation_count",
            "domain_memory_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_quorum_score",
            "min_quorum_score",
            "max_open_review_load_pressure_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        else:
            _require_public_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        if self.public_digest != _public_digest_for_report(self):
            raise ValueError("public_digest must match report payload")
        payload = _json_ready(self)
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("public_payload", payload)
        _reject_public_numeric_values(payload)
        return payload


def build_research_team_cross_domain_memory_quorum_report(
    observations: Iterable[ResearchTeamCrossDomainMemoryQuorumObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamCrossDomainMemoryQuorumConfig | None = None,
) -> ResearchTeamCrossDomainMemoryQuorumReport:
    cfg = config if config is not None else ResearchTeamCrossDomainMemoryQuorumConfig()
    if type(cfg) is not ResearchTeamCrossDomainMemoryQuorumConfig:
        raise ValueError("config must be a ResearchTeamCrossDomainMemoryQuorumConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at=report_time)
    rows = _build_rows(normalized, generated_at=report_time, config=cfg)
    report_status = _report_status(rows)
    return ResearchTeamCrossDomainMemoryQuorumReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        report_status=report_status,
        quorum_count=_count(len(rows)),
        observation_count=_count(len(normalized)),
        domain_memory_count=_count(len(normalized)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        average_quorum_score=_average_decimal(tuple(row.quorum_score for row in rows)),
        min_quorum_score=min((row.quorum_score for row in rows), default=ZERO),
        max_open_review_load_pressure_score=max(
            (row.open_review_load_pressure_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows, report_status),
    )


def research_team_cross_domain_memory_quorum_public_payload(
    report: ResearchTeamCrossDomainMemoryQuorumReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamCrossDomainMemoryQuorumReport:
        return report.public_payload
    if type(report) is dict:
        _reject_unsafe_public_payload("public_payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("public_payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamCrossDomainMemoryQuorumReport or public payload",
    )


def _normalize_observations(
    observations: Iterable[ResearchTeamCrossDomainMemoryQuorumObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamCrossDomainMemoryQuorumObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchTeamCrossDomainMemoryQuorumObservation:
            raise ValueError(
                "observations must contain ResearchTeamCrossDomainMemoryQuorumObservation",
            )
        _require_hard_flags("observation", item)
        if item.captured_at > generated_at:
            raise ValueError("captured_at must not be after generated_at")
        if item.calibrated_at > generated_at:
            raise ValueError("calibrated_at must not be after generated_at")
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.quorum_key,
                item.domain_key,
                item.captured_at,
                item.calibrated_at,
            ),
        ),
    )


def _build_rows(
    observations: tuple[ResearchTeamCrossDomainMemoryQuorumObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchTeamCrossDomainMemoryQuorumConfig,
) -> tuple[ResearchTeamCrossDomainMemoryQuorumRow, ...]:
    grouped: dict[str, list[ResearchTeamCrossDomainMemoryQuorumObservation]] = {}
    for item in observations:
        if item.quorum_key not in grouped:
            grouped[item.quorum_key] = []
        grouped[item.quorum_key].append(item)
    rows = tuple(
        _build_row(
            quorum_key=quorum_key,
            observations=tuple(grouped[quorum_key]),
            generated_at=generated_at,
            config=config,
        )
        for quorum_key in sorted(grouped)
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _build_row(
    *,
    quorum_key: str,
    observations: tuple[ResearchTeamCrossDomainMemoryQuorumObservation, ...],
    generated_at: datetime,
    config: ResearchTeamCrossDomainMemoryQuorumConfig,
) -> ResearchTeamCrossDomainMemoryQuorumRow:
    domain_keys = frozenset(item.domain_key for item in observations)
    independent_count = _count(len(domain_keys))
    memory_count = _count(len(observations))
    latest_memory_captured_at = max(item.captured_at for item in observations)
    latest_calibrated_at = max(item.calibrated_at for item in observations)
    max_memory_age_seconds = max(
        _age_seconds(generated_at, item.captured_at) for item in observations
    )
    max_calibration_age_seconds = max(
        _age_seconds(generated_at, item.calibrated_at) for item in observations
    )
    independent_score = _clamp_ratio(
        independent_count / config.min_pass_independent_domain_memory_count,
    )
    memory_freshness_score = _freshness_score(
        max_memory_age_seconds,
        config.stale_memory_age_seconds,
    )
    calibration_recency_score = _freshness_score(
        max_calibration_age_seconds,
        config.stale_calibration_age_seconds,
    )
    contradiction_pressure = _average_decimal(
        tuple(item.contradiction_pressure_score for item in observations),
    )
    evidence_reuse_quality = _average_decimal(
        tuple(item.evidence_reuse_quality_score for item in observations),
    )
    open_review_count = _sum_decimal(tuple(item.open_review_count for item in observations))
    open_review_pressure = _clamp_ratio(open_review_count / config.max_open_review_count)
    quorum_score = _quorum_score(
        independent_domain_memory_score=independent_score,
        memory_freshness_score=memory_freshness_score,
        calibration_recency_score=calibration_recency_score,
        contradiction_pressure_score=contradiction_pressure,
        evidence_reuse_quality_score=evidence_reuse_quality,
        open_review_load_pressure_score=open_review_pressure,
        config=config,
    )
    component_reasons = _component_reason_codes(
        independent_domain_memory_count=independent_count,
        memory_freshness_score=memory_freshness_score,
        calibration_recency_score=calibration_recency_score,
        contradiction_pressure_score=contradiction_pressure,
        evidence_reuse_quality_score=evidence_reuse_quality,
        open_review_load_pressure_score=open_review_pressure,
        config=config,
    )
    status = _row_status(component_reasons, quorum_score, config)
    return ResearchTeamCrossDomainMemoryQuorumRow(
        quorum_key=quorum_key,
        status=status,
        independent_domain_memory_count=independent_count,
        domain_memory_count=memory_count,
        independent_domain_memory_score=independent_score,
        max_memory_age_seconds=max_memory_age_seconds,
        memory_freshness_score=memory_freshness_score,
        max_calibration_age_seconds=max_calibration_age_seconds,
        calibration_recency_score=calibration_recency_score,
        average_contradiction_pressure_score=contradiction_pressure,
        average_evidence_reuse_quality_score=evidence_reuse_quality,
        total_open_review_count=open_review_count,
        open_review_load_pressure_score=open_review_pressure,
        quorum_score=quorum_score,
        latest_memory_captured_at=latest_memory_captured_at,
        latest_calibrated_at=latest_calibrated_at,
        reason_codes=_row_reason_codes(status, component_reasons),
    )


def _component_reason_codes(
    *,
    independent_domain_memory_count: Decimal,
    memory_freshness_score: Decimal,
    calibration_recency_score: Decimal,
    contradiction_pressure_score: Decimal,
    evidence_reuse_quality_score: Decimal,
    open_review_load_pressure_score: Decimal,
    config: ResearchTeamCrossDomainMemoryQuorumConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if independent_domain_memory_count < config.min_watch_independent_domain_memory_count:
        reasons.append("insufficient_independent_domain_memory_block")
    elif independent_domain_memory_count < config.min_pass_independent_domain_memory_count:
        reasons.append("insufficient_independent_domain_memory_watch")
    reasons.extend(
        (
            _quality_reason(
                "memory_freshness",
                memory_freshness_score,
                config.block_component_score_threshold,
                config.pass_component_score_threshold,
            ),
            _quality_reason(
                "calibration_recency",
                calibration_recency_score,
                config.block_component_score_threshold,
                config.pass_component_score_threshold,
            ),
            _pressure_reason(
                "contradiction_pressure",
                contradiction_pressure_score,
                config.pass_contradiction_pressure_score,
                config.block_contradiction_pressure_score,
            ),
            _quality_reason(
                "evidence_reuse_quality",
                evidence_reuse_quality_score,
                config.block_evidence_reuse_quality_score,
                config.pass_evidence_reuse_quality_score,
            ),
            _pressure_reason(
                "open_review_load",
                open_review_load_pressure_score,
                config.pass_open_review_load_pressure_score,
                config.block_open_review_load_pressure_score,
            ),
        ),
    )
    return tuple(reason for reason in reasons if reason)


def _quality_reason(
    prefix: str,
    value: Decimal,
    block_threshold: Decimal,
    pass_threshold: Decimal,
) -> str:
    if value <= block_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return ""


def _pressure_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return f"{prefix}_block"
    if value > pass_threshold:
        return f"{prefix}_watch"
    return ""


def _row_status(
    component_reasons: tuple[str, ...],
    quorum_score: Decimal,
    config: ResearchTeamCrossDomainMemoryQuorumConfig,
) -> str:
    if any(reason in BLOCK_REASON_CODES for reason in component_reasons):
        return "block"
    if quorum_score < config.block_quorum_score_threshold:
        return "block"
    if any(reason in WATCH_REASON_CODES for reason in component_reasons):
        return "watch"
    if quorum_score < config.pass_quorum_score_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    status: str,
    component_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    if status == "pass" and not component_reasons:
        return ("cross_domain_memory_quorum_pass",)
    return _normalize_reason_codes(
        "reason_codes",
        (f"cross_domain_memory_quorum_{status}", *component_reasons),
        ROW_REASON_CODES,
    )


def _report_reason_codes(
    rows: tuple[ResearchTeamCrossDomainMemoryQuorumRow, ...],
    report_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("cross_domain_memory_quorum_report_empty",)
    row_status_codes = frozenset(ROW_STATUS_REASON_CODES)
    component_reasons = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason not in row_status_codes
    )
    return _normalize_reason_codes(
        "reason_codes",
        (f"cross_domain_memory_quorum_report_{report_status}", *component_reasons),
        REPORT_REASON_CODES,
    )


def _quorum_score(
    *,
    independent_domain_memory_score: Decimal,
    memory_freshness_score: Decimal,
    calibration_recency_score: Decimal,
    contradiction_pressure_score: Decimal,
    evidence_reuse_quality_score: Decimal,
    open_review_load_pressure_score: Decimal,
    config: ResearchTeamCrossDomainMemoryQuorumConfig,
) -> Decimal:
    contradiction_quality = _clamp_ratio(ONE - contradiction_pressure_score)
    open_review_quality = _clamp_ratio(ONE - open_review_load_pressure_score)
    return _clamp_ratio(
        independent_domain_memory_score * config.independent_domain_memory_weight
        + memory_freshness_score * config.memory_freshness_weight
        + calibration_recency_score * config.calibration_recency_weight
        + contradiction_quality * config.contradiction_pressure_weight
        + evidence_reuse_quality_score * config.evidence_reuse_quality_weight
        + open_review_quality * config.open_review_load_weight,
    )


def _freshness_score(age_seconds: Decimal, stale_seconds: Decimal) -> Decimal:
    return _clamp_ratio(ONE - age_seconds / stale_seconds)


def _row_sort_key(
    row: ResearchTeamCrossDomainMemoryQuorumRow,
) -> tuple[int, Decimal, str]:
    return (STATUS_RANK[row.status], row.quorum_score, row.quorum_key)


def _report_status(rows: tuple[ResearchTeamCrossDomainMemoryQuorumRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamCrossDomainMemoryQuorumRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamCrossDomainMemoryQuorumRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamCrossDomainMemoryQuorumRow")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamCrossDomainMemoryQuorumRow",
        ) from exc
    for row in normalized:
        if type(row) is not ResearchTeamCrossDomainMemoryQuorumRow:
            raise ValueError("rows must contain ResearchTeamCrossDomainMemoryQuorumRow")
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"reason_code must be one of {allowed}")
    unique = tuple(dict.fromkeys(normalized))
    return tuple(reason_code for reason_code in allowed if reason_code in unique)


def _validate_config(config: ResearchTeamCrossDomainMemoryQuorumConfig) -> None:
    if config.pass_quorum_score_threshold <= config.block_quorum_score_threshold:
        raise ValueError(
            "pass_quorum_score_threshold must exceed block_quorum_score_threshold",
        )
    if config.pass_component_score_threshold <= config.block_component_score_threshold:
        raise ValueError(
            "pass_component_score_threshold must exceed block_component_score_threshold",
        )
    if (
        config.min_watch_independent_domain_memory_count
        > config.min_pass_independent_domain_memory_count
    ):
        raise ValueError(
            "min_watch_independent_domain_memory_count must not exceed "
            "min_pass_independent_domain_memory_count",
        )
    if config.block_contradiction_pressure_score <= config.pass_contradiction_pressure_score:
        raise ValueError(
            "block_contradiction_pressure_score must exceed "
            "pass_contradiction_pressure_score",
        )
    if config.pass_evidence_reuse_quality_score <= config.block_evidence_reuse_quality_score:
        raise ValueError(
            "pass_evidence_reuse_quality_score must exceed "
            "block_evidence_reuse_quality_score",
        )
    if (
        config.block_open_review_load_pressure_score
        <= config.pass_open_review_load_pressure_score
    ):
        raise ValueError(
            "block_open_review_load_pressure_score must exceed "
            "pass_open_review_load_pressure_score",
        )
    weight_sum = _sum_decimal(
        (
            config.independent_domain_memory_weight,
            config.memory_freshness_weight,
            config.calibration_recency_weight,
            config.contradiction_pressure_weight,
            config.evidence_reuse_quality_weight,
            config.open_review_load_weight,
        ),
    )
    if weight_sum != ONE:
        raise ValueError("component weights must sum to 1.000000")


def _validate_row(row: ResearchTeamCrossDomainMemoryQuorumRow) -> None:
    if row.domain_memory_count <= ZERO:
        raise ValueError("domain_memory_count must be positive")
    if row.independent_domain_memory_count <= ZERO:
        raise ValueError("independent_domain_memory_count must be positive")
    if row.independent_domain_memory_count > row.domain_memory_count:
        raise ValueError("independent_domain_memory_count cannot exceed domain_memory_count")
    if row.status == "pass" and row.reason_codes != ("cross_domain_memory_quorum_pass",):
        raise ValueError("pass rows must only contain the pass reason")
    if row.status != "pass" and "cross_domain_memory_quorum_pass" in row.reason_codes:
        raise ValueError("non-pass rows must not contain the pass reason")
    expected_status_reason = f"cross_domain_memory_quorum_{row.status}"
    if row.status != "pass" and expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include the row status reason")


def _validate_report(report: ResearchTeamCrossDomainMemoryQuorumReport) -> None:
    if report.quorum_count != _count(len(report.rows)):
        raise ValueError("quorum_count must match rows")
    if report.observation_count != _sum_decimal(
        tuple(row.domain_memory_count for row in report.rows),
    ):
        raise ValueError("observation_count must match rows")
    if report.domain_memory_count != report.observation_count:
        raise ValueError("domain_memory_count must match observations")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.average_quorum_score != _average_decimal(
        tuple(row.quorum_score for row in report.rows),
    ):
        raise ValueError("average_quorum_score must match rows")
    if report.min_quorum_score != min((row.quorum_score for row in report.rows), default=ZERO):
        raise ValueError("min_quorum_score must match rows")
    if report.max_open_review_load_pressure_score != max(
        (row.open_review_load_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_open_review_load_pressure_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.report_status):
        raise ValueError("reason_codes must match rows")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of {PUBLIC_STATUSES}")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public sha256 digest")


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized.quantize(COUNT_QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must set {field_name}=True")


def _validate_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in FLAG_NAMES:
        if field_name not in payload or payload[field_name] is not True:
            raise ValueError(f"public_payload must set {field_name}=True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if field.name != "public_digest":
                _reject_unsafe_text(label, field.name)
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            if key != "public_digest":
                _reject_unsafe_text(label, str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(_unsafe_term_matches(lowered, term) for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public content")


def _unsafe_term_matches(value: str, term: str) -> bool:
    if "://" in term or "_" in term:
        return term in value
    return re.search(rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)", value) is not None


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public_payload must not contain raw numeric values")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _public_digest_for_report(report: ResearchTeamCrossDomainMemoryQuorumReport) -> str:
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "public_digest"
    }
    return _public_digest(values)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "public_digest" not in payload:
        raise ValueError("public_digest is required")
    digest = payload["public_digest"]
    _require_public_digest("public_digest", digest)
    values = {key: item for key, item in payload.items() if key != "public_digest"}
    expected = _public_digest(values)
    if digest != expected:
        raise ValueError("public_digest must match payload")


def _public_digest(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    return value


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )
    return _decimal(seconds)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANT)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _decimal(total + value)
    return total


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _decimal(_sum_decimal(values) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PREC
        context.rounding = ROUND_HALF_UP
        return value.quantize(QUANT)
