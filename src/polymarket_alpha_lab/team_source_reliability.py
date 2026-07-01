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
SAFETY_FIELD_NAMES = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class TeamSourceReliabilityConfig:
    config_version: str = "team-source-reliability-v0"
    min_settled_evidence_count: int = 30
    max_dispute_rate: Decimal = Decimal("0.050000")
    min_profitable_rate: Decimal = Decimal("0.500000")
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
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("source_id", self.source_id)
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
        if self.row_count != len(self.rows):
            raise ValueError("row_count must match rows")
        if self.settled_evidence_count != sum(
            row.settled_evidence_count for row in self.rows
        ):
            raise ValueError("settled_evidence_count must match rows")
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

    evidence_items = _normalize_evidence_rows(evidence_rows)
    outcome_items = _normalize_outcome_rows(outcome_rows)
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

    rows = tuple(
        _build_row(
            team_id=team_id,
            source_id=source_id,
            items=tuple(grouped[(team_id, source_id)]),
            config=config,
        )
        for team_id, source_id in sorted(grouped)
    )

    return TeamSourceReliabilityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        evidence_count=len(evidence_items),
        outcome_count=len(outcome_items),
        settled_evidence_count=sum(row.settled_evidence_count for row in rows),
        pending_evidence_count=pending_evidence_count,
        missing_source_evidence_count=missing_source_evidence_count,
        row_count=len(rows),
        rows=rows,
    )


def _normalize_evidence_rows(
    value: object,
) -> tuple[TeamForecastEvidenceDbRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamForecastEvidenceDbRow:
            raise ValueError("evidence_rows must contain TeamForecastEvidenceDbRow values")
        _require_safety_values("evidence_rows item", row)
        _require_payload_safety_values(row.payload_json)
    return rows


def _normalize_outcome_rows(
    value: object,
) -> tuple[TeamForecastOutcomeDbRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("outcome_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamForecastOutcomeDbRow:
            raise ValueError("outcome_rows must contain TeamForecastOutcomeDbRow values")
        _require_safety_values("outcome_rows item", row)
        _require_payload_safety_values(row.payload_json)
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
        latest_generated_at=max(
            _as_utc("generated_at", item.evidence.generated_at)
            for item in items
        ),
        status=_row_status(
            settled_evidence_count=settled_evidence_count,
            dispute_rate=_ratio_optional(dispute_count, settled_evidence_count),
            profitable_rate=profitable_rate,
            config=config,
        ),
    )


def _row_status(
    *,
    settled_evidence_count: int,
    dispute_rate: Decimal | None,
    profitable_rate: Decimal | None,
    config: TeamSourceReliabilityConfig,
) -> str:
    if (
        dispute_rate is not None
        and dispute_rate > config.max_dispute_rate
    ) or (
        profitable_rate is not None
        and profitable_rate < config.min_profitable_rate
    ):
        return SOURCE_RELIABILITY_WATCH
    if settled_evidence_count >= config.min_settled_evidence_count:
        return SOURCE_RELIABILITY_VALIDATED
    return SOURCE_RELIABILITY_CANDIDATE


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
        _require_canonical_string("source_id", value)
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
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
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
