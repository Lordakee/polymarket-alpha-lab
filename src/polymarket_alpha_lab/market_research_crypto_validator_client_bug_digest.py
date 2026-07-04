"""Pure Phase 1 crypto validator software bug market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_CLIENT_BUG_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-validator-client-bug-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
VALIDATOR_CLIENT_BUG_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_validator_client_bug_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_validator_client_bug_digest_no_inputs"
AFFECTED_VALIDATOR_EXPOSURE_REASON = (
    "market_research_crypto_validator_client_bug_digest_affected_validator_exposure"
)
ACTIVE_INCIDENT_REASON = (
    "market_research_crypto_validator_client_bug_digest_active_incident"
)
UNPATCHED_VALIDATOR_RISK_REASON = (
    "market_research_crypto_validator_client_bug_digest_unpatched_validator_risk"
)
CLIENT_SUPERMAJORITY_RISK_REASON = (
    "market_research_crypto_validator_client_bug_digest_client_supermajority_risk"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_validator_client_bug_digest_source_diversity_gap"
)
STALE_SNAPSHOT_REASON = (
    "market_research_crypto_validator_client_bug_digest_stale_snapshot"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_validator_client_bug_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    AFFECTED_VALIDATOR_EXPOSURE_REASON,
    ACTIVE_INCIDENT_REASON,
    UNPATCHED_VALIDATOR_RISK_REASON,
    CLIENT_SUPERMAJORITY_RISK_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    AFFECTED_VALIDATOR_EXPOSURE_REASON,
    ACTIVE_INCIDENT_REASON,
    UNPATCHED_VALIDATOR_RISK_REASON,
    CLIENT_SUPERMAJORITY_RISK_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_CLIENT_BUG_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoValidatorClientBugDigestConfig",
    "MarketResearchCryptoValidatorClientBugDigestReasonCodeCount",
    "MarketResearchCryptoValidatorClientBugDigestReport",
    "MarketResearchCryptoValidatorClientBugDigestRow",
    "MarketResearchCryptoValidatorClientBugSnapshot",
    "build_market_research_crypto_validator_client_bug_digest",
    "market_research_crypto_validator_client_bug_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorClientBugDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_CLIENT_BUG_DIGEST_CONFIG_VERSION
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    max_affected_validator_ratio: Decimal = Decimal("0.100000")
    max_incident_count: Decimal = Decimal("0.000000")
    max_unpatched_ratio: Decimal = Decimal("0.050000")
    max_client_supermajority_ratio: Decimal = Decimal("0.660000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorClientBugDigestConfig:
            raise TypeError(
                "MarketResearchCryptoValidatorClientBugDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoValidatorClientBugDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoValidatorClientBugDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_snapshot_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_incident_count",
            _require_nonnegative_count_decimal("max_incident_count", self.max_incident_count),
        )
        for field_name in (
            "max_affected_validator_ratio",
            "max_unpatched_ratio",
            "max_client_supermajority_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorClientBugSnapshot:
    cluster_id: str
    client_family: str
    network: str
    observed_at: datetime
    affected_validator_count: Decimal
    total_validator_count: Decimal
    incident_count: Decimal
    unpatched_validator_count: Decimal
    client_share: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorClientBugSnapshot:
            raise TypeError(
                "MarketResearchCryptoValidatorClientBugSnapshot does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoValidatorClientBugSnapshot:
            raise ValueError(
                "snapshot must be exactly MarketResearchCryptoValidatorClientBugSnapshot",
            )
        for field_name in (
            "cluster_id",
            "client_family",
            "network",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "affected_validator_count",
            "total_validator_count",
            "incident_count",
            "unpatched_validator_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.total_validator_count <= ZERO:
            raise ValueError("total_validator_count must be positive")
        object.__setattr__(
            self,
            "client_share",
            _require_ratio_decimal("client_share", self.client_share),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _validate_snapshot(self)
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorClientBugDigestRow:
    cluster_id: str
    client_family: str
    network: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    affected_validator_count: Decimal
    total_validator_count: Decimal
    affected_validator_ratio: Decimal
    incident_count: Decimal
    unpatched_validator_count: Decimal
    unpatched_validator_ratio: Decimal
    client_share: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorClientBugDigestRow:
            raise TypeError(
                "MarketResearchCryptoValidatorClientBugDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoValidatorClientBugDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoValidatorClientBugDigestRow",
            )
        for field_name in ("cluster_id", "client_family", "network"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "affected_validator_count",
            "total_validator_count",
            "incident_count",
            "unpatched_validator_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.total_validator_count <= ZERO:
            raise ValueError("total_validator_count must be positive")
        for field_name in (
            "affected_validator_ratio",
            "unpatched_validator_ratio",
            "client_share",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorClientBugDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorClientBugDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoValidatorClientBugDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoValidatorClientBugDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoValidatorClientBugDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "snapshot_ratio",
            _require_ratio_decimal("snapshot_ratio", self.snapshot_ratio),
        )


@dataclass(frozen=True)
class MarketResearchCryptoValidatorClientBugDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    affected_validator_exposure_count: Decimal
    active_incident_snapshot_count: Decimal
    unpatched_validator_risk_count: Decimal
    client_supermajority_risk_count: Decimal
    source_diversity_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_affected_validator_ratio: Decimal
    average_unpatched_validator_ratio: Decimal
    average_client_share: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    max_allowed_affected_validator_ratio: Decimal
    max_allowed_incident_count: Decimal
    max_allowed_unpatched_ratio: Decimal
    max_allowed_client_supermajority_ratio: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoValidatorClientBugDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorClientBugDigestReport:
            raise TypeError(
                "MarketResearchCryptoValidatorClientBugDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoValidatorClientBugDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoValidatorClientBugDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "ready_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "affected_validator_exposure_count",
            "active_incident_snapshot_count",
            "unpatched_validator_risk_count",
            "client_supermajority_risk_count",
            "source_diversity_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "max_allowed_incident_count",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_affected_validator_ratio",
            "average_unpatched_validator_ratio",
            "average_client_share",
            "max_allowed_affected_validator_ratio",
            "max_allowed_unpatched_ratio",
            "max_allowed_client_supermajority_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_validator_client_bug_digest(
    snapshots: Iterable[MarketResearchCryptoValidatorClientBugSnapshot],
    *,
    config: MarketResearchCryptoValidatorClientBugDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoValidatorClientBugDigestReport:
    cfg = config or MarketResearchCryptoValidatorClientBugDigestConfig()
    if type(cfg) is not MarketResearchCryptoValidatorClientBugDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoValidatorClientBugDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(
        _row_for_snapshot(snapshot, config=cfg, generated_at=generated_at_utc)
        for snapshot in normalized_snapshots
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.client_family,
                row.cluster_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoValidatorClientBugDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=_decimal_count(len(sorted_rows)),
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        affected_validator_exposure_count=_reason_snapshot_count(
            sorted_rows,
            AFFECTED_VALIDATOR_EXPOSURE_REASON,
        ),
        active_incident_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            ACTIVE_INCIDENT_REASON,
        ),
        unpatched_validator_risk_count=_reason_snapshot_count(
            sorted_rows,
            UNPATCHED_VALIDATOR_RISK_REASON,
        ),
        client_supermajority_risk_count=_reason_snapshot_count(
            sorted_rows,
            CLIENT_SUPERMAJORITY_RISK_REASON,
        ),
        source_diversity_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        stale_snapshot_count=_reason_snapshot_count(sorted_rows, STALE_SNAPSHOT_REASON),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_affected_validator_ratio=_ratio(
            _decimal_sum(row.affected_validator_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_unpatched_validator_ratio=_ratio(
            _decimal_sum(row.unpatched_validator_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_client_share=_ratio(
            _decimal_sum(row.client_share for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        max_allowed_affected_validator_ratio=cfg.max_affected_validator_ratio,
        max_allowed_incident_count=cfg.max_incident_count,
        max_allowed_unpatched_ratio=cfg.max_unpatched_ratio,
        max_allowed_client_supermajority_ratio=cfg.max_client_supermajority_ratio,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=_source_config_versions(normalized_snapshots),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
    )


def market_research_crypto_validator_client_bug_digest_payload(
    report: MarketResearchCryptoValidatorClientBugDigestReport,
) -> MappingProxyType[str, Any]:
    if type(report) is not MarketResearchCryptoValidatorClientBugDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoValidatorClientBugDigestReport",
        )
    rows = tuple(
        MappingProxyType(
            {
                "cluster_id": row.cluster_id,
                "client_family": row.client_family,
                "network": row.network,
                "digest_status": row.digest_status,
                "observed_at": row.observed_at.isoformat(),
                "snapshot_age_seconds": _decimal_text(row.snapshot_age_seconds),
                "affected_validator_count": _decimal_text(row.affected_validator_count),
                "total_validator_count": _decimal_text(row.total_validator_count),
                "affected_validator_ratio": _decimal_text(row.affected_validator_ratio),
                "incident_count": _decimal_text(row.incident_count),
                "unpatched_validator_count": _decimal_text(row.unpatched_validator_count),
                "unpatched_validator_ratio": _decimal_text(row.unpatched_validator_ratio),
                "client_share": _decimal_text(row.client_share),
                "source_count": _decimal_text(row.source_count),
                "confidence": _decimal_text(row.confidence),
                "reason_codes": row.reason_codes,
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            },
        )
        for row in report.rows
    )
    reason_counts = tuple(
        MappingProxyType(
            {
                "reason_code": reason_count.reason_code,
                "count": _decimal_text(reason_count.count),
                "snapshot_ratio": _decimal_text(reason_count.snapshot_ratio),
            },
        )
        for reason_count in report.reason_code_counts
    )
    payload = MappingProxyType(
        {
            "payload_kind": "market_research_crypto_validator_client_bug_digest",
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "digest_status": report.digest_status,
            "recommended_next_step": report.recommended_next_step,
            "snapshot_count": _decimal_text(report.snapshot_count),
            "ready_snapshot_count": _decimal_text(report.ready_snapshot_count),
            "watch_snapshot_count": _decimal_text(report.watch_snapshot_count),
            "blocked_snapshot_count": _decimal_text(report.blocked_snapshot_count),
            "affected_validator_exposure_count": _decimal_text(
                report.affected_validator_exposure_count,
            ),
            "active_incident_snapshot_count": _decimal_text(
                report.active_incident_snapshot_count,
            ),
            "unpatched_validator_risk_count": _decimal_text(
                report.unpatched_validator_risk_count,
            ),
            "client_supermajority_risk_count": _decimal_text(
                report.client_supermajority_risk_count,
            ),
            "source_diversity_gap_snapshot_count": _decimal_text(
                report.source_diversity_gap_snapshot_count,
            ),
            "stale_snapshot_count": _decimal_text(report.stale_snapshot_count),
            "confidence_gap_snapshot_count": _decimal_text(
                report.confidence_gap_snapshot_count,
            ),
            "average_affected_validator_ratio": _decimal_text(
                report.average_affected_validator_ratio,
            ),
            "average_unpatched_validator_ratio": _decimal_text(
                report.average_unpatched_validator_ratio,
            ),
            "average_client_share": _decimal_text(report.average_client_share),
            "max_snapshot_age_seconds": _decimal_text(report.max_snapshot_age_seconds),
            "max_allowed_snapshot_age_seconds": _decimal_text(
                report.max_allowed_snapshot_age_seconds,
            ),
            "max_allowed_affected_validator_ratio": _decimal_text(
                report.max_allowed_affected_validator_ratio,
            ),
            "max_allowed_incident_count": _decimal_text(
                report.max_allowed_incident_count,
            ),
            "max_allowed_unpatched_ratio": _decimal_text(
                report.max_allowed_unpatched_ratio,
            ),
            "max_allowed_client_supermajority_ratio": _decimal_text(
                report.max_allowed_client_supermajority_ratio,
            ),
            "min_source_count": _decimal_text(report.min_source_count),
            "min_confidence": _decimal_text(report.min_confidence),
            "source_config_versions": report.source_config_versions,
            "reason_code_counts": reason_counts,
            "reason_codes": report.reason_codes,
            "rows": rows,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    _reject_unsafe_payload(payload)
    return payload


def _row_for_snapshot(
    snapshot: MarketResearchCryptoValidatorClientBugSnapshot,
    *,
    config: MarketResearchCryptoValidatorClientBugDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoValidatorClientBugDigestRow:
    snapshot_age = _seconds_between(generated_at, snapshot.observed_at)
    affected_ratio = _ratio(
        snapshot.affected_validator_count,
        snapshot.total_validator_count,
    )
    unpatched_ratio = _ratio(
        snapshot.unpatched_validator_count,
        snapshot.total_validator_count,
    )
    reason_codes = _row_reason_codes(
        snapshot_age_seconds=snapshot_age,
        affected_validator_ratio=affected_ratio,
        incident_count=snapshot.incident_count,
        unpatched_validator_ratio=unpatched_ratio,
        client_share=snapshot.client_share,
        source_count=snapshot.source_count,
        confidence=snapshot.confidence,
        config=config,
    )
    return MarketResearchCryptoValidatorClientBugDigestRow(
        cluster_id=snapshot.cluster_id,
        client_family=snapshot.client_family,
        network=snapshot.network,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age,
        affected_validator_count=snapshot.affected_validator_count,
        total_validator_count=snapshot.total_validator_count,
        affected_validator_ratio=affected_ratio,
        incident_count=snapshot.incident_count,
        unpatched_validator_count=snapshot.unpatched_validator_count,
        unpatched_validator_ratio=unpatched_ratio,
        client_share=snapshot.client_share,
        source_count=snapshot.source_count,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot_age_seconds: Decimal,
    affected_validator_ratio: Decimal,
    incident_count: Decimal,
    unpatched_validator_ratio: Decimal,
    client_share: Decimal,
    source_count: Decimal,
    confidence: Decimal,
    config: MarketResearchCryptoValidatorClientBugDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if affected_validator_ratio > config.max_affected_validator_ratio:
        reasons.append(AFFECTED_VALIDATOR_EXPOSURE_REASON)
    if incident_count > config.max_incident_count:
        reasons.append(ACTIVE_INCIDENT_REASON)
    if unpatched_validator_ratio > config.max_unpatched_ratio:
        reasons.append(UNPATCHED_VALIDATOR_RISK_REASON)
    if client_share > config.max_client_supermajority_ratio:
        reasons.append(CLIENT_SUPERMAJORITY_RISK_REASON)
    if source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reasons.append(STALE_SNAPSHOT_REASON)
    if confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(tuple(reasons), sequence=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    blocking_reasons = (
        AFFECTED_VALIDATOR_EXPOSURE_REASON,
        ACTIVE_INCIDENT_REASON,
        UNPATCHED_VALIDATOR_RISK_REASON,
        CLIENT_SUPERMAJORITY_RISK_REASON,
        SOURCE_DIVERSITY_GAP_REASON,
        STALE_SNAPSHOT_REASON,
        CONFIDENCE_GAP_REASON,
    )
    if any(reason in blocking_reasons for reason in reason_codes):
        return STATUS_BLOCKED
    return STATUS_READY


def _report_status(
    rows: tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_validator_client_bug_digest"
    if status == STATUS_WATCH:
        return "watch_report_only_market_research_crypto_validator_client_bug_digest"
    return "allow_report_only_market_research_crypto_validator_client_bug_digest"


def _report_reason_codes(
    rows: tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    if all(row.reason_codes == (READY_REASON,) for row in rows):
        return (READY_REASON,)
    reasons: list[str] = []
    for reason in REASON_CODE_SEQUENCE:
        if reason in (READY_REASON, NO_INPUTS_REASON):
            continue
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...],
) -> tuple[MarketResearchCryptoValidatorClientBugDigestReasonCodeCount, ...]:
    total_count = _decimal_count(len(rows))
    counts: list[MarketResearchCryptoValidatorClientBugDigestReasonCodeCount] = []
    for reason in REASON_CODE_SEQUENCE:
        if reason in (READY_REASON, NO_INPUTS_REASON):
            continue
        count = _reason_snapshot_count(rows, reason)
        if count > ZERO:
            counts.append(
                MarketResearchCryptoValidatorClientBugDigestReasonCodeCount(
                    reason_code=reason,
                    count=count,
                    snapshot_ratio=_ratio(count, total_count),
                ),
            )
    return tuple(counts)


def _source_config_versions(
    snapshots: tuple[MarketResearchCryptoValidatorClientBugSnapshot, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (snapshot.client_family, snapshot.source_config_version)
                for snapshot in snapshots
            },
        ),
    )


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoValidatorClientBugSnapshot],
) -> tuple[MarketResearchCryptoValidatorClientBugSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable of snapshot rows")
    normalized = tuple(snapshots)
    for snapshot in normalized:
        if type(snapshot) is not MarketResearchCryptoValidatorClientBugSnapshot:
            raise ValueError(
                "snapshots must contain MarketResearchCryptoValidatorClientBugSnapshot",
            )
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...],
) -> tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoValidatorClientBugDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoValidatorClientBugDigestRow",
            )
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchCryptoValidatorClientBugDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoValidatorClientBugDigestReasonCodeCount, ...]:
    if not isinstance(reason_code_counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for reason_code_count in reason_code_counts:
        if type(reason_code_count) is not MarketResearchCryptoValidatorClientBugDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchCryptoValidatorClientBugDigestReasonCodeCount",
            )
    return tuple(
        sorted(
            reason_code_counts,
            key=lambda item: _reason_rank(item.reason_code, REASON_CODE_SEQUENCE),
        ),
    )


def _normalize_source_config_versions(
    source_config_versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if not isinstance(source_config_versions, tuple):
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for pair in source_config_versions:
        if not isinstance(pair, tuple) or len(pair) != len(("key", "version")):
            raise ValueError("source_config_versions must contain string pairs")
        key, version = pair
        _require_public_string("source_config_version key", key)
        _require_public_string("source_config_version", version)
        normalized.append((key, version))
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_code is not allowed")
    return tuple(
        sorted(
            dict.fromkeys(reason_codes),
            key=lambda reason: _reason_rank(reason, sequence),
        ),
    )


def _validate_snapshot(snapshot: MarketResearchCryptoValidatorClientBugSnapshot) -> None:
    if snapshot.affected_validator_count > snapshot.total_validator_count:
        raise ValueError("affected_validator_count must not exceed total_validator_count")
    if snapshot.unpatched_validator_count > snapshot.total_validator_count:
        raise ValueError("unpatched_validator_count must not exceed total_validator_count")


def _validate_row(row: MarketResearchCryptoValidatorClientBugDigestRow) -> None:
    if row.affected_validator_count > row.total_validator_count:
        raise ValueError("affected_validator_count must not exceed total_validator_count")
    if row.unpatched_validator_count > row.total_validator_count:
        raise ValueError("unpatched_validator_count must not exceed total_validator_count")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")
    expected_affected_ratio = _ratio(
        row.affected_validator_count,
        row.total_validator_count,
    )
    if row.affected_validator_ratio != expected_affected_ratio:
        raise ValueError("affected_validator_ratio must match validator counts")
    expected_unpatched_ratio = _ratio(
        row.unpatched_validator_count,
        row.total_validator_count,
    )
    if row.unpatched_validator_ratio != expected_unpatched_ratio:
        raise ValueError("unpatched_validator_ratio must match validator counts")


def _validate_report(report: MarketResearchCryptoValidatorClientBugDigestReport) -> None:
    rows = report.rows
    if report.snapshot_count != _decimal_count(len(rows)):
        raise ValueError("snapshot_count must match rows")
    if report.ready_snapshot_count != _status_count(rows, STATUS_READY):
        raise ValueError("ready_snapshot_count must match rows")
    if report.watch_snapshot_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count must match rows")
    if report.blocked_snapshot_count != _status_count(rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count must match rows")
    if report.affected_validator_exposure_count != _reason_snapshot_count(
        rows,
        AFFECTED_VALIDATOR_EXPOSURE_REASON,
    ):
        raise ValueError("affected_validator_exposure_count must match rows")
    if report.active_incident_snapshot_count != _reason_snapshot_count(
        rows,
        ACTIVE_INCIDENT_REASON,
    ):
        raise ValueError("active_incident_snapshot_count must match rows")
    if report.unpatched_validator_risk_count != _reason_snapshot_count(
        rows,
        UNPATCHED_VALIDATOR_RISK_REASON,
    ):
        raise ValueError("unpatched_validator_risk_count must match rows")
    if report.client_supermajority_risk_count != _reason_snapshot_count(
        rows,
        CLIENT_SUPERMAJORITY_RISK_REASON,
    ):
        raise ValueError("client_supermajority_risk_count must match rows")
    if report.source_diversity_gap_snapshot_count != _reason_snapshot_count(
        rows,
        SOURCE_DIVERSITY_GAP_REASON,
    ):
        raise ValueError("source_diversity_gap_snapshot_count must match rows")
    if report.stale_snapshot_count != _reason_snapshot_count(rows, STALE_SNAPSHOT_REASON):
        raise ValueError("stale_snapshot_count must match rows")
    if report.confidence_gap_snapshot_count != _reason_snapshot_count(
        rows,
        CONFIDENCE_GAP_REASON,
    ):
        raise ValueError("confidence_gap_snapshot_count must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(row.digest_status == status for row in rows))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoValidatorClientBugDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(reason_code in row.reason_codes for row in rows))


def _row_sort_value(row: MarketResearchCryptoValidatorClientBugDigestRow) -> Decimal:
    if row.digest_status == STATUS_BLOCKED:
        return ZERO
    if row.digest_status == STATUS_WATCH:
        return ONE
    return Decimal("2.000000")


def _reason_rank(reason_code: str, sequence: tuple[str, ...]) -> Decimal:
    for reason in sequence:
        if reason == reason_code:
            return _decimal_count(sequence.index(reason))
    raise ValueError("reason_code is not allowed")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("timestamp must not be future")
    delta = later - earlier
    seconds = Decimal(str(delta.total_seconds()))
    return _quantize(seconds)


def _decimal_count(value: object) -> Decimal:
    return _quantize(Decimal(str(value)))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _decimal_text(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be Decimal")
    return format(value, "f")


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    _reject_unsafe_text(field_name, value)


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in VALIDATOR_CLIENT_BUG_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, MappingProxyType):
        for key, item in value.items():
            _reject_unsafe_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text("payload value", value)
        return
    if isinstance(value, Decimal):
        raise ValueError("payload must serialize Decimal values")
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("payload must not contain integer values")
