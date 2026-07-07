"""Pure Phase 1 source contradiction stoplight reports."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_CONTRADICTION_STOPLIGHT_V2_CONFIG_VERSION = (
    "strategy-recommendation-source-contradiction-stoplight-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MINUS_ONE = Decimal("-1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_ROLES = ("official", "independent", "supporting")
_STOPLIGHT_STATUSES = ("green", "watch", "red")
_STATUS_RANK = {"red": 0, "watch": 1, "green": 2}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REASON_CODE_SEQUENCE = (
    "no_recommendations",
    "no_sources",
    "source_contradiction_count_red",
    "source_contradiction_present",
    "source_contradiction_severity_red",
    "source_contradiction_severity_watch",
    "official_source_conflict",
    "independent_confirmation_gap",
    "source_recency_stale",
    "resolution_rule_ambiguity_red",
    "resolution_rule_ambiguity_watch",
    "cost_adjusted_edge_margin_red",
    "cost_adjusted_edge_margin_watch",
    "source_contradiction_stoplight_green",
)


@dataclass(frozen=True)
class StrategyRecommendationSourceContradictionStoplightV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_CONTRADICTION_STOPLIGHT_V2_CONFIG_VERSION
    )
    red_contradiction_count: Decimal = Decimal("2.000000")
    red_contradiction_severity_score: Decimal = Decimal("0.750000")
    watch_contradiction_severity_score: Decimal = Decimal("0.250000")
    min_independent_confirmations: Decimal = Decimal("2.000000")
    max_source_age_seconds: Decimal = Decimal("3600.000000")
    watch_resolution_rule_ambiguity_score: Decimal = Decimal("0.250000")
    red_resolution_rule_ambiguity_score: Decimal = Decimal("0.750000")
    min_green_cost_adjusted_edge_margin: Decimal = Decimal("0.030000")
    min_watch_cost_adjusted_edge_margin: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationSourceContradictionStoplightV2Config:
            raise TypeError(
                "StrategyRecommendationSourceContradictionStoplightV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyRecommendationSourceContradictionStoplightV2Config,
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_CONTRADICTION_STOPLIGHT_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "red_contradiction_count",
            "min_independent_confirmations",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.red_contradiction_count <= _ZERO:
            raise ValueError("red_contradiction_count must be positive")
        for field_name in (
            "red_contradiction_severity_score",
            "watch_contradiction_severity_score",
            "watch_resolution_rule_ambiguity_score",
            "red_resolution_rule_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "min_green_cost_adjusted_edge_margin",
            "min_watch_cost_adjusted_edge_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_margin_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.watch_contradiction_severity_score
            > self.red_contradiction_severity_score
        ):
            raise ValueError("watch_contradiction_severity_score must not exceed red")
        if (
            self.watch_resolution_rule_ambiguity_score
            > self.red_resolution_rule_ambiguity_score
        ):
            raise ValueError("watch_resolution_rule_ambiguity_score must not exceed red")
        if (
            self.min_watch_cost_adjusted_edge_margin
            > self.min_green_cost_adjusted_edge_margin
        ):
            raise ValueError("min_watch_cost_adjusted_edge_margin must not exceed green")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationSourceContradictionEvidence:
    source_id: str
    source_family: str
    source_role: str
    independence_group: str
    observed_at: datetime
    supports_recommendation: bool
    contradiction_severity_score: Decimal
    resolution_rule_ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationSourceContradictionEvidence:
            raise TypeError(
                "StrategyRecommendationSourceContradictionEvidence does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("source", self, StrategyRecommendationSourceContradictionEvidence)
        for field_name in ("source_id", "source_family", "independence_group"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_source_role("source_role", self.source_role)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("supports_recommendation", self.supports_recommendation)
        object.__setattr__(
            self,
            "contradiction_severity_score",
            _require_probability_decimal(
                "contradiction_severity_score",
                self.contradiction_severity_score,
            ),
        )
        object.__setattr__(
            self,
            "resolution_rule_ambiguity_score",
            _require_probability_decimal(
                "resolution_rule_ambiguity_score",
                self.resolution_rule_ambiguity_score,
            ),
        )
        if self.supports_recommendation and self.contradiction_severity_score != _ZERO:
            raise ValueError(
                "contradiction_severity_score must be zero when support is present",
            )
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class StrategyRecommendationSourceContradictionCandidate:
    recommendation_id: str
    market_slug: str
    side: str
    cost_adjusted_edge_margin: Decimal
    sources: tuple[StrategyRecommendationSourceContradictionEvidence, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationSourceContradictionCandidate:
            raise TypeError(
                "StrategyRecommendationSourceContradictionCandidate does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "candidate",
            self,
            StrategyRecommendationSourceContradictionCandidate,
        )
        for field_name in ("recommendation_id", "market_slug", "side"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "cost_adjusted_edge_margin",
            _require_margin_decimal(
                "cost_adjusted_edge_margin",
                self.cost_adjusted_edge_margin,
            ),
        )
        object.__setattr__(self, "sources", _normalize_sources(self.sources))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationSourceContradictionStoplightRow:
    recommendation_id: str
    market_slug: str
    side: str
    source_count: Decimal
    contradiction_count: Decimal
    official_source_conflict_count: Decimal
    independent_confirmation_count: Decimal
    newest_source_age_seconds: Decimal
    max_source_age_seconds: Decimal
    max_contradiction_severity_score: Decimal
    max_resolution_rule_ambiguity_score: Decimal
    cost_adjusted_edge_margin: Decimal
    stoplight_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationSourceContradictionStoplightRow:
            raise TypeError(
                "StrategyRecommendationSourceContradictionStoplightRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyRecommendationSourceContradictionStoplightRow)
        for field_name in ("recommendation_id", "market_slug", "side"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "source_count",
            "contradiction_count",
            "official_source_conflict_count",
            "independent_confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_source_age_seconds",
            "max_source_age_seconds",
            "max_contradiction_severity_score",
            "max_resolution_rule_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_probability_decimal(
            "max_contradiction_severity_score",
            self.max_contradiction_severity_score,
        )
        _require_probability_decimal(
            "max_resolution_rule_ambiguity_score",
            self.max_resolution_rule_ambiguity_score,
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_margin",
            _require_margin_decimal(
                "cost_adjusted_edge_margin",
                self.cost_adjusted_edge_margin,
            ),
        )
        _require_stoplight_status("stoplight_status", self.stoplight_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_shape(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyRecommendationSourceContradictionStoplightReport:
    generated_at: datetime
    config_version: str
    red_contradiction_count: Decimal
    red_contradiction_severity_score: Decimal
    watch_contradiction_severity_score: Decimal
    min_independent_confirmations: Decimal
    max_allowed_source_age_seconds: Decimal
    watch_resolution_rule_ambiguity_score: Decimal
    red_resolution_rule_ambiguity_score: Decimal
    min_green_cost_adjusted_edge_margin: Decimal
    min_watch_cost_adjusted_edge_margin: Decimal
    stoplight_status: str
    recommendation_count: Decimal
    green_count: Decimal
    watch_count: Decimal
    red_count: Decimal
    source_count: Decimal
    contradiction_count: Decimal
    official_source_conflict_count: Decimal
    independent_confirmation_count: Decimal
    stale_recommendation_count: Decimal
    ambiguous_resolution_rule_count: Decimal
    max_contradiction_severity_score: Decimal
    min_cost_adjusted_edge_margin: Decimal
    rows: tuple[StrategyRecommendationSourceContradictionStoplightRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationSourceContradictionStoplightReport:
            raise TypeError(
                "StrategyRecommendationSourceContradictionStoplightReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyRecommendationSourceContradictionStoplightReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_CONTRADICTION_STOPLIGHT_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "red_contradiction_count",
            _require_nonnegative_count_decimal(
                "red_contradiction_count",
                self.red_contradiction_count,
            ),
        )
        if self.red_contradiction_count <= _ZERO:
            raise ValueError("red_contradiction_count must be positive")
        object.__setattr__(
            self,
            "min_independent_confirmations",
            _require_nonnegative_count_decimal(
                "min_independent_confirmations",
                self.min_independent_confirmations,
            ),
        )
        for field_name in (
            "red_contradiction_severity_score",
            "watch_contradiction_severity_score",
            "watch_resolution_rule_ambiguity_score",
            "red_resolution_rule_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_allowed_source_age_seconds",
            _require_positive_decimal(
                "max_allowed_source_age_seconds",
                self.max_allowed_source_age_seconds,
            ),
        )
        for field_name in (
            "min_green_cost_adjusted_edge_margin",
            "min_watch_cost_adjusted_edge_margin",
            "min_cost_adjusted_edge_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_margin_decimal(field_name, getattr(self, field_name)),
            )
        _require_stoplight_status("stoplight_status", self.stoplight_status)
        for field_name in (
            "recommendation_count",
            "green_count",
            "watch_count",
            "red_count",
            "source_count",
            "contradiction_count",
            "official_source_conflict_count",
            "independent_confirmation_count",
            "stale_recommendation_count",
            "ambiguous_resolution_rule_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_contradiction_severity_score",
            _require_probability_decimal(
                "max_contradiction_severity_score",
                self.max_contradiction_severity_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                _DERIVED_VALIDATION_DIGEST_FIELD,
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                _DERIVED_VALIDATION_DIGEST_FIELD,
                _require_digest(
                    _DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_consistency(self)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest mismatch")

    @property
    def payload(self) -> dict[str, object]:
        return strategy_recommendation_source_contradiction_stoplight_v2_payload(self)


def build_strategy_recommendation_source_contradiction_stoplight_v2(
    candidates: list[StrategyRecommendationSourceContradictionCandidate]
    | tuple[StrategyRecommendationSourceContradictionCandidate, ...],
    *,
    config: StrategyRecommendationSourceContradictionStoplightV2Config,
    generated_at: datetime,
) -> StrategyRecommendationSourceContradictionStoplightReport:
    if type(config) is not StrategyRecommendationSourceContradictionStoplightV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationSourceContradictionStoplightV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for candidate in normalized_candidates:
        for item in candidate.sources:
            if item.observed_at > generated_at_utc:
                raise ValueError("source observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "red_contradiction_count": config.red_contradiction_count,
        "red_contradiction_severity_score": config.red_contradiction_severity_score,
        "watch_contradiction_severity_score": config.watch_contradiction_severity_score,
        "min_independent_confirmations": config.min_independent_confirmations,
        "max_allowed_source_age_seconds": config.max_source_age_seconds,
        "watch_resolution_rule_ambiguity_score": (
            config.watch_resolution_rule_ambiguity_score
        ),
        "red_resolution_rule_ambiguity_score": config.red_resolution_rule_ambiguity_score,
        "min_green_cost_adjusted_edge_margin": (
            config.min_green_cost_adjusted_edge_margin
        ),
        "min_watch_cost_adjusted_edge_margin": (
            config.min_watch_cost_adjusted_edge_margin
        ),
        "stoplight_status": _report_status(rows),
        "recommendation_count": _count(len(rows)),
        "green_count": _count(_status_count(rows, "green")),
        "watch_count": _count(_status_count(rows, "watch")),
        "red_count": _count(_status_count(rows, "red")),
        "source_count": _sum_row_count(rows, "source_count"),
        "contradiction_count": _sum_row_count(rows, "contradiction_count"),
        "official_source_conflict_count": _sum_row_count(
            rows,
            "official_source_conflict_count",
        ),
        "independent_confirmation_count": _sum_row_count(
            rows,
            "independent_confirmation_count",
        ),
        "stale_recommendation_count": _count(
            sum(1 for row in rows if row.max_source_age_seconds > config.max_source_age_seconds),
        ),
        "ambiguous_resolution_rule_count": _count(
            sum(
                1
                for row in rows
                if row.max_resolution_rule_ambiguity_score
                >= config.watch_resolution_rule_ambiguity_score
            ),
        ),
        "max_contradiction_severity_score": _max_decimal(
            tuple(row.max_contradiction_severity_score for row in rows),
        ),
        "min_cost_adjusted_edge_margin": _min_margin(
            tuple(row.cost_adjusted_edge_margin for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationSourceContradictionStoplightReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def strategy_recommendation_source_contradiction_stoplight_v2_payload(
    value: StrategyRecommendationSourceContradictionStoplightReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is StrategyRecommendationSourceContradictionStoplightReport:
        _require_hard_flags("report", value)
        _validate_report_consistency(value)
        if value.derived_validation_digest != _report_digest(value):
            raise ValueError("derived_validation_digest mismatch")
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a StrategyRecommendationSourceContradictionStoplightReport or dict",
        )
    _validate_public_payload_digest(payload)
    return payload


def _row_from_candidate(
    candidate: StrategyRecommendationSourceContradictionCandidate,
    *,
    config: StrategyRecommendationSourceContradictionStoplightV2Config,
    generated_at: datetime,
) -> StrategyRecommendationSourceContradictionStoplightRow:
    source_count = _count(len(candidate.sources))
    contradiction_count = _count(
        sum(1 for item in candidate.sources if not item.supports_recommendation),
    )
    official_conflict_count = _count(
        sum(
            1
            for item in candidate.sources
            if item.source_role == "official" and not item.supports_recommendation
        ),
    )
    independent_confirmations = _count(
        len(
            {
                item.independence_group
                for item in candidate.sources
                if item.source_role == "independent" and item.supports_recommendation
            },
        ),
    )
    ages = tuple(_seconds_between(item.observed_at, generated_at) for item in candidate.sources)
    newest_age = min(ages, default=_ZERO)
    max_age = max(ages, default=_ZERO)
    max_severity = _max_decimal(
        tuple(item.contradiction_severity_score for item in candidate.sources),
    )
    max_ambiguity = _max_decimal(
        tuple(item.resolution_rule_ambiguity_score for item in candidate.sources),
    )
    reason_codes = _row_reason_codes(
        source_count=source_count,
        contradiction_count=contradiction_count,
        official_source_conflict_count=official_conflict_count,
        independent_confirmation_count=independent_confirmations,
        max_source_age_seconds=max_age,
        max_contradiction_severity_score=max_severity,
        max_resolution_rule_ambiguity_score=max_ambiguity,
        cost_adjusted_edge_margin=candidate.cost_adjusted_edge_margin,
        red_contradiction_count=config.red_contradiction_count,
        red_contradiction_severity_score=config.red_contradiction_severity_score,
        watch_contradiction_severity_score=config.watch_contradiction_severity_score,
        min_independent_confirmations=config.min_independent_confirmations,
        max_allowed_source_age_seconds=config.max_source_age_seconds,
        watch_resolution_rule_ambiguity_score=(
            config.watch_resolution_rule_ambiguity_score
        ),
        red_resolution_rule_ambiguity_score=config.red_resolution_rule_ambiguity_score,
        min_green_cost_adjusted_edge_margin=(
            config.min_green_cost_adjusted_edge_margin
        ),
        min_watch_cost_adjusted_edge_margin=(
            config.min_watch_cost_adjusted_edge_margin
        ),
    )
    return StrategyRecommendationSourceContradictionStoplightRow(
        recommendation_id=candidate.recommendation_id,
        market_slug=candidate.market_slug,
        side=candidate.side,
        source_count=source_count,
        contradiction_count=contradiction_count,
        official_source_conflict_count=official_conflict_count,
        independent_confirmation_count=independent_confirmations,
        newest_source_age_seconds=newest_age,
        max_source_age_seconds=max_age,
        max_contradiction_severity_score=max_severity,
        max_resolution_rule_ambiguity_score=max_ambiguity,
        cost_adjusted_edge_margin=candidate.cost_adjusted_edge_margin,
        stoplight_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    contradiction_count: Decimal,
    official_source_conflict_count: Decimal,
    independent_confirmation_count: Decimal,
    max_source_age_seconds: Decimal,
    max_contradiction_severity_score: Decimal,
    max_resolution_rule_ambiguity_score: Decimal,
    cost_adjusted_edge_margin: Decimal,
    red_contradiction_count: Decimal,
    red_contradiction_severity_score: Decimal,
    watch_contradiction_severity_score: Decimal,
    min_independent_confirmations: Decimal,
    max_allowed_source_age_seconds: Decimal,
    watch_resolution_rule_ambiguity_score: Decimal,
    red_resolution_rule_ambiguity_score: Decimal,
    min_green_cost_adjusted_edge_margin: Decimal,
    min_watch_cost_adjusted_edge_margin: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_count == _ZERO:
        reason_codes.append("no_sources")
    if contradiction_count >= red_contradiction_count:
        reason_codes.append("source_contradiction_count_red")
    elif contradiction_count > _ZERO:
        reason_codes.append("source_contradiction_present")
    if max_contradiction_severity_score >= red_contradiction_severity_score:
        reason_codes.append("source_contradiction_severity_red")
    elif max_contradiction_severity_score >= watch_contradiction_severity_score:
        reason_codes.append("source_contradiction_severity_watch")
    if official_source_conflict_count > _ZERO:
        reason_codes.append("official_source_conflict")
    if independent_confirmation_count < min_independent_confirmations:
        reason_codes.append("independent_confirmation_gap")
    if max_source_age_seconds > max_allowed_source_age_seconds:
        reason_codes.append("source_recency_stale")
    if max_resolution_rule_ambiguity_score >= red_resolution_rule_ambiguity_score:
        reason_codes.append("resolution_rule_ambiguity_red")
    elif max_resolution_rule_ambiguity_score >= watch_resolution_rule_ambiguity_score:
        reason_codes.append("resolution_rule_ambiguity_watch")
    if cost_adjusted_edge_margin < min_watch_cost_adjusted_edge_margin:
        reason_codes.append("cost_adjusted_edge_margin_red")
    elif cost_adjusted_edge_margin < min_green_cost_adjusted_edge_margin:
        reason_codes.append("cost_adjusted_edge_margin_watch")
    if not reason_codes:
        reason_codes.append("source_contradiction_stoplight_green")
    return _normalize_reason_codes(tuple(reason_codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            "no_recommendations",
            "no_sources",
            "source_contradiction_count_red",
            "source_contradiction_severity_red",
            "official_source_conflict",
            "resolution_rule_ambiguity_red",
            "cost_adjusted_edge_margin_red",
        )
    ):
        return "red"
    if reason_codes == ("source_contradiction_stoplight_green",):
        return "green"
    return "watch"


def _report_status(
    rows: tuple[StrategyRecommendationSourceContradictionStoplightRow, ...],
) -> str:
    if not rows:
        return "red"
    if any(row.stoplight_status == "red" for row in rows):
        return "red"
    if any(row.stoplight_status == "watch" for row in rows):
        return "watch"
    return "green"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationSourceContradictionStoplightRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_recommendations",)
    codes = tuple(
        code
        for row in rows
        for code in row.reason_codes
        if code != "source_contradiction_stoplight_green"
    )
    if not codes:
        return ("source_contradiction_stoplight_green",)
    return _normalize_reason_codes(codes)


def _status_count(
    rows: tuple[StrategyRecommendationSourceContradictionStoplightRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.stoplight_status == status)


def _row_sort_key(
    row: StrategyRecommendationSourceContradictionStoplightRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _STATUS_RANK[row.stoplight_status],
        -row.max_contradiction_severity_score,
        -row.official_source_conflict_count,
        row.market_slug,
        row.recommendation_id,
    )


def _validate_row_shape(
    row: StrategyRecommendationSourceContradictionStoplightRow,
) -> None:
    if row.contradiction_count > row.source_count:
        raise ValueError("contradiction_count must not exceed source_count")
    if row.official_source_conflict_count > row.contradiction_count:
        raise ValueError("official_source_conflict_count must not exceed contradictions")
    if row.independent_confirmation_count > row.source_count:
        raise ValueError("independent_confirmation_count must not exceed source_count")
    if row.newest_source_age_seconds > row.max_source_age_seconds:
        raise ValueError("newest_source_age_seconds must not exceed max_source_age_seconds")
    if row.stoplight_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("stoplight_status must match reason_codes")


def _validate_report_consistency(
    report: StrategyRecommendationSourceContradictionStoplightReport,
) -> None:
    rows = report.rows
    if report.recommendation_count != _count(len(rows)):
        raise ValueError("recommendation_count must match rows")
    if report.green_count != _count(_status_count(rows, "green")):
        raise ValueError("green_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.red_count != _count(_status_count(rows, "red")):
        raise ValueError("red_count must match rows")
    if report.source_count != _sum_row_count(rows, "source_count"):
        raise ValueError("source_count must match rows")
    if report.contradiction_count != _sum_row_count(rows, "contradiction_count"):
        raise ValueError("contradiction_count must match rows")
    if report.official_source_conflict_count != _sum_row_count(
        rows,
        "official_source_conflict_count",
    ):
        raise ValueError("official_source_conflict_count must match rows")
    if report.independent_confirmation_count != _sum_row_count(
        rows,
        "independent_confirmation_count",
    ):
        raise ValueError("independent_confirmation_count must match rows")
    expected_stale_count = _count(
        sum(
            1
            for row in rows
            if row.max_source_age_seconds > report.max_allowed_source_age_seconds
        ),
    )
    if report.stale_recommendation_count != expected_stale_count:
        raise ValueError("stale_recommendation_count must match rows")
    expected_ambiguous_count = _count(
        sum(
            1
            for row in rows
            if row.max_resolution_rule_ambiguity_score
            >= report.watch_resolution_rule_ambiguity_score
        ),
    )
    if report.ambiguous_resolution_rule_count != expected_ambiguous_count:
        raise ValueError("ambiguous_resolution_rule_count must match rows")
    if report.max_contradiction_severity_score != _max_decimal(
        tuple(row.max_contradiction_severity_score for row in rows),
    ):
        raise ValueError("max_contradiction_severity_score must match rows")
    if report.min_cost_adjusted_edge_margin != _min_margin(
        tuple(row.cost_adjusted_edge_margin for row in rows),
    ):
        raise ValueError("min_cost_adjusted_edge_margin must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    expected_reason_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.stoplight_status != _report_status(rows):
        raise ValueError("stoplight_status must match rows")
    for row in rows:
        expected_row_reason_codes = _row_reason_codes(
            source_count=row.source_count,
            contradiction_count=row.contradiction_count,
            official_source_conflict_count=row.official_source_conflict_count,
            independent_confirmation_count=row.independent_confirmation_count,
            max_source_age_seconds=row.max_source_age_seconds,
            max_contradiction_severity_score=row.max_contradiction_severity_score,
            max_resolution_rule_ambiguity_score=(
                row.max_resolution_rule_ambiguity_score
            ),
            cost_adjusted_edge_margin=row.cost_adjusted_edge_margin,
            red_contradiction_count=report.red_contradiction_count,
            red_contradiction_severity_score=report.red_contradiction_severity_score,
            watch_contradiction_severity_score=(
                report.watch_contradiction_severity_score
            ),
            min_independent_confirmations=report.min_independent_confirmations,
            max_allowed_source_age_seconds=report.max_allowed_source_age_seconds,
            watch_resolution_rule_ambiguity_score=(
                report.watch_resolution_rule_ambiguity_score
            ),
            red_resolution_rule_ambiguity_score=(
                report.red_resolution_rule_ambiguity_score
            ),
            min_green_cost_adjusted_edge_margin=(
                report.min_green_cost_adjusted_edge_margin
            ),
            min_watch_cost_adjusted_edge_margin=(
                report.min_watch_cost_adjusted_edge_margin
            ),
        )
        if row.reason_codes != expected_row_reason_codes:
            raise ValueError("row reason_codes must match stoplight rules")


def _normalize_candidates(value: object) -> tuple[StrategyRecommendationSourceContradictionCandidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    rows = tuple(value)
    recommendation_ids: list[str] = []
    for row in rows:
        if type(row) is not StrategyRecommendationSourceContradictionCandidate:
            raise ValueError(
                "candidates must contain StrategyRecommendationSourceContradictionCandidate",
            )
        _require_hard_flags("candidate", row)
        recommendation_ids.append(row.recommendation_id)
    if len(set(recommendation_ids)) != len(recommendation_ids):
        raise ValueError("recommendation_id values must be unique")
    return tuple(sorted(rows, key=lambda item: (item.market_slug, item.recommendation_id)))


def _normalize_sources(value: object) -> tuple[StrategyRecommendationSourceContradictionEvidence, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    rows = tuple(value)
    source_ids: list[str] = []
    for row in rows:
        if type(row) is not StrategyRecommendationSourceContradictionEvidence:
            raise ValueError(
                "sources must contain StrategyRecommendationSourceContradictionEvidence",
            )
        _require_hard_flags("source", row)
        source_ids.append(row.source_id)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("source_id values must be unique")
    return tuple(sorted(rows, key=lambda item: (item.source_family, item.source_id)))


def _normalize_rows(value: object) -> tuple[StrategyRecommendationSourceContradictionStoplightRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    recommendation_ids: list[str] = []
    for row in rows:
        if type(row) is not StrategyRecommendationSourceContradictionStoplightRow:
            raise ValueError(
                "rows must contain StrategyRecommendationSourceContradictionStoplightRow",
            )
        _require_hard_flags("row", row)
        recommendation_ids.append(row.recommendation_id)
    if len(set(recommendation_ids)) != len(recommendation_ids):
        raise ValueError("rows recommendation_id values must be unique")
    return rows


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        rows = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not rows:
        raise ValueError("reason_codes must not be empty")
    for reason_code in rows:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(rows)) != len(rows):
        raise ValueError("reason_codes must not contain duplicates")
    if "source_contradiction_stoplight_green" in rows and len(rows) > 1:
        raise ValueError("green reason code must not be mixed with issue reasons")
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in rows)


def _report_payload(
    report: StrategyRecommendationSourceContradictionStoplightReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        red_contradiction_count=report.red_contradiction_count,
        red_contradiction_severity_score=report.red_contradiction_severity_score,
        watch_contradiction_severity_score=report.watch_contradiction_severity_score,
        min_independent_confirmations=report.min_independent_confirmations,
        max_allowed_source_age_seconds=report.max_allowed_source_age_seconds,
        watch_resolution_rule_ambiguity_score=(
            report.watch_resolution_rule_ambiguity_score
        ),
        red_resolution_rule_ambiguity_score=report.red_resolution_rule_ambiguity_score,
        min_green_cost_adjusted_edge_margin=(
            report.min_green_cost_adjusted_edge_margin
        ),
        min_watch_cost_adjusted_edge_margin=(
            report.min_watch_cost_adjusted_edge_margin
        ),
        stoplight_status=report.stoplight_status,
        recommendation_count=report.recommendation_count,
        green_count=report.green_count,
        watch_count=report.watch_count,
        red_count=report.red_count,
        source_count=report.source_count,
        contradiction_count=report.contradiction_count,
        official_source_conflict_count=report.official_source_conflict_count,
        independent_confirmation_count=report.independent_confirmation_count,
        stale_recommendation_count=report.stale_recommendation_count,
        ambiguous_resolution_rule_count=report.ambiguous_resolution_rule_count,
        max_contradiction_severity_score=report.max_contradiction_severity_score,
        min_cost_adjusted_edge_margin=report.min_cost_adjusted_edge_margin,
        rows=report.rows,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    red_contradiction_count: Decimal,
    red_contradiction_severity_score: Decimal,
    watch_contradiction_severity_score: Decimal,
    min_independent_confirmations: Decimal,
    max_allowed_source_age_seconds: Decimal,
    watch_resolution_rule_ambiguity_score: Decimal,
    red_resolution_rule_ambiguity_score: Decimal,
    min_green_cost_adjusted_edge_margin: Decimal,
    min_watch_cost_adjusted_edge_margin: Decimal,
    stoplight_status: str,
    recommendation_count: Decimal,
    green_count: Decimal,
    watch_count: Decimal,
    red_count: Decimal,
    source_count: Decimal,
    contradiction_count: Decimal,
    official_source_conflict_count: Decimal,
    independent_confirmation_count: Decimal,
    stale_recommendation_count: Decimal,
    ambiguous_resolution_rule_count: Decimal,
    max_contradiction_severity_score: Decimal,
    min_cost_adjusted_edge_margin: Decimal,
    rows: tuple[StrategyRecommendationSourceContradictionStoplightRow, ...],
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "red_contradiction_count": _json_ready(red_contradiction_count),
        "red_contradiction_severity_score": _json_ready(
            red_contradiction_severity_score,
        ),
        "watch_contradiction_severity_score": _json_ready(
            watch_contradiction_severity_score,
        ),
        "min_independent_confirmations": _json_ready(min_independent_confirmations),
        "max_allowed_source_age_seconds": _json_ready(max_allowed_source_age_seconds),
        "watch_resolution_rule_ambiguity_score": _json_ready(
            watch_resolution_rule_ambiguity_score,
        ),
        "red_resolution_rule_ambiguity_score": _json_ready(
            red_resolution_rule_ambiguity_score,
        ),
        "min_green_cost_adjusted_edge_margin": _json_ready(
            min_green_cost_adjusted_edge_margin,
        ),
        "min_watch_cost_adjusted_edge_margin": _json_ready(
            min_watch_cost_adjusted_edge_margin,
        ),
        "stoplight_status": stoplight_status,
        "recommendation_count": _json_ready(recommendation_count),
        "green_count": _json_ready(green_count),
        "watch_count": _json_ready(watch_count),
        "red_count": _json_ready(red_count),
        "source_count": _json_ready(source_count),
        "contradiction_count": _json_ready(contradiction_count),
        "official_source_conflict_count": _json_ready(official_source_conflict_count),
        "independent_confirmation_count": _json_ready(independent_confirmation_count),
        "stale_recommendation_count": _json_ready(stale_recommendation_count),
        "ambiguous_resolution_rule_count": _json_ready(ambiguous_resolution_rule_count),
        "max_contradiction_severity_score": _json_ready(
            max_contradiction_severity_score,
        ),
        "min_cost_adjusted_edge_margin": _json_ready(min_cost_adjusted_edge_margin),
        "rows": [_row_payload(row) for row in rows],
        "reason_codes": list(reason_codes),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: StrategyRecommendationSourceContradictionStoplightRow) -> dict[str, object]:
    return {
        "recommendation_id": row.recommendation_id,
        "market_slug": row.market_slug,
        "side": row.side,
        "source_count": _json_ready(row.source_count),
        "contradiction_count": _json_ready(row.contradiction_count),
        "official_source_conflict_count": _json_ready(row.official_source_conflict_count),
        "independent_confirmation_count": _json_ready(row.independent_confirmation_count),
        "newest_source_age_seconds": _json_ready(row.newest_source_age_seconds),
        "max_source_age_seconds": _json_ready(row.max_source_age_seconds),
        "max_contradiction_severity_score": _json_ready(
            row.max_contradiction_severity_score,
        ),
        "max_resolution_rule_ambiguity_score": _json_ready(
            row.max_resolution_rule_ambiguity_score,
        ),
        "cost_adjusted_edge_margin": _json_ready(row.cost_adjusted_edge_margin),
        "stoplight_status": row.stoplight_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest(report: StrategyRecommendationSourceContradictionStoplightReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "red_contradiction_count": report.red_contradiction_count,
            "red_contradiction_severity_score": report.red_contradiction_severity_score,
            "watch_contradiction_severity_score": (
                report.watch_contradiction_severity_score
            ),
            "min_independent_confirmations": report.min_independent_confirmations,
            "max_allowed_source_age_seconds": report.max_allowed_source_age_seconds,
            "watch_resolution_rule_ambiguity_score": (
                report.watch_resolution_rule_ambiguity_score
            ),
            "red_resolution_rule_ambiguity_score": (
                report.red_resolution_rule_ambiguity_score
            ),
            "min_green_cost_adjusted_edge_margin": (
                report.min_green_cost_adjusted_edge_margin
            ),
            "min_watch_cost_adjusted_edge_margin": (
                report.min_watch_cost_adjusted_edge_margin
            ),
            "stoplight_status": report.stoplight_status,
            "recommendation_count": report.recommendation_count,
            "green_count": report.green_count,
            "watch_count": report.watch_count,
            "red_count": report.red_count,
            "source_count": report.source_count,
            "contradiction_count": report.contradiction_count,
            "official_source_conflict_count": report.official_source_conflict_count,
            "independent_confirmation_count": report.independent_confirmation_count,
            "stale_recommendation_count": report.stale_recommendation_count,
            "ambiguous_resolution_rule_count": report.ambiguous_resolution_rule_count,
            "max_contradiction_severity_score": report.max_contradiction_severity_score,
            "min_cost_adjusted_edge_margin": report.min_cost_adjusted_edge_margin,
            "rows": report.rows,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        red_contradiction_count=_require_mapping_value(
            values,
            "red_contradiction_count",
            Decimal,
        ),
        red_contradiction_severity_score=_require_mapping_value(
            values,
            "red_contradiction_severity_score",
            Decimal,
        ),
        watch_contradiction_severity_score=_require_mapping_value(
            values,
            "watch_contradiction_severity_score",
            Decimal,
        ),
        min_independent_confirmations=_require_mapping_value(
            values,
            "min_independent_confirmations",
            Decimal,
        ),
        max_allowed_source_age_seconds=_require_mapping_value(
            values,
            "max_allowed_source_age_seconds",
            Decimal,
        ),
        watch_resolution_rule_ambiguity_score=_require_mapping_value(
            values,
            "watch_resolution_rule_ambiguity_score",
            Decimal,
        ),
        red_resolution_rule_ambiguity_score=_require_mapping_value(
            values,
            "red_resolution_rule_ambiguity_score",
            Decimal,
        ),
        min_green_cost_adjusted_edge_margin=_require_mapping_value(
            values,
            "min_green_cost_adjusted_edge_margin",
            Decimal,
        ),
        min_watch_cost_adjusted_edge_margin=_require_mapping_value(
            values,
            "min_watch_cost_adjusted_edge_margin",
            Decimal,
        ),
        stoplight_status=_require_mapping_value(values, "stoplight_status", str),
        recommendation_count=_require_mapping_value(
            values,
            "recommendation_count",
            Decimal,
        ),
        green_count=_require_mapping_value(values, "green_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        red_count=_require_mapping_value(values, "red_count", Decimal),
        source_count=_require_mapping_value(values, "source_count", Decimal),
        contradiction_count=_require_mapping_value(
            values,
            "contradiction_count",
            Decimal,
        ),
        official_source_conflict_count=_require_mapping_value(
            values,
            "official_source_conflict_count",
            Decimal,
        ),
        independent_confirmation_count=_require_mapping_value(
            values,
            "independent_confirmation_count",
            Decimal,
        ),
        stale_recommendation_count=_require_mapping_value(
            values,
            "stale_recommendation_count",
            Decimal,
        ),
        ambiguous_resolution_rule_count=_require_mapping_value(
            values,
            "ambiguous_resolution_rule_count",
            Decimal,
        ),
        max_contradiction_severity_score=_require_mapping_value(
            values,
            "max_contradiction_severity_score",
            Decimal,
        ),
        min_cost_adjusted_edge_margin=_require_mapping_value(
            values,
            "min_cost_adjusted_edge_margin",
            Decimal,
        ),
        rows=_require_mapping_value(values, "rows", tuple),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    provided_digest = _require_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if provided_digest != _digest_json_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")
    _require_payload_ready(payload)
    for flag_name in _PHASE_FLAG_FIELDS:
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _digest_json_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is StrategyRecommendationSourceContradictionStoplightReport:
        return _report_payload(value)
    if type(value) is StrategyRecommendationSourceContradictionStoplightRow:
        return _row_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric values must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


def _require_payload_ready(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_payload_ready(item)
        return
    if type(value) is list:
        for item in value:
            _require_payload_ready(item)
        return
    if value is None or type(value) in (str, bool):
        return
    if isinstance(value, Decimal) or type(value) is int or isinstance(value, float):
        raise ValueError("payload numeric values must be Decimal-derived strings")
    raise ValueError("payload value is not JSON-ready")


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_source_role(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SOURCE_ROLES:
        raise ValueError(f"{field_name} must be official, independent, or supporting")


def _require_stoplight_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STOPLIGHT_STATUSES:
        raise ValueError(f"{field_name} must be green, watch, or red")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_margin_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _MINUS_ONE or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between minus one and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start_at: datetime, end_at: datetime) -> Decimal:
    delta = end_at - start_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _sum_row_count(
    rows: tuple[StrategyRecommendationSourceContradictionStoplightRow, ...],
    field_name: str,
) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), _ZERO))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _require_probability_decimal("max_decimal", max(values))


def _min_margin(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _require_margin_decimal("min_margin", min(values))


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_CONTRADICTION_STOPLIGHT_V2_CONFIG_VERSION",
    "StrategyRecommendationSourceContradictionStoplightV2Config",
    "StrategyRecommendationSourceContradictionEvidence",
    "StrategyRecommendationSourceContradictionCandidate",
    "StrategyRecommendationSourceContradictionStoplightRow",
    "StrategyRecommendationSourceContradictionStoplightReport",
    "build_strategy_recommendation_source_contradiction_stoplight_v2",
    "strategy_recommendation_source_contradiction_stoplight_v2_payload",
)
