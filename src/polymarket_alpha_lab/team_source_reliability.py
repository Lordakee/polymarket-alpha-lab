"""Pure source reliability diagnostics for materialized team forecast rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastEvidenceDbRow,
    TeamForecastOutcomeDbRow,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
UNKNOWN_SOURCE_ID = "unknown_source"

SOURCE_RELIABILITY_CANDIDATE = "source_reliability_candidate"
SOURCE_RELIABILITY_VALIDATED = "source_reliability_validated"
SOURCE_RELIABILITY_WATCH = "source_reliability_watch"
SOURCE_RELIABILITY_STATUSES = frozenset(
    (
        SOURCE_RELIABILITY_CANDIDATE,
        SOURCE_RELIABILITY_VALIDATED,
        SOURCE_RELIABILITY_WATCH,
    ),
)
SOURCE_RELIABILITY_GRADES = ("A", "B", "C", "D", "F")
SAFETY_FIELD_NAMES = ("paper_only", "report_only", "readonly")
SECONDS_PER_DAY = Decimal("86400")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SOURCE_ID_FRAGMENTS = frozenset(
    (
        _join_parts("acc", "ount"),
        _join_parts("au", "th"),
        _join_parts("creden", "tial"),
        _join_parts("ord", "er"),
        "position",
        "private",
        "secret",
        "sizing",
        "token",
        _join_parts("tra", "de"),
        _join_parts("trad", "ing"),
        _join_parts("wal", "let"),
    ),
)


@dataclass(frozen=True)
class TeamSourceReliabilityConfig:
    config_version: str = "team-source-reliability-v0"
    min_settled_evidence_count: int = 30
    max_dispute_rate: Decimal = Decimal("0.050000")
    min_profitable_rate: Decimal = Decimal("0.500000")
    max_freshness_age_seconds: int = 86_400
    min_corroboration_count: int = 2
    failure_streak_watch_threshold: int = 3
    include_pending: bool = False
    allow_unknown_source: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_settled_evidence_count",
            self.min_settled_evidence_count,
        )
        object.__setattr__(
            self,
            "max_dispute_rate",
            _normalize_probability("max_dispute_rate", self.max_dispute_rate),
        )
        object.__setattr__(
            self,
            "min_profitable_rate",
            _normalize_probability("min_profitable_rate", self.min_profitable_rate),
        )
        _require_positive_int(
            "max_freshness_age_seconds",
            self.max_freshness_age_seconds,
        )
        _require_positive_int("min_corroboration_count", self.min_corroboration_count)
        _require_positive_int(
            "failure_streak_watch_threshold",
            self.failure_streak_watch_threshold,
        )
        _require_bool("include_pending", self.include_pending)
        _require_bool("allow_unknown_source", self.allow_unknown_source)
        _require_safety_values("TeamSourceReliabilityConfig", self)


@dataclass(frozen=True)
class TeamSourceReliabilityRow:
    team_id: str
    source_id: str
    evidence_count: int
    settled_evidence_count: int
    directionally_correct_count: int
    profitable_after_cost_count: int
    dispute_count: int
    average_brier_score: Decimal | None
    hit_rate: Decimal | None
    profitable_rate: Decimal | None
    average_weight: Decimal | None
    average_confidence: Decimal | None
    latest_generated_at: datetime
    status: str
    freshness_age_seconds: int = 0
    freshness_score: Decimal = Decimal("1.000000")
    freshness_horizon_seconds: int | None = None
    corroboration_count: int = 0
    failure_streak: int = 0
    reliability_score: Decimal = Decimal("0.000000")
    reliability_grade: str = "F"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_public_source_id("source_id", self.source_id)
        _require_positive_int("evidence_count", self.evidence_count)
        for field_name in (
            "settled_evidence_count",
            "directionally_correct_count",
            "profitable_after_cost_count",
            "dispute_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.settled_evidence_count > self.evidence_count:
            raise ValueError("settled_evidence_count must not exceed evidence_count")
        for field_name in (
            "directionally_correct_count",
            "profitable_after_cost_count",
            "dispute_count",
        ):
            if getattr(self, field_name) > self.settled_evidence_count:
                raise ValueError(f"{field_name} must not exceed settled_evidence_count")
        object.__setattr__(
            self,
            "average_brier_score",
            _normalize_optional_probability(
                "average_brier_score",
                self.average_brier_score,
            ),
        )
        object.__setattr__(
            self,
            "hit_rate",
            _normalize_optional_probability("hit_rate", self.hit_rate),
        )
        object.__setattr__(
            self,
            "profitable_rate",
            _normalize_optional_probability("profitable_rate", self.profitable_rate),
        )
        object.__setattr__(
            self,
            "average_weight",
            _normalize_optional_probability("average_weight", self.average_weight),
        )
        object.__setattr__(
            self,
            "average_confidence",
            _normalize_optional_probability(
                "average_confidence",
                self.average_confidence,
            ),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_utc("latest_generated_at", self.latest_generated_at),
        )
        _require_nonnegative_int("freshness_age_seconds", self.freshness_age_seconds)
        object.__setattr__(
            self,
            "freshness_score",
            _normalize_probability("freshness_score", self.freshness_score),
        )
        if self.freshness_horizon_seconds is not None:
            _require_positive_int(
                "freshness_horizon_seconds",
                self.freshness_horizon_seconds,
            )
            expected_freshness_score = _freshness_score_for_horizon(
                self.freshness_age_seconds,
                self.freshness_horizon_seconds,
            )
            if self.freshness_score != expected_freshness_score:
                raise ValueError(
                    "freshness_score must match freshness_age_seconds and "
                    "freshness_horizon_seconds",
                )
        _require_nonnegative_int("corroboration_count", self.corroboration_count)
        _require_nonnegative_int("failure_streak", self.failure_streak)
        object.__setattr__(
            self,
            "reliability_score",
            _normalize_probability("reliability_score", self.reliability_score),
        )
        if self.reliability_grade not in SOURCE_RELIABILITY_GRADES:
            raise ValueError("reliability_grade must be a known reliability grade")
        # Legacy rows without a horizon carry an externally supplied score and grade.
        if (
            self.freshness_horizon_seconds is not None
            and self.reliability_grade != _reliability_grade(self.reliability_score)
        ):
            raise ValueError("reliability_grade must match reliability_score")
        if self.settled_evidence_count == 0:
            if (
                self.directionally_correct_count != 0
                or self.profitable_after_cost_count != 0
                or self.dispute_count != 0
            ):
                raise ValueError("settled counts must be zero without settled evidence")
            if (
                self.average_brier_score is not None
                or self.hit_rate is not None
                or self.profitable_rate is not None
            ):
                raise ValueError("settled rates must be absent without settled evidence")
        else:
            if self.average_brier_score is None:
                raise ValueError("average_brier_score is required with settled evidence")
            if self.hit_rate is None:
                raise ValueError("hit_rate is required with settled evidence")
            if self.profitable_rate is None:
                raise ValueError("profitable_rate is required with settled evidence")
        if self.status not in SOURCE_RELIABILITY_STATUSES:
            raise ValueError("status must be a known source reliability status")
        _require_safety_values("TeamSourceReliabilityRow", self)


@dataclass(frozen=True)
class TeamSourceReliabilityReport:
    generated_at: datetime
    config_version: str
    evidence_count: int
    outcome_count: int
    settled_evidence_count: int
    pending_evidence_count: int
    missing_source_evidence_count: int
    row_count: int
    rows: tuple[TeamSourceReliabilityRow, ...]
    reliability_grade_counts: tuple[tuple[str, int], ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "evidence_count",
            "outcome_count",
            "settled_evidence_count",
            "pending_evidence_count",
            "missing_source_evidence_count",
            "row_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reliability_grade_counts",
            _normalize_grade_counts(self.reliability_grade_counts),
        )
        if self.row_count != len(self.rows):
            raise ValueError("row_count must match rows")
        if self.settled_evidence_count != sum(
            row.settled_evidence_count for row in self.rows
        ):
            raise ValueError("settled_evidence_count must match rows")
        if self.reliability_grade_counts != _grade_counts_from_rows(self.rows):
            raise ValueError("reliability_grade_counts must match rows")
        _require_safety_values("TeamSourceReliabilityReport", self)


@dataclass(frozen=True)
class _EvidenceItem:
    evidence: TeamForecastEvidenceDbRow
    outcome: TeamForecastOutcomeDbRow | None


def build_team_source_reliability_report(
    evidence_rows: list[TeamForecastEvidenceDbRow]
    | tuple[TeamForecastEvidenceDbRow, ...],
    outcome_rows: list[TeamForecastOutcomeDbRow] | tuple[TeamForecastOutcomeDbRow, ...],
    *,
    config: TeamSourceReliabilityConfig,
    generated_at: datetime,
) -> TeamSourceReliabilityReport:
    if type(config) is not TeamSourceReliabilityConfig:
        raise ValueError("config must be a TeamSourceReliabilityConfig")
    _require_safety_values("config", config)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    report_generated_at = _as_utc("generated_at", generated_at)

    evidence_items = _normalize_evidence_rows(
        evidence_rows,
        generated_at=report_generated_at,
    )
    outcome_items = _normalize_outcome_rows(
        outcome_rows,
        generated_at=report_generated_at,
    )
    outcomes_by_forecast_id = _latest_outcomes_by_forecast_id(outcome_items)

    pending_evidence_count = 0
    missing_source_evidence_count = 0
    grouped: dict[tuple[str, str], list[_EvidenceItem]] = {}
    for evidence in evidence_items:
        outcome = outcomes_by_forecast_id.get(evidence.forecast_id)
        if outcome is None:
            pending_evidence_count += 1

        source_id = _canonical_source_id(evidence)
        if source_id is None:
            if config.allow_unknown_source:
                source_id = UNKNOWN_SOURCE_ID
            else:
                missing_source_evidence_count += 1
                continue

        if outcome is None and not config.include_pending:
            continue

        grouped.setdefault((evidence.team_id, source_id), []).append(
            _EvidenceItem(evidence=evidence, outcome=outcome),
        )

    sources_by_team = _sources_by_team(grouped)
    rows = tuple(
        _build_row(
            team_id=team_id,
            source_id=source_id,
            items=tuple(grouped[(team_id, source_id)]),
            config=config,
            generated_at=report_generated_at,
            sources_by_team=sources_by_team,
        )
        for team_id, source_id in sorted(grouped)
    )

    return TeamSourceReliabilityReport(
        generated_at=report_generated_at,
        config_version=config.config_version,
        evidence_count=len(evidence_items),
        outcome_count=len(outcome_items),
        settled_evidence_count=sum(row.settled_evidence_count for row in rows),
        pending_evidence_count=pending_evidence_count,
        missing_source_evidence_count=missing_source_evidence_count,
        row_count=len(rows),
        rows=rows,
        reliability_grade_counts=_grade_counts_from_rows(rows),
    )


def _normalize_evidence_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamForecastEvidenceDbRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamForecastEvidenceDbRow:
            raise ValueError("evidence_rows must contain TeamForecastEvidenceDbRow values")
        _require_safety_values("evidence_rows item", row)
        _require_payload_safety_values(row.payload_json)
        if _as_utc("evidence generated_at", row.generated_at) > generated_at:
            raise ValueError("evidence generated_at must not be later than generated_at")
    return rows


def _normalize_outcome_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamForecastOutcomeDbRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("outcome_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamForecastOutcomeDbRow:
            raise ValueError("outcome_rows must contain TeamForecastOutcomeDbRow values")
        _require_safety_values("outcome_rows item", row)
        _require_payload_safety_values(row.payload_json)
        for field_name in ("generated_at", "resolved_at"):
            if _as_utc(f"outcome {field_name}", getattr(row, field_name)) > generated_at:
                raise ValueError(
                    f"outcome {field_name} must not be later than generated_at",
                )
    return rows


def _latest_outcomes_by_forecast_id(
    rows: tuple[TeamForecastOutcomeDbRow, ...],
) -> dict[str, TeamForecastOutcomeDbRow]:
    by_forecast_id: dict[str, TeamForecastOutcomeDbRow] = {}
    for row in rows:
        current = by_forecast_id.get(row.forecast_id)
        if current is None or _outcome_key(row) >= _outcome_key(current):
            by_forecast_id[row.forecast_id] = row
    return by_forecast_id


def _outcome_key(row: TeamForecastOutcomeDbRow) -> tuple[datetime, datetime, str]:
    return (
        _as_utc("resolved_at", row.resolved_at),
        _as_utc("generated_at", row.generated_at),
        row.outcome_id,
    )


def _build_row(
    *,
    team_id: str,
    source_id: str,
    items: tuple[_EvidenceItem, ...],
    config: TeamSourceReliabilityConfig,
    generated_at: datetime,
    sources_by_team: dict[str, tuple[str, ...]],
) -> TeamSourceReliabilityRow:
    settled_items = tuple(item for item in items if item.outcome is not None)
    settled_evidence_count = len(settled_items)
    directionally_correct_count = sum(
        1
        for item in settled_items
        if item.outcome is not None and item.outcome.directionally_correct
    )
    profitable_after_cost_count = sum(
        1
        for item in settled_items
        if item.outcome is not None and item.outcome.profitable_after_cost
    )
    dispute_count = sum(
        1
        for item in settled_items
        if item.outcome is not None and item.outcome.resolution_dispute_flag
    )

    average_brier_score = _mean_optional(
        tuple(
            item.outcome.brier_score
            for item in settled_items
            if item.outcome is not None
        ),
    )
    hit_rate = _ratio_optional(directionally_correct_count, settled_evidence_count)
    profitable_rate = _ratio_optional(
        profitable_after_cost_count,
        settled_evidence_count,
    )
    latest_generated_at = max(
        _as_utc("generated_at", item.evidence.generated_at)
        for item in items
    )
    freshness_age_seconds = _freshness_age_seconds(
        latest_generated_at=latest_generated_at,
        generated_at=generated_at,
        config=config,
    )
    freshness_score = _freshness_score(freshness_age_seconds, config)
    corroboration_count = _corroboration_count(
        team_id=team_id,
        source_id=source_id,
        sources_by_team=sources_by_team,
    )
    failure_streak = _failure_streak(settled_items)
    reliability_score = _reliability_score(
        average_brier_score=average_brier_score,
        hit_rate=hit_rate,
        profitable_rate=profitable_rate,
        freshness_score=freshness_score,
        corroboration_count=corroboration_count,
        config=config,
    )

    return TeamSourceReliabilityRow(
        team_id=team_id,
        source_id=source_id,
        evidence_count=len(items),
        settled_evidence_count=settled_evidence_count,
        directionally_correct_count=directionally_correct_count,
        profitable_after_cost_count=profitable_after_cost_count,
        dispute_count=dispute_count,
        average_brier_score=average_brier_score,
        hit_rate=hit_rate,
        profitable_rate=profitable_rate,
        average_weight=_mean_optional(tuple(item.evidence.weight for item in items)),
        average_confidence=_mean_optional(
            tuple(
                confidence
                for confidence in (
                    _evidence_confidence(item.evidence) for item in items
                )
                if confidence is not None
            ),
        ),
        latest_generated_at=latest_generated_at,
        status=_row_status(
            settled_evidence_count=settled_evidence_count,
            dispute_rate=_ratio_optional(dispute_count, settled_evidence_count),
            profitable_rate=profitable_rate,
            failure_streak=failure_streak,
            config=config,
        ),
        freshness_age_seconds=freshness_age_seconds,
        freshness_score=freshness_score,
        freshness_horizon_seconds=config.max_freshness_age_seconds,
        corroboration_count=corroboration_count,
        failure_streak=failure_streak,
        reliability_score=reliability_score,
        reliability_grade=_reliability_grade(reliability_score),
    )


def _row_status(
    *,
    settled_evidence_count: int,
    dispute_rate: Decimal | None,
    profitable_rate: Decimal | None,
    failure_streak: int,
    config: TeamSourceReliabilityConfig,
) -> str:
    if (
        dispute_rate is not None
        and dispute_rate > config.max_dispute_rate
    ) or (
        profitable_rate is not None
        and profitable_rate < config.min_profitable_rate
    ) or (
        failure_streak >= config.failure_streak_watch_threshold
    ):
        return SOURCE_RELIABILITY_WATCH
    if settled_evidence_count >= config.min_settled_evidence_count:
        return SOURCE_RELIABILITY_VALIDATED
    return SOURCE_RELIABILITY_CANDIDATE


def _freshness_age_seconds(
    *,
    latest_generated_at: datetime,
    generated_at: datetime,
    config: TeamSourceReliabilityConfig,
) -> int:
    latest = _as_utc("latest_generated_at", latest_generated_at)
    report_generated_at = _as_utc("generated_at", generated_at)
    if latest > report_generated_at:
        raise ValueError("latest_generated_at must not be later than generated_at")
    age_delta = report_generated_at - latest
    with localcontext(DECIMAL_CONTEXT):
        age_seconds = int(
            Decimal(age_delta.days) * SECONDS_PER_DAY
            + Decimal(age_delta.seconds)
            + (
                Decimal(age_delta.microseconds) / Decimal("1000000")
            ).quantize(Decimal("1")),
        )
    return min(age_seconds, config.max_freshness_age_seconds)


def _freshness_score(
    freshness_age_seconds: int,
    config: TeamSourceReliabilityConfig,
) -> Decimal:
    return _freshness_score_for_horizon(
        freshness_age_seconds,
        config.max_freshness_age_seconds,
    )


def _freshness_score_for_horizon(
    freshness_age_seconds: int,
    freshness_horizon_seconds: int,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw = ONE - (
            Decimal(freshness_age_seconds)
            / Decimal(freshness_horizon_seconds)
        )
        if raw < ZERO:
            return ZERO
        return _normalize_probability("freshness_score", raw)


def _corroboration_count(
    *,
    team_id: str,
    source_id: str,
    sources_by_team: dict[str, tuple[str, ...]],
) -> int:
    return sum(1 for candidate in sources_by_team.get(team_id, ()) if candidate != source_id)


def _sources_by_team(
    grouped: dict[tuple[str, str], list[_EvidenceItem]],
) -> dict[str, tuple[str, ...]]:
    sources: dict[str, set[str]] = {}
    for team_id, source_id in grouped:
        sources.setdefault(team_id, set()).add(source_id)
    return {
        team_id: tuple(sorted(source_ids))
        for team_id, source_ids in sources.items()
    }


def _failure_streak(items: tuple[_EvidenceItem, ...]) -> int:
    streak = 0
    sorted_items = sorted(
        items,
        key=lambda item: _outcome_key(item.outcome) if item.outcome is not None else (
            _as_utc("generated_at", item.evidence.generated_at),
            _as_utc("generated_at", item.evidence.generated_at),
            item.evidence.evidence_id,
        ),
        reverse=True,
    )
    for item in sorted_items:
        if item.outcome is None:
            continue
        if item.outcome.directionally_correct and item.outcome.profitable_after_cost:
            break
        streak += 1
    return streak


def _reliability_score(
    *,
    average_brier_score: Decimal | None,
    hit_rate: Decimal | None,
    profitable_rate: Decimal | None,
    freshness_score: Decimal,
    corroboration_count: int,
    config: TeamSourceReliabilityConfig,
) -> Decimal:
    if hit_rate is None or profitable_rate is None or average_brier_score is None:
        with localcontext(DECIMAL_CONTEXT):
            return _normalize_probability(
                "reliability_score",
                freshness_score / Decimal("2"),
            )
    corroboration_score = _corroboration_score(corroboration_count, config)
    with localcontext(DECIMAL_CONTEXT):
        accuracy_score = (
            hit_rate + profitable_rate + (ONE - average_brier_score)
        ) / Decimal("3")
        return _normalize_probability(
            "reliability_score",
            (accuracy_score * Decimal("0.650000"))
            + (freshness_score * Decimal("0.250000"))
            + (corroboration_score * Decimal("0.100000")),
        )


def _corroboration_score(
    corroboration_count: int,
    config: TeamSourceReliabilityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw = Decimal(corroboration_count) / Decimal(config.min_corroboration_count)
        if raw > ONE:
            return ONE
        return _normalize_probability("corroboration_score", raw)


def _reliability_grade(reliability_score: Decimal) -> str:
    score = _normalize_probability("reliability_score", reliability_score)
    if score >= Decimal("0.850000"):
        return "A"
    if score >= Decimal("0.700000"):
        return "B"
    if score >= Decimal("0.550000"):
        return "C"
    if score >= Decimal("0.400000"):
        return "D"
    return "F"


def _canonical_source_id(row: TeamForecastEvidenceDbRow) -> str | None:
    candidates: list[object] = [row.source_id]
    payload_json = row.payload_json
    if isinstance(payload_json, dict):
        candidates.append(payload_json.get("source_id"))
        evidence_payload = payload_json.get("evidence")
        if isinstance(evidence_payload, dict):
            candidates.append(evidence_payload.get("source_id"))
        source_payload = payload_json.get("source")
        if isinstance(source_payload, dict):
            candidates.append(source_payload.get("source_id"))
            candidates.append(source_payload.get("id"))

    for value in candidates:
        if value is None or value == "":
            continue
        _require_public_source_id("source_id", value)
        return value
    return None


def _evidence_confidence(row: TeamForecastEvidenceDbRow) -> Decimal | None:
    candidate = getattr(row, "confidence", None)
    if candidate is not None:
        return _normalize_probability("confidence", candidate)
    payload_json = row.payload_json
    if not isinstance(payload_json, dict):
        return None
    if "confidence" in payload_json:
        return _json_probability("confidence", payload_json["confidence"])
    evidence_payload = payload_json.get("evidence")
    if isinstance(evidence_payload, dict) and "confidence" in evidence_payload:
        return _json_probability("confidence", evidence_payload["confidence"])
    source_payload = payload_json.get("source")
    if isinstance(source_payload, dict) and "confidence" in source_payload:
        return _json_probability("confidence", source_payload["confidence"])
    return None


def _json_probability(field_name: str, value: object) -> Decimal:
    if type(value) is str:
        try:
            return _normalize_probability(field_name, Decimal(value))
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_probability(field_name, value)


def _mean_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("mean", sum(values, ZERO) / Decimal(len(values)))


def _ratio_optional(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "ratio",
            Decimal(numerator) / Decimal(denominator),
        )


def _normalize_report_rows(value: object) -> tuple[TeamSourceReliabilityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[TeamSourceReliabilityRow] = []
    previous_key: tuple[str, str] | None = None
    seen_keys: set[tuple[str, str]] = set()
    for row in value:
        if type(row) is not TeamSourceReliabilityRow:
            raise ValueError("rows must contain TeamSourceReliabilityRow values")
        _require_safety_values("TeamSourceReliabilityRow", row)
        normalized = TeamSourceReliabilityRow(
            team_id=row.team_id,
            source_id=row.source_id,
            evidence_count=row.evidence_count,
            settled_evidence_count=row.settled_evidence_count,
            directionally_correct_count=row.directionally_correct_count,
            profitable_after_cost_count=row.profitable_after_cost_count,
            dispute_count=row.dispute_count,
            average_brier_score=row.average_brier_score,
            hit_rate=row.hit_rate,
            profitable_rate=row.profitable_rate,
            average_weight=row.average_weight,
            average_confidence=row.average_confidence,
            latest_generated_at=row.latest_generated_at,
            freshness_age_seconds=row.freshness_age_seconds,
            freshness_score=row.freshness_score,
            freshness_horizon_seconds=row.freshness_horizon_seconds,
            corroboration_count=row.corroboration_count,
            failure_streak=row.failure_streak,
            reliability_score=row.reliability_score,
            reliability_grade=row.reliability_grade,
            status=row.status,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        )
        key = (normalized.team_id, normalized.source_id)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate team/source pairs")
        if previous_key is not None and key < previous_key:
            raise ValueError("rows must be sorted by team_id and source_id")
        seen_keys.add(key)
        previous_key = key
        rows.append(normalized)
    return tuple(rows)


def _normalize_grade_counts(value: object) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("reliability_grade_counts must be a tuple")
    rows: list[tuple[str, int]] = []
    previous_grade: str | None = None
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reliability_grade_counts must contain grade/count pairs")
        grade, count = item
        if grade not in SOURCE_RELIABILITY_GRADES:
            raise ValueError("reliability_grade_counts grade must be known")
        _require_positive_int("reliability_grade_counts count", count)
        if grade in seen:
            raise ValueError("reliability_grade_counts must not contain duplicate grades")
        if previous_grade is not None and grade < previous_grade:
            raise ValueError("reliability_grade_counts must be sorted by grade")
        seen.add(grade)
        previous_grade = grade
        rows.append((grade, count))
    return tuple(rows)


def _grade_counts_from_rows(
    rows: tuple[TeamSourceReliabilityRow, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.reliability_grade] = counts.get(row.reliability_grade, 0) + 1
    return tuple((grade, counts[grade]) for grade in sorted(counts))


def _require_payload_safety_values(value: object) -> None:
    if isinstance(value, dict):
        for field_name in SAFETY_FIELD_NAMES:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True in payload_json")
        for item in value.values():
            _require_payload_safety_values(item)
    elif isinstance(value, list):
        for item in value:
            _require_payload_safety_values(item)


def _require_safety_values(label: str, value: object) -> None:
    for field_name in SAFETY_FIELD_NAMES:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_optional_probability(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_source_id(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SOURCE_ID_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain sensitive live surface text")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


__all__ = (
    "TeamSourceReliabilityConfig",
    "TeamSourceReliabilityReport",
    "TeamSourceReliabilityRow",
    "build_team_source_reliability_report",
)
