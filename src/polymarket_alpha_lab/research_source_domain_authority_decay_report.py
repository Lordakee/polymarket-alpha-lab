"""Pure report-only reducer for source authority decay by sanitized domain."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "ResearchSourceDomainAuthorityDecayObservation",
    "ResearchSourceDomainAuthorityDecayReasonCodeCount",
    "ResearchSourceDomainAuthorityDecayReport",
    "ResearchSourceDomainAuthorityDecayReportConfig",
    "ResearchSourceDomainAuthorityDecayReportRow",
    "build_research_source_domain_authority_decay_report",
    "research_source_domain_authority_decay_report_digest",
    "research_source_domain_authority_decay_report_payload",
)


DEFAULT_RESEARCH_SOURCE_DOMAIN_AUTHORITY_DECAY_REPORT_CONFIG_VERSION = (
    "source-domain-authority-decay-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

PASS_REASON = "source_domain_authority_decay_passed"
NO_INPUTS_REASON = "source_domain_authority_decay_no_inputs"
REPORT_BLOCK_REASON = "source_domain_authority_decay_report_block"
REPORT_WATCH_REASON = "source_domain_authority_decay_report_watch"
REPORT_PASS_REASON = "source_domain_authority_decay_report_pass"
ROW_BLOCK_REASON = "source_domain_authority_decay_block"
ROW_WATCH_REASON = "source_domain_authority_decay_watch"
REASON_CODE_ORDER = (
    "authority_freshness_block",
    "authority_freshness_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "corroboration_decay_block",
    "corroboration_decay_watch",
    "domain_authority_score_block",
    "domain_authority_score_watch",
    "retrieval_reliability_block",
    "retrieval_reliability_watch",
    NO_INPUTS_REASON,
    ROW_BLOCK_REASON,
    ROW_WATCH_REASON,
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
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "condition_id",
    "condition-id",
    "slug",
    "question",
    "dsn",
    "table",
    "token",
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
    "bearer",
    "credential",
    "trade",
    "trading",
    "live",
    "recommendation",
    "sizing",
)


@dataclass(frozen=True)
class ResearchSourceDomainAuthorityDecayReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_DOMAIN_AUTHORITY_DECAY_REPORT_CONFIG_VERSION
    )
    fresh_authority_age_seconds: Decimal = Decimal("3600.000000")
    stale_authority_age_seconds: Decimal = Decimal("86400.000000")
    pass_domain_authority_score: Decimal = Decimal("0.750000")
    block_domain_authority_score: Decimal = Decimal("0.350000")
    watch_contradiction_pressure: Decimal = Decimal("0.250000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    watch_retrieval_reliability: Decimal = Decimal("0.700000")
    block_retrieval_reliability: Decimal = Decimal("0.400000")
    authority_freshness_weight: Decimal = Decimal("0.350000")
    corroboration_decay_weight: Decimal = Decimal("0.250000")
    retrieval_reliability_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceDomainAuthorityDecayReportConfig:
            raise TypeError(
                "ResearchSourceDomainAuthorityDecayReportConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDomainAuthorityDecayReportConfig:
            raise ValueError(
                "config must be exactly ResearchSourceDomainAuthorityDecayReportConfig",
            )
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_DOMAIN_AUTHORITY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_authority_age_seconds",
            _normalize_positive_decimal(
                "fresh_authority_age_seconds",
                self.fresh_authority_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "stale_authority_age_seconds",
            _normalize_positive_decimal(
                "stale_authority_age_seconds",
                self.stale_authority_age_seconds,
            ),
        )
        if self.stale_authority_age_seconds <= self.fresh_authority_age_seconds:
            raise ValueError(
                "stale_authority_age_seconds must exceed fresh_authority_age_seconds",
            )
        for field_name in (
            "pass_domain_authority_score",
            "block_domain_authority_score",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_retrieval_reliability",
            "block_retrieval_reliability",
            "authority_freshness_weight",
            "corroboration_decay_weight",
            "retrieval_reliability_weight",
            "contradiction_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_domain_authority_score <= self.block_domain_authority_score:
            raise ValueError(
                "pass_domain_authority_score must exceed block_domain_authority_score",
            )
        if self.block_contradiction_pressure <= self.watch_contradiction_pressure:
            raise ValueError(
                "block_contradiction_pressure must exceed "
                "watch_contradiction_pressure",
            )
        if self.watch_retrieval_reliability <= self.block_retrieval_reliability:
            raise ValueError(
                "watch_retrieval_reliability must exceed block_retrieval_reliability",
            )
        if (
            self.authority_freshness_weight
            + self.corroboration_decay_weight
            + self.retrieval_reliability_weight
            + self.contradiction_pressure_weight
        ) != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceDomainAuthorityDecayObservation:
    source_domain: str
    source_family: str
    observed_at: datetime
    authority_score: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal = ZERO
    retrieval_attempt_count: Decimal = COUNT_ZERO
    retrieval_failure_count: Decimal = COUNT_ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceDomainAuthorityDecayObservation:
            raise TypeError(
                "ResearchSourceDomainAuthorityDecayObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDomainAuthorityDecayObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceDomainAuthorityDecayObservation",
            )
        _require_public_identifier("source_domain", self.source_domain)
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "corroboration_score",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("retrieval_attempt_count", "retrieval_failure_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.retrieval_failure_count > self.retrieval_attempt_count:
            raise ValueError(
                "retrieval_failure_count must not exceed retrieval_attempt_count",
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceDomainAuthorityDecayReportRow:
    source_domain: str
    observation_count: Decimal
    source_family_count: Decimal
    latest_authority_age_seconds: Decimal
    average_authority_score: Decimal
    authority_freshness_score: Decimal
    corroboration_decay_score: Decimal
    contradiction_pressure: Decimal
    retrieval_reliability_score: Decimal
    domain_authority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceDomainAuthorityDecayReportRow:
            raise TypeError(
                "ResearchSourceDomainAuthorityDecayReportRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDomainAuthorityDecayReportRow:
            raise ValueError(
                "row must be exactly ResearchSourceDomainAuthorityDecayReportRow",
            )
        _require_public_identifier("source_domain", self.source_domain)
        for field_name in ("observation_count", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_authority_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_authority_age_seconds",
                self.latest_authority_age_seconds,
            ),
        )
        for field_name in (
            "average_authority_score",
            "authority_freshness_score",
            "corroboration_decay_score",
            "contradiction_pressure",
            "retrieval_reliability_score",
            "domain_authority_score",
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
class ResearchSourceDomainAuthorityDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceDomainAuthorityDecayReasonCodeCount:
            raise TypeError(
                "ResearchSourceDomainAuthorityDecayReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDomainAuthorityDecayReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchSourceDomainAuthorityDecayReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceDomainAuthorityDecayReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_domain_authority_score: Decimal | None
    max_contradiction_pressure: Decimal
    min_retrieval_reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceDomainAuthorityDecayReasonCodeCount, ...]
    rows: tuple[ResearchSourceDomainAuthorityDecayReportRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceDomainAuthorityDecayReport:
            raise TypeError(
                "ResearchSourceDomainAuthorityDecayReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDomainAuthorityDecayReport:
            raise ValueError(
                "report must be exactly ResearchSourceDomainAuthorityDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "domain_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_domain_authority_score",
            _normalize_optional_probability(
                "average_domain_authority_score",
                self.average_domain_authority_score,
            ),
        )
        for field_name in (
            "max_contradiction_pressure",
            "min_retrieval_reliability_score",
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
        return research_source_domain_authority_decay_report_payload(self)


def build_research_source_domain_authority_decay_report(
    observations: Iterable[ResearchSourceDomainAuthorityDecayObservation],
    *,
    config: ResearchSourceDomainAuthorityDecayReportConfig,
    generated_at: datetime,
) -> ResearchSourceDomainAuthorityDecayReport:
    if type(config) is not ResearchSourceDomainAuthorityDecayReportConfig:
        raise ValueError(
            "config must be exactly ResearchSourceDomainAuthorityDecayReportConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    grouped: dict[str, list[ResearchSourceDomainAuthorityDecayObservation]] = {}
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        grouped.setdefault(observation.source_domain, []).append(observation)

    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    domain,
                    tuple(domain_observations),
                    generated_at=generated_at,
                    config=config,
                )
                for domain, domain_observations in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    domain_count = _count_decimal(len(rows))
    observation_count = sum((row.observation_count for row in rows), COUNT_ZERO)
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    average_score = _average_report_score(rows)
    max_contradiction = max((row.contradiction_pressure for row in rows), default=ZERO)
    min_reliability = min(
        (row.retrieval_reliability_score for row in rows),
        default=ONE,
    )
    status = _report_status(rows)
    unsigned_payload = _json_ready(
        {
            "generated_at": generated_at,
            "config_version": config.config_version,
            "domain_count": domain_count,
            "observation_count": observation_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "block_count": block_count,
            "average_domain_authority_score": average_score,
            "max_contradiction_pressure": max_contradiction,
            "min_retrieval_reliability_score": min_reliability,
            "status": status,
            "reason_codes": reason_codes,
            "reason_code_counts": reason_code_counts,
            "rows": rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return ResearchSourceDomainAuthorityDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        domain_count=domain_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_domain_authority_score=average_score,
        max_contradiction_pressure=max_contradiction,
        min_retrieval_reliability_score=min_reliability,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_digest_payload(unsigned_payload),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_domain_authority_decay_report_payload(
    report: ResearchSourceDomainAuthorityDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceDomainAuthorityDecayReport:
        raise ValueError(
            "report must be exactly ResearchSourceDomainAuthorityDecayReport",
        )
    _validate_report_consistency(report)
    _verify_report_digest(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_domain_authority_decay_report_digest(
    report: ResearchSourceDomainAuthorityDecayReport,
) -> str:
    payload = research_source_domain_authority_decay_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_observations(
    domain: str,
    observations: tuple[ResearchSourceDomainAuthorityDecayObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceDomainAuthorityDecayReportConfig,
) -> ResearchSourceDomainAuthorityDecayReportRow:
    observation_count = _count_decimal(len(observations))
    family_count = _count_decimal(len({observation.source_family for observation in observations}))
    latest_age = min(
        (_age_seconds(generated_at, observation.observed_at) for observation in observations),
        default=ZERO,
    )
    average_authority = _average_decimal(
        tuple(observation.authority_score for observation in observations),
    )
    age_decay_factor = _age_decay_factor(latest_age, config=config)
    authority_freshness = _normalize_probability(
        "authority_freshness_score",
        average_authority * age_decay_factor,
    )
    corroboration_decay = _normalize_probability(
        "corroboration_decay_score",
        _average_decimal(
            tuple(
                observation.corroboration_score * _age_decay_factor(
                    _age_seconds(generated_at, observation.observed_at),
                    config=config,
                )
                for observation in observations
            ),
        ),
    )
    contradiction_pressure = max(
        (observation.contradiction_pressure for observation in observations),
        default=ZERO,
    )
    attempts = sum((observation.retrieval_attempt_count for observation in observations), COUNT_ZERO)
    failures = sum((observation.retrieval_failure_count for observation in observations), COUNT_ZERO)
    retrieval_reliability = (
        ONE if attempts == COUNT_ZERO else _normalize_probability(
            "retrieval_reliability_score",
            ONE - _safe_ratio(failures, attempts),
        )
    )
    domain_authority_score = _normalize_probability(
        "domain_authority_score",
        config.authority_freshness_weight * authority_freshness
        + config.corroboration_decay_weight * corroboration_decay
        + config.retrieval_reliability_weight * retrieval_reliability
        + config.contradiction_pressure_weight * (ONE - contradiction_pressure),
    )
    reason_codes = _row_reason_codes(
        authority_freshness_score=authority_freshness,
        corroboration_decay_score=corroboration_decay,
        contradiction_pressure=contradiction_pressure,
        retrieval_reliability_score=retrieval_reliability,
        domain_authority_score=domain_authority_score,
        config=config,
    )
    return ResearchSourceDomainAuthorityDecayReportRow(
        source_domain=domain,
        observation_count=observation_count,
        source_family_count=family_count,
        latest_authority_age_seconds=latest_age,
        average_authority_score=average_authority,
        authority_freshness_score=authority_freshness,
        corroboration_decay_score=corroboration_decay,
        contradiction_pressure=contradiction_pressure,
        retrieval_reliability_score=retrieval_reliability,
        domain_authority_score=domain_authority_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_reason_codes(
    *,
    authority_freshness_score: Decimal,
    corroboration_decay_score: Decimal,
    contradiction_pressure: Decimal,
    retrieval_reliability_score: Decimal,
    domain_authority_score: Decimal,
    config: ResearchSourceDomainAuthorityDecayReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    has_block = False
    has_watch = False
    if authority_freshness_score <= config.block_domain_authority_score:
        reasons.append("authority_freshness_block")
        has_block = True
    elif authority_freshness_score < config.pass_domain_authority_score:
        reasons.append("authority_freshness_watch")
        has_watch = True
    if contradiction_pressure >= config.block_contradiction_pressure:
        reasons.append("contradiction_pressure_block")
        has_block = True
    elif contradiction_pressure >= config.watch_contradiction_pressure:
        reasons.append("contradiction_pressure_watch")
        has_watch = True
    if corroboration_decay_score <= config.block_domain_authority_score:
        reasons.append("corroboration_decay_block")
        has_block = True
    elif corroboration_decay_score < config.pass_domain_authority_score:
        reasons.append("corroboration_decay_watch")
        has_watch = True
    if retrieval_reliability_score <= config.block_retrieval_reliability:
        reasons.append("retrieval_reliability_block")
        has_block = True
    elif retrieval_reliability_score < config.watch_retrieval_reliability:
        reasons.append("retrieval_reliability_watch")
        has_watch = True
    if domain_authority_score <= config.block_domain_authority_score:
        reasons.append("domain_authority_score_block")
        has_block = True
    elif domain_authority_score < config.pass_domain_authority_score:
        reasons.append("domain_authority_score_watch")
        has_watch = True
    if has_block:
        reasons.append(ROW_BLOCK_REASON)
    elif has_watch:
        reasons.append(ROW_WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return _ordered_reason_codes(reasons)


def _row_sort_key(
    row: ResearchSourceDomainAuthorityDecayReportRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], row.domain_authority_score, row.source_domain)


def _report_reason_codes(
    rows: tuple[ResearchSourceDomainAuthorityDecayReportRow, ...],
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
    rows: tuple[ResearchSourceDomainAuthorityDecayReportRow, ...],
) -> tuple[ResearchSourceDomainAuthorityDecayReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceDomainAuthorityDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in sorted(reason_code for reason_code in REASON_CODE_ORDER if counts[reason_code] > 0)
    )


def _report_status(rows: tuple[ResearchSourceDomainAuthorityDecayReportRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if ROW_BLOCK_REASON in reason_codes:
        return "block"
    if ROW_WATCH_REASON in reason_codes:
        return "watch"
    if PASS_REASON in reason_codes:
        return "pass"
    raise ValueError("status reason code is missing")


def _validate_row(row: ResearchSourceDomainAuthorityDecayReportRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchSourceDomainAuthorityDecayReport) -> None:
    if report.domain_count != _count_decimal(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.observation_count != sum(
        (row.observation_count for row in report.rows),
        COUNT_ZERO,
    ):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _count_decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_domain_authority_score != _average_report_score(report.rows):
        raise ValueError("average_domain_authority_score must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.min_retrieval_reliability_score != min(
        (row.retrieval_reliability_score for row in report.rows),
        default=ONE,
    ):
        raise ValueError("min_retrieval_reliability_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_observations(
    observations: Iterable[ResearchSourceDomainAuthorityDecayObservation],
) -> tuple[ResearchSourceDomainAuthorityDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceDomainAuthorityDecayObservation] = []
    for value in values:
        if type(value) is not ResearchSourceDomainAuthorityDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceDomainAuthorityDecayObservation values",
            )
        _require_hard_flags("observation", value)
        normalized.append(value)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.source_domain,
                item.source_family,
                item.observed_at,
                item.authority_score,
                item.corroboration_score,
            ),
        ),
    )


def _normalize_rows(
    rows: tuple[ResearchSourceDomainAuthorityDecayReportRow, ...],
) -> tuple[ResearchSourceDomainAuthorityDecayReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceDomainAuthorityDecayReportRow:
            raise ValueError(
                "rows must contain ResearchSourceDomainAuthorityDecayReportRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by status and domain authority score")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceDomainAuthorityDecayReasonCodeCount, ...],
) -> tuple[ResearchSourceDomainAuthorityDecayReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceDomainAuthorityDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceDomainAuthorityDecayReasonCodeCount values",
            )
        _require_hard_flags("reason count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _average_report_score(
    rows: tuple[ResearchSourceDomainAuthorityDecayReportRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    total = sum((row.domain_authority_score for row in rows), ZERO)
    return _quantize(total / Decimal(len(rows)))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _age_decay_factor(
    age_seconds: Decimal,
    *,
    config: ResearchSourceDomainAuthorityDecayReportConfig,
) -> Decimal:
    if age_seconds <= config.fresh_authority_age_seconds:
        return ONE
    if age_seconds >= config.stale_authority_age_seconds:
        return ZERO
    return _normalize_probability(
        "authority_age_decay_factor",
        ONE - (age_seconds / config.stale_authority_age_seconds),
    )


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_ZERO:
        return ZERO
    return _normalize_probability("ratio", numerator / denominator)


def _ordered_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    unique = set(reason_codes)
    unknown = sorted(unique.difference(REASON_CODE_ORDER))
    if unknown:
        raise ValueError(f"unknown reason code: {unknown[0]}")
    return tuple(reason_code for reason_code in REASON_CODE_ORDER if reason_code in unique)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    for item in value:
        _require_reason_code(field_name, item)
    return _ordered_reason_codes(value)


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in REASON_CODE_ORDER:
        raise ValueError(f"{field_name} has unsupported reason code")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= COUNT_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _verify_report_digest(report: ResearchSourceDomainAuthorityDecayReport) -> None:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    supplied = payload.pop("derived_validation_digest")
    expected = _digest_payload(payload)
    if supplied != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _digest_payload(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        if not value.is_finite():
            raise ValueError("value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _validate_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_string("payload key", key)
            _validate_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _validate_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_string("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload values must be public JSON strings, bools, lists, or objects")


def _reject_unsafe_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe public surface")
