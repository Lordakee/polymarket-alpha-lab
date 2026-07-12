"""Pure report-only reducer for event claim source freshness quorum checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_EVENT_CLAIM_FRESHNESS_QUORUM_CONFIG_VERSION = (
    "research-source-event-claim-freshness-quorum-v0"
)

STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "raw",
    "http",
    "https",
    "url",
    "source-url",
    "source_url",
    "source-text",
    "source_text",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "private",
    "secret",
    "credential",
)
_REASON_CODE_SEQUENCE = (
    "fresh_source_quorum_watch",
    "fresh_source_quorum_block",
    "primary_fresh_source_quorum_watch",
    "primary_fresh_source_quorum_block",
    "latest_verification_missing",
    "latest_verification_age_watch",
    "latest_verification_age_block",
    "stale_source_ratio_watch",
    "stale_source_ratio_block",
    "source_agreement_watch",
    "source_agreement_block",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "extraction_confidence_watch",
    "extraction_confidence_block",
    "event_claim_freshness_quorum_pass",
)


@dataclass(frozen=True)
class ResearchSourceEventClaimFreshnessQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_EVENT_CLAIM_FRESHNESS_QUORUM_CONFIG_VERSION
    )
    watch_fresh_source_quorum: Decimal = Decimal("2")
    block_fresh_source_quorum: Decimal = Decimal("0")
    watch_primary_fresh_source_quorum: Decimal = Decimal("1")
    block_primary_fresh_source_quorum: Decimal = Decimal("0")
    watch_latest_verification_age_seconds: Decimal = Decimal("7200.000000")
    block_latest_verification_age_seconds: Decimal = Decimal("21600.000000")
    watch_stale_source_ratio: Decimal = Decimal("0.500000")
    block_stale_source_ratio: Decimal = Decimal("0.800000")
    watch_source_agreement_score: Decimal = Decimal("0.700000")
    block_source_agreement_score: Decimal = Decimal("0.400000")
    watch_contradiction_pressure: Decimal = Decimal("0.300000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    watch_extraction_confidence: Decimal = Decimal("0.800000")
    block_extraction_confidence: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEventClaimFreshnessQuorumConfig:
            raise TypeError(
                "ResearchSourceEventClaimFreshnessQuorumConfig cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEventClaimFreshnessQuorumConfig:
            raise ValueError(
                "config must be exactly ResearchSourceEventClaimFreshnessQuorumConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVENT_CLAIM_FRESHNESS_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_fresh_source_quorum",
            "block_fresh_source_quorum",
            "watch_primary_fresh_source_quorum",
            "block_primary_fresh_source_quorum",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_latest_verification_age_seconds",
            "block_latest_verification_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_source_ratio",
            "block_stale_source_ratio",
            "watch_source_agreement_score",
            "block_source_agreement_score",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_extraction_confidence",
            "block_extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_before_block_low(
            "fresh_source_quorum",
            self.watch_fresh_source_quorum,
            self.block_fresh_source_quorum,
        )
        _require_watch_before_block_low(
            "primary_fresh_source_quorum",
            self.watch_primary_fresh_source_quorum,
            self.block_primary_fresh_source_quorum,
        )
        _require_watch_before_block_high(
            "latest_verification_age_seconds",
            self.watch_latest_verification_age_seconds,
            self.block_latest_verification_age_seconds,
        )
        _require_watch_before_block_high(
            "stale_source_ratio",
            self.watch_stale_source_ratio,
            self.block_stale_source_ratio,
        )
        _require_watch_before_block_low(
            "source_agreement_score",
            self.watch_source_agreement_score,
            self.block_source_agreement_score,
        )
        _require_watch_before_block_high(
            "contradiction_pressure",
            self.watch_contradiction_pressure,
            self.block_contradiction_pressure,
        )
        _require_watch_before_block_low(
            "extraction_confidence",
            self.watch_extraction_confidence,
            self.block_extraction_confidence,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceEventClaimFreshnessQuorumObservation:
    event_claim_bucket: str
    source_family_count: Decimal
    fresh_source_count: Decimal
    primary_fresh_source_count: Decimal
    latest_verified_at: datetime | None
    source_agreement_score: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEventClaimFreshnessQuorumObservation:
            raise TypeError(
                "ResearchSourceEventClaimFreshnessQuorumObservation cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEventClaimFreshnessQuorumObservation:
            raise ValueError(
                "observation must be exactly ResearchSourceEventClaimFreshnessQuorumObservation",
            )
        _require_public_identifier("event_claim_bucket", self.event_claim_bucket)
        object.__setattr__(
            self,
            "source_family_count",
            _require_positive_whole_decimal("source_family_count", self.source_family_count),
        )
        for field_name in ("fresh_source_count", "primary_fresh_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_source_count > self.source_family_count:
            raise ValueError("fresh_source_count must not exceed source_family_count")
        if self.primary_fresh_source_count > self.fresh_source_count:
            raise ValueError("primary_fresh_source_count must not exceed fresh_source_count")
        if self.latest_verified_at is not None:
            object.__setattr__(
                self,
                "latest_verified_at",
                _as_utc("latest_verified_at", self.latest_verified_at),
            )
        for field_name in (
            "source_agreement_score",
            "contradiction_pressure",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceEventClaimFreshnessQuorumRow:
    event_claim_bucket: str
    source_family_count: Decimal
    fresh_source_count: Decimal
    primary_fresh_source_count: Decimal
    stale_source_count: Decimal
    freshness_ratio: Decimal
    stale_source_ratio: Decimal
    latest_verification_missing: bool
    latest_verification_age_seconds: Decimal
    source_agreement_score: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    quorum_gap_count: Decimal
    primary_quorum_gap_count: Decimal
    freshness_quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEventClaimFreshnessQuorumRow:
            raise TypeError(
                "ResearchSourceEventClaimFreshnessQuorumRow cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEventClaimFreshnessQuorumRow:
            raise ValueError("row must be exactly ResearchSourceEventClaimFreshnessQuorumRow")
        _require_public_identifier("event_claim_bucket", self.event_claim_bucket)
        object.__setattr__(
            self,
            "source_family_count",
            _require_positive_whole_decimal("source_family_count", self.source_family_count),
        )
        for field_name in (
            "fresh_source_count",
            "primary_fresh_source_count",
            "stale_source_count",
            "quorum_gap_count",
            "primary_quorum_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_ratio",
            "stale_source_ratio",
            "source_agreement_score",
            "contradiction_pressure",
            "extraction_confidence",
            "freshness_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_verification_age_seconds",
            _require_nonnegative_decimal(
                "latest_verification_age_seconds",
                self.latest_verification_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceEventClaimFreshnessQuorumReport:
    generated_at: datetime
    config_version: str
    event_claim_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_fresh_source_count: Decimal
    min_primary_fresh_source_count: Decimal
    missing_latest_verification_count: Decimal
    max_latest_verification_age_seconds: Decimal
    max_stale_source_ratio: Decimal
    max_contradiction_pressure: Decimal
    min_source_agreement_score: Decimal
    min_extraction_confidence: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceEventClaimFreshnessQuorumRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEventClaimFreshnessQuorumReport:
            raise TypeError(
                "ResearchSourceEventClaimFreshnessQuorumReport cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEventClaimFreshnessQuorumReport:
            raise ValueError(
                "report must be exactly ResearchSourceEventClaimFreshnessQuorumReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVENT_CLAIM_FRESHNESS_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "event_claim_bucket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_fresh_source_count",
            "min_primary_fresh_source_count",
            "missing_latest_verification_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_verification_age_seconds",
            _require_nonnegative_decimal(
                "max_latest_verification_age_seconds",
                self.max_latest_verification_age_seconds,
            ),
        )
        for field_name in (
            "max_stale_source_ratio",
            "max_contradiction_pressure",
            "min_source_agreement_score",
            "min_extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_event_claim_freshness_quorum_report(
    observations: Sequence[ResearchSourceEventClaimFreshnessQuorumObservation],
    *,
    config: ResearchSourceEventClaimFreshnessQuorumConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceEventClaimFreshnessQuorumReport:
    if config is None:
        config = ResearchSourceEventClaimFreshnessQuorumConfig()
    if type(config) is not ResearchSourceEventClaimFreshnessQuorumConfig:
        raise ValueError("config must be a ResearchSourceEventClaimFreshnessQuorumConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_empty_observations(normalized)
    for item in normalized:
        if item.latest_verified_at is not None:
            _reject_future_time("latest_verified_at", item.latest_verified_at, generated_at)

    rows = tuple(
        _row_for_observation(item, generated_at=generated_at, config=config)
        for item in normalized
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "event_claim_bucket_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "min_fresh_source_count": min(
            (row.fresh_source_count for row in rows),
            default=_ZERO,
        ),
        "min_primary_fresh_source_count": min(
            (row.primary_fresh_source_count for row in rows),
            default=_ZERO,
        ),
        "missing_latest_verification_count": _decimal_count(
            sum(1 for row in rows if row.latest_verification_missing),
        ),
        "max_latest_verification_age_seconds": max(
            (row.latest_verification_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_stale_source_ratio": max((row.stale_source_ratio for row in rows), default=_ZERO),
        "max_contradiction_pressure": max(
            (row.contradiction_pressure for row in rows),
            default=_ZERO,
        ),
        "min_source_agreement_score": min(
            (row.source_agreement_score for row in rows),
            default=_ONE,
        ),
        "min_extraction_confidence": min(
            (row.extraction_confidence for row in rows),
            default=_ONE,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceEventClaimFreshnessQuorumReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_event_claim_freshness_quorum_report_payload(
    report: ResearchSourceEventClaimFreshnessQuorumReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceEventClaimFreshnessQuorumReport:
        raise ValueError("report must be a ResearchSourceEventClaimFreshnessQuorumReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_for_observation(
    observation: ResearchSourceEventClaimFreshnessQuorumObservation,
    *,
    generated_at: datetime,
    config: ResearchSourceEventClaimFreshnessQuorumConfig,
) -> ResearchSourceEventClaimFreshnessQuorumRow:
    stale_count = observation.source_family_count - observation.fresh_source_count
    freshness_ratio = _quantize(observation.fresh_source_count / observation.source_family_count)
    stale_ratio = _quantize(stale_count / observation.source_family_count)
    latest_verification_missing = observation.latest_verified_at is None
    latest_age = _latest_verification_age_seconds(observation, config, generated_at)
    quorum_gap = _quorum_gap(
        config.watch_fresh_source_quorum,
        observation.fresh_source_count,
    )
    primary_quorum_gap = _quorum_gap(
        config.watch_primary_fresh_source_quorum,
        observation.primary_fresh_source_count,
    )
    reason_codes = _row_reason_codes(
        fresh_source_count=observation.fresh_source_count,
        primary_fresh_source_count=observation.primary_fresh_source_count,
        latest_verification_age_seconds=latest_age,
        latest_verification_missing=latest_verification_missing,
        stale_source_ratio=stale_ratio,
        source_agreement_score=observation.source_agreement_score,
        contradiction_pressure=observation.contradiction_pressure,
        extraction_confidence=observation.extraction_confidence,
        config=config,
    )
    return ResearchSourceEventClaimFreshnessQuorumRow(
        event_claim_bucket=observation.event_claim_bucket,
        source_family_count=observation.source_family_count,
        fresh_source_count=observation.fresh_source_count,
        primary_fresh_source_count=observation.primary_fresh_source_count,
        stale_source_count=stale_count,
        freshness_ratio=freshness_ratio,
        stale_source_ratio=stale_ratio,
        latest_verification_missing=latest_verification_missing,
        latest_verification_age_seconds=latest_age,
        source_agreement_score=observation.source_agreement_score,
        contradiction_pressure=observation.contradiction_pressure,
        extraction_confidence=observation.extraction_confidence,
        quorum_gap_count=quorum_gap,
        primary_quorum_gap_count=primary_quorum_gap,
        freshness_quorum_score=_freshness_quorum_score(reason_codes),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _latest_verification_age_seconds(
    observation: ResearchSourceEventClaimFreshnessQuorumObservation,
    config: ResearchSourceEventClaimFreshnessQuorumConfig,
    generated_at: datetime,
) -> Decimal:
    if observation.latest_verified_at is None:
        return config.block_latest_verification_age_seconds
    return _elapsed_seconds(observation.latest_verified_at, generated_at)


def _quorum_gap(required_count: Decimal, actual_count: Decimal) -> Decimal:
    if actual_count >= required_count:
        return _ZERO.quantize(_COUNT_QUANT)
    return (required_count - actual_count).quantize(_COUNT_QUANT)


def _row_reason_codes(
    *,
    fresh_source_count: Decimal,
    primary_fresh_source_count: Decimal,
    latest_verification_missing: bool,
    latest_verification_age_seconds: Decimal,
    stale_source_ratio: Decimal,
    source_agreement_score: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence: Decimal,
    config: ResearchSourceEventClaimFreshnessQuorumConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_low_quorum_reason(
        reason_codes,
        prefix="fresh_source_quorum",
        value=fresh_source_count,
        watch_threshold=config.watch_fresh_source_quorum,
        block_threshold=config.block_fresh_source_quorum,
    )
    _append_low_quorum_reason(
        reason_codes,
        prefix="primary_fresh_source_quorum",
        value=primary_fresh_source_count,
        watch_threshold=config.watch_primary_fresh_source_quorum,
        block_threshold=config.block_primary_fresh_source_quorum,
    )
    if latest_verification_missing:
        reason_codes.append("latest_verification_missing")
    _append_high_threshold_reason(
        reason_codes,
        prefix="latest_verification_age",
        value=latest_verification_age_seconds,
        watch_threshold=config.watch_latest_verification_age_seconds,
        block_threshold=config.block_latest_verification_age_seconds,
    )
    _append_high_threshold_reason(
        reason_codes,
        prefix="stale_source_ratio",
        value=stale_source_ratio,
        watch_threshold=config.watch_stale_source_ratio,
        block_threshold=config.block_stale_source_ratio,
    )
    _append_low_threshold_reason(
        reason_codes,
        prefix="source_agreement",
        value=source_agreement_score,
        watch_threshold=config.watch_source_agreement_score,
        block_threshold=config.block_source_agreement_score,
    )
    _append_high_threshold_reason(
        reason_codes,
        prefix="contradiction_pressure",
        value=contradiction_pressure,
        watch_threshold=config.watch_contradiction_pressure,
        block_threshold=config.block_contradiction_pressure,
    )
    _append_low_threshold_reason(
        reason_codes,
        prefix="extraction_confidence",
        value=extraction_confidence,
        watch_threshold=config.watch_extraction_confidence,
        block_threshold=config.block_extraction_confidence,
    )
    if not reason_codes:
        reason_codes.append("event_claim_freshness_quorum_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_high_threshold_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value >= watch_threshold:
        reason_codes.append(f"{prefix}_watch")


def _append_low_threshold_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value <= block_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value <= watch_threshold:
        reason_codes.append(f"{prefix}_watch")


def _append_low_quorum_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value <= block_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value < watch_threshold:
        reason_codes.append(f"{prefix}_watch")


def _freshness_quorum_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == ("event_claim_freshness_quorum_pass",):
        return _ZERO
    severity_total = sum(
        (
            _ONE
            if reason_code.endswith("_block")
            else Decimal("0.500000")
            if reason_code.endswith("_watch")
            else _ZERO
        )
        for reason_code in reason_codes
    )
    return _clamp_ratio(severity_total / Decimal("7"))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceEventClaimFreshnessQuorumRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEventClaimFreshnessQuorumRow, ...],
) -> tuple[str, ...]:
    if all(row.status == "pass" for row in rows):
        return ("event_claim_freshness_quorum_pass",)
    return _normalize_reason_codes(
        tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != "event_claim_freshness_quorum_pass"
        ),
    )


def _status_count(
    rows: tuple[ResearchSourceEventClaimFreshnessQuorumRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchSourceEventClaimFreshnessQuorumRow) -> None:
    if row.fresh_source_count > row.source_family_count:
        raise ValueError("fresh_source_count must not exceed source_family_count")
    if row.primary_fresh_source_count > row.fresh_source_count:
        raise ValueError("primary_fresh_source_count must not exceed fresh_source_count")
    if row.stale_source_count != row.source_family_count - row.fresh_source_count:
        raise ValueError("stale_source_count must match source_family_count")
    if row.freshness_ratio != _quantize(row.fresh_source_count / row.source_family_count):
        raise ValueError("freshness_ratio must match source counts")
    if row.stale_source_ratio != _quantize(row.stale_source_count / row.source_family_count):
        raise ValueError("stale_source_ratio must match source counts")
    if type(row.latest_verification_missing) is not bool:
        raise ValueError("latest_verification_missing must be a bool")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        row.reason_codes == ("event_claim_freshness_quorum_pass",)
        and row.freshness_quorum_score != _ZERO
    ):
        raise ValueError("freshness_quorum_score must be zero for pass rows")


def _validate_report_consistency(report: ResearchSourceEventClaimFreshnessQuorumReport) -> None:
    _reject_empty_rows(report.rows)
    if report.event_claim_bucket_count != _decimal_count(len(report.rows)):
        raise ValueError("event_claim_bucket_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.min_fresh_source_count != min(
        (row.fresh_source_count for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_fresh_source_count must match rows")
    if report.min_primary_fresh_source_count != min(
        (row.primary_fresh_source_count for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_primary_fresh_source_count must match rows")
    if report.missing_latest_verification_count != _decimal_count(
        sum(1 for row in report.rows if row.latest_verification_missing),
    ):
        raise ValueError("missing_latest_verification_count must match rows")
    if report.max_latest_verification_age_seconds != max(
        (row.latest_verification_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_latest_verification_age_seconds must match rows")
    if report.max_stale_source_ratio != max(
        (row.stale_source_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_stale_source_ratio must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.min_source_agreement_score != min(
        (row.source_agreement_score for row in report.rows),
        default=_ONE,
    ):
        raise ValueError("min_source_agreement_score must match rows")
    if report.min_extraction_confidence != min(
        (row.extraction_confidence for row in report.rows),
        default=_ONE,
    ):
        raise ValueError("min_extraction_confidence must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    buckets = tuple(row.event_claim_bucket for row in report.rows)
    if len(buckets) != len(set(buckets)):
        raise ValueError("rows must contain unique event_claim_bucket values")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.event_claim_bucket)):
        raise ValueError("rows must be deterministic")


def _normalize_observations(
    observations: Sequence[ResearchSourceEventClaimFreshnessQuorumObservation],
) -> tuple[ResearchSourceEventClaimFreshnessQuorumObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSourceEventClaimFreshnessQuorumObservation] = []
    seen: set[str] = set()
    for item in observations:
        if type(item) is not ResearchSourceEventClaimFreshnessQuorumObservation:
            raise ValueError(
                "observations must contain ResearchSourceEventClaimFreshnessQuorumObservation values",
            )
        _require_hard_flags("observation", item)
        if item.event_claim_bucket in seen:
            raise ValueError("observations must contain unique event_claim_bucket values")
        seen.add(item.event_claim_bucket)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.event_claim_bucket))


def _normalize_rows(
    rows: Sequence[ResearchSourceEventClaimFreshnessQuorumRow],
) -> tuple[ResearchSourceEventClaimFreshnessQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceEventClaimFreshnessQuorumRow] = []
    for row in rows:
        if type(row) is not ResearchSourceEventClaimFreshnessQuorumRow:
            raise ValueError(
                "rows must contain ResearchSourceEventClaimFreshnessQuorumRow values",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.event_claim_bucket))


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
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)


def _reject_empty_observations(
    observations: tuple[ResearchSourceEventClaimFreshnessQuorumObservation, ...],
) -> None:
    if not observations:
        raise ValueError("observations must not be empty")


def _reject_empty_rows(rows: tuple[ResearchSourceEventClaimFreshnessQuorumRow, ...]) -> None:
    if not rows:
        raise ValueError("rows must not be empty")


def _reject_future_time(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_watch_before_block_high(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"block_{field_name} must be greater than or equal to watch")


def _require_watch_before_block_low(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"block_{field_name} must be less than or equal to watch")


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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return value.quantize(_COUNT_QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
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
    return Decimal(value).quantize(_COUNT_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _elapsed_seconds(started_at: datetime, ended_at: datetime) -> Decimal:
    elapsed = ended_at - started_at
    if elapsed.days < 0:
        raise ValueError("elapsed seconds must be nonnegative")
    elapsed_microseconds = (
        ((elapsed.days * 86400) + elapsed.seconds) * 1000000
    ) + elapsed.microseconds
    return _quantize(Decimal(elapsed_microseconds) / Decimal("1000000"))


def _report_values_without_digest(
    report: ResearchSourceEventClaimFreshnessQuorumReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("derived_validation_digest payload", payload)
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
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    del allow_json_containers
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_string(f"{label} payload key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(f"{label} payload value", value)
