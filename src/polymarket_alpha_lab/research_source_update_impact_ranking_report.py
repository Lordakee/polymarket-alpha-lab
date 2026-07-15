"""Pure in-memory source update probability-review impact ranking report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


DEFAULT_RESEARCH_SOURCE_UPDATE_IMPACT_RANKING_CONFIG_VERSION = (
    "research-source-update-impact-ranking-report-v0"
)

IMPACT_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "source_update_impact_ranking_pass"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_DECIMAL_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{6}$")
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
PRIVATE_SOURCE_MARKERS = (
    "private",
    "confidential",
    "invite_only",
    "secret",
    "internal",
    "restricted",
    "discord",
    "telegram",
    "slack",
    "email",
)
REDACTED_PRIVATE_SOURCE_FAMILY_LABEL = "private_source_redacted"

CONFIG_PROBABILITY_FIELDS = (
    "component_watch_threshold",
    "component_block_threshold",
    "impact_watch_threshold",
    "impact_block_threshold",
    "freshness_weight",
    "authority_weight",
    "independence_weight",
    "contradiction_weight",
    "domain_relevance_weight",
    "resolution_rule_connection_weight",
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
    "resolution_rule_connection_watch",
    "resolution_rule_connection_block",
    "probability_review_impact_watch",
    "probability_review_impact_block",
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
    "resolution_rule_connection_score",
    "probability_review_impact_score",
    "impact_status",
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
    "max_update_age_seconds",
    *CONFIG_PROBABILITY_FIELDS,
    "generated_at",
    "status",
    "update_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_probability_review_impact_score",
    "max_probability_review_impact_score",
    "max_contradiction_severity",
    "average_freshness_score",
    "average_authority_score",
    "average_independence_score",
    "average_domain_relevance_score",
    "average_resolution_rule_connection_score",
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
    "DEFAULT_RESEARCH_SOURCE_UPDATE_IMPACT_RANKING_CONFIG_VERSION",
    "IMPACT_STATUSES",
    "ResearchSourceUpdateImpactObservation",
    "ResearchSourceUpdateImpactRankingConfig",
    "ResearchSourceUpdateImpactRankingReport",
    "ResearchSourceUpdateImpactRankingRow",
    "build_research_source_update_impact_ranking_report",
    "research_source_update_impact_ranking_report_digest",
    "research_source_update_impact_ranking_report_payload",
    "validate_research_source_update_impact_ranking_public_payload",
)


@final
@dataclass(frozen=True, slots=True)
class ResearchSourceUpdateImpactRankingConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_UPDATE_IMPACT_RANKING_CONFIG_VERSION
    max_update_age_seconds: Decimal = Decimal("7200.000000")
    component_watch_threshold: Decimal = Decimal("0.500000")
    component_block_threshold: Decimal = Decimal("0.800000")
    impact_watch_threshold: Decimal = Decimal("0.350000")
    impact_block_threshold: Decimal = Decimal("0.700000")
    freshness_weight: Decimal = Decimal("0.150000")
    authority_weight: Decimal = Decimal("0.200000")
    independence_weight: Decimal = Decimal("0.150000")
    contradiction_weight: Decimal = Decimal("0.200000")
    domain_relevance_weight: Decimal = Decimal("0.150000")
    resolution_rule_connection_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchSourceUpdateImpactRankingConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceUpdateImpactRankingConfig)
        _require_public_label("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_update_age_seconds",
            _normalize_positive_decimal(
                "max_update_age_seconds",
                self.max_update_age_seconds,
            ),
        )
        for field_name in CONFIG_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.component_block_threshold <= self.component_watch_threshold:
            raise ValueError(
                "component_block_threshold must exceed component_watch_threshold",
            )
        if self.impact_block_threshold <= self.impact_watch_threshold:
            raise ValueError("impact_block_threshold must exceed impact_watch_threshold")
        _require_weight_sum(self)
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchSourceUpdateImpactObservation:
    update_label: str
    source_family_label: str
    domain_bucket: str
    observed_at: datetime
    authority_score: Decimal
    independent_source_count: Decimal
    expected_independent_source_count: Decimal
    contradiction_severity: Decimal
    domain_relevance_score: Decimal
    resolution_rule_connection_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchSourceUpdateImpactObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("observation", self, ResearchSourceUpdateImpactObservation)
        for field_name in ("update_label", "domain_bucket"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_family_label",
            _normalize_source_family_label(self.source_family_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "contradiction_severity",
            "domain_relevance_score",
            "resolution_rule_connection_score",
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


@final
@dataclass(frozen=True, slots=True)
class ResearchSourceUpdateImpactRankingRow:
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
    resolution_rule_connection_score: Decimal
    probability_review_impact_score: Decimal
    impact_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchSourceUpdateImpactRankingRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceUpdateImpactRankingRow)
        for field_name in ("config_version", "update_label", "domain_bucket"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_family_label",
            _normalize_source_family_label(self.source_family_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_whole_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "update_age_seconds",
            _normalize_nonnegative_decimal(
                "update_age_seconds",
                self.update_age_seconds,
            ),
        )
        for field_name in (
            "freshness_score",
            "authority_score",
            "independence_score",
            "contradiction_severity",
            "domain_relevance_score",
            "resolution_rule_connection_score",
            "probability_review_impact_score",
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
        _require_status("impact_status", self.impact_status)
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
        _validate_row_derived_validation_digest(self)
        _validate_row_consistency(self)


@final
@dataclass(frozen=True, slots=True)
class ResearchSourceUpdateImpactRankingReport:
    config_version: str
    max_update_age_seconds: Decimal
    component_watch_threshold: Decimal
    component_block_threshold: Decimal
    impact_watch_threshold: Decimal
    impact_block_threshold: Decimal
    freshness_weight: Decimal
    authority_weight: Decimal
    independence_weight: Decimal
    contradiction_weight: Decimal
    domain_relevance_weight: Decimal
    resolution_rule_connection_weight: Decimal
    generated_at: datetime
    status: str
    update_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_probability_review_impact_score: Decimal
    max_probability_review_impact_score: Decimal
    max_contradiction_severity: Decimal
    average_freshness_score: Decimal
    average_authority_score: Decimal
    average_independence_score: Decimal
    average_domain_relevance_score: Decimal
    average_resolution_rule_connection_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceUpdateImpactRankingRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchSourceUpdateImpactRankingReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceUpdateImpactRankingReport)
        _require_public_label("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_update_age_seconds",
            _normalize_positive_decimal(
                "max_update_age_seconds",
                self.max_update_age_seconds,
            ),
        )
        for field_name in CONFIG_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.component_block_threshold <= self.component_watch_threshold:
            raise ValueError(
                "component_block_threshold must exceed component_watch_threshold",
            )
        if self.impact_block_threshold <= self.impact_watch_threshold:
            raise ValueError("impact_block_threshold must exceed impact_watch_threshold")
        _require_weight_sum(self)
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
            "average_probability_review_impact_score",
            "max_probability_review_impact_score",
            "max_contradiction_severity",
            "average_freshness_score",
            "average_authority_score",
            "average_independence_score",
            "average_domain_relevance_score",
            "average_resolution_rule_connection_score",
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
        _validate_report_derived_validation_digest(self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_source_update_impact_ranking_report_payload(self)


def build_research_source_update_impact_ranking_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceUpdateImpactRankingConfig | None = None,
) -> ResearchSourceUpdateImpactRankingReport:
    """Build a deterministic local ranking of source updates for probability review."""

    if config is None:
        config = ResearchSourceUpdateImpactRankingConfig()
    config = _revalidate_config(config)
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
        ResearchSourceUpdateImpactRankingRow(
            priority_rank=_count(index),
            **metrics,
        )
        for index, metrics in enumerate(ranked_metrics, start=1)
    )
    return ResearchSourceUpdateImpactRankingReport(
        config_version=config.config_version,
        max_update_age_seconds=config.max_update_age_seconds,
        component_watch_threshold=config.component_watch_threshold,
        component_block_threshold=config.component_block_threshold,
        impact_watch_threshold=config.impact_watch_threshold,
        impact_block_threshold=config.impact_block_threshold,
        freshness_weight=config.freshness_weight,
        authority_weight=config.authority_weight,
        independence_weight=config.independence_weight,
        contradiction_weight=config.contradiction_weight,
        domain_relevance_weight=config.domain_relevance_weight,
        resolution_rule_connection_weight=config.resolution_rule_connection_weight,
        generated_at=generated_at_utc,
        status=_report_status(rows),
        update_count=_count(len(normalized_observations)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        block_count=_row_status_count(rows, "block"),
        average_probability_review_impact_score=_average(
            tuple(row.probability_review_impact_score for row in rows),
        ),
        max_probability_review_impact_score=_max_decimal(
            tuple(row.probability_review_impact_score for row in rows),
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
        average_resolution_rule_connection_score=_average(
            tuple(row.resolution_rule_connection_score for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_update_impact_ranking_report_payload(
    report: ResearchSourceUpdateImpactRankingReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceUpdateImpactRankingReport:
        _validate_report_for_public_use(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        validated_report = _report_from_public_payload(report)
        return _report_public_payload(validated_report)
    raise ValueError("report must be a ResearchSourceUpdateImpactRankingReport")


def research_source_update_impact_ranking_report_digest(
    report: ResearchSourceUpdateImpactRankingReport,
) -> str:
    if type(report) is not ResearchSourceUpdateImpactRankingReport:
        raise ValueError("report must be a ResearchSourceUpdateImpactRankingReport")
    _validate_report_for_public_use(report)
    return report.derived_validation_digest


def validate_research_source_update_impact_ranking_public_payload(payload: object) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload("payload", payload)
        _validate_public_report_payload(payload)
        return True
    except (TypeError, ValueError):
        return False


def _metrics_from_observation(
    observation: ResearchSourceUpdateImpactObservation,
    *,
    generated_at: datetime,
    config: ResearchSourceUpdateImpactRankingConfig,
) -> dict[str, Any]:
    update_age_seconds = _datetime_delta_seconds(generated_at, observation.observed_at)
    freshness_score = _freshness_score(
        update_age_seconds,
        config.max_update_age_seconds,
    )
    independence_score = _ratio(
        observation.independent_source_count,
        observation.expected_independent_source_count,
    )
    probability_review_impact_score = _weighted_probability_review_impact_score(
        freshness_score=freshness_score,
        authority_score=observation.authority_score,
        independence_score=independence_score,
        contradiction_severity=observation.contradiction_severity,
        domain_relevance_score=observation.domain_relevance_score,
        resolution_rule_connection_score=observation.resolution_rule_connection_score,
        config=config,
    )
    impact_status = _impact_status(
        probability_review_impact_score,
        component_values=(
            freshness_score,
            observation.authority_score,
            independence_score,
            observation.contradiction_severity,
            observation.domain_relevance_score,
            observation.resolution_rule_connection_score,
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
        "resolution_rule_connection_score": observation.resolution_rule_connection_score,
        "probability_review_impact_score": probability_review_impact_score,
        "impact_status": impact_status,
        "reason_codes": _row_reason_codes(
            freshness_score=freshness_score,
            authority_score=observation.authority_score,
            independence_score=independence_score,
            contradiction_severity=observation.contradiction_severity,
            domain_relevance_score=observation.domain_relevance_score,
            resolution_rule_connection_score=observation.resolution_rule_connection_score,
            probability_review_impact_score=probability_review_impact_score,
            impact_status=impact_status,
            config=config,
        ),
    }


def _freshness_score(
    update_age_seconds: Decimal,
    max_update_age_seconds: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _cap_probability(
            ONE - _ratio_raw(update_age_seconds, max_update_age_seconds),
        )


def _weighted_probability_review_impact_score(
    *,
    freshness_score: Decimal,
    authority_score: Decimal,
    independence_score: Decimal,
    contradiction_severity: Decimal,
    domain_relevance_score: Decimal,
    resolution_rule_connection_score: Decimal,
    config: ResearchSourceUpdateImpactRankingConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _cap_probability(
            (freshness_score * config.freshness_weight)
            + (authority_score * config.authority_weight)
            + (independence_score * config.independence_weight)
            + (contradiction_severity * config.contradiction_weight)
            + (domain_relevance_score * config.domain_relevance_weight)
            + (
                resolution_rule_connection_score
                * config.resolution_rule_connection_weight
            ),
        )


def _row_reason_codes(
    *,
    freshness_score: Decimal,
    authority_score: Decimal,
    independence_score: Decimal,
    contradiction_severity: Decimal,
    domain_relevance_score: Decimal,
    resolution_rule_connection_score: Decimal,
    probability_review_impact_score: Decimal,
    impact_status: str,
    config: ResearchSourceUpdateImpactRankingConfig,
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
        "resolution_rule_connection",
        resolution_rule_connection_score,
        config,
    )
    if probability_review_impact_score >= config.impact_block_threshold:
        reason_codes.append("probability_review_impact_block")
    elif probability_review_impact_score >= config.impact_watch_threshold:
        reason_codes.append("probability_review_impact_watch")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    if impact_status == "pass" and reason_codes != [PASS_REASON_CODE]:
        raise ValueError("pass rows must only use pass reason code")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_component_reason(
    reason_codes: list[str],
    component_name: str,
    component_value: Decimal,
    config: ResearchSourceUpdateImpactRankingConfig,
) -> None:
    if component_value >= config.component_block_threshold:
        reason_codes.append(f"{component_name}_block")
    elif component_value >= config.component_watch_threshold:
        reason_codes.append(f"{component_name}_watch")


def _impact_status(
    probability_review_impact_score: Decimal,
    *,
    component_values: tuple[Decimal, ...],
    config: ResearchSourceUpdateImpactRankingConfig,
) -> str:
    if (
        probability_review_impact_score >= config.impact_block_threshold
        or any(value >= config.component_block_threshold for value in component_values)
    ):
        return "block"
    if (
        probability_review_impact_score >= config.impact_watch_threshold
        or any(value >= config.component_watch_threshold for value in component_values)
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceUpdateImpactRankingRow, ...]) -> str:
    if any(row.impact_status == "block" for row in rows):
        return "block"
    if any(row.impact_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceUpdateImpactRankingRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON_CODE,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status_count(
    rows: tuple[ResearchSourceUpdateImpactRankingRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _count(sum(1 for row in rows if row.impact_status == status))


def _metrics_sort_key(metrics: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -metrics["probability_review_impact_score"],
        -metrics["contradiction_severity"],
        metrics["update_label"],
        metrics["source_family_label"],
        metrics["domain_bucket"],
        metrics["observed_at"],
        -metrics["freshness_score"],
        -metrics["authority_score"],
        -metrics["independence_score"],
        -metrics["domain_relevance_score"],
        -metrics["resolution_rule_connection_score"],
        metrics["independent_source_count"],
        metrics["expected_independent_source_count"],
    )


def _row_sort_key(
    row: ResearchSourceUpdateImpactRankingRow,
) -> tuple[Any, ...]:
    return (
        -row.probability_review_impact_score,
        -row.contradiction_severity,
        row.update_label,
        row.source_family_label,
        row.domain_bucket,
        row.observed_at,
        -row.freshness_score,
        -row.authority_score,
        -row.independence_score,
        -row.domain_relevance_score,
        -row.resolution_rule_connection_score,
        row.independent_source_count,
        row.expected_independent_source_count,
    )


def _report_public_payload_without_digest(
    report: ResearchSourceUpdateImpactRankingReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "max_update_age_seconds": _decimal_payload(report.max_update_age_seconds),
        "component_watch_threshold": _decimal_payload(
            report.component_watch_threshold,
        ),
        "component_block_threshold": _decimal_payload(
            report.component_block_threshold,
        ),
        "impact_watch_threshold": _decimal_payload(report.impact_watch_threshold),
        "impact_block_threshold": _decimal_payload(report.impact_block_threshold),
        "freshness_weight": _decimal_payload(report.freshness_weight),
        "authority_weight": _decimal_payload(report.authority_weight),
        "independence_weight": _decimal_payload(report.independence_weight),
        "contradiction_weight": _decimal_payload(report.contradiction_weight),
        "domain_relevance_weight": _decimal_payload(
            report.domain_relevance_weight,
        ),
        "resolution_rule_connection_weight": _decimal_payload(
            report.resolution_rule_connection_weight,
        ),
        "generated_at": _datetime_payload(report.generated_at),
        "status": report.status,
        "update_count": _decimal_payload(report.update_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_probability_review_impact_score": _decimal_payload(
            report.average_probability_review_impact_score,
        ),
        "max_probability_review_impact_score": _decimal_payload(
            report.max_probability_review_impact_score,
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
        "average_resolution_rule_connection_score": _decimal_payload(
            report.average_resolution_rule_connection_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_public_payload(
    report: ResearchSourceUpdateImpactRankingReport,
) -> dict[str, object]:
    _validate_report_derived_validation_digest(report)
    payload = _report_public_payload_without_digest(report)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _row_public_payload(row: ResearchSourceUpdateImpactRankingRow) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchSourceUpdateImpactRankingRow,
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
        "resolution_rule_connection_score": _decimal_payload(
            row.resolution_rule_connection_score,
        ),
        "probability_review_impact_score": _decimal_payload(
            row.probability_review_impact_score,
        ),
        "impact_status": row.impact_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(row: ResearchSourceUpdateImpactRankingRow) -> str:
    return _derived_validation_digest(
        "research_source_update_impact_ranking_report_row",
        _row_public_payload_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(
    report: ResearchSourceUpdateImpactRankingReport,
) -> str:
    return _derived_validation_digest(
        "research_source_update_impact_ranking_report",
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
    row: ResearchSourceUpdateImpactRankingRow,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchSourceUpdateImpactRankingReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_report_for_public_use(
    report: ResearchSourceUpdateImpactRankingReport,
) -> None:
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _revalidate_report(report)
    _validate_report_consistency(report)
    _validate_report_derived_validation_digest(report)


def _revalidate_report(
    value: object,
) -> ResearchSourceUpdateImpactRankingReport:
    _require_exact_type("report", value, ResearchSourceUpdateImpactRankingReport)
    report = value
    validated = ResearchSourceUpdateImpactRankingReport(
        **{
            field.name: getattr(report, field.name)
            for field in fields(ResearchSourceUpdateImpactRankingReport)
        },
    )
    if validated != report:
        raise ValueError("report must be canonically validated")
    return validated


def _validate_row_consistency(row: ResearchSourceUpdateImpactRankingRow) -> None:
    if row.independent_source_count > row.expected_independent_source_count:
        raise ValueError(
            "independent_source_count must not exceed expected_independent_source_count",
        )
    if row.independence_score != _ratio(
        row.independent_source_count,
        row.expected_independent_source_count,
    ):
        raise ValueError("independence_score must match independent source counts")
    if row.impact_status == "pass" and row.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass rows must only use pass reason code")
    if row.impact_status != "pass" and row.reason_codes == (PASS_REASON_CODE,):
        raise ValueError("non-pass rows must not only use pass reason code")


def _validate_row_metrics(
    row: ResearchSourceUpdateImpactRankingRow,
    *,
    generated_at: datetime,
    config: ResearchSourceUpdateImpactRankingConfig,
) -> None:
    if row.config_version != config.config_version:
        raise ValueError("row config_version must match report config_version")
    if row.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    expected_update_age_seconds = _datetime_delta_seconds(
        generated_at,
        row.observed_at,
    )
    if row.update_age_seconds != expected_update_age_seconds:
        raise ValueError("update_age_seconds must match report timestamps")
    expected_freshness_score = _freshness_score(
        expected_update_age_seconds,
        config.max_update_age_seconds,
    )
    if row.freshness_score != expected_freshness_score:
        raise ValueError("freshness_score must match update age")
    expected_independence_score = _ratio(
        row.independent_source_count,
        row.expected_independent_source_count,
    )
    if row.independence_score != expected_independence_score:
        raise ValueError("independence_score must match independent source counts")
    expected_impact_score = _weighted_probability_review_impact_score(
        freshness_score=expected_freshness_score,
        authority_score=row.authority_score,
        independence_score=expected_independence_score,
        contradiction_severity=row.contradiction_severity,
        domain_relevance_score=row.domain_relevance_score,
        resolution_rule_connection_score=row.resolution_rule_connection_score,
        config=config,
    )
    if row.probability_review_impact_score != expected_impact_score:
        raise ValueError(
            "probability_review_impact_score must match row components",
        )
    component_values = (
        expected_freshness_score,
        row.authority_score,
        expected_independence_score,
        row.contradiction_severity,
        row.domain_relevance_score,
        row.resolution_rule_connection_score,
    )
    expected_status = _impact_status(
        expected_impact_score,
        component_values=component_values,
        config=config,
    )
    if row.impact_status != expected_status:
        raise ValueError("impact_status must match row metrics")
    expected_reason_codes = _row_reason_codes(
        freshness_score=expected_freshness_score,
        authority_score=row.authority_score,
        independence_score=expected_independence_score,
        contradiction_severity=row.contradiction_severity,
        domain_relevance_score=row.domain_relevance_score,
        resolution_rule_connection_score=row.resolution_rule_connection_score,
        probability_review_impact_score=expected_impact_score,
        impact_status=expected_status,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics")


def _report_config(
    report: ResearchSourceUpdateImpactRankingReport,
) -> ResearchSourceUpdateImpactRankingConfig:
    return ResearchSourceUpdateImpactRankingConfig(
        config_version=report.config_version,
        max_update_age_seconds=report.max_update_age_seconds,
        component_watch_threshold=report.component_watch_threshold,
        component_block_threshold=report.component_block_threshold,
        impact_watch_threshold=report.impact_watch_threshold,
        impact_block_threshold=report.impact_block_threshold,
        freshness_weight=report.freshness_weight,
        authority_weight=report.authority_weight,
        independence_weight=report.independence_weight,
        contradiction_weight=report.contradiction_weight,
        domain_relevance_weight=report.domain_relevance_weight,
        resolution_rule_connection_weight=report.resolution_rule_connection_weight,
    )


def _validate_report_consistency(
    report: ResearchSourceUpdateImpactRankingReport,
) -> None:
    config = _report_config(report)
    for row in report.rows:
        _validate_row_metrics(
            row,
            generated_at=report.generated_at,
            config=config,
        )
    if report.update_count != _count(len(report.rows)):
        raise ValueError("update_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_probability_review_impact_score != _average(
        tuple(row.probability_review_impact_score for row in report.rows),
    ):
        raise ValueError("average_probability_review_impact_score must match rows")
    if report.max_probability_review_impact_score != _max_decimal(
        tuple(row.probability_review_impact_score for row in report.rows),
    ):
        raise ValueError("max_probability_review_impact_score must match rows")
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
    if report.average_resolution_rule_connection_score != _average(
        tuple(row.resolution_rule_connection_score for row in report.rows),
    ):
        raise ValueError("average_resolution_rule_connection_score must match rows")
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
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, object],
) -> ResearchSourceUpdateImpactRankingReport:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_PAYLOAD_FIELDS, "report")
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(
        _row_from_public_payload(row_payload, index=index)
        for index, row_payload in enumerate(rows_value)
    )
    return ResearchSourceUpdateImpactRankingReport(
        config_version=_require_public_label(
            "config_version",
            payload["config_version"],
        ),
        max_update_age_seconds=_require_decimal_payload_string(
            "max_update_age_seconds",
            payload["max_update_age_seconds"],
        ),
        component_watch_threshold=_require_decimal_payload_string(
            "component_watch_threshold",
            payload["component_watch_threshold"],
            probability=True,
        ),
        component_block_threshold=_require_decimal_payload_string(
            "component_block_threshold",
            payload["component_block_threshold"],
            probability=True,
        ),
        impact_watch_threshold=_require_decimal_payload_string(
            "impact_watch_threshold",
            payload["impact_watch_threshold"],
            probability=True,
        ),
        impact_block_threshold=_require_decimal_payload_string(
            "impact_block_threshold",
            payload["impact_block_threshold"],
            probability=True,
        ),
        freshness_weight=_require_decimal_payload_string(
            "freshness_weight",
            payload["freshness_weight"],
            probability=True,
        ),
        authority_weight=_require_decimal_payload_string(
            "authority_weight",
            payload["authority_weight"],
            probability=True,
        ),
        independence_weight=_require_decimal_payload_string(
            "independence_weight",
            payload["independence_weight"],
            probability=True,
        ),
        contradiction_weight=_require_decimal_payload_string(
            "contradiction_weight",
            payload["contradiction_weight"],
            probability=True,
        ),
        domain_relevance_weight=_require_decimal_payload_string(
            "domain_relevance_weight",
            payload["domain_relevance_weight"],
            probability=True,
        ),
        resolution_rule_connection_weight=_require_decimal_payload_string(
            "resolution_rule_connection_weight",
            payload["resolution_rule_connection_weight"],
            probability=True,
        ),
        generated_at=_require_datetime_payload_string(
            "generated_at",
            payload["generated_at"],
        ),
        status=_require_status("status", payload["status"]),
        update_count=_require_decimal_payload_string(
            "update_count",
            payload["update_count"],
            whole=True,
        ),
        pass_count=_require_decimal_payload_string(
            "pass_count",
            payload["pass_count"],
            whole=True,
        ),
        watch_count=_require_decimal_payload_string(
            "watch_count",
            payload["watch_count"],
            whole=True,
        ),
        block_count=_require_decimal_payload_string(
            "block_count",
            payload["block_count"],
            whole=True,
        ),
        average_probability_review_impact_score=_require_decimal_payload_string(
            "average_probability_review_impact_score",
            payload["average_probability_review_impact_score"],
            probability=True,
        ),
        max_probability_review_impact_score=_require_decimal_payload_string(
            "max_probability_review_impact_score",
            payload["max_probability_review_impact_score"],
            probability=True,
        ),
        max_contradiction_severity=_require_decimal_payload_string(
            "max_contradiction_severity",
            payload["max_contradiction_severity"],
            probability=True,
        ),
        average_freshness_score=_require_decimal_payload_string(
            "average_freshness_score",
            payload["average_freshness_score"],
            probability=True,
        ),
        average_authority_score=_require_decimal_payload_string(
            "average_authority_score",
            payload["average_authority_score"],
            probability=True,
        ),
        average_independence_score=_require_decimal_payload_string(
            "average_independence_score",
            payload["average_independence_score"],
            probability=True,
        ),
        average_domain_relevance_score=_require_decimal_payload_string(
            "average_domain_relevance_score",
            payload["average_domain_relevance_score"],
            probability=True,
        ),
        average_resolution_rule_connection_score=_require_decimal_payload_string(
            "average_resolution_rule_connection_score",
            payload["average_resolution_rule_connection_score"],
            probability=True,
        ),
        reason_codes=_normalize_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        rows=rows,
        derived_validation_digest=_require_sha256_digest(
            DERIVED_VALIDATION_DIGEST_FIELD,
            payload[DERIVED_VALIDATION_DIGEST_FIELD],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchSourceUpdateImpactRankingRow:
    if type(value) is not dict:
        raise ValueError("rows must contain row payload dictionaries")
    payload = value
    _reject_unsafe_public_payload(f"rows[{index}]", payload)
    _require_exact_payload_fields(payload, PUBLIC_ROW_PAYLOAD_FIELDS, "row")
    return ResearchSourceUpdateImpactRankingRow(
        config_version=_require_public_label(
            "config_version",
            payload["config_version"],
        ),
        priority_rank=_require_decimal_payload_string(
            "priority_rank",
            payload["priority_rank"],
            whole=True,
        ),
        update_label=_require_public_label("update_label", payload["update_label"]),
        source_family_label=_require_public_label(
            "source_family_label",
            payload["source_family_label"],
        ),
        domain_bucket=_require_public_label(
            "domain_bucket",
            payload["domain_bucket"],
        ),
        observed_at=_require_datetime_payload_string(
            "observed_at",
            payload["observed_at"],
        ),
        update_age_seconds=_require_decimal_payload_string(
            "update_age_seconds",
            payload["update_age_seconds"],
        ),
        freshness_score=_require_decimal_payload_string(
            "freshness_score",
            payload["freshness_score"],
            probability=True,
        ),
        authority_score=_require_decimal_payload_string(
            "authority_score",
            payload["authority_score"],
            probability=True,
        ),
        independent_source_count=_require_decimal_payload_string(
            "independent_source_count",
            payload["independent_source_count"],
            whole=True,
        ),
        expected_independent_source_count=_require_decimal_payload_string(
            "expected_independent_source_count",
            payload["expected_independent_source_count"],
            whole=True,
        ),
        independence_score=_require_decimal_payload_string(
            "independence_score",
            payload["independence_score"],
            probability=True,
        ),
        contradiction_severity=_require_decimal_payload_string(
            "contradiction_severity",
            payload["contradiction_severity"],
            probability=True,
        ),
        domain_relevance_score=_require_decimal_payload_string(
            "domain_relevance_score",
            payload["domain_relevance_score"],
            probability=True,
        ),
        resolution_rule_connection_score=_require_decimal_payload_string(
            "resolution_rule_connection_score",
            payload["resolution_rule_connection_score"],
            probability=True,
        ),
        probability_review_impact_score=_require_decimal_payload_string(
            "probability_review_impact_score",
            payload["probability_review_impact_score"],
            probability=True,
        ),
        impact_status=_require_status("impact_status", payload["impact_status"]),
        reason_codes=_normalize_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=_require_sha256_digest(
            DERIVED_VALIDATION_DIGEST_FIELD,
            payload[DERIVED_VALIDATION_DIGEST_FIELD],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


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
) -> tuple[ResearchSourceUpdateImpactObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceUpdateImpactObservation] = []
    for observation in observations:
        validated_observation = _revalidate_observation(observation)
        _reject_unsafe_public_payload("observation", validated_observation)
        _require_hard_flags("observation", validated_observation)
        normalized.append(validated_observation)
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
) -> tuple[ResearchSourceUpdateImpactRankingRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchSourceUpdateImpactRankingRow] = []
    for row in value:
        _require_exact_type("row", row, ResearchSourceUpdateImpactRankingRow)
        _require_hard_flags("row", row)
        _validate_row_derived_validation_digest(row)
        rows.append(row)
    return tuple(rows)


def _revalidate_config(
    value: object,
) -> ResearchSourceUpdateImpactRankingConfig:
    _require_exact_type("config", value, ResearchSourceUpdateImpactRankingConfig)
    config = value
    validated = ResearchSourceUpdateImpactRankingConfig(
        config_version=config.config_version,
        max_update_age_seconds=config.max_update_age_seconds,
        component_watch_threshold=config.component_watch_threshold,
        component_block_threshold=config.component_block_threshold,
        impact_watch_threshold=config.impact_watch_threshold,
        impact_block_threshold=config.impact_block_threshold,
        freshness_weight=config.freshness_weight,
        authority_weight=config.authority_weight,
        independence_weight=config.independence_weight,
        contradiction_weight=config.contradiction_weight,
        domain_relevance_weight=config.domain_relevance_weight,
        resolution_rule_connection_weight=config.resolution_rule_connection_weight,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )
    if validated != config:
        raise ValueError("config must be canonically validated")
    return validated


def _revalidate_observation(
    value: object,
) -> ResearchSourceUpdateImpactObservation:
    _require_exact_type("observation", value, ResearchSourceUpdateImpactObservation)
    observation = value
    validated = ResearchSourceUpdateImpactObservation(
        update_label=observation.update_label,
        source_family_label=observation.source_family_label,
        domain_bucket=observation.domain_bucket,
        observed_at=observation.observed_at,
        authority_score=observation.authority_score,
        independent_source_count=observation.independent_source_count,
        expected_independent_source_count=observation.expected_independent_source_count,
        contradiction_severity=observation.contradiction_severity,
        domain_relevance_score=observation.domain_relevance_score,
        resolution_rule_connection_score=observation.resolution_rule_connection_score,
        paper_only=observation.paper_only,
        report_only=observation.report_only,
        readonly=observation.readonly,
    )
    if validated != observation:
        raise ValueError("observation must be canonically validated")
    return validated


def _reject_future_observations(
    observations: tuple[ResearchSourceUpdateImpactObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _require_weight_sum(config: object) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_sum = _quantize_decimal(
            getattr(config, "freshness_weight")
            + getattr(config, "authority_weight")
            + getattr(config, "independence_weight")
            + getattr(config, "contradiction_weight")
            + getattr(config, "domain_relevance_weight")
            + getattr(config, "resolution_rule_connection_weight"),
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
    with localcontext(DECIMAL_CONTEXT):
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
    with localcontext(DECIMAL_CONTEXT):
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
    with localcontext(DECIMAL_CONTEXT):
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


def _normalize_source_family_label(value: object) -> str:
    if type(value) is not str:
        raise ValueError("source_family_label must be a string")
    lowered = value.lower()
    if any(marker in lowered for marker in PRIVATE_SOURCE_MARKERS):
        return REDACTED_PRIVATE_SOURCE_FAMILY_LABEL
    return _require_public_label("source_family_label", value)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in IMPACT_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize_decimal(raw)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(raw)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(raw)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize_decimal(raw)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize_decimal(raw)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_decimal(_require_raw_decimal(field_name, value))


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    if normalized.is_zero() and normalized.is_signed():
        return ZERO
    return normalized


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
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    if CANONICAL_DECIMAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if probability and decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(decimal_value)


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
