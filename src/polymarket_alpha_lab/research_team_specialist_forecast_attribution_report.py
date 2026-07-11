"""Pure report-only specialist forecast contribution attribution."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_FORECAST_ATTRIBUTION_CONFIG_VERSION",
    "SPECIALIST_FORECAST_ATTRIBUTION_STATUSES",
    "ResearchTeamSpecialistForecastAttributionConfig",
    "ResearchTeamSpecialistForecastAttributionObservation",
    "ResearchTeamSpecialistForecastAttributionRow",
    "ResearchTeamSpecialistForecastAttributionBucket",
    "ResearchTeamSpecialistForecastAttributionReport",
    "build_research_team_specialist_forecast_attribution_report",
    "research_team_specialist_forecast_attribution_report_payload",
    "validate_research_team_specialist_forecast_attribution_report_payload",
)


DEFAULT_RESEARCH_TEAM_SPECIALIST_FORECAST_ATTRIBUTION_CONFIG_VERSION = (
    "research-team-specialist-forecast-attribution-report-v0"
)
SPECIALIST_FORECAST_ATTRIBUTION_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DIGEST_REFERENCE_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")

_CALIBRATION_WEIGHT = Decimal("0.300000")
_EVIDENCE_QUALITY_WEIGHT = Decimal("0.200000")
_TIMELINESS_WEIGHT = Decimal("0.150000")
_DISAGREEMENT_HANDLING_WEIGHT = Decimal("0.150000")
_OUTCOME_LEARNING_WEIGHT = Decimal("0.200000")
_PASS_SCORE_THRESHOLD = Decimal("0.700000")
_BLOCK_SCORE_THRESHOLD = Decimal("0.400000")
_COMPONENT_SUPPORT_THRESHOLD = Decimal("0.700000")
_COMPONENT_DRAG_THRESHOLD = Decimal("0.400000")

_CONTRIBUTION_SEQUENCE = (
    "calibration",
    "evidence_quality",
    "timeliness",
    "disagreement_handling",
    "outcome_learning",
)
_STATUS_ORDER = {"pass": 0, "watch": 1, "block": 2}
_REASON_CODE_SEQUENCE = (
    "specialist_forecast_attribution_report_block",
    "specialist_forecast_attribution_report_watch",
    "specialist_forecast_attribution_report_pass",
    "specialist_forecast_attribution_block",
    "specialist_forecast_attribution_watch",
    "specialist_forecast_attribution_pass",
    "empty_specialist_forecasts",
    "calibration_support",
    "calibration_drag",
    "evidence_quality_support",
    "evidence_quality_drag",
    "timeliness_support",
    "timeliness_drag",
    "disagreement_handling_support",
    "disagreement_handling_drag",
    "outcome_learning_support",
    "outcome_learning_drag",
    "calibration_dominant",
    "evidence_quality_dominant",
    "timeliness_dominant",
    "disagreement_handling_dominant",
    "outcome_learning_dominant",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    "observation_count",
    "specialist_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_attribution_score",
    "max_attribution_score",
    "average_calibration_contribution_score",
    "average_evidence_quality_contribution_score",
    "average_timeliness_contribution_score",
    "average_disagreement_handling_contribution_score",
    "average_outcome_learning_contribution_score",
    "rows",
    "contribution_buckets",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "rank",
    "specialist_digest",
    "observation_count",
    "observation_digests",
    "source_count",
    "source_digests",
    "average_absolute_forecast_error",
    "calibration_score",
    "evidence_quality_score",
    "timeliness_score",
    "disagreement_handling_score",
    "outcome_learning_score",
    "calibration_contribution_score",
    "evidence_quality_contribution_score",
    "timeliness_contribution_score",
    "disagreement_handling_contribution_score",
    "outcome_learning_contribution_score",
    "attribution_score",
    "dominant_contribution",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_BUCKET_PAYLOAD_KEYS = (
    "contribution_code",
    "specialist_count",
    "observation_count",
    "average_attribution_score",
    "paper_only",
    "report_only",
    "readonly",
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
class ResearchTeamSpecialistForecastAttributionConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_FORECAST_ATTRIBUTION_CONFIG_VERSION
    )
    calibration_weight: Decimal = _CALIBRATION_WEIGHT
    evidence_quality_weight: Decimal = _EVIDENCE_QUALITY_WEIGHT
    timeliness_weight: Decimal = _TIMELINESS_WEIGHT
    disagreement_handling_weight: Decimal = _DISAGREEMENT_HANDLING_WEIGHT
    outcome_learning_weight: Decimal = _OUTCOME_LEARNING_WEIGHT
    pass_score_threshold: Decimal = _PASS_SCORE_THRESHOLD
    block_score_threshold: Decimal = _BLOCK_SCORE_THRESHOLD
    component_support_threshold: Decimal = _COMPONENT_SUPPORT_THRESHOLD
    component_drag_threshold: Decimal = _COMPONENT_DRAG_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistForecastAttributionConfig,
            "config",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "calibration_weight",
            "evidence_quality_weight",
            "timeliness_weight",
            "disagreement_handling_weight",
            "outcome_learning_weight",
            "pass_score_threshold",
            "block_score_threshold",
            "component_support_threshold",
            "component_drag_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        supported_values = {
            "calibration_weight": _CALIBRATION_WEIGHT,
            "evidence_quality_weight": _EVIDENCE_QUALITY_WEIGHT,
            "timeliness_weight": _TIMELINESS_WEIGHT,
            "disagreement_handling_weight": _DISAGREEMENT_HANDLING_WEIGHT,
            "outcome_learning_weight": _OUTCOME_LEARNING_WEIGHT,
            "pass_score_threshold": _PASS_SCORE_THRESHOLD,
            "block_score_threshold": _BLOCK_SCORE_THRESHOLD,
            "component_support_threshold": _COMPONENT_SUPPORT_THRESHOLD,
            "component_drag_threshold": _COMPONENT_DRAG_THRESHOLD,
        }
        for field_name, supported in supported_values.items():
            if getattr(self, field_name) != supported:
                raise ValueError(f"{field_name} must use the supported value")
        if self.block_score_threshold >= self.pass_score_threshold:
            raise ValueError("block_score_threshold must be below pass_score_threshold")
        if self.component_drag_threshold >= self.component_support_threshold:
            raise ValueError(
                "component_drag_threshold must be below "
                "component_support_threshold",
            )
        with localcontext(_DECIMAL_CONTEXT):
            weight_sum = _quantize(
                self.calibration_weight
                + self.evidence_quality_weight
                + self.timeliness_weight
                + self.disagreement_handling_weight
                + self.outcome_learning_weight,
            )
        if weight_sum != _ONE:
            raise ValueError("contribution weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistForecastAttributionObservation(_FinalPublicDataclass):
    observation_digest: str
    specialist_identifier: str
    source_identifiers: tuple[str, ...]
    observed_at: datetime
    forecast_probability: Decimal
    resolved_probability: Decimal
    evidence_quality_score: Decimal
    timeliness_score: Decimal
    disagreement_handling_score: Decimal
    outcome_learning_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistForecastAttributionObservation,
            "observation",
        )
        _require_digest("observation_digest", self.observation_digest)
        _require_private_identifier(
            "specialist_identifier",
            self.specialist_identifier,
        )
        object.__setattr__(
            self,
            "source_identifiers",
            _normalize_private_identifiers(
                "source_identifiers",
                self.source_identifiers,
            ),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "evidence_quality_score",
            "timeliness_score",
            "disagreement_handling_score",
            "outcome_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistForecastAttributionRow(_FinalPublicDataclass):
    rank: Decimal
    specialist_digest: str
    observation_count: Decimal
    observation_digests: tuple[str, ...]
    source_count: Decimal
    source_digests: tuple[str, ...]
    average_absolute_forecast_error: Decimal
    calibration_score: Decimal
    evidence_quality_score: Decimal
    timeliness_score: Decimal
    disagreement_handling_score: Decimal
    outcome_learning_score: Decimal
    calibration_contribution_score: Decimal
    evidence_quality_contribution_score: Decimal
    timeliness_contribution_score: Decimal
    disagreement_handling_contribution_score: Decimal
    outcome_learning_contribution_score: Decimal
    attribution_score: Decimal
    dominant_contribution: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistForecastAttributionRow,
            "row",
        )
        object.__setattr__(self, "rank", _require_positive_count("rank", self.rank))
        _require_digest_reference("specialist_digest", self.specialist_digest)
        object.__setattr__(
            self,
            "observation_digests",
            _normalize_digests("observation_digests", self.observation_digests),
        )
        object.__setattr__(
            self,
            "source_digests",
            _normalize_digest_references("source_digests", self.source_digests),
        )
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_count("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_positive_count("source_count", self.source_count),
        )
        for field_name in (
            "average_absolute_forecast_error",
            "calibration_score",
            "evidence_quality_score",
            "timeliness_score",
            "disagreement_handling_score",
            "outcome_learning_score",
            "calibration_contribution_score",
            "evidence_quality_contribution_score",
            "timeliness_contribution_score",
            "disagreement_handling_contribution_score",
            "outcome_learning_contribution_score",
            "attribution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member(
            "dominant_contribution",
            self.dominant_contribution,
            _CONTRIBUTION_SEQUENCE,
        )
        _require_member(
            "status",
            self.status,
            SPECIALIST_FORECAST_ATTRIBUTION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistForecastAttributionBucket(_FinalPublicDataclass):
    contribution_code: str
    specialist_count: Decimal
    observation_count: Decimal
    average_attribution_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistForecastAttributionBucket,
            "bucket",
        )
        _require_member(
            "contribution_code",
            self.contribution_code,
            _CONTRIBUTION_SEQUENCE,
        )
        for field_name in ("specialist_count", "observation_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_attribution_score",
            _require_ratio(
                "average_attribution_score",
                self.average_attribution_score,
            ),
        )
        _require_hard_flags("bucket", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistForecastAttributionReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_attribution_score: Decimal
    max_attribution_score: Decimal
    average_calibration_contribution_score: Decimal
    average_evidence_quality_contribution_score: Decimal
    average_timeliness_contribution_score: Decimal
    average_disagreement_handling_contribution_score: Decimal
    average_outcome_learning_contribution_score: Decimal
    rows: tuple[ResearchTeamSpecialistForecastAttributionRow, ...]
    contribution_buckets: tuple[
        ResearchTeamSpecialistForecastAttributionBucket,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistForecastAttributionReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_config_version(self.config_version)
        _require_member(
            "status",
            self.status,
            SPECIALIST_FORECAST_ATTRIBUTION_STATUSES,
        )
        for field_name in (
            "observation_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_attribution_score",
            "max_attribution_score",
            "average_calibration_contribution_score",
            "average_evidence_quality_contribution_score",
            "average_timeliness_contribution_score",
            "average_disagreement_handling_contribution_score",
            "average_outcome_learning_contribution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchTeamSpecialistForecastAttributionRow:
                raise ValueError(
                    "rows must contain ResearchTeamSpecialistForecastAttributionRow",
                )
        if type(self.contribution_buckets) is not tuple:
            raise ValueError("contribution_buckets must be a tuple")
        for bucket in self.contribution_buckets:
            if type(bucket) is not ResearchTeamSpecialistForecastAttributionBucket:
                raise ValueError(
                    "contribution_buckets must contain "
                    "ResearchTeamSpecialistForecastAttributionBucket",
                )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(
            _report_values_without_digest(self),
        )
        if self.derived_validation_digest != expected_digest:
            raise ValueError(
                "derived_validation_digest does not match report payload",
            )

    @property
    def payload(self) -> dict[str, Any]:
        with localcontext(_DECIMAL_CONTEXT):
            _validate_report_consistency(self)
            expected_digest = _report_digest_from_values(
                _report_values_without_digest(self),
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError(
                    "derived_validation_digest does not match report payload",
                )
            payload = _json_ready(asdict(self))
            if type(payload) is not dict:
                raise ValueError("payload must be a dict")
            return payload


def build_research_team_specialist_forecast_attribution_report(
    observations: Sequence[ResearchTeamSpecialistForecastAttributionObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistForecastAttributionConfig | None = None,
) -> ResearchTeamSpecialistForecastAttributionReport:
    """Build a deterministic in-memory report for human research review."""

    with localcontext(_DECIMAL_CONTEXT):
        return _build_research_team_specialist_forecast_attribution_report(
            observations,
            generated_at=generated_at,
            config=config,
        )


def _build_research_team_specialist_forecast_attribution_report(
    observations: Sequence[ResearchTeamSpecialistForecastAttributionObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistForecastAttributionConfig | None,
) -> ResearchTeamSpecialistForecastAttributionReport:
    if config is None:
        config = ResearchTeamSpecialistForecastAttributionConfig()
    if type(config) is not ResearchTeamSpecialistForecastAttributionConfig:
        raise ValueError(
            "config must be ResearchTeamSpecialistForecastAttributionConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for observation in normalized:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[
        str,
        list[ResearchTeamSpecialistForecastAttributionObservation],
    ] = {}
    for observation in normalized:
        grouped.setdefault(observation.specialist_identifier, []).append(observation)

    row_values = [
        _specialist_row_values(identifier, tuple(items), config)
        for identifier, items in grouped.items()
    ]
    row_values.sort(
        key=lambda values: (
            -values["attribution_score"],
            values["specialist_digest"],
        ),
    )
    rows = tuple(
        ResearchTeamSpecialistForecastAttributionRow(
            rank=_count(index),
            **values,
        )
        for index, values in enumerate(row_values, start=1)
    )
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": status,
        "observation_count": _count(len(normalized)),
        "specialist_count": _count(len(rows)),
        "pass_count": _count(_status_count(rows, "pass")),
        "watch_count": _count(_status_count(rows, "watch")),
        "block_count": _count(_status_count(rows, "block")),
        "average_attribution_score": _average(
            tuple(row.attribution_score for row in rows),
        ),
        "max_attribution_score": max(
            (row.attribution_score for row in rows),
            default=_ZERO,
        ),
        "average_calibration_contribution_score": _average(
            tuple(row.calibration_contribution_score for row in rows),
        ),
        "average_evidence_quality_contribution_score": _average(
            tuple(row.evidence_quality_contribution_score for row in rows),
        ),
        "average_timeliness_contribution_score": _average(
            tuple(row.timeliness_contribution_score for row in rows),
        ),
        "average_disagreement_handling_contribution_score": _average(
            tuple(row.disagreement_handling_contribution_score for row in rows),
        ),
        "average_outcome_learning_contribution_score": _average(
            tuple(row.outcome_learning_contribution_score for row in rows),
        ),
        "rows": rows,
        "contribution_buckets": _build_buckets(rows),
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecialistForecastAttributionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_specialist_forecast_attribution_report_payload(
    report: ResearchTeamSpecialistForecastAttributionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamSpecialistForecastAttributionReport:
        raise ValueError(
            "report must be ResearchTeamSpecialistForecastAttributionReport",
        )
    _require_hard_flags("report", report)
    payload = report.payload
    validate_research_team_specialist_forecast_attribution_report_payload(payload)
    return payload


def validate_research_team_specialist_forecast_attribution_report_payload(
    payload: dict[str, Any],
) -> bool:
    _report_from_public_payload(payload)
    return True


def _specialist_row_values(
    specialist_identifier: str,
    observations: tuple[ResearchTeamSpecialistForecastAttributionObservation, ...],
    config: ResearchTeamSpecialistForecastAttributionConfig,
) -> dict[str, object]:
    with localcontext(_DECIMAL_CONTEXT):
        return _specialist_row_values_in_context(
            specialist_identifier,
            observations,
            config,
        )


def _specialist_row_values_in_context(
    specialist_identifier: str,
    observations: tuple[ResearchTeamSpecialistForecastAttributionObservation, ...],
    config: ResearchTeamSpecialistForecastAttributionConfig,
) -> dict[str, object]:
    absolute_errors = tuple(
        _absolute(
            _quantize(
                observation.resolved_probability
                - observation.forecast_probability,
            ),
        )
        for observation in observations
    )
    average_error = _average(absolute_errors)
    calibration_score = _quantize(_ONE - average_error)
    evidence_quality_score = _average(
        tuple(item.evidence_quality_score for item in observations),
    )
    timeliness_score = _average(
        tuple(item.timeliness_score for item in observations),
    )
    disagreement_handling_score = _average(
        tuple(item.disagreement_handling_score for item in observations),
    )
    outcome_learning_score = _average(
        tuple(item.outcome_learning_score for item in observations),
    )
    contributions = {
        "calibration": _quantize(
            calibration_score * config.calibration_weight,
        ),
        "evidence_quality": _quantize(
            evidence_quality_score * config.evidence_quality_weight,
        ),
        "timeliness": _quantize(
            timeliness_score * config.timeliness_weight,
        ),
        "disagreement_handling": _quantize(
            disagreement_handling_score
            * config.disagreement_handling_weight,
        ),
        "outcome_learning": _quantize(
            outcome_learning_score * config.outcome_learning_weight,
        ),
    }
    attribution_score = _quantize(sum(contributions.values(), _ZERO))
    dominant_contribution = _dominant_contribution(contributions)
    status = _row_status(attribution_score, config)
    source_digests = tuple(
        sorted(
            {
                _private_digest("source", identifier)
                for observation in observations
                for identifier in observation.source_identifiers
            },
        ),
    )
    observation_digests = tuple(
        sorted(item.observation_digest for item in observations),
    )
    return {
        "specialist_digest": _private_digest(
            "specialist",
            specialist_identifier,
        ),
        "observation_count": _count(len(observation_digests)),
        "observation_digests": observation_digests,
        "source_count": _count(len(source_digests)),
        "source_digests": source_digests,
        "average_absolute_forecast_error": average_error,
        "calibration_score": calibration_score,
        "evidence_quality_score": evidence_quality_score,
        "timeliness_score": timeliness_score,
        "disagreement_handling_score": disagreement_handling_score,
        "outcome_learning_score": outcome_learning_score,
        "calibration_contribution_score": contributions["calibration"],
        "evidence_quality_contribution_score": contributions["evidence_quality"],
        "timeliness_contribution_score": contributions["timeliness"],
        "disagreement_handling_contribution_score": contributions[
            "disagreement_handling"
        ],
        "outcome_learning_contribution_score": contributions["outcome_learning"],
        "attribution_score": attribution_score,
        "dominant_contribution": dominant_contribution,
        "status": status,
        "reason_codes": _row_reason_codes(
            status=status,
            dominant_contribution=dominant_contribution,
            calibration_score=calibration_score,
            evidence_quality_score=evidence_quality_score,
            timeliness_score=timeliness_score,
            disagreement_handling_score=disagreement_handling_score,
            outcome_learning_score=outcome_learning_score,
            config=config,
        ),
    }


def _dominant_contribution(contributions: dict[str, Decimal]) -> str:
    return max(
        _CONTRIBUTION_SEQUENCE,
        key=lambda contribution: (
            contributions[contribution],
            -_CONTRIBUTION_SEQUENCE.index(contribution),
        ),
    )


def _row_status(
    attribution_score: Decimal,
    config: ResearchTeamSpecialistForecastAttributionConfig,
) -> str:
    if attribution_score >= config.pass_score_threshold:
        return "pass"
    if attribution_score < config.block_score_threshold:
        return "block"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    dominant_contribution: str,
    calibration_score: Decimal,
    evidence_quality_score: Decimal,
    timeliness_score: Decimal,
    disagreement_handling_score: Decimal,
    outcome_learning_score: Decimal,
    config: ResearchTeamSpecialistForecastAttributionConfig,
) -> tuple[str, ...]:
    reasons: list[str] = [f"specialist_forecast_attribution_{status}"]
    component_scores = (
        ("calibration", calibration_score),
        ("evidence_quality", evidence_quality_score),
        ("timeliness", timeliness_score),
        ("disagreement_handling", disagreement_handling_score),
        ("outcome_learning", outcome_learning_score),
    )
    for component, score in component_scores:
        if score >= config.component_support_threshold:
            reasons.append(f"{component}_support")
        elif score < config.component_drag_threshold:
            reasons.append(f"{component}_drag")
    reasons.append(f"{dominant_contribution}_dominant")
    return _normalize_reason_codes(tuple(reasons))


def _report_status(
    rows: tuple[ResearchTeamSpecialistForecastAttributionRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistForecastAttributionRow, ...],
    status: str,
) -> tuple[str, ...]:
    reasons: list[str] = [f"specialist_forecast_attribution_report_{status}"]
    if not rows:
        reasons.append("empty_specialist_forecasts")
    for row in rows:
        reasons.extend(row.reason_codes)
    return _canonical_reason_codes(reasons)


def _build_buckets(
    rows: tuple[ResearchTeamSpecialistForecastAttributionRow, ...],
) -> tuple[ResearchTeamSpecialistForecastAttributionBucket, ...]:
    with localcontext(_DECIMAL_CONTEXT):
        return _build_buckets_in_context(rows)


def _build_buckets_in_context(
    rows: tuple[ResearchTeamSpecialistForecastAttributionRow, ...],
) -> tuple[ResearchTeamSpecialistForecastAttributionBucket, ...]:
    buckets: list[ResearchTeamSpecialistForecastAttributionBucket] = []
    for contribution_code in _CONTRIBUTION_SEQUENCE:
        bucket_rows = tuple(
            row
            for row in rows
            if row.dominant_contribution == contribution_code
        )
        buckets.append(
            ResearchTeamSpecialistForecastAttributionBucket(
                contribution_code=contribution_code,
                specialist_count=_count(len(bucket_rows)),
                observation_count=_quantize(
                    sum((row.observation_count for row in bucket_rows), _ZERO),
                ),
                average_attribution_score=_average(
                    tuple(row.attribution_score for row in bucket_rows),
                ),
            ),
        )
    return tuple(buckets)


def _validate_row_consistency(
    row: ResearchTeamSpecialistForecastAttributionRow,
) -> None:
    with localcontext(_DECIMAL_CONTEXT):
        _validate_row_consistency_in_context(row)


def _validate_row_consistency_in_context(
    row: ResearchTeamSpecialistForecastAttributionRow,
) -> None:
    config = ResearchTeamSpecialistForecastAttributionConfig()
    if row.observation_count != _count(len(row.observation_digests)):
        raise ValueError("observation_count must match observation_digests")
    if row.source_count != _count(len(row.source_digests)):
        raise ValueError("source_count must match source_digests")
    expected_calibration = _quantize(
        _ONE - row.average_absolute_forecast_error,
    )
    if row.calibration_score != expected_calibration:
        raise ValueError(
            "calibration_score must match average_absolute_forecast_error",
        )
    expected_contributions = {
        "calibration": _quantize(
            row.calibration_score * config.calibration_weight,
        ),
        "evidence_quality": _quantize(
            row.evidence_quality_score * config.evidence_quality_weight,
        ),
        "timeliness": _quantize(
            row.timeliness_score * config.timeliness_weight,
        ),
        "disagreement_handling": _quantize(
            row.disagreement_handling_score
            * config.disagreement_handling_weight,
        ),
        "outcome_learning": _quantize(
            row.outcome_learning_score * config.outcome_learning_weight,
        ),
    }
    actual_contributions = {
        "calibration": row.calibration_contribution_score,
        "evidence_quality": row.evidence_quality_contribution_score,
        "timeliness": row.timeliness_contribution_score,
        "disagreement_handling": row.disagreement_handling_contribution_score,
        "outcome_learning": row.outcome_learning_contribution_score,
    }
    for contribution_code in _CONTRIBUTION_SEQUENCE:
        if (
            actual_contributions[contribution_code]
            != expected_contributions[contribution_code]
        ):
            raise ValueError(
                f"{contribution_code}_contribution_score must match "
                "component score",
            )
    expected_score = _quantize(sum(expected_contributions.values(), _ZERO))
    if row.attribution_score != expected_score:
        raise ValueError("attribution_score must match contribution scores")
    expected_dominant = _dominant_contribution(expected_contributions)
    if row.dominant_contribution != expected_dominant:
        raise ValueError("dominant_contribution must match contribution scores")
    expected_status = _row_status(expected_score, config)
    if row.status != expected_status:
        raise ValueError("status must match attribution_score")
    expected_reasons = _row_reason_codes(
        status=expected_status,
        dominant_contribution=expected_dominant,
        calibration_score=row.calibration_score,
        evidence_quality_score=row.evidence_quality_score,
        timeliness_score=row.timeliness_score,
        disagreement_handling_score=row.disagreement_handling_score,
        outcome_learning_score=row.outcome_learning_score,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row attribution")


def _validate_report_consistency(
    report: ResearchTeamSpecialistForecastAttributionReport,
) -> None:
    with localcontext(_DECIMAL_CONTEXT):
        _validate_report_consistency_in_context(report)


def _validate_report_consistency_in_context(
    report: ResearchTeamSpecialistForecastAttributionReport,
) -> None:
    if len({row.specialist_digest for row in report.rows}) != len(report.rows):
        raise ValueError("rows must have unique specialist_digest values")
    observation_digests = tuple(
        digest
        for row in report.rows
        for digest in row.observation_digests
    )
    if len(set(observation_digests)) != len(observation_digests):
        raise ValueError("observation_digests must be unique across rows")
    expected_rows = tuple(
        sorted(
            report.rows,
            key=lambda row: (-row.attribution_score, row.specialist_digest),
        ),
    )
    if report.rows != expected_rows:
        raise ValueError("rows must use deterministic sequence")
    for index, row in enumerate(report.rows, start=1):
        if row.rank != _count(index):
            raise ValueError("rank must match deterministic sequence")
    expected_observation_count = _quantize(
        sum((row.observation_count for row in report.rows), _ZERO),
    )
    if report.observation_count != expected_observation_count:
        raise ValueError("observation_count must match rows")
    if report.specialist_count != _count(len(report.rows)):
        raise ValueError("specialist_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _count(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    average_fields = (
        ("average_attribution_score", "attribution_score"),
        (
            "average_calibration_contribution_score",
            "calibration_contribution_score",
        ),
        (
            "average_evidence_quality_contribution_score",
            "evidence_quality_contribution_score",
        ),
        (
            "average_timeliness_contribution_score",
            "timeliness_contribution_score",
        ),
        (
            "average_disagreement_handling_contribution_score",
            "disagreement_handling_contribution_score",
        ),
        (
            "average_outcome_learning_contribution_score",
            "outcome_learning_contribution_score",
        ),
    )
    for report_field, row_field in average_fields:
        expected_average = _average(
            tuple(getattr(row, row_field) for row in report.rows),
        )
        if getattr(report, report_field) != expected_average:
            raise ValueError(f"{report_field} must match rows")
    expected_maximum = max(
        (row.attribution_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_attribution_score != expected_maximum:
        raise ValueError("max_attribution_score must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_buckets = _build_buckets(report.rows)
    if report.contribution_buckets != expected_buckets:
        raise ValueError("contribution_buckets must match rows")
    expected_reasons = _report_reason_codes(report.rows, expected_status)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")


def _report_from_public_payload(
    payload: object,
) -> ResearchTeamSpecialistForecastAttributionReport:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _require_public_payload_shape(payload)
    _require_payload_flags("payload", payload)
    report = ResearchTeamSpecialistForecastAttributionReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string(
            "config_version",
            payload["config_version"],
        ),
        status=_public_member(
            "status",
            payload["status"],
            SPECIALIST_FORECAST_ATTRIBUTION_STATUSES,
        ),
        observation_count=_public_count(
            "observation_count",
            payload["observation_count"],
        ),
        specialist_count=_public_count(
            "specialist_count",
            payload["specialist_count"],
        ),
        pass_count=_public_count("pass_count", payload["pass_count"]),
        watch_count=_public_count("watch_count", payload["watch_count"]),
        block_count=_public_count("block_count", payload["block_count"]),
        average_attribution_score=_public_ratio(
            "average_attribution_score",
            payload["average_attribution_score"],
        ),
        max_attribution_score=_public_ratio(
            "max_attribution_score",
            payload["max_attribution_score"],
        ),
        average_calibration_contribution_score=_public_ratio(
            "average_calibration_contribution_score",
            payload["average_calibration_contribution_score"],
        ),
        average_evidence_quality_contribution_score=_public_ratio(
            "average_evidence_quality_contribution_score",
            payload["average_evidence_quality_contribution_score"],
        ),
        average_timeliness_contribution_score=_public_ratio(
            "average_timeliness_contribution_score",
            payload["average_timeliness_contribution_score"],
        ),
        average_disagreement_handling_contribution_score=_public_ratio(
            "average_disagreement_handling_contribution_score",
            payload["average_disagreement_handling_contribution_score"],
        ),
        average_outcome_learning_contribution_score=_public_ratio(
            "average_outcome_learning_contribution_score",
            payload["average_outcome_learning_contribution_score"],
        ),
        rows=tuple(_row_from_public_payload(row) for row in payload["rows"]),
        contribution_buckets=tuple(
            _bucket_from_public_payload(bucket)
            for bucket in payload["contribution_buckets"]
        ),
        reason_codes=_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=_public_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if report.payload != payload:
        raise ValueError("public payload must use canonical ordering and values")
    return report


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamSpecialistForecastAttributionRow:
    _require_payload_flags("payload row", payload)
    return ResearchTeamSpecialistForecastAttributionRow(
        rank=_public_positive_count("rank", payload["rank"]),
        specialist_digest=_public_digest_reference(
            "specialist_digest",
            payload["specialist_digest"],
        ),
        observation_count=_public_positive_count(
            "observation_count",
            payload["observation_count"],
        ),
        observation_digests=_public_digests(
            "observation_digests",
            payload["observation_digests"],
        ),
        source_count=_public_positive_count(
            "source_count",
            payload["source_count"],
        ),
        source_digests=_public_digest_references(
            "source_digests",
            payload["source_digests"],
        ),
        average_absolute_forecast_error=_public_ratio(
            "average_absolute_forecast_error",
            payload["average_absolute_forecast_error"],
        ),
        calibration_score=_public_ratio(
            "calibration_score",
            payload["calibration_score"],
        ),
        evidence_quality_score=_public_ratio(
            "evidence_quality_score",
            payload["evidence_quality_score"],
        ),
        timeliness_score=_public_ratio(
            "timeliness_score",
            payload["timeliness_score"],
        ),
        disagreement_handling_score=_public_ratio(
            "disagreement_handling_score",
            payload["disagreement_handling_score"],
        ),
        outcome_learning_score=_public_ratio(
            "outcome_learning_score",
            payload["outcome_learning_score"],
        ),
        calibration_contribution_score=_public_ratio(
            "calibration_contribution_score",
            payload["calibration_contribution_score"],
        ),
        evidence_quality_contribution_score=_public_ratio(
            "evidence_quality_contribution_score",
            payload["evidence_quality_contribution_score"],
        ),
        timeliness_contribution_score=_public_ratio(
            "timeliness_contribution_score",
            payload["timeliness_contribution_score"],
        ),
        disagreement_handling_contribution_score=_public_ratio(
            "disagreement_handling_contribution_score",
            payload["disagreement_handling_contribution_score"],
        ),
        outcome_learning_contribution_score=_public_ratio(
            "outcome_learning_contribution_score",
            payload["outcome_learning_contribution_score"],
        ),
        attribution_score=_public_ratio(
            "attribution_score",
            payload["attribution_score"],
        ),
        dominant_contribution=_public_member(
            "dominant_contribution",
            payload["dominant_contribution"],
            _CONTRIBUTION_SEQUENCE,
        ),
        status=_public_member(
            "status",
            payload["status"],
            SPECIALIST_FORECAST_ATTRIBUTION_STATUSES,
        ),
        reason_codes=_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _bucket_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamSpecialistForecastAttributionBucket:
    _require_payload_flags("payload bucket", payload)
    return ResearchTeamSpecialistForecastAttributionBucket(
        contribution_code=_public_member(
            "contribution_code",
            payload["contribution_code"],
            _CONTRIBUTION_SEQUENCE,
        ),
        specialist_count=_public_count(
            "specialist_count",
            payload["specialist_count"],
        ),
        observation_count=_public_count(
            "observation_count",
            payload["observation_count"],
        ),
        average_attribution_score=_public_ratio(
            "average_attribution_score",
            payload["average_attribution_score"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_public_payload_shape(payload: dict[str, Any]) -> None:
    if tuple(payload) != _REPORT_PAYLOAD_KEYS:
        raise ValueError("payload keys must match the exact report schema")
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        if tuple(row) != _ROW_PAYLOAD_KEYS:
            raise ValueError("row keys must match the exact row schema")
    buckets = payload["contribution_buckets"]
    if type(buckets) is not list:
        raise ValueError("contribution_buckets must be a list")
    for bucket in buckets:
        if type(bucket) is not dict:
            raise ValueError("contribution_buckets must contain JSON objects")
        if tuple(bucket) != _BUCKET_PAYLOAD_KEYS:
            raise ValueError("bucket keys must match the exact bucket schema")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _public_member(
    field_name: str,
    value: object,
    allowed: Sequence[str],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not _PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(value)


def _public_ratio(field_name: str, value: object) -> Decimal:
    return _require_ratio(field_name, _public_decimal(field_name, value))


def _public_count(field_name: str, value: object) -> Decimal:
    return _require_count(field_name, _public_decimal(field_name, value))


def _public_positive_count(field_name: str, value: object) -> Decimal:
    return _require_positive_count(
        field_name,
        _public_decimal(field_name, value),
    )


def _public_digest(field_name: str, value: object) -> str:
    return _require_digest(field_name, value)


def _public_digest_reference(field_name: str, value: object) -> str:
    return _require_digest_reference(field_name, value)


def _public_digests(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_public_digest(field_name, item) for item in value)


def _public_digest_references(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_public_digest_reference(field_name, item) for item in value)


def _public_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


def _normalize_observations(
    observations: Sequence[ResearchTeamSpecialistForecastAttributionObservation],
) -> tuple[ResearchTeamSpecialistForecastAttributionObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(
        observations,
        Sequence,
    ):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchTeamSpecialistForecastAttributionObservation] = []
    seen_digests: set[str] = set()
    for observation in observations:
        if type(observation) is not ResearchTeamSpecialistForecastAttributionObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamSpecialistForecastAttributionObservation",
            )
        if observation.observation_digest in seen_digests:
            raise ValueError("observation_digest values must be unique")
        seen_digests.add(observation.observation_digest)
        normalized.append(observation)
    return tuple(sorted(normalized, key=lambda item: item.observation_digest))


def _normalize_private_identifiers(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_private_identifier(field_name, value))
    return tuple(sorted(set(normalized)))


def _normalize_digests(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    for value in values:
        _require_digest(field_name, value)
    normalized = tuple(sorted(set(values)))
    if normalized != values:
        raise ValueError(f"{field_name} must be unique and sorted")
    return normalized


def _normalize_digest_references(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    for value in values:
        _require_digest_reference(field_name, value)
    normalized = tuple(sorted(set(values)))
    if normalized != values:
        raise ValueError(f"{field_name} must be unique and sorted")
    return normalized


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for value in values:
        if type(value) is not str or value not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain supported values")
    normalized = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in values
    )
    if normalized != values:
        raise ValueError("reason_codes must be unique and canonical")
    return normalized


def _canonical_reason_codes(values: Sequence[str]) -> tuple[str, ...]:
    for value in values:
        if type(value) is not str or value not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain supported values")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in values
    )


def _require_exact_type(value: object, expected: type[object], label: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _require_config_version(value: object) -> None:
    if (
        type(value) is not str
        or value
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_FORECAST_ATTRIBUTION_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")


def _require_private_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty exact string")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_digest_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_REFERENCE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest reference")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed: Sequence[str],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0") or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be from zero through one")
    return _quantize(decimal_value)


def _require_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        integral_value = decimal_value.to_integral_value()
    if decimal_value != integral_value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(decimal_value)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be an exact timezone-aware datetime")
    return value.astimezone(UTC)


def _private_digest(kind: str, value: str) -> str:
    digest = sha256(f"{kind}\0{value}".encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _status_count(
    rows: tuple[ResearchTeamSpecialistForecastAttributionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _absolute(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(-value if value < _ZERO else value)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            quantized = value.quantize(_QUANT)
    except DecimalException as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    return _ZERO if quantized.is_zero() else quantized


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    return value


def _report_values_without_digest(
    report: ResearchTeamSpecialistForecastAttributionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    # Exact key order is enforced separately by _require_public_payload_shape.
    canonical = json.dumps(
        _json_ready(values),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
