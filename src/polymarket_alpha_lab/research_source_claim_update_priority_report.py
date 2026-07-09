"""Pure report-only source-claim update priority report.

The module ranks caller-supplied source-claim update observations for analyst
review. It performs no network access, scraping, persistence, execution,
recommendation, sizing, wallet, auth, order, or trade work.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_PRIORITY_CONFIG_VERSION = (
    "research-source-claim-update-priority-report-v0"
)

PRIORITY_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "source_claim_update_priority_pass"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DOMAIN_LIKE_RE = re.compile(
    r"(?:^|[._-])[a-z0-9-]+\."
    r"(?:ai|app|co|com|dev|edu|gov|io|net|org|test|xyz)"
    r"(?:$|[._-])",
)
RAW_PUBLIC_ID_RE = re.compile(
    r"(?:^|[._-])0x[0-9a-f]{8,}(?:$|[._-])"
    r"|(?:^|[._-])[0-9a-f]{8}-[0-9a-f]{4}-"
    r"[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?:$|[._-])",
)

SAFE_REASON_CODES = (
    "freshness_watch",
    "freshness_block",
    "authority_watch",
    "authority_block",
    "independence_watch",
    "independence_block",
    "contradiction_watch",
    "contradiction_block",
    "domain_relevance_watch",
    "domain_relevance_block",
    "resolution_rule_linkage_watch",
    "resolution_rule_linkage_block",
    "claim_update_priority_watch",
    "claim_update_priority_block",
    PASS_REASON_CODE,
)

UNSAFE_KEY_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "raw_text",
    "raw",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "private_key",
    "api_key",
)
UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "raw_text",
    "raw",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "private_key",
    "api_key",
    "secret",
    "credential",
    "database",
    "network",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
)

PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "priority_rank",
    "update_label",
    "source_family_label",
    "domain_bucket",
    "observed_at",
    "update_age_seconds",
    "freshness_score",
    "authority_score",
    "independent_source_count",
    "expected_independent_source_count",
    "independence_score",
    "contradiction_severity",
    "domain_relevance_score",
    "resolution_rule_linkage_score",
    "analyst_update_priority_score",
    "priority_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_PAYLOAD_FIELDS = (
    *PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "generated_at",
    "status",
    "update_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_analyst_update_priority_score",
    "max_analyst_update_priority_score",
    "max_contradiction_severity",
    "average_freshness_score",
    "average_authority_score",
    "average_independence_score",
    "average_domain_relevance_score",
    "average_resolution_rule_linkage_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_PAYLOAD_FIELDS = (
    *PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_PRIORITY_CONFIG_VERSION",
    "PRIORITY_STATUSES",
    "ResearchSourceClaimUpdatePriorityConfig",
    "ResearchSourceClaimUpdatePriorityObservation",
    "ResearchSourceClaimUpdatePriorityReport",
    "ResearchSourceClaimUpdatePriorityRow",
    "build_research_source_claim_update_priority_report",
    "research_source_claim_update_priority_report_digest",
    "research_source_claim_update_priority_report_payload",
    "validate_research_source_claim_update_priority_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceClaimUpdatePriorityConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_PRIORITY_CONFIG_VERSION
    max_update_age_seconds: Decimal = Decimal("7200.000000")
    component_watch_threshold: Decimal = Decimal("0.500000")
    component_block_threshold: Decimal = Decimal("0.800000")
    priority_watch_threshold: Decimal = Decimal("0.350000")
    priority_block_threshold: Decimal = Decimal("0.700000")
    freshness_weight: Decimal = Decimal("0.150000")
    authority_weight: Decimal = Decimal("0.200000")
    independence_weight: Decimal = Decimal("0.150000")
    contradiction_weight: Decimal = Decimal("0.200000")
    domain_relevance_weight: Decimal = Decimal("0.150000")
    resolution_rule_linkage_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimUpdatePriorityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceClaimUpdatePriorityConfig)
        _require_public_label("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_update_age_seconds",
            _normalize_positive_decimal(
                "max_update_age_seconds",
                self.max_update_age_seconds,
            ),
        )
        for field_name in (
            "component_watch_threshold",
            "component_block_threshold",
            "priority_watch_threshold",
            "priority_block_threshold",
            "freshness_weight",
            "authority_weight",
            "independence_weight",
            "contradiction_weight",
            "domain_relevance_weight",
            "resolution_rule_linkage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.component_block_threshold <= self.component_watch_threshold:
            raise ValueError(
                "component_block_threshold must exceed component_watch_threshold",
            )
        if self.priority_block_threshold <= self.priority_watch_threshold:
            raise ValueError("priority_block_threshold must exceed priority_watch_threshold")
        _require_weight_sum(self)
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimUpdatePriorityObservation:
    update_label: str
    source_family_label: str
    domain_bucket: str
    observed_at: datetime
    authority_score: Decimal
    independent_source_count: Decimal
    expected_independent_source_count: Decimal
    contradiction_severity: Decimal
    domain_relevance_score: Decimal
    resolution_rule_linkage_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimUpdatePriorityObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("observation", self, ResearchSourceClaimUpdatePriorityObservation)
        for field_name in ("update_label", "source_family_label", "domain_bucket"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "contradiction_severity",
            "domain_relevance_score",
            "resolution_rule_linkage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_nonnegative_whole_decimal(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "expected_independent_source_count",
            _normalize_positive_whole_decimal(
                "expected_independent_source_count",
                self.expected_independent_source_count,
            ),
        )
        if self.independent_source_count > self.expected_independent_source_count:
            raise ValueError(
                "independent_source_count must not exceed "
                "expected_independent_source_count",
            )
        _reject_unsafe_public_payload("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceClaimUpdatePriorityRow:
    config_version: str
    priority_rank: Decimal
    update_label: str
    source_family_label: str
    domain_bucket: str
    observed_at: datetime
    update_age_seconds: Decimal
    freshness_score: Decimal
    authority_score: Decimal
    independent_source_count: Decimal
    expected_independent_source_count: Decimal
    independence_score: Decimal
    contradiction_severity: Decimal
    domain_relevance_score: Decimal
    resolution_rule_linkage_score: Decimal
    analyst_update_priority_score: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimUpdatePriorityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceClaimUpdatePriorityRow)
        for field_name in (
            "config_version",
            "update_label",
            "source_family_label",
            "domain_bucket",
        ):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("priority_rank", "update_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_score",
            "authority_score",
            "independence_score",
            "contradiction_severity",
            "domain_relevance_score",
            "resolution_rule_linkage_score",
            "analyst_update_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_nonnegative_whole_decimal(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "expected_independent_source_count",
            _normalize_positive_whole_decimal(
                "expected_independent_source_count",
                self.expected_independent_source_count,
            ),
        )
        _require_status("priority_status", self.priority_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_consistency(self)
        _validate_row_derived_validation_digest(self)


@dataclass(frozen=True)
class ResearchSourceClaimUpdatePriorityReport:
    config_version: str
    generated_at: datetime
    status: str
    update_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_analyst_update_priority_score: Decimal
    max_analyst_update_priority_score: Decimal
    max_contradiction_severity: Decimal
    average_freshness_score: Decimal
    average_authority_score: Decimal
    average_independence_score: Decimal
    average_domain_relevance_score: Decimal
    average_resolution_rule_linkage_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceClaimUpdatePriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimUpdatePriorityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceClaimUpdatePriorityReport)
        _require_public_label("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in ("update_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_analyst_update_priority_score",
            "max_analyst_update_priority_score",
            "max_contradiction_severity",
            "average_freshness_score",
            "average_authority_score",
            "average_independence_score",
            "average_domain_relevance_score",
            "average_resolution_rule_linkage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_consistency(self)
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_source_claim_update_priority_report_payload(self)


def build_research_source_claim_update_priority_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimUpdatePriorityConfig | None = None,
) -> ResearchSourceClaimUpdatePriorityReport:
    """Build a deterministic local priority report for source-claim updates."""

    if config is None:
        config = ResearchSourceClaimUpdatePriorityConfig()
    _require_exact_type("config", config, ResearchSourceClaimUpdatePriorityConfig)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _reject_future_observations(normalized_observations, generated_at_utc)

    ranked_metrics = tuple(
        sorted(
            (
                _metrics_from_observation(
                    observation,
                    generated_at=generated_at_utc,
                    config=config,
                )
                for observation in normalized_observations
            ),
            key=_metrics_sort_key,
        ),
    )
    rows = tuple(
        ResearchSourceClaimUpdatePriorityRow(
            priority_rank=_count(index),
            **metrics,
        )
        for index, metrics in enumerate(ranked_metrics, start=1)
    )
    return ResearchSourceClaimUpdatePriorityReport(
        config_version=config.config_version,
        generated_at=generated_at_utc,
        status=_report_status(rows),
        update_count=_count(len(normalized_observations)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        block_count=_row_status_count(rows, "block"),
        average_analyst_update_priority_score=_average(
            tuple(row.analyst_update_priority_score for row in rows),
        ),
        max_analyst_update_priority_score=_max_decimal(
            tuple(row.analyst_update_priority_score for row in rows),
        ),
        max_contradiction_severity=_max_decimal(
            tuple(row.contradiction_severity for row in rows),
        ),
        average_freshness_score=_average(tuple(row.freshness_score for row in rows)),
        average_authority_score=_average(tuple(row.authority_score for row in rows)),
        average_independence_score=_average(
            tuple(row.independence_score for row in rows),
        ),
        average_domain_relevance_score=_average(
            tuple(row.domain_relevance_score for row in rows),
        ),
        average_resolution_rule_linkage_score=_average(
            tuple(row.resolution_rule_linkage_score for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_claim_update_priority_report_payload(
    report: ResearchSourceClaimUpdatePriorityReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceClaimUpdatePriorityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError("report must be a ResearchSourceClaimUpdatePriorityReport")


def research_source_claim_update_priority_report_digest(
    report: ResearchSourceClaimUpdatePriorityReport,
) -> str:
    if type(report) is not ResearchSourceClaimUpdatePriorityReport:
        raise ValueError("report must be a ResearchSourceClaimUpdatePriorityReport")
    _require_hard_flags("report", report)
    _validate_report_derived_validation_digest(report)
    return report.derived_validation_digest


def validate_research_source_claim_update_priority_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload("payload", payload)
        _validate_public_report_payload(payload)
        return True
    except (TypeError, ValueError):
        return False


def _metrics_from_observation(
    observation: ResearchSourceClaimUpdatePriorityObservation,
    *,
    generated_at: datetime,
    config: ResearchSourceClaimUpdatePriorityConfig,
) -> dict[str, Any]:
    update_age_seconds = _datetime_delta_seconds(generated_at, observation.observed_at)
    freshness_score = _cap_probability(
        ONE - _ratio_raw(update_age_seconds, config.max_update_age_seconds),
    )
    independence_score = _ratio(
        observation.independent_source_count,
        observation.expected_independent_source_count,
    )
    analyst_update_priority_score = _weighted_analyst_update_priority_score(
        freshness_score=freshness_score,
        authority_score=observation.authority_score,
        independence_score=independence_score,
        contradiction_severity=observation.contradiction_severity,
        domain_relevance_score=observation.domain_relevance_score,
        resolution_rule_linkage_score=observation.resolution_rule_linkage_score,
        config=config,
    )
    priority_status = _priority_status(
        analyst_update_priority_score,
        component_values=(
            freshness_score,
            observation.authority_score,
            independence_score,
            observation.contradiction_severity,
            observation.domain_relevance_score,
            observation.resolution_rule_linkage_score,
        ),
        config=config,
    )
    return {
        "config_version": config.config_version,
        "update_label": observation.update_label,
        "source_family_label": observation.source_family_label,
        "domain_bucket": observation.domain_bucket,
        "observed_at": observation.observed_at,
        "update_age_seconds": update_age_seconds,
        "freshness_score": freshness_score,
        "authority_score": observation.authority_score,
        "independent_source_count": observation.independent_source_count,
        "expected_independent_source_count": observation.expected_independent_source_count,
        "independence_score": independence_score,
        "contradiction_severity": observation.contradiction_severity,
        "domain_relevance_score": observation.domain_relevance_score,
        "resolution_rule_linkage_score": observation.resolution_rule_linkage_score,
        "analyst_update_priority_score": analyst_update_priority_score,
        "priority_status": priority_status,
        "reason_codes": _row_reason_codes(
            freshness_score=freshness_score,
            authority_score=observation.authority_score,
            independence_score=independence_score,
            contradiction_severity=observation.contradiction_severity,
            domain_relevance_score=observation.domain_relevance_score,
            resolution_rule_linkage_score=observation.resolution_rule_linkage_score,
            analyst_update_priority_score=analyst_update_priority_score,
            priority_status=priority_status,
            config=config,
        ),
    }


def _weighted_analyst_update_priority_score(
    *,
    freshness_score: Decimal,
    authority_score: Decimal,
    independence_score: Decimal,
    contradiction_severity: Decimal,
    domain_relevance_score: Decimal,
    resolution_rule_linkage_score: Decimal,
    config: ResearchSourceClaimUpdatePriorityConfig,
) -> Decimal:
    return _cap_probability(
        (freshness_score * config.freshness_weight)
        + (authority_score * config.authority_weight)
        + (independence_score * config.independence_weight)
        + (contradiction_severity * config.contradiction_weight)
        + (domain_relevance_score * config.domain_relevance_weight)
        + (resolution_rule_linkage_score * config.resolution_rule_linkage_weight),
    )


def _row_reason_codes(
    *,
    freshness_score: Decimal,
    authority_score: Decimal,
    independence_score: Decimal,
    contradiction_severity: Decimal,
    domain_relevance_score: Decimal,
    resolution_rule_linkage_score: Decimal,
    analyst_update_priority_score: Decimal,
    priority_status: str,
    config: ResearchSourceClaimUpdatePriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_component_reason(reason_codes, "freshness", freshness_score, config)
    _append_component_reason(reason_codes, "authority", authority_score, config)
    _append_component_reason(reason_codes, "independence", independence_score, config)
    _append_component_reason(reason_codes, "contradiction", contradiction_severity, config)
    _append_component_reason(
        reason_codes,
        "domain_relevance",
        domain_relevance_score,
        config,
    )
    _append_component_reason(
        reason_codes,
        "resolution_rule_linkage",
        resolution_rule_linkage_score,
        config,
    )
    if analyst_update_priority_score >= config.priority_block_threshold:
        reason_codes.append("claim_update_priority_block")
    elif analyst_update_priority_score >= config.priority_watch_threshold:
        reason_codes.append("claim_update_priority_watch")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    if priority_status == "pass" and reason_codes != [PASS_REASON_CODE]:
        raise ValueError("pass rows must only use pass reason code")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_component_reason(
    reason_codes: list[str],
    component_name: str,
    component_value: Decimal,
    config: ResearchSourceClaimUpdatePriorityConfig,
) -> None:
    if component_value >= config.component_block_threshold:
        reason_codes.append(f"{component_name}_block")
    elif component_value >= config.component_watch_threshold:
        reason_codes.append(f"{component_name}_watch")


def _priority_status(
    analyst_update_priority_score: Decimal,
    *,
    component_values: tuple[Decimal, ...],
    config: ResearchSourceClaimUpdatePriorityConfig,
) -> str:
    if (
        analyst_update_priority_score >= config.priority_block_threshold
        or any(value >= config.component_block_threshold for value in component_values)
    ):
        return "block"
    if (
        analyst_update_priority_score >= config.priority_watch_threshold
        or any(value >= config.component_watch_threshold for value in component_values)
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceClaimUpdatePriorityRow, ...]) -> str:
    if any(row.priority_status == "block" for row in rows):
        return "block"
    if any(row.priority_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimUpdatePriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON_CODE,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status_count(
    rows: tuple[ResearchSourceClaimUpdatePriorityRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _count(sum(1 for row in rows if row.priority_status == status))


def _metrics_sort_key(metrics: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    return (
        -metrics["analyst_update_priority_score"],
        -metrics["contradiction_severity"],
        metrics["update_label"],
    )


def _row_sort_key(
    row: ResearchSourceClaimUpdatePriorityRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -row.analyst_update_priority_score,
        -row.contradiction_severity,
        row.update_label,
    )


def _report_public_payload_without_digest(
    report: ResearchSourceClaimUpdatePriorityReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "generated_at": _datetime_payload(report.generated_at),
        "status": report.status,
        "update_count": _decimal_payload(report.update_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_analyst_update_priority_score": _decimal_payload(
            report.average_analyst_update_priority_score,
        ),
        "max_analyst_update_priority_score": _decimal_payload(
            report.max_analyst_update_priority_score,
        ),
        "max_contradiction_severity": _decimal_payload(
            report.max_contradiction_severity,
        ),
        "average_freshness_score": _decimal_payload(report.average_freshness_score),
        "average_authority_score": _decimal_payload(report.average_authority_score),
        "average_independence_score": _decimal_payload(
            report.average_independence_score,
        ),
        "average_domain_relevance_score": _decimal_payload(
            report.average_domain_relevance_score,
        ),
        "average_resolution_rule_linkage_score": _decimal_payload(
            report.average_resolution_rule_linkage_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: ResearchSourceClaimUpdatePriorityRow) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchSourceClaimUpdatePriorityRow,
) -> dict[str, object]:
    return {
        "config_version": row.config_version,
        "priority_rank": _decimal_payload(row.priority_rank),
        "update_label": row.update_label,
        "source_family_label": row.source_family_label,
        "domain_bucket": row.domain_bucket,
        "observed_at": _datetime_payload(row.observed_at),
        "update_age_seconds": _decimal_payload(row.update_age_seconds),
        "freshness_score": _decimal_payload(row.freshness_score),
        "authority_score": _decimal_payload(row.authority_score),
        "independent_source_count": _decimal_payload(row.independent_source_count),
        "expected_independent_source_count": _decimal_payload(
            row.expected_independent_source_count,
        ),
        "independence_score": _decimal_payload(row.independence_score),
        "contradiction_severity": _decimal_payload(row.contradiction_severity),
        "domain_relevance_score": _decimal_payload(row.domain_relevance_score),
        "resolution_rule_linkage_score": _decimal_payload(
            row.resolution_rule_linkage_score,
        ),
        "analyst_update_priority_score": _decimal_payload(
            row.analyst_update_priority_score,
        ),
        "priority_status": row.priority_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(row: ResearchSourceClaimUpdatePriorityRow) -> str:
    return _derived_validation_digest(
        "research_source_claim_update_priority_report_row",
        _row_public_payload_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(
    report: ResearchSourceClaimUpdatePriorityReport,
) -> str:
    return _derived_validation_digest(
        "research_source_claim_update_priority_report",
        _report_public_payload_without_digest(report),
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _derived_validation_digest(
    label: str,
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> str:
    canonical = json.dumps(
        {field_name: payload[field_name] for field_name in field_names},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()


def _validate_row_derived_validation_digest(
    row: ResearchSourceClaimUpdatePriorityRow,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchSourceClaimUpdatePriorityReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_row_consistency(row: ResearchSourceClaimUpdatePriorityRow) -> None:
    if row.independent_source_count > row.expected_independent_source_count:
        raise ValueError(
            "independent_source_count must not exceed expected_independent_source_count",
        )
    if row.independence_score != _ratio(
        row.independent_source_count,
        row.expected_independent_source_count,
    ):
        raise ValueError("independence_score must match independent source counts")
    if row.priority_status == "pass" and row.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass rows must only use pass reason code")
    if row.priority_status != "pass" and row.reason_codes == (PASS_REASON_CODE,):
        raise ValueError("non-pass rows must not only use pass reason code")


def _validate_report_consistency(
    report: ResearchSourceClaimUpdatePriorityReport,
) -> None:
    if report.update_count != _count(len(report.rows)):
        raise ValueError("update_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_analyst_update_priority_score != _average(
        tuple(row.analyst_update_priority_score for row in report.rows),
    ):
        raise ValueError("average_analyst_update_priority_score must match rows")
    if report.max_analyst_update_priority_score != _max_decimal(
        tuple(row.analyst_update_priority_score for row in report.rows),
    ):
        raise ValueError("max_analyst_update_priority_score must match rows")
    if report.max_contradiction_severity != _max_decimal(
        tuple(row.contradiction_severity for row in report.rows),
    ):
        raise ValueError("max_contradiction_severity must match rows")
    if report.average_freshness_score != _average(
        tuple(row.freshness_score for row in report.rows),
    ):
        raise ValueError("average_freshness_score must match rows")
    if report.average_authority_score != _average(
        tuple(row.authority_score for row in report.rows),
    ):
        raise ValueError("average_authority_score must match rows")
    if report.average_independence_score != _average(
        tuple(row.independence_score for row in report.rows),
    ):
        raise ValueError("average_independence_score must match rows")
    if report.average_domain_relevance_score != _average(
        tuple(row.domain_relevance_score for row in report.rows),
    ):
        raise ValueError("average_domain_relevance_score must match rows")
    if report.average_resolution_rule_linkage_score != _average(
        tuple(row.resolution_rule_linkage_score for row in report.rows),
    ):
        raise ValueError("average_resolution_rule_linkage_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for expected_rank, row in enumerate(report.rows, start=1):
        if row.priority_rank != _count(expected_rank):
            raise ValueError("priority_rank values must match row order")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_PAYLOAD_FIELDS, "report")
    _require_public_label("config_version", payload["config_version"])
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_status("status", payload["status"])
    for field_name in ("update_count", "pass_count", "watch_count", "block_count"):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "average_analyst_update_priority_score",
        "max_analyst_update_priority_score",
        "max_contradiction_severity",
        "average_freshness_score",
        "average_authority_score",
        "average_independence_score",
        "average_domain_relevance_score",
        "average_resolution_rule_linkage_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain row payload dictionaries")
        _reject_unsafe_public_payload("row payload", row_payload)
        _validate_public_row_payload(row_payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_source_claim_update_priority_report",
        payload,
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_ROW_PAYLOAD_FIELDS, "row")
    for field_name in (
        "config_version",
        "update_label",
        "source_family_label",
        "domain_bucket",
    ):
        _require_public_label(field_name, payload[field_name])
    _require_datetime_payload_string("observed_at", payload["observed_at"])
    for field_name in (
        "priority_rank",
        "update_age_seconds",
        "independent_source_count",
        "expected_independent_source_count",
    ):
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            whole=field_name
            in {
                "priority_rank",
                "independent_source_count",
                "expected_independent_source_count",
            },
        )
    for field_name in (
        "freshness_score",
        "authority_score",
        "independence_score",
        "contradiction_severity",
        "domain_relevance_score",
        "resolution_rule_linkage_score",
        "analyst_update_priority_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_status("priority_status", payload["priority_status"])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_source_claim_update_priority_report_row",
        payload,
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match row payload fields")


def _require_exact_payload_fields(
    payload: dict[str, object],
    field_names: tuple[str, ...],
    label: str,
) -> None:
    missing = [field_name for field_name in field_names if field_name not in payload]
    if missing:
        raise ValueError(f"{missing[0]} is required")
    extra = sorted(set(payload) - set(field_names))
    if extra:
        raise ValueError(f"unexpected {label} payload field: {extra[0]}")


def _normalize_observations(
    values: Iterable[object],
) -> tuple[ResearchSourceClaimUpdatePriorityObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceClaimUpdatePriorityObservation] = []
    for observation in observations:
        _require_exact_type("observation", observation, ResearchSourceClaimUpdatePriorityObservation)
        _reject_unsafe_public_payload("observation", observation)
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.update_label,
                observation.source_family_label,
                observation.domain_bucket,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceClaimUpdatePriorityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchSourceClaimUpdatePriorityRow] = []
    for row in value:
        _require_exact_type("row", row, ResearchSourceClaimUpdatePriorityRow)
        _require_hard_flags("row", row)
        _validate_row_derived_validation_digest(row)
        rows.append(row)
    return tuple(sorted(rows, key=_row_sort_key))


def _reject_future_observations(
    observations: tuple[ResearchSourceClaimUpdatePriorityObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _require_weight_sum(config: ResearchSourceClaimUpdatePriorityConfig) -> None:
    weight_sum = _quantize_decimal(
        config.freshness_weight
        + config.authority_weight
        + config.independence_weight
        + config.contradiction_weight
        + config.domain_relevance_weight
        + config.resolution_rule_linkage_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to one")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _cap_probability(_ratio_raw(numerator, denominator))


def _ratio_raw(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return numerator / denominator


def _cap_probability(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECOND_DIVISOR
    return _quantize_decimal(seconds + microseconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_label(field_name, reason_code)
        if reason_code not in SAFE_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in SAFE_REASON_CODES if reason_code in seen)


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    codes: list[str] = []
    for reason_code in value:
        _require_public_label(field_name, reason_code)
        if reason_code not in SAFE_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        codes.append(reason_code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(codes)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


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


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_payload(value: Decimal) -> str:
    return str(_normalize_decimal("payload numeric", value))


def _datetime_payload(value: datetime) -> str:
    return _as_utc("payload datetime", value).isoformat()


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    whole: bool = False,
    probability: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal payload string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal payload string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime payload string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime payload string") from exc
    return _as_utc(field_name, parsed)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_string(label, field.name, is_key=True)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(label, key, is_key=True)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(
    field_name: str,
    value: str,
    *,
    is_key: bool = False,
) -> None:
    lowered = value.lower()
    fragments = UNSAFE_KEY_FRAGMENTS if is_key else UNSAFE_VALUE_FRAGMENTS
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"unsafe public value in {field_name}")
    if not is_key and (DOMAIN_LIKE_RE.search(lowered) or RAW_PUBLIC_ID_RE.search(lowered)):
        raise ValueError(f"unsafe public value in {field_name}")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
