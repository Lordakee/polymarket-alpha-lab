"""Read-only quality gate for specialist forecast revision quality."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_FORECAST_REVISION_QUALITY_GATE_V2_CONFIG_VERSION = (
    "team-specialist-forecast-revision-quality-gate-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

GATE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "team_specialist_forecast_revision_quality_pass",
    "team_specialist_forecast_revision_quality_watch",
    "team_specialist_forecast_revision_quality_blocked",
    "unsupported_revision_penalty_applied",
    "learning_feedback_boost_applied",
    "revision_quality_score_below_pass_floor",
    "revision_quality_score_below_watch_floor",
)
REPORT_REASON_CODES = (
    "team_specialist_forecast_revision_quality_gate_passed",
    "team_specialist_forecast_revision_quality_gate_watch_rows",
    "team_specialist_forecast_revision_quality_gate_blocked_rows",
    "team_specialist_forecast_revision_quality_gate_unsupported_revision_penalty_rows",
    "team_specialist_forecast_revision_quality_gate_learning_feedback_boost_rows",
    "team_specialist_forecast_revision_quality_gate_empty",
)
NEXT_STEPS = {
    "pass": "continue_specialist_revision_quality_monitoring",
    "watch": "review_specialist_revision_quality",
    "blocked": "hold_specialist_revision_quality_until_remediated",
}
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_FORECAST_REVISION_QUALITY_GATE_V2_CONFIG_VERSION",
    "TeamSpecialistForecastRevisionQualityGateV2Config",
    "TeamSpecialistForecastRevisionQualityGateV2Input",
    "TeamSpecialistForecastRevisionQualityGateV2Row",
    "TeamSpecialistForecastRevisionQualityGateV2Report",
    "build_team_specialist_forecast_revision_quality_gate_v2",
    "team_specialist_forecast_revision_quality_gate_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistForecastRevisionQualityGateV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_FORECAST_REVISION_QUALITY_GATE_V2_CONFIG_VERSION
    )
    evidence_support_weight: Decimal = Decimal("0.350000")
    rationale_quality_weight: Decimal = Decimal("0.250000")
    calibration_improvement_weight: Decimal = Decimal("0.250000")
    timeliness_weight: Decimal = Decimal("0.150000")
    unsupported_revision_penalty: Decimal = Decimal("0.300000")
    max_learning_feedback_boost: Decimal = Decimal("0.050000")
    pass_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_FORECAST_REVISION_QUALITY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_support_weight",
            "rationale_quality_weight",
            "calibration_improvement_weight",
            "timeliness_weight",
            "unsupported_revision_penalty",
            "max_learning_feedback_boost",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(asdict(self)))


@dataclass(frozen=True)
class TeamSpecialistForecastRevisionQualityGateV2Input:
    team_id: str
    specialist_id: str
    forecast_id: str
    category_id: str
    revised_at: datetime
    prior_probability: Decimal
    revised_probability: Decimal
    evidence_support_score: Decimal
    rationale_quality_score: Decimal
    calibration_improvement_score: Decimal
    timeliness_score: Decimal
    revision_supported: bool
    learning_feedback_available: bool
    learning_feedback_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "forecast_id", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "revised_at", _as_utc("revised_at", self.revised_at))
        for field_name in (
            "prior_probability",
            "revised_probability",
            "evidence_support_score",
            "rationale_quality_score",
            "calibration_improvement_score",
            "timeliness_score",
            "learning_feedback_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "revision_supported",
            _require_bool("revision_supported", self.revision_supported),
        )
        object.__setattr__(
            self,
            "learning_feedback_available",
            _require_bool(
                "learning_feedback_available",
                self.learning_feedback_available,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(asdict(self)))


@dataclass(frozen=True)
class TeamSpecialistForecastRevisionQualityGateV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    forecast_id: str
    category_id: str
    revised_at: datetime
    prior_probability: Decimal
    revised_probability: Decimal
    probability_delta_abs: Decimal
    evidence_support_score: Decimal
    rationale_quality_score: Decimal
    calibration_improvement_score: Decimal
    timeliness_score: Decimal
    revision_supported: bool
    unsupported_revision_penalty_applied: Decimal
    learning_feedback_available: bool
    learning_feedback_score: Decimal
    learning_feedback_boost_applied: Decimal
    revision_quality_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_count("rank", self.rank))
        if self.rank <= ZERO:
            raise ValueError("rank must be positive")
        for field_name in ("team_id", "specialist_id", "forecast_id", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "revised_at", _as_utc("revised_at", self.revised_at))
        for field_name in (
            "prior_probability",
            "revised_probability",
            "probability_delta_abs",
            "evidence_support_score",
            "rationale_quality_score",
            "calibration_improvement_score",
            "timeliness_score",
            "unsupported_revision_penalty_applied",
            "learning_feedback_score",
            "learning_feedback_boost_applied",
            "revision_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "revision_supported",
            _require_bool("revision_supported", self.revision_supported),
        )
        object.__setattr__(
            self,
            "learning_feedback_available",
            _require_bool(
                "learning_feedback_available",
                self.learning_feedback_available,
            ),
        )
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(asdict(self)))
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistForecastRevisionQualityGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    revision_count: Decimal
    pass_revision_count: Decimal
    watch_revision_count: Decimal
    blocked_revision_count: Decimal
    unsupported_revision_count: Decimal
    learning_feedback_revision_count: Decimal
    average_revision_quality_score: Decimal
    top_revision_quality_score: Decimal
    bottom_revision_quality_score: Decimal
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_FORECAST_REVISION_QUALITY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_public_string("recommended_next_step", self.recommended_next_step),
        )
        if self.recommended_next_step != NEXT_STEPS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        for field_name in (
            "revision_count",
            "pass_revision_count",
            "watch_revision_count",
            "blocked_revision_count",
            "unsupported_revision_count",
            "learning_feedback_revision_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_revision_quality_score",
            "top_revision_quality_score",
            "bottom_revision_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
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
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(asdict(self)))
        _validate_derived_validation_digest(self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        _validate_derived_validation_digest(self)
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        return payload


def build_team_specialist_forecast_revision_quality_gate_v2(
    revisions: object,
    *,
    config: TeamSpecialistForecastRevisionQualityGateV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistForecastRevisionQualityGateV2Report:
    if config is None:
        config = TeamSpecialistForecastRevisionQualityGateV2Config()
    if type(config) is not TeamSpecialistForecastRevisionQualityGateV2Config:
        raise ValueError(
            "config must be exactly TeamSpecialistForecastRevisionQualityGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_revisions = _normalize_inputs(revisions)
    rows = tuple(
        _row_for_revision(rank=index, revision=revision, config=config)
        for index, revision in enumerate(
            _sorted_revisions(normalized_revisions, config),
            start=1,
        )
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": status,
        "recommended_next_step": NEXT_STEPS[status],
        "revision_count": _decimal_count(len(rows)),
        "pass_revision_count": _status_count(rows, "pass"),
        "watch_revision_count": _status_count(rows, "watch"),
        "blocked_revision_count": _status_count(rows, "blocked"),
        "unsupported_revision_count": _unsupported_revision_count(rows),
        "learning_feedback_revision_count": _learning_feedback_revision_count(rows),
        "average_revision_quality_score": _average_score(rows),
        "top_revision_quality_score": _top_score(rows),
        "bottom_revision_quality_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistForecastRevisionQualityGateV2Report(**values)


def team_specialist_forecast_revision_quality_gate_v2_payload(
    report: TeamSpecialistForecastRevisionQualityGateV2Report,
) -> dict[str, object]:
    if type(report) is not TeamSpecialistForecastRevisionQualityGateV2Report:
        raise ValueError(
            "report must be exactly TeamSpecialistForecastRevisionQualityGateV2Report",
        )
    return report.payload


def _row_for_revision(
    *,
    rank: int,
    revision: TeamSpecialistForecastRevisionQualityGateV2Input,
    config: TeamSpecialistForecastRevisionQualityGateV2Config,
) -> TeamSpecialistForecastRevisionQualityGateV2Row:
    score = _score_for_revision(revision, config)
    status = _row_status(score, revision, config)
    return TeamSpecialistForecastRevisionQualityGateV2Row(
        rank=_decimal_count(rank),
        team_id=revision.team_id,
        specialist_id=revision.specialist_id,
        forecast_id=revision.forecast_id,
        category_id=revision.category_id,
        revised_at=revision.revised_at,
        prior_probability=revision.prior_probability,
        revised_probability=revision.revised_probability,
        probability_delta_abs=_probability_delta_abs(revision),
        evidence_support_score=revision.evidence_support_score,
        rationale_quality_score=revision.rationale_quality_score,
        calibration_improvement_score=revision.calibration_improvement_score,
        timeliness_score=revision.timeliness_score,
        revision_supported=revision.revision_supported,
        unsupported_revision_penalty_applied=_unsupported_revision_penalty(
            revision,
            config,
        ),
        learning_feedback_available=revision.learning_feedback_available,
        learning_feedback_score=revision.learning_feedback_score,
        learning_feedback_boost_applied=_learning_feedback_boost(revision, config),
        revision_quality_score=score,
        gate_status=status,
        reason_codes=_row_reason_codes(score, status, revision, config),
    )


def _sorted_revisions(
    revisions: tuple[TeamSpecialistForecastRevisionQualityGateV2Input, ...],
    config: TeamSpecialistForecastRevisionQualityGateV2Config,
) -> tuple[TeamSpecialistForecastRevisionQualityGateV2Input, ...]:
    return tuple(
        sorted(
            revisions,
            key=lambda revision: (
                -_score_for_revision(revision, config),
                revision.team_id,
                revision.specialist_id,
                revision.forecast_id,
            ),
        ),
    )


def _score_for_revision(
    revision: TeamSpecialistForecastRevisionQualityGateV2Input,
    config: TeamSpecialistForecastRevisionQualityGateV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            revision.evidence_support_score * config.evidence_support_weight
            + revision.rationale_quality_score * config.rationale_quality_weight
            + revision.calibration_improvement_score
            * config.calibration_improvement_weight
            + revision.timeliness_score * config.timeliness_weight
            - _unsupported_revision_penalty(revision, config)
            + _learning_feedback_boost(revision, config)
        )
        return _clamp_ratio(score)


def _unsupported_revision_penalty(
    revision: TeamSpecialistForecastRevisionQualityGateV2Input,
    config: TeamSpecialistForecastRevisionQualityGateV2Config,
) -> Decimal:
    if revision.revision_supported:
        return ZERO
    return config.unsupported_revision_penalty


def _learning_feedback_boost(
    revision: TeamSpecialistForecastRevisionQualityGateV2Input,
    config: TeamSpecialistForecastRevisionQualityGateV2Config,
) -> Decimal:
    if not revision.learning_feedback_available:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(revision.learning_feedback_score * config.max_learning_feedback_boost)


def _probability_delta_abs(
    revision: TeamSpecialistForecastRevisionQualityGateV2Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(abs(revision.revised_probability - revision.prior_probability))


def _row_status(
    score: Decimal,
    revision: TeamSpecialistForecastRevisionQualityGateV2Input,
    config: TeamSpecialistForecastRevisionQualityGateV2Config,
) -> str:
    if score < config.watch_score_floor:
        return "blocked"
    if score < config.pass_score_floor or not revision.revision_supported:
        return "watch"
    return "pass"


def _row_reason_codes(
    score: Decimal,
    status: str,
    revision: TeamSpecialistForecastRevisionQualityGateV2Input,
    config: TeamSpecialistForecastRevisionQualityGateV2Config,
) -> tuple[str, ...]:
    reason_codes = [f"team_specialist_forecast_revision_quality_{status}"]
    if not revision.revision_supported:
        reason_codes.append("unsupported_revision_penalty_applied")
    if revision.learning_feedback_available:
        reason_codes.append("learning_feedback_boost_applied")
    if score < config.watch_score_floor:
        reason_codes.append("revision_quality_score_below_watch_floor")
    elif score < config.pass_score_floor:
        reason_codes.append("revision_quality_score_below_pass_floor")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODES,
    )


def _report_status(
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_forecast_revision_quality_gate_empty",)
    reason_codes: list[str] = []
    if any(row.gate_status == "blocked" for row in rows):
        reason_codes.append("team_specialist_forecast_revision_quality_gate_blocked_rows")
    if any(row.gate_status == "watch" for row in rows):
        reason_codes.append("team_specialist_forecast_revision_quality_gate_watch_rows")
    if any(not row.revision_supported for row in rows):
        reason_codes.append(
            "team_specialist_forecast_revision_quality_gate_unsupported_revision_penalty_rows",
        )
    if any(row.learning_feedback_available for row in rows):
        reason_codes.append(
            "team_specialist_forecast_revision_quality_gate_learning_feedback_boost_rows",
        )
    if not reason_codes:
        reason_codes.append("team_specialist_forecast_revision_quality_gate_passed")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODES,
    )


def _status_count(
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.gate_status == status))


def _unsupported_revision_count(
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if not row.revision_supported))


def _learning_feedback_revision_count(
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.learning_feedback_available))


def _average_score(
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.revision_quality_score for row in rows), ZERO)
            / _decimal_count(len(rows)),
        )


def _top_score(rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...]) -> Decimal:
    return max((row.revision_quality_score for row in rows), default=ZERO)


def _bottom_score(
    rows: tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...],
) -> Decimal:
    return min((row.revision_quality_score for row in rows), default=ZERO)


def _normalize_inputs(
    revisions: object,
) -> tuple[TeamSpecialistForecastRevisionQualityGateV2Input, ...]:
    if type(revisions) not in (list, tuple):
        raise ValueError("revisions must be a list or tuple")
    normalized = tuple(revisions)
    seen_forecast_ids: set[str] = set()
    for revision in normalized:
        if type(revision) is not TeamSpecialistForecastRevisionQualityGateV2Input:
            raise ValueError(
                "revisions must contain TeamSpecialistForecastRevisionQualityGateV2Input",
            )
        _require_hard_flags("input", revision)
        if revision.forecast_id in seen_forecast_ids:
            raise ValueError("forecast_id values must be unique")
        seen_forecast_ids.add(revision.forecast_id)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[TeamSpecialistForecastRevisionQualityGateV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TeamSpecialistForecastRevisionQualityGateV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistForecastRevisionQualityGateV2Row",
            )
        _require_hard_flags("row", row)
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(normalized) + 1))
    if tuple(row.rank for row in normalized) != expected_ranks:
        raise ValueError("rows must have sequential positive ranks")
    sorted_rows = tuple(
        sorted(
            normalized,
            key=lambda row: (
                -row.revision_quality_score,
                row.team_id,
                row.specialist_id,
                row.forecast_id,
            ),
        ),
    )
    if normalized != sorted_rows:
        raise ValueError("rows must be sorted by quality score and identifiers")
    return normalized


def _validate_config(config: TeamSpecialistForecastRevisionQualityGateV2Config) -> None:
    weight_total = _clamp_ratio(
        config.evidence_support_weight
        + config.rationale_quality_weight
        + config.calibration_improvement_weight
        + config.timeliness_weight,
    )
    if weight_total != ONE:
        raise ValueError("quality component weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must be less than or equal to pass_score_floor")


def _validate_row_consistency(
    row: TeamSpecialistForecastRevisionQualityGateV2Row,
) -> None:
    expected_delta = _clamp_ratio(abs(row.revised_probability - row.prior_probability))
    if row.probability_delta_abs != expected_delta:
        raise ValueError("probability_delta_abs must match probability values")
    if row.revision_supported and row.unsupported_revision_penalty_applied != ZERO:
        raise ValueError("supported revisions must not carry unsupported penalty")
    if not row.revision_supported and row.unsupported_revision_penalty_applied == ZERO:
        raise ValueError("unsupported revisions must carry unsupported penalty")
    if row.learning_feedback_available and row.learning_feedback_boost_applied == ZERO:
        raise ValueError("available learning feedback must carry a boost")
    if not row.learning_feedback_available and row.learning_feedback_boost_applied != ZERO:
        raise ValueError("unavailable learning feedback must not carry a boost")
    if row.gate_status not in GATE_STATUSES:
        raise ValueError("gate_status is unsupported")
    if row.gate_status == "pass" and (
        "revision_quality_score_below_pass_floor" in row.reason_codes
        or "revision_quality_score_below_watch_floor" in row.reason_codes
    ):
        raise ValueError("passing rows must not carry floor breach reasons")


def _validate_report_consistency(
    report: TeamSpecialistForecastRevisionQualityGateV2Report,
) -> None:
    rows = report.rows
    if report.revision_count != _decimal_count(len(rows)):
        raise ValueError("revision_count must match rows")
    if report.pass_revision_count != _status_count(rows, "pass"):
        raise ValueError("pass_revision_count must match rows")
    if report.watch_revision_count != _status_count(rows, "watch"):
        raise ValueError("watch_revision_count must match rows")
    if report.blocked_revision_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_revision_count must match rows")
    if report.unsupported_revision_count != _unsupported_revision_count(rows):
        raise ValueError("unsupported_revision_count must match rows")
    if report.learning_feedback_revision_count != _learning_feedback_revision_count(rows):
        raise ValueError("learning_feedback_revision_count must match rows")
    if report.average_revision_quality_score != _average_score(rows):
        raise ValueError("average_revision_quality_score must match rows")
    if report.top_revision_quality_score != _top_score(rows):
        raise ValueError("top_revision_quality_score must match rows")
    if report.bottom_revision_quality_score != _bottom_score(rows):
        raise ValueError("bottom_revision_quality_score must match rows")
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_derived_validation_digest(
    report: TeamSpecialistForecastRevisionQualityGateV2Report,
) -> None:
    expected = _derived_validation_digest(asdict(report))
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match report values")


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = {
        key: value
        for key, value in values.items()
        if key != "derived_validation_digest"
    }
    json_payload = json.dumps(
        _payload_value(payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(json_payload.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric values must use Decimal")
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if type(value) is str:
        if _has_unsafe_public_text(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if value is None or type(value) in (bool, Decimal):
        return
    if type(value) is datetime:
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_text(key):
                raise ValueError(f"{path or label} has unsafe public key")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_gate_status(field_name: str, value: object) -> str:
    value = _require_public_string(field_name, value)
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    value = _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected_order = tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in reason_codes
    )
    if reason_codes != expected_order:
        raise ValueError(f"{field_name} must follow reason code order")
    return reason_codes


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _quantize(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
