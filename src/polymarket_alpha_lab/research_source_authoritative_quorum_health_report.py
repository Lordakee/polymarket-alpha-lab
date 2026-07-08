"""Pure report-only reducer for authoritative-source quorum health."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITATIVE_QUORUM_HEALTH_REPORT_CONFIG_VERSION = (
    "source-authoritative-quorum-health-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

OFFICIAL_AUTHORITY_ROLE = "official_authority"
INDEPENDENT_CORROBORATOR_ROLE = "independent_corroborator"
SOURCE_ROLES = (OFFICIAL_AUTHORITY_ROLE, INDEPENDENT_CORROBORATOR_ROLE)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

PASS_REASON = "authoritative_quorum_health_passed"
NO_INPUTS_REASON = "authoritative_quorum_health_no_inputs"
REPORT_BLOCK_REASON = "authoritative_quorum_health_block"
REPORT_WATCH_REASON = "authoritative_quorum_health_watch"
REPORT_PASS_REASON = "authoritative_quorum_health_pass"
REASON_CODE_ORDER = (
    "contradiction_exposure_block",
    "contradiction_exposure_watch",
    "independent_corroboration_gap_block",
    "independent_corroboration_gap_watch",
    "manual_review_urgency_block",
    "manual_review_urgency_watch",
    "official_quorum_gap_block",
    "official_quorum_gap_watch",
    "stale_authority_pressure_block",
    "stale_authority_pressure_watch",
    NO_INPUTS_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "www.",
    "raw",
    "url",
    "text",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "condition_id",
    "condition-id",
    "question",
    "wallet",
    "order",
    "network",
    "database",
    "secret",
    "password",
    "private_key",
    "api_key",
    "authentication",
    "authorization",
    "auth_token",
    "bearer",
    "credential",
    "trade",
    "trading",
    "live",
    "recommendation",
    "sizing",
)


@dataclass(frozen=True)
class ResearchSourceAuthoritativeQuorumHealthReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITATIVE_QUORUM_HEALTH_REPORT_CONFIG_VERSION
    )
    min_official_source_count: Decimal = Decimal("2")
    min_independent_corroboration_count: Decimal = Decimal("2")
    max_authority_age_seconds: Decimal = Decimal("7200.000000")
    watch_stale_authority_pressure: Decimal = Decimal("0.250000")
    block_stale_authority_pressure: Decimal = Decimal("0.600000")
    watch_contradiction_exposure: Decimal = Decimal("0.250000")
    block_contradiction_exposure: Decimal = Decimal("0.600000")
    watch_manual_review_urgency: Decimal = Decimal("0.350000")
    block_manual_review_urgency: Decimal = Decimal("0.700000")
    official_quorum_gap_weight: Decimal = Decimal("0.250000")
    independent_corroboration_gap_weight: Decimal = Decimal("0.250000")
    stale_authority_pressure_weight: Decimal = Decimal("0.250000")
    contradiction_exposure_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritativeQuorumHealthReportConfig:
            raise TypeError(
                "ResearchSourceAuthoritativeQuorumHealthReportConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritativeQuorumHealthReportConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceAuthoritativeQuorumHealthReportConfig",
            )
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITATIVE_QUORUM_HEALTH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "min_official_source_count",
            "min_independent_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_authority_age_seconds",
            _normalize_positive_decimal(
                "max_authority_age_seconds",
                self.max_authority_age_seconds,
            ),
        )
        for field_name in (
            "watch_stale_authority_pressure",
            "block_stale_authority_pressure",
            "watch_contradiction_exposure",
            "block_contradiction_exposure",
            "watch_manual_review_urgency",
            "block_manual_review_urgency",
            "official_quorum_gap_weight",
            "independent_corroboration_gap_weight",
            "stale_authority_pressure_weight",
            "contradiction_exposure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.block_stale_authority_pressure <= self.watch_stale_authority_pressure:
            raise ValueError(
                "block_stale_authority_pressure must exceed "
                "watch_stale_authority_pressure",
            )
        if self.block_contradiction_exposure <= self.watch_contradiction_exposure:
            raise ValueError(
                "block_contradiction_exposure must exceed "
                "watch_contradiction_exposure",
            )
        if self.block_manual_review_urgency <= self.watch_manual_review_urgency:
            raise ValueError(
                "block_manual_review_urgency must exceed watch_manual_review_urgency",
            )
        if (
            self.official_quorum_gap_weight
            + self.independent_corroboration_gap_weight
            + self.stale_authority_pressure_weight
            + self.contradiction_exposure_weight
        ) != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritativeQuorumObservation:
    quorum_scope_id: str
    source_family: str
    source_role: str
    observed_at: datetime
    contradiction_exposure: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritativeQuorumObservation:
            raise TypeError(
                "ResearchSourceAuthoritativeQuorumObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritativeQuorumObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceAuthoritativeQuorumObservation",
            )
        _require_public_identifier("quorum_scope_id", self.quorum_scope_id)
        _require_public_identifier("source_family", self.source_family)
        _require_member("source_role", self.source_role, SOURCE_ROLES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "contradiction_exposure",
            _normalize_probability(
                "contradiction_exposure",
                self.contradiction_exposure,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritativeQuorumHealthReportRow:
    quorum_scope_id: str
    official_source_count: Decimal
    independent_corroboration_count: Decimal
    stale_authority_count: Decimal
    max_authority_age_seconds: Decimal
    stale_authority_pressure: Decimal
    contradiction_exposure: Decimal
    manual_review_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritativeQuorumHealthReportRow:
            raise TypeError(
                "ResearchSourceAuthoritativeQuorumHealthReportRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritativeQuorumHealthReportRow:
            raise ValueError(
                "row must be exactly ResearchSourceAuthoritativeQuorumHealthReportRow",
            )
        _require_public_identifier("quorum_scope_id", self.quorum_scope_id)
        for field_name in (
            "official_source_count",
            "independent_corroboration_count",
            "stale_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_authority_age_seconds",
            _normalize_nonnegative_decimal(
                "max_authority_age_seconds",
                self.max_authority_age_seconds,
            ),
        )
        for field_name in (
            "stale_authority_pressure",
            "contradiction_exposure",
            "manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritativeQuorumHealthReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritativeQuorumHealthReasonCodeCount:
            raise TypeError(
                "ResearchSourceAuthoritativeQuorumHealthReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritativeQuorumHealthReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchSourceAuthoritativeQuorumHealthReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritativeQuorumHealthReport:
    generated_at: datetime
    config_version: str
    scope_count: Decimal
    official_source_count: Decimal
    independent_corroboration_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_stale_authority_pressure: Decimal
    max_contradiction_exposure: Decimal
    max_manual_review_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceAuthoritativeQuorumHealthReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceAuthoritativeQuorumHealthReportRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritativeQuorumHealthReport:
            raise TypeError(
                "ResearchSourceAuthoritativeQuorumHealthReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritativeQuorumHealthReport:
            raise ValueError(
                "report must be exactly ResearchSourceAuthoritativeQuorumHealthReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "scope_count",
            "official_source_count",
            "independent_corroboration_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_stale_authority_pressure",
            "max_contradiction_exposure",
            "max_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _verify_report_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_authoritative_quorum_health_report_payload(self)


def build_research_source_authoritative_quorum_health_report(
    observations: Iterable[ResearchSourceAuthoritativeQuorumObservation],
    *,
    config: ResearchSourceAuthoritativeQuorumHealthReportConfig,
    generated_at: datetime,
) -> ResearchSourceAuthoritativeQuorumHealthReport:
    if type(config) is not ResearchSourceAuthoritativeQuorumHealthReportConfig:
        raise ValueError(
            "config must be exactly "
            "ResearchSourceAuthoritativeQuorumHealthReportConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    grouped: dict[str, list[ResearchSourceAuthoritativeQuorumObservation]] = {}
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        grouped.setdefault(observation.quorum_scope_id, []).append(observation)

    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    scope_id,
                    tuple(group_observations),
                    generated_at=generated_at,
                    config=config,
                )
                for scope_id, group_observations in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    scope_count = _count_decimal(len(rows))
    official_count = sum((row.official_source_count for row in rows), COUNT_ZERO)
    independent_count = sum(
        (row.independent_corroboration_count for row in rows),
        COUNT_ZERO,
    )
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    status = _report_status(rows)
    max_stale = max((row.stale_authority_pressure for row in rows), default=ZERO)
    max_contradiction = max((row.contradiction_exposure for row in rows), default=ZERO)
    max_urgency = max((row.manual_review_urgency for row in rows), default=ONE)
    unsigned_payload = _json_ready(
        {
            "generated_at": generated_at,
            "config_version": config.config_version,
            "scope_count": scope_count,
            "official_source_count": official_count,
            "independent_corroboration_count": independent_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "block_count": block_count,
            "max_stale_authority_pressure": max_stale,
            "max_contradiction_exposure": max_contradiction,
            "max_manual_review_urgency": max_urgency,
            "status": status,
            "reason_codes": reason_codes,
            "reason_code_counts": reason_code_counts,
            "rows": rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return ResearchSourceAuthoritativeQuorumHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        scope_count=scope_count,
        official_source_count=official_count,
        independent_corroboration_count=independent_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_stale_authority_pressure=max_stale,
        max_contradiction_exposure=max_contradiction,
        max_manual_review_urgency=max_urgency,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_digest_payload(unsigned_payload),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_authoritative_quorum_health_report_payload(
    report: ResearchSourceAuthoritativeQuorumHealthReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthoritativeQuorumHealthReport:
        raise ValueError(
            "report must be exactly ResearchSourceAuthoritativeQuorumHealthReport",
        )
    _validate_report_consistency(report)
    _verify_report_digest(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_authoritative_quorum_health_report_digest(
    report: ResearchSourceAuthoritativeQuorumHealthReport,
) -> str:
    payload = research_source_authoritative_quorum_health_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_observations(
    scope_id: str,
    observations: tuple[ResearchSourceAuthoritativeQuorumObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceAuthoritativeQuorumHealthReportConfig,
) -> ResearchSourceAuthoritativeQuorumHealthReportRow:
    official_ages = _latest_source_family_ages(
        observations,
        role=OFFICIAL_AUTHORITY_ROLE,
        generated_at=generated_at,
    )
    independent_families = frozenset(
        observation.source_family
        for observation in observations
        if observation.source_role == INDEPENDENT_CORROBORATOR_ROLE
    )
    official_count = _count_decimal(len(official_ages))
    independent_count = _count_decimal(len(independent_families))
    stale_count = _count_decimal(
        sum(1 for age in official_ages.values() if age > config.max_authority_age_seconds),
    )
    max_authority_age = max(official_ages.values(), default=ZERO)
    stale_pressure = _safe_ratio(stale_count, official_count)
    contradiction_exposure = max(
        (observation.contradiction_exposure for observation in observations),
        default=ZERO,
    )
    official_gap = _safe_ratio(
        _nonnegative_delta(config.min_official_source_count, official_count),
        config.min_official_source_count,
    )
    independent_gap = _safe_ratio(
        _nonnegative_delta(
            config.min_independent_corroboration_count,
            independent_count,
        ),
        config.min_independent_corroboration_count,
    )
    manual_review_urgency = _normalize_probability(
        "manual_review_urgency",
        (
            config.official_quorum_gap_weight * official_gap
            + config.independent_corroboration_gap_weight * independent_gap
            + config.stale_authority_pressure_weight * stale_pressure
            + config.contradiction_exposure_weight * contradiction_exposure
        ),
    )
    reason_codes = _row_reason_codes(
        official_count=official_count,
        independent_count=independent_count,
        stale_pressure=stale_pressure,
        contradiction_exposure=contradiction_exposure,
        manual_review_urgency=manual_review_urgency,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchSourceAuthoritativeQuorumHealthReportRow(
        quorum_scope_id=scope_id,
        official_source_count=official_count,
        independent_corroboration_count=independent_count,
        stale_authority_count=stale_count,
        max_authority_age_seconds=max_authority_age,
        stale_authority_pressure=stale_pressure,
        contradiction_exposure=contradiction_exposure,
        manual_review_urgency=manual_review_urgency,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _latest_source_family_ages(
    observations: tuple[ResearchSourceAuthoritativeQuorumObservation, ...],
    *,
    role: str,
    generated_at: datetime,
) -> dict[str, Decimal]:
    ages: dict[str, Decimal] = {}
    for observation in observations:
        if observation.source_role != role:
            continue
        age = _age_seconds(generated_at, observation.observed_at)
        existing = ages.get(observation.source_family)
        if existing is None or age < existing:
            ages[observation.source_family] = age
    return ages


def _row_reason_codes(
    *,
    official_count: Decimal,
    independent_count: Decimal,
    stale_pressure: Decimal,
    contradiction_exposure: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchSourceAuthoritativeQuorumHealthReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    has_block = False
    has_watch = False
    if contradiction_exposure >= config.block_contradiction_exposure:
        reasons.append("contradiction_exposure_block")
        has_block = True
    elif contradiction_exposure >= config.watch_contradiction_exposure:
        reasons.append("contradiction_exposure_watch")
        has_watch = True
    if independent_count == COUNT_ZERO:
        reasons.append("independent_corroboration_gap_block")
        has_block = True
    elif independent_count < config.min_independent_corroboration_count:
        reasons.append("independent_corroboration_gap_watch")
        has_watch = True
    if manual_review_urgency >= config.block_manual_review_urgency:
        reasons.append("manual_review_urgency_block")
        has_block = True
    elif manual_review_urgency >= config.watch_manual_review_urgency:
        reasons.append("manual_review_urgency_watch")
        has_watch = True
    if official_count == COUNT_ZERO:
        reasons.append("official_quorum_gap_block")
        has_block = True
    elif official_count < config.min_official_source_count:
        reasons.append("official_quorum_gap_watch")
        has_watch = True
    if stale_pressure >= config.block_stale_authority_pressure:
        reasons.append("stale_authority_pressure_block")
        has_block = True
    elif stale_pressure >= config.watch_stale_authority_pressure:
        reasons.append("stale_authority_pressure_watch")
        has_watch = True
    if has_block:
        reasons.append(REPORT_BLOCK_REASON)
    elif has_watch:
        reasons.append(REPORT_WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return _ordered_reason_codes(reasons)


def _row_sort_key(
    row: ResearchSourceAuthoritativeQuorumHealthReportRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], -row.manual_review_urgency, row.quorum_scope_id)


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthoritativeQuorumHealthReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, REPORT_BLOCK_REASON)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    status = _report_status(rows)
    if status == "block":
        reasons.append(REPORT_BLOCK_REASON)
    elif status == "watch":
        reasons.append(REPORT_WATCH_REASON)
    else:
        reasons.append(REPORT_PASS_REASON)
    return _ordered_reason_codes(reasons)


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthoritativeQuorumHealthReportRow, ...],
) -> tuple[ResearchSourceAuthoritativeQuorumHealthReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceAuthoritativeQuorumHealthReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_ORDER
        if counts[reason_code] > 0
    )


def _report_status(
    rows: tuple[ResearchSourceAuthoritativeQuorumHealthReportRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if REPORT_BLOCK_REASON in reason_codes:
        return "block"
    if REPORT_WATCH_REASON in reason_codes:
        return "watch"
    if PASS_REASON in reason_codes or REPORT_PASS_REASON in reason_codes:
        return "pass"
    raise ValueError("status reason code is missing")


def _validate_row(row: ResearchSourceAuthoritativeQuorumHealthReportRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.stale_authority_count > row.official_source_count:
        raise ValueError("stale_authority_count cannot exceed official_source_count")
    if row.official_source_count == COUNT_ZERO:
        if row.stale_authority_pressure != ZERO:
            raise ValueError("stale_authority_pressure must be zero without authority")
    elif row.stale_authority_pressure != _safe_ratio(
        row.stale_authority_count,
        row.official_source_count,
    ):
        raise ValueError("stale_authority_pressure must match stale authority count")


def _validate_report_consistency(
    report: ResearchSourceAuthoritativeQuorumHealthReport,
) -> None:
    if report.scope_count != _count_decimal(len(report.rows)):
        raise ValueError("scope_count must match rows")
    if report.official_source_count != sum(
        (row.official_source_count for row in report.rows),
        COUNT_ZERO,
    ):
        raise ValueError("official_source_count must match rows")
    if report.independent_corroboration_count != sum(
        (row.independent_corroboration_count for row in report.rows),
        COUNT_ZERO,
    ):
        raise ValueError("independent_corroboration_count must match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.max_stale_authority_pressure != max(
        (row.stale_authority_pressure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_stale_authority_pressure must match rows")
    if report.max_contradiction_exposure != max(
        (row.contradiction_exposure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_exposure must match rows")
    if report.max_manual_review_urgency != max(
        (row.manual_review_urgency for row in report.rows),
        default=ONE,
    ):
        raise ValueError("max_manual_review_urgency must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _verify_report_digest(report: ResearchSourceAuthoritativeQuorumHealthReport) -> None:
    expected_digest = _digest_payload(_unsigned_report_payload(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")


def _unsigned_report_payload(
    report: ResearchSourceAuthoritativeQuorumHealthReport,
) -> dict[str, Any]:
    return _json_ready(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "scope_count": report.scope_count,
            "official_source_count": report.official_source_count,
            "independent_corroboration_count": report.independent_corroboration_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "max_stale_authority_pressure": report.max_stale_authority_pressure,
            "max_contradiction_exposure": report.max_contradiction_exposure,
            "max_manual_review_urgency": report.max_manual_review_urgency,
            "status": report.status,
            "reason_codes": report.reason_codes,
            "reason_code_counts": report.reason_code_counts,
            "rows": report.rows,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _normalize_observations(
    observations: Iterable[ResearchSourceAuthoritativeQuorumObservation],
) -> tuple[ResearchSourceAuthoritativeQuorumObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    normalized: list[ResearchSourceAuthoritativeQuorumObservation] = []
    for observation in observations:
        if type(observation) is not ResearchSourceAuthoritativeQuorumObservation:
            raise ValueError(
                "observations must contain exactly "
                "ResearchSourceAuthoritativeQuorumObservation",
            )
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchSourceAuthoritativeQuorumHealthReportRow, ...],
) -> tuple[ResearchSourceAuthoritativeQuorumHealthReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceAuthoritativeQuorumHealthReportRow:
            raise ValueError(
                "rows must contain exactly "
                "ResearchSourceAuthoritativeQuorumHealthReportRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        ResearchSourceAuthoritativeQuorumHealthReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchSourceAuthoritativeQuorumHealthReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_code_count in reason_code_counts:
        if type(reason_code_count) is not (
            ResearchSourceAuthoritativeQuorumHealthReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchSourceAuthoritativeQuorumHealthReasonCodeCount",
            )
        _require_hard_flags("reason count", reason_code_count)
    return reason_code_counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
    return _ordered_reason_codes(value)


def _ordered_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    unique = frozenset(reason_codes)
    return tuple(reason_code for reason_code in REASON_CODE_ORDER if reason_code in unique)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value not in REASON_CODE_ORDER:
        raise ValueError(f"{field_name} has an unsupported reason code")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed)}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have non-None utcoffset")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


COUNT_ZERO = Decimal("0")


def _normalize_count(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole number")
    return value.quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= COUNT_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_ZERO or denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("ratio", numerator / denominator)


def _nonnegative_delta(value: Decimal, offset: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        result = value - offset
    if result <= COUNT_ZERO:
        return COUNT_ZERO
    return result.quantize(COUNT_QUANTUM)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "source_age_seconds",
        Decimal(str((generated_at - observed_at).total_seconds())),
    )


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, field_name, None)
        if type(flag_value) is not bool:
            raise ValueError(f"{name} {field_name} must be a bool")
        if flag_value is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _digest_payload(payload: dict[str, Any]) -> str:
    _validate_public_payload(payload)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _validate_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _validate_public_payload(asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError("payload contains unsafe public field")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _validate_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_public_payload(item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError("payload contains unsafe public value")
    if type(value) in (float, int):
        raise ValueError("payload numeric values must be Decimal-derived strings")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) in (float, int):
        raise ValueError("JSON numeric value must be Decimal-derived string")
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


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITATIVE_QUORUM_HEALTH_REPORT_CONFIG_VERSION",
    "ResearchSourceAuthoritativeQuorumHealthReasonCodeCount",
    "ResearchSourceAuthoritativeQuorumHealthReport",
    "ResearchSourceAuthoritativeQuorumHealthReportConfig",
    "ResearchSourceAuthoritativeQuorumHealthReportRow",
    "ResearchSourceAuthoritativeQuorumObservation",
    "build_research_source_authoritative_quorum_health_report",
    "research_source_authoritative_quorum_health_report_digest",
    "research_source_authoritative_quorum_health_report_payload",
)
