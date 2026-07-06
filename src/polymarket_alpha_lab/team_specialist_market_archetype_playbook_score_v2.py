"""Phase 1 readonly score module for specialist market archetype playbooks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_MARKET_ARCHETYPE_PLAYBOOK_SCORE_V2_CONFIG_VERSION = (
    "team-specialist-market-archetype-playbook-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

SCORE_STATUSES = ("strong", "watch", "weak")
ROW_REASON_CODES = (
    "team_specialist_market_archetype_playbook_strong",
    "team_specialist_market_archetype_playbook_watch",
    "team_specialist_market_archetype_playbook_weak",
    "archetype_fit_strong",
    "archetype_fit_watch",
    "archetype_fit_weak",
    "playbook_coverage_strong",
    "playbook_coverage_watch",
    "playbook_coverage_weak",
    "evidence_alignment_strong",
    "evidence_alignment_watch",
    "evidence_alignment_weak",
    "risk_control_strong",
    "risk_control_watch",
    "risk_control_weak",
    "review_learning_strong",
    "review_learning_watch",
    "review_learning_weak",
    "weak_playbook_gap_flag",
    "playbook_gap_clear",
)
REPORT_REASON_CODES = (
    "team_specialist_market_archetype_playbook_score_strong",
    "team_specialist_market_archetype_playbook_score_watch_rows",
    "team_specialist_market_archetype_playbook_score_weak_rows",
    "team_specialist_market_archetype_playbook_score_empty",
    "weak_playbook_gap_flags",
)
UNSAFE_PUBLIC_SURFACE_TERMS = (
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
    "DEFAULT_TEAM_SPECIALIST_MARKET_ARCHETYPE_PLAYBOOK_SCORE_V2_CONFIG_VERSION",
    "TeamSpecialistMarketArchetypePlaybookScoreV2Config",
    "TeamSpecialistMarketArchetypePlaybookScoreV2Observation",
    "TeamSpecialistMarketArchetypePlaybookScoreV2Row",
    "TeamSpecialistMarketArchetypePlaybookScoreV2Report",
    "build_team_specialist_market_archetype_playbook_score_v2",
    "team_specialist_market_archetype_playbook_score_v2_payload",
    "validate_team_specialist_market_archetype_playbook_score_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistMarketArchetypePlaybookScoreV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_MARKET_ARCHETYPE_PLAYBOOK_SCORE_V2_CONFIG_VERSION
    )
    archetype_fit_weight: Decimal = Decimal("0.300000")
    playbook_readiness_weight: Decimal = Decimal("0.250000")
    evidence_alignment_weight: Decimal = Decimal("0.200000")
    risk_control_weight: Decimal = Decimal("0.150000")
    review_learning_weight: Decimal = Decimal("0.100000")
    max_critical_gap_count: Decimal = Decimal("4")
    weak_gap_floor: Decimal = Decimal("0.500000")
    strong_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not allowed")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "archetype_fit_weight",
            "playbook_readiness_weight",
            "evidence_alignment_weight",
            "risk_control_weight",
            "review_learning_weight",
            "weak_gap_floor",
            "strong_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_critical_gap_count",
            _normalize_positive_integral_decimal(
                "max_critical_gap_count",
                self.max_critical_gap_count,
            ),
        )
        _require_hard_flags("TeamSpecialistMarketArchetypePlaybookScoreV2Config", self)
        _validate_config(self)
        _reject_unsafe_public_surface(
            "TeamSpecialistMarketArchetypePlaybookScoreV2Config",
            _public_payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistMarketArchetypePlaybookScoreV2Observation:
    team_id: str
    archetype_id: str
    archetype_fit_score: Decimal
    playbook_step_coverage_score: Decimal
    evidence_alignment_score: Decimal
    risk_control_score: Decimal
    review_learning_score: Decimal
    critical_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not allowed")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "archetype_id",
            _require_public_string("archetype_id", self.archetype_id),
        )
        for field_name in (
            "archetype_fit_score",
            "playbook_step_coverage_score",
            "evidence_alignment_score",
            "risk_control_score",
            "review_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "critical_gap_count",
            _normalize_nonnegative_integral_decimal(
                "critical_gap_count",
                self.critical_gap_count,
            ),
        )
        _require_hard_flags(
            "TeamSpecialistMarketArchetypePlaybookScoreV2Observation",
            self,
        )
        _reject_unsafe_public_surface(
            "TeamSpecialistMarketArchetypePlaybookScoreV2Observation",
            _public_payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistMarketArchetypePlaybookScoreV2Row:
    score_rank: Decimal
    team_id: str
    archetype_id: str
    archetype_fit_score: Decimal
    playbook_step_coverage_score: Decimal
    playbook_gap_health_score: Decimal
    playbook_readiness_score: Decimal
    evidence_alignment_score: Decimal
    risk_control_score: Decimal
    review_learning_score: Decimal
    critical_gap_count: Decimal
    market_archetype_playbook_score: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not allowed")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "score_rank",
            _normalize_positive_integral_decimal("score_rank", self.score_rank),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "archetype_id",
            _require_public_string("archetype_id", self.archetype_id),
        )
        for field_name in (
            "archetype_fit_score",
            "playbook_step_coverage_score",
            "playbook_gap_health_score",
            "playbook_readiness_score",
            "evidence_alignment_score",
            "risk_control_score",
            "review_learning_score",
            "market_archetype_playbook_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "critical_gap_count",
            _normalize_nonnegative_integral_decimal(
                "critical_gap_count",
                self.critical_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "score_status",
            _require_score_status("score_status", self.score_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistMarketArchetypePlaybookScoreV2Row", self)
        _reject_unsafe_public_surface(
            "TeamSpecialistMarketArchetypePlaybookScoreV2Row",
            _public_payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistMarketArchetypePlaybookScoreV2Report:
    generated_at: datetime
    config_version: str
    score_status: str
    team_count: Decimal
    strong_team_count: Decimal
    watch_team_count: Decimal
    weak_team_count: Decimal
    weak_playbook_gap_count: Decimal
    average_market_archetype_playbook_score: Decimal
    top_market_archetype_playbook_score: Decimal
    bottom_market_archetype_playbook_score: Decimal
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not allowed")

    def __post_init__(self) -> None:
        _require_hard_flags("TeamSpecialistMarketArchetypePlaybookScoreV2Report", self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "score_status",
            _require_score_status("score_status", self.score_status),
        )
        for field_name in (
            "team_count",
            "strong_team_count",
            "watch_team_count",
            "weak_team_count",
            "weak_playbook_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_market_archetype_playbook_score",
            "top_market_archetype_playbook_score",
            "bottom_market_archetype_playbook_score",
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
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _reject_unsafe_public_surface(
            "TeamSpecialistMarketArchetypePlaybookScoreV2Report",
            _public_payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        return team_specialist_market_archetype_playbook_score_v2_payload(self)


def build_team_specialist_market_archetype_playbook_score_v2(
    observations: object,
    *,
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistMarketArchetypePlaybookScoreV2Report:
    if config is None:
        config = TeamSpecialistMarketArchetypePlaybookScoreV2Config()
    if type(config) is not TeamSpecialistMarketArchetypePlaybookScoreV2Config:
        raise ValueError(
            "config must be a TeamSpecialistMarketArchetypePlaybookScoreV2Config",
        )
    _require_hard_flags("TeamSpecialistMarketArchetypePlaybookScoreV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(score_rank=index, observation=item, config=config)
        for index, item in enumerate(_sorted_observations(normalized, config), start=1)
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "score_status": status,
        "team_count": _decimal_count(len(rows)),
        "strong_team_count": _status_count(rows, "strong"),
        "watch_team_count": _status_count(rows, "watch"),
        "weak_team_count": _status_count(rows, "weak"),
        "weak_playbook_gap_count": _weak_playbook_gap_count(rows),
        "average_market_archetype_playbook_score": _average_score(rows),
        "top_market_archetype_playbook_score": _top_score(rows),
        "bottom_market_archetype_playbook_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistMarketArchetypePlaybookScoreV2Report(**values)


def team_specialist_market_archetype_playbook_score_v2_payload(
    report: TeamSpecialistMarketArchetypePlaybookScoreV2Report,
) -> dict[str, object]:
    if type(report) is not TeamSpecialistMarketArchetypePlaybookScoreV2Report:
        raise ValueError(
            "report must be a TeamSpecialistMarketArchetypePlaybookScoreV2Report",
        )
    _validate_report_consistency(report)
    payload = _public_payload_value(asdict(report))
    _reject_unsafe_public_surface(
        "team_specialist_market_archetype_playbook_score_v2_payload",
        payload,
    )
    _reject_public_payload_numbers(payload)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    return payload


def validate_team_specialist_market_archetype_playbook_score_v2_payload(
    payload: object,
) -> bool:
    _reject_unsafe_public_surface(
        "validate_team_specialist_market_archetype_playbook_score_v2_payload",
        payload,
    )
    _reject_public_payload_numbers(payload)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    TeamSpecialistMarketArchetypePlaybookScoreV2Report(
        generated_at=_parse_datetime("generated_at", payload.get("generated_at")),
        config_version=_parse_string("config_version", payload.get("config_version")),
        score_status=_parse_string("score_status", payload.get("score_status")),
        team_count=_parse_decimal("team_count", payload.get("team_count")),
        strong_team_count=_parse_decimal(
            "strong_team_count",
            payload.get("strong_team_count"),
        ),
        watch_team_count=_parse_decimal(
            "watch_team_count",
            payload.get("watch_team_count"),
        ),
        weak_team_count=_parse_decimal("weak_team_count", payload.get("weak_team_count")),
        weak_playbook_gap_count=_parse_decimal(
            "weak_playbook_gap_count",
            payload.get("weak_playbook_gap_count"),
        ),
        average_market_archetype_playbook_score=_parse_decimal(
            "average_market_archetype_playbook_score",
            payload.get("average_market_archetype_playbook_score"),
        ),
        top_market_archetype_playbook_score=_parse_decimal(
            "top_market_archetype_playbook_score",
            payload.get("top_market_archetype_playbook_score"),
        ),
        bottom_market_archetype_playbook_score=_parse_decimal(
            "bottom_market_archetype_playbook_score",
            payload.get("bottom_market_archetype_playbook_score"),
        ),
        rows=_parse_rows(payload.get("rows")),
        reason_codes=_parse_reason_codes_from_payload(
            "reason_codes",
            payload.get("reason_codes"),
        ),
        derived_validation_digest=_parse_string(
            "derived_validation_digest",
            payload.get("derived_validation_digest"),
        ),
        paper_only=_parse_bool("paper_only", payload.get("paper_only")),
        report_only=_parse_bool("report_only", payload.get("report_only")),
        readonly=_parse_bool("readonly", payload.get("readonly")),
    )
    return True


def _sorted_observations(
    observations: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Observation, ...],
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Observation, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                -_score_for_observation(item, config),
                item.team_id,
                item.archetype_id,
            ),
        ),
    )


def _row_for_observation(
    *,
    score_rank: int,
    observation: TeamSpecialistMarketArchetypePlaybookScoreV2Observation,
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> TeamSpecialistMarketArchetypePlaybookScoreV2Row:
    gap_health = _gap_health_score(observation.critical_gap_count, config)
    readiness = _playbook_readiness_score(observation, config)
    score = _score_for_observation(observation, config)
    status = _score_status(score, config)
    return TeamSpecialistMarketArchetypePlaybookScoreV2Row(
        score_rank=_decimal_count(score_rank),
        team_id=observation.team_id,
        archetype_id=observation.archetype_id,
        archetype_fit_score=observation.archetype_fit_score,
        playbook_step_coverage_score=observation.playbook_step_coverage_score,
        playbook_gap_health_score=gap_health,
        playbook_readiness_score=readiness,
        evidence_alignment_score=observation.evidence_alignment_score,
        risk_control_score=observation.risk_control_score,
        review_learning_score=observation.review_learning_score,
        critical_gap_count=observation.critical_gap_count,
        market_archetype_playbook_score=score,
        score_status=status,
        reason_codes=_row_reason_codes(observation, status, readiness, config),
    )


def _score_for_observation(
    observation: TeamSpecialistMarketArchetypePlaybookScoreV2Observation,
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            observation.archetype_fit_score * config.archetype_fit_weight
            + _playbook_readiness_score(observation, config)
            * config.playbook_readiness_weight
            + observation.evidence_alignment_score * config.evidence_alignment_weight
            + observation.risk_control_score * config.risk_control_weight
            + observation.review_learning_score * config.review_learning_weight
        )
        return _clamp_ratio(score)


def _playbook_readiness_score(
    observation: TeamSpecialistMarketArchetypePlaybookScoreV2Observation,
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            observation.playbook_step_coverage_score
            + _gap_health_score(observation.critical_gap_count, config)
        ) / Decimal("2")
        return _clamp_ratio(score)


def _gap_health_score(
    critical_gap_count: Decimal,
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - critical_gap_count / config.max_critical_gap_count)


def _score_status(
    score: Decimal,
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> str:
    if score >= config.strong_score_floor:
        return "strong"
    if score >= config.watch_score_floor:
        return "watch"
    return "weak"


def _report_status(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
) -> str:
    if not rows:
        return "weak"
    if any(row.score_status == "weak" for row in rows):
        return "weak"
    if any(row.score_status == "watch" for row in rows):
        return "watch"
    return "strong"


def _row_reason_codes(
    observation: TeamSpecialistMarketArchetypePlaybookScoreV2Observation,
    status: str,
    readiness: Decimal,
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> tuple[str, ...]:
    gap_reason = "weak_playbook_gap_flag"
    if readiness >= config.weak_gap_floor:
        gap_reason = "playbook_gap_clear"
    return (
        f"team_specialist_market_archetype_playbook_{status}",
        _tier_reason(
            observation.archetype_fit_score,
            strong_reason="archetype_fit_strong",
            watch_reason="archetype_fit_watch",
            weak_reason="archetype_fit_weak",
        ),
        _tier_reason(
            observation.playbook_step_coverage_score,
            strong_reason="playbook_coverage_strong",
            watch_reason="playbook_coverage_watch",
            weak_reason="playbook_coverage_weak",
        ),
        _tier_reason(
            observation.evidence_alignment_score,
            strong_reason="evidence_alignment_strong",
            watch_reason="evidence_alignment_watch",
            weak_reason="evidence_alignment_weak",
        ),
        _tier_reason(
            observation.risk_control_score,
            strong_reason="risk_control_strong",
            watch_reason="risk_control_watch",
            weak_reason="risk_control_weak",
        ),
        _tier_reason(
            observation.review_learning_score,
            strong_reason="review_learning_strong",
            watch_reason="review_learning_watch",
            weak_reason="review_learning_weak",
        ),
        gap_reason,
    )


def _tier_reason(
    value: Decimal,
    *,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= Decimal("0.800000"):
        return strong_reason
    if value >= Decimal("0.600000"):
        return watch_reason
    return weak_reason


def _report_reason_codes(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_market_archetype_playbook_score_empty",)
    reasons: list[str] = []
    if any(row.score_status == "weak" for row in rows):
        reasons.append("team_specialist_market_archetype_playbook_score_weak_rows")
    if any(row.score_status == "watch" for row in rows):
        reasons.append("team_specialist_market_archetype_playbook_score_watch_rows")
    if _weak_playbook_gap_count(rows) > ZERO:
        reasons.append("weak_playbook_gap_flags")
    if not reasons and status == "strong":
        reasons.append("team_specialist_market_archetype_playbook_score_strong")
    return tuple(reasons)


def _normalize_observations(
    value: object,
) -> tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Observation, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("observations must be an iterable")
    observations = tuple(value)
    for item in observations:
        if type(item) is not TeamSpecialistMarketArchetypePlaybookScoreV2Observation:
            raise ValueError(
                "observations must contain "
                "TeamSpecialistMarketArchetypePlaybookScoreV2Observation",
            )
        _require_hard_flags(
            "TeamSpecialistMarketArchetypePlaybookScoreV2Observation",
            item,
        )
    keys = tuple((item.team_id, item.archetype_id) for item in observations)
    if len(set(keys)) != len(keys):
        raise ValueError("observations must not contain duplicate team/archetype keys")
    return observations


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not TeamSpecialistMarketArchetypePlaybookScoreV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistMarketArchetypePlaybookScoreV2Row",
            )
    return value


def _status_count(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.score_status == status))


def _weak_playbook_gap_count(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if "weak_playbook_gap_flag" in row.reason_codes),
    )


def _average_score(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.market_archetype_playbook_score for row in rows)
            / Decimal(len(rows)),
        )


def _top_score(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.market_archetype_playbook_score for row in rows)


def _bottom_score(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.market_archetype_playbook_score for row in rows)


def _validate_config(
    config: TeamSpecialistMarketArchetypePlaybookScoreV2Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.archetype_fit_weight
            + config.playbook_readiness_weight
            + config.evidence_alignment_weight
            + config.risk_control_weight
            + config.review_learning_weight
        ).quantize(SCORE_QUANT)
    if weight_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_score_floor > config.strong_score_floor:
        raise ValueError("watch_score_floor must not exceed strong_score_floor")


def _validate_row_consistency(
    row: TeamSpecialistMarketArchetypePlaybookScoreV2Row,
) -> None:
    readiness = _clamp_ratio(
        (row.playbook_step_coverage_score + row.playbook_gap_health_score)
        / Decimal("2"),
    )
    if row.playbook_readiness_score != readiness:
        raise ValueError("playbook_readiness_score must match inputs")


def _validate_report_consistency(
    report: TeamSpecialistMarketArchetypePlaybookScoreV2Report,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    rows = report.rows
    if report.team_count != _decimal_count(len(rows)):
        raise ValueError("team_count must match rows")
    if (
        report.strong_team_count != _status_count(rows, "strong")
        or report.watch_team_count != _status_count(rows, "watch")
        or report.weak_team_count != _status_count(rows, "weak")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.strong_team_count + report.watch_team_count + report.weak_team_count
        != report.team_count
    ):
        raise ValueError("status counts must sum to team_count")
    if report.weak_playbook_gap_count != _weak_playbook_gap_count(rows):
        raise ValueError("weak_playbook_gap_count must match rows")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.score_status != expected_status:
        raise ValueError("score_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.score_status):
        raise ValueError("reason_codes must match rows")
    if report.average_market_archetype_playbook_score != _average_score(rows):
        raise ValueError("average_market_archetype_playbook_score must match rows")
    if report.top_market_archetype_playbook_score != _top_score(rows):
        raise ValueError("top_market_archetype_playbook_score must match rows")
    if report.bottom_market_archetype_playbook_score != _bottom_score(rows):
        raise ValueError("bottom_market_archetype_playbook_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.market_archetype_playbook_score,
                row.team_id,
                row.archetype_id,
            ),
        ),
    )
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if rows != expected or tuple(row.score_rank for row in rows) != expected_ranks:
        raise ValueError("rows must be sorted by score and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_surface(field_name, normalized)
    return normalized


def _require_score_status(field_name: str, value: object) -> str:
    normalized = _require_public_string(field_name, value)
    if normalized not in SCORE_STATUSES:
        raise ValueError(f"{field_name} must be strong, watch, or weak")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _public_payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _public_payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("public payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _public_payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_public_payload_value(item) for item in value]
    if type(value) is list:
        return [_public_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("public payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _public_payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_surface("derived_validation_digest", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public surface in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_PUBLIC_SURFACE_TERMS):
        raise ValueError(f"unsafe public surface in {label}")


def _reject_public_payload_numbers(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_payload_numbers(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_payload_numbers(item)
        return
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be Decimal strings")


def _parse_rows(
    value: object,
) -> tuple[TeamSpecialistMarketArchetypePlaybookScoreV2Row, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list in public payload")
    return tuple(_parse_row(item) for item in value)


def _parse_row(value: object) -> TeamSpecialistMarketArchetypePlaybookScoreV2Row:
    if type(value) is not dict:
        raise ValueError("rows must contain dict values")
    return TeamSpecialistMarketArchetypePlaybookScoreV2Row(
        score_rank=_parse_decimal("score_rank", value.get("score_rank")),
        team_id=_parse_string("team_id", value.get("team_id")),
        archetype_id=_parse_string("archetype_id", value.get("archetype_id")),
        archetype_fit_score=_parse_decimal(
            "archetype_fit_score",
            value.get("archetype_fit_score"),
        ),
        playbook_step_coverage_score=_parse_decimal(
            "playbook_step_coverage_score",
            value.get("playbook_step_coverage_score"),
        ),
        playbook_gap_health_score=_parse_decimal(
            "playbook_gap_health_score",
            value.get("playbook_gap_health_score"),
        ),
        playbook_readiness_score=_parse_decimal(
            "playbook_readiness_score",
            value.get("playbook_readiness_score"),
        ),
        evidence_alignment_score=_parse_decimal(
            "evidence_alignment_score",
            value.get("evidence_alignment_score"),
        ),
        risk_control_score=_parse_decimal(
            "risk_control_score",
            value.get("risk_control_score"),
        ),
        review_learning_score=_parse_decimal(
            "review_learning_score",
            value.get("review_learning_score"),
        ),
        critical_gap_count=_parse_decimal(
            "critical_gap_count",
            value.get("critical_gap_count"),
        ),
        market_archetype_playbook_score=_parse_decimal(
            "market_archetype_playbook_score",
            value.get("market_archetype_playbook_score"),
        ),
        score_status=_parse_string("score_status", value.get("score_status")),
        reason_codes=_parse_reason_codes_from_payload(
            "reason_codes",
            value.get("reason_codes"),
        ),
        paper_only=_parse_bool("paper_only", value.get("paper_only")),
        report_only=_parse_bool("report_only", value.get("report_only")),
        readonly=_parse_bool("readonly", value.get("readonly")),
    )


def _parse_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string in public payload")
    try:
        parsed = Decimal(value)
    except Exception as error:
        raise ValueError(
            f"{field_name} must be a Decimal string in public payload",
        ) from error
    return parsed


def _parse_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an ISO datetime string") from error
    return parsed


def _parse_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string in public payload")
    return value


def _parse_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool in public payload")
    return value


def _parse_reason_codes_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list in public payload")
    return tuple(_parse_string(field_name, item) for item in value)
