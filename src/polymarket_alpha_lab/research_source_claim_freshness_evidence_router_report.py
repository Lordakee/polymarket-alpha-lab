"""Pure report-only routing for claim freshness evidence readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_CLAIM_FRESHNESS_EVIDENCE_ROUTER_REPORT_CONFIG_VERSION = (
    "research-source-claim-freshness-evidence-router-report-v0"
)

STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_EVIDENCE_POSITIONS = ("supports", "contradicts", "neutral")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REASON_CODE_SEQUENCE = (
    "claim_age_watch",
    "claim_age_block",
    "evidence_age_watch",
    "evidence_age_block",
    "fresh_evidence_quorum_watch",
    "fresh_evidence_quorum_block",
    "source_family_quorum_block",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "freshness_evidence_router_pass",
)
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "raw",
    "http",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "auth",
    "private",
    "secret",
    "credential",
)


@dataclass(frozen=True)
class ResearchSourceClaimFreshnessEvidenceRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_FRESHNESS_EVIDENCE_ROUTER_REPORT_CONFIG_VERSION
    )
    watch_claim_age_seconds: Decimal = Decimal("21600.000000")
    block_claim_age_seconds: Decimal = Decimal("86400.000000")
    max_fresh_evidence_age_seconds: Decimal = Decimal("7200.000000")
    block_evidence_age_seconds: Decimal = Decimal("21600.000000")
    min_fresh_evidence_count: Decimal = Decimal("2")
    min_source_family_count: Decimal = Decimal("2")
    watch_contradiction_pressure: Decimal = Decimal("0.250000")
    block_contradiction_pressure: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimFreshnessEvidenceRouterConfig:
            raise TypeError(
                "ResearchSourceClaimFreshnessEvidenceRouterConfig cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimFreshnessEvidenceRouterConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceClaimFreshnessEvidenceRouterConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_FRESHNESS_EVIDENCE_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_claim_age_seconds",
            "block_claim_age_seconds",
            "max_fresh_evidence_age_seconds",
            "block_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_fresh_evidence_count", "min_source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_before_block(
            "claim_age_seconds",
            self.watch_claim_age_seconds,
            self.block_claim_age_seconds,
        )
        _require_watch_before_block(
            "evidence_age_seconds",
            self.max_fresh_evidence_age_seconds,
            self.block_evidence_age_seconds,
        )
        _require_watch_before_block(
            "contradiction_pressure",
            self.watch_contradiction_pressure,
            self.block_contradiction_pressure,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimFreshnessEvidenceRouterObservation:
    claim_bucket: str
    source_family: str
    claim_observed_at: datetime
    evidence_observed_at: datetime
    evidence_position: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimFreshnessEvidenceRouterObservation:
            raise TypeError(
                "ResearchSourceClaimFreshnessEvidenceRouterObservation cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimFreshnessEvidenceRouterObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceClaimFreshnessEvidenceRouterObservation",
            )
        _require_public_identifier("claim_bucket", self.claim_bucket)
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        if self.evidence_observed_at < self.claim_observed_at:
            raise ValueError("evidence_observed_at must not be before claim_observed_at")
        _require_member("evidence_position", self.evidence_position, _EVIDENCE_POSITIONS)
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceClaimFreshnessEvidenceRouterRow:
    claim_bucket: str
    evidence_count: Decimal
    source_family_count: Decimal
    fresh_evidence_count: Decimal
    stale_evidence_count: Decimal
    max_claim_age_seconds: Decimal
    max_evidence_age_seconds: Decimal
    fresh_evidence_ratio: Decimal
    contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimFreshnessEvidenceRouterRow:
            raise TypeError(
                "ResearchSourceClaimFreshnessEvidenceRouterRow cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimFreshnessEvidenceRouterRow:
            raise ValueError(
                "row must be exactly ResearchSourceClaimFreshnessEvidenceRouterRow",
            )
        _require_public_identifier("claim_bucket", self.claim_bucket)
        for field_name in (
            "evidence_count",
            "source_family_count",
            "fresh_evidence_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_claim_age_seconds", "max_evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_evidence_ratio", "contradiction_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceClaimFreshnessEvidenceRouterReport:
    generated_at: datetime
    config_version: str
    claim_bucket_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_evidence_count: Decimal
    max_claim_age_seconds: Decimal
    max_evidence_age_seconds: Decimal
    max_contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceClaimFreshnessEvidenceRouterRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimFreshnessEvidenceRouterReport:
            raise TypeError(
                "ResearchSourceClaimFreshnessEvidenceRouterReport cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimFreshnessEvidenceRouterReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceClaimFreshnessEvidenceRouterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_FRESHNESS_EVIDENCE_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "claim_bucket_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_claim_age_seconds", "max_evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_contradiction_pressure",
            _require_ratio_decimal(
                "max_contradiction_pressure",
                self.max_contradiction_pressure,
            ),
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

    @property
    def payload(self) -> dict[str, object]:
        return research_source_claim_freshness_evidence_router_report_payload(self)


def build_research_source_claim_freshness_evidence_router_report(
    observations: Sequence[ResearchSourceClaimFreshnessEvidenceRouterObservation],
    *,
    config: ResearchSourceClaimFreshnessEvidenceRouterConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceClaimFreshnessEvidenceRouterReport:
    if config is None:
        config = ResearchSourceClaimFreshnessEvidenceRouterConfig()
    if type(config) is not ResearchSourceClaimFreshnessEvidenceRouterConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimFreshnessEvidenceRouterConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_empty_observations(normalized)
    for item in normalized:
        _reject_future_time("claim_observed_at", item.claim_observed_at, generated_at)
        _reject_future_time("evidence_observed_at", item.evidence_observed_at, generated_at)

    rows = _build_rows(normalized, generated_at, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "claim_bucket_count": _decimal_count(len(rows)),
        "evidence_count": _decimal_count(len(normalized)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "stale_evidence_count": sum(
            (row.stale_evidence_count for row in rows),
            Decimal("0"),
        ),
        "max_claim_age_seconds": max(
            (row.max_claim_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_evidence_age_seconds": max(
            (row.max_evidence_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_contradiction_pressure": max(
            (row.contradiction_pressure for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimFreshnessEvidenceRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_freshness_evidence_router_report_payload(
    report: ResearchSourceClaimFreshnessEvidenceRouterReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceClaimFreshnessEvidenceRouterReport:
        raise ValueError(
            "report must be a ResearchSourceClaimFreshnessEvidenceRouterReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_rows(
    observations: tuple[ResearchSourceClaimFreshnessEvidenceRouterObservation, ...],
    generated_at: datetime,
    config: ResearchSourceClaimFreshnessEvidenceRouterConfig,
) -> tuple[ResearchSourceClaimFreshnessEvidenceRouterRow, ...]:
    grouped: dict[str, list[ResearchSourceClaimFreshnessEvidenceRouterObservation]] = {}
    for item in observations:
        grouped.setdefault(item.claim_bucket, []).append(item)
    rows = tuple(
        _row_for_claim_bucket(
            claim_bucket=claim_bucket,
            observations=tuple(grouped[claim_bucket]),
            generated_at=generated_at,
            config=config,
        )
        for claim_bucket in sorted(grouped)
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_claim_bucket(
    *,
    claim_bucket: str,
    observations: tuple[ResearchSourceClaimFreshnessEvidenceRouterObservation, ...],
    generated_at: datetime,
    config: ResearchSourceClaimFreshnessEvidenceRouterConfig,
) -> ResearchSourceClaimFreshnessEvidenceRouterRow:
    claim_ages = tuple(_elapsed_seconds(item.claim_observed_at, generated_at) for item in observations)
    evidence_ages = tuple(
        _elapsed_seconds(item.evidence_observed_at, generated_at) for item in observations
    )
    fresh_evidence_count = _decimal_count(
        sum(
            1
            for evidence_age in evidence_ages
            if evidence_age <= config.max_fresh_evidence_age_seconds
        ),
    )
    evidence_count = _decimal_count(len(observations))
    stale_evidence_count = evidence_count - fresh_evidence_count
    source_family_count = _decimal_count(len({item.source_family for item in observations}))
    contradiction_pressure = _ratio(
        _decimal_count(
            sum(1 for item in observations if item.evidence_position == "contradicts"),
        ),
        evidence_count,
    )
    fresh_evidence_ratio = _ratio(fresh_evidence_count, evidence_count)
    reason_codes = _row_reason_codes(
        max_claim_age_seconds=max(claim_ages, default=_ZERO),
        max_evidence_age_seconds=max(evidence_ages, default=_ZERO),
        fresh_evidence_count=fresh_evidence_count,
        source_family_count=source_family_count,
        contradiction_pressure=contradiction_pressure,
        config=config,
    )
    return ResearchSourceClaimFreshnessEvidenceRouterRow(
        claim_bucket=claim_bucket,
        evidence_count=evidence_count,
        source_family_count=source_family_count,
        fresh_evidence_count=fresh_evidence_count,
        stale_evidence_count=stale_evidence_count,
        max_claim_age_seconds=max(claim_ages, default=_ZERO),
        max_evidence_age_seconds=max(evidence_ages, default=_ZERO),
        fresh_evidence_ratio=fresh_evidence_ratio,
        contradiction_pressure=contradiction_pressure,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    max_claim_age_seconds: Decimal,
    max_evidence_age_seconds: Decimal,
    fresh_evidence_count: Decimal,
    source_family_count: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchSourceClaimFreshnessEvidenceRouterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        prefix="claim_age",
        value=max_claim_age_seconds,
        watch_threshold=config.watch_claim_age_seconds,
        block_threshold=config.block_claim_age_seconds,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="evidence_age",
        value=max_evidence_age_seconds,
        watch_threshold=config.max_fresh_evidence_age_seconds,
        block_threshold=config.block_evidence_age_seconds,
    )
    if fresh_evidence_count == _ZERO:
        reason_codes.append("fresh_evidence_quorum_block")
    elif fresh_evidence_count < config.min_fresh_evidence_count:
        reason_codes.append("fresh_evidence_quorum_watch")
    if source_family_count < config.min_source_family_count:
        reason_codes.append("source_family_quorum_block")
    _append_threshold_reason(
        reason_codes,
        prefix="contradiction_pressure",
        value=contradiction_pressure,
        watch_threshold=config.watch_contradiction_pressure,
        block_threshold=config.block_contradiction_pressure,
    )
    if not reason_codes:
        reason_codes.append("freshness_evidence_router_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_threshold_reason(
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


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceClaimFreshnessEvidenceRouterRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimFreshnessEvidenceRouterRow, ...],
) -> tuple[str, ...]:
    if all(row.status == "pass" for row in rows):
        return ("freshness_evidence_router_pass",)
    return _normalize_reason_codes(
        tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != "freshness_evidence_router_pass"
        ),
    )


def _status_count(
    rows: tuple[ResearchSourceClaimFreshnessEvidenceRouterRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchSourceClaimFreshnessEvidenceRouterRow,
) -> tuple[int, str]:
    return (_STATUS_RANK[row.status], row.claim_bucket)


def _validate_row_consistency(
    row: ResearchSourceClaimFreshnessEvidenceRouterRow,
) -> None:
    if row.evidence_count <= _ZERO:
        raise ValueError("evidence_count must be positive")
    if row.source_family_count > row.evidence_count:
        raise ValueError("source_family_count must not exceed evidence_count")
    if row.fresh_evidence_count + row.stale_evidence_count != row.evidence_count:
        raise ValueError("fresh and stale evidence counts must match evidence_count")
    if row.fresh_evidence_ratio != _ratio(row.fresh_evidence_count, row.evidence_count):
        raise ValueError("fresh_evidence_ratio must match counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchSourceClaimFreshnessEvidenceRouterReport,
) -> None:
    _reject_empty_rows(report.rows)
    if report.claim_bucket_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_bucket_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), _ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.stale_evidence_count != sum(
        (row.stale_evidence_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("stale_evidence_count must match rows")
    if report.max_claim_age_seconds != max(
        (row.max_claim_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_claim_age_seconds must match rows")
    if report.max_evidence_age_seconds != max(
        (row.max_evidence_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    claim_buckets = tuple(row.claim_bucket for row in report.rows)
    if len(claim_buckets) != len(set(claim_buckets)):
        raise ValueError("rows must contain unique claim_bucket values")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")


def _normalize_observations(
    observations: Sequence[ResearchSourceClaimFreshnessEvidenceRouterObservation],
) -> tuple[ResearchSourceClaimFreshnessEvidenceRouterObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSourceClaimFreshnessEvidenceRouterObservation] = []
    for item in observations:
        if type(item) is not ResearchSourceClaimFreshnessEvidenceRouterObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceClaimFreshnessEvidenceRouterObservation values",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.claim_bucket,
                item.source_family,
                item.claim_observed_at,
                item.evidence_observed_at,
                item.evidence_position,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimFreshnessEvidenceRouterRow],
) -> tuple[ResearchSourceClaimFreshnessEvidenceRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceClaimFreshnessEvidenceRouterRow] = []
    for row in rows:
        if type(row) is not ResearchSourceClaimFreshnessEvidenceRouterRow:
            raise ValueError(
                "rows must contain ResearchSourceClaimFreshnessEvidenceRouterRow values",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


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
    observations: tuple[ResearchSourceClaimFreshnessEvidenceRouterObservation, ...],
) -> None:
    if not observations:
        raise ValueError("observations must not be empty")


def _reject_empty_rows(
    rows: tuple[ResearchSourceClaimFreshnessEvidenceRouterRow, ...],
) -> None:
    if not rows:
        raise ValueError("rows must not be empty")


def _reject_future_time(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
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
    for term in _UNSAFE_PUBLIC_TERMS:
        if term in lowered:
            raise ValueError(f"{field_name} has unsafe public value")


def _require_member(field_name: str, value: object, supported: Sequence[str]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in supported:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, STATUSES)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_decimal(field_name, value)
    if decimal > _ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return decimal


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = decimal.quantize(_COUNT_QUANT)
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_whole_decimal(field_name, value)
    if decimal <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


def _require_watch_before_block(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"block {field_name} threshold must exceed watch threshold")


def _as_utc(field_name: str, value: datetime) -> datetime:
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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _report_values_without_digest(
    report: ResearchSourceClaimFreshnessEvidenceRouterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            _reject_unsafe_public_string(f"{label}.{item.name}", item.name)
            _reject_unsafe_public_payload(
                f"{label}.{item.name}",
                getattr(value, item.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose mapping values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_string(f"{label}.{key}", key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers and all(type(item) is str for item in value):
            for index, item in enumerate(value):
                _reject_unsafe_public_string(f"{label}[{index}]", item)
            return
        if not allow_json_containers and not all(
            is_dataclass(item) and not isinstance(item, type) for item in value
        ):
            raise ValueError(f"{label} must not expose sequence values")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if type(value) in (datetime, Decimal, bool) or value is None:
        return
    raise ValueError(f"{label} has unsupported public payload value")
