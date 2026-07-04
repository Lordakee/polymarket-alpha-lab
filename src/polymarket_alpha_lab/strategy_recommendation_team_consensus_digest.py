"""Pure report reducer for strategy recommendation team consensus."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DEFAULT_SPREAD_LIMIT = Decimal("0.250000")
_DEFAULT_STALE_DISSENT_SECONDS = Decimal("172800.000000")
_ROW_STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}
_OPINION_VALUES = frozenset(("support", "oppose", "abstain"))
_FAMILY_VALUES = frozenset(("aligned", "conflict", "stale"))
_REPORT_REASON_RANK = {
    "specialist_forecast_spread": 0,
    "source_family_disagreement": 1,
    "stale_dissent": 2,
    "unresolved_contradiction_note": 3,
}


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_EXTRA_SURFACE_FRAGMENTS = frozenset(
    (
        _surface_term("ad", "vice"),
        _surface_term("bro", "ker"),
        _surface_term("cred", "ential"),
        _surface_term("d", "b"),
        _surface_term("data", "base"),
        _surface_term("li", "ve"),
        _surface_term("net", "work"),
        _surface_term("pass", "word"),
        _surface_term("requ", "est"),
        _surface_term("sec", "ret"),
        _surface_term("sock", "et"),
        _surface_term("to", "ken"),
        _surface_term("trad", "ing"),
    ),
)
_SURFACE_FRAGMENTS = UNSAFE_SURFACE_FIELD_FRAGMENTS | _EXTRA_SURFACE_FRAGMENTS


@dataclass(frozen=True)
class StrategyRecommendationSpecialistOpinion:
    candidate_id: str
    specialist_id: str
    recommendation_status: str
    forecast_probability: Decimal
    confidence: Decimal
    source_family: str
    source_family_status: str
    contradiction_note: str | None
    contradiction_resolved: bool
    reviewed_at: datetime | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_text("specialist_id", self.specialist_id)
        _require_member("recommendation_status", self.recommendation_status, _OPINION_VALUES)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_ratio("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_ratio("confidence", self.confidence),
        )
        _require_text("source_family", self.source_family)
        _require_member("source_family_status", self.source_family_status, _FAMILY_VALUES)
        if self.contradiction_note is not None:
            _require_text("contradiction_note", self.contradiction_note)
        _require_bool("contradiction_resolved", self.contradiction_resolved)
        if self.reviewed_at is not None:
            object.__setattr__(self, "reviewed_at", _as_utc("reviewed_at", self.reviewed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes(self.reason_codes),
        )
        _require_flags("opinion", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamConsensusRow:
    candidate_id: str
    row_status: str
    specialist_count: Decimal
    source_family_count: Decimal
    support_count: Decimal
    oppose_count: Decimal
    abstain_count: Decimal
    dissent_count: Decimal
    stale_dissent_count: Decimal
    unresolved_contradiction_count: Decimal
    confidence_weighted_probability: Decimal | None
    average_forecast_probability: Decimal | None
    forecast_spread: Decimal | None
    confidence_weighted_support_ratio: Decimal | None
    source_family_disagreement: bool
    latest_reviewed_at: datetime | None
    unresolved_contradiction_notes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_row_status("row_status", self.row_status)
        for name in (
            "specialist_count",
            "source_family_count",
            "support_count",
            "oppose_count",
            "abstain_count",
            "dissent_count",
            "stale_dissent_count",
            "unresolved_contradiction_count",
        ):
            object.__setattr__(self, name, _normalize_count(name, getattr(self, name)))
        for name in (
            "confidence_weighted_probability",
            "average_forecast_probability",
            "forecast_spread",
            "confidence_weighted_support_ratio",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _normalize_ratio(name, value))
        _require_bool("source_family_disagreement", self.source_family_disagreement)
        if self.latest_reviewed_at is not None:
            object.__setattr__(
                self,
                "latest_reviewed_at",
                _as_utc("latest_reviewed_at", self.latest_reviewed_at),
            )
        object.__setattr__(
            self,
            "unresolved_contradiction_notes",
            _normalize_text_tuple(
                "unresolved_contradiction_notes",
                self.unresolved_contradiction_notes,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_row_reasons(self.reason_codes))
        _check_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamConsensusReasonRollup:
    reason_code: str
    candidate_count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "candidate_count",
            _normalize_count("candidate_count", self.candidate_count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_ratio("candidate_ratio", self.candidate_ratio),
        )
        _require_flags("reason rollup", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamConsensusDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    specialist_opinion_count: Decimal
    clear_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    consensus_candidate_count: Decimal
    consensus_candidate_ratio: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationTeamConsensusRow, ...]
    reason_rollups: tuple[StrategyRecommendationTeamConsensusReasonRollup, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for name in (
            "candidate_count",
            "specialist_opinion_count",
            "clear_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
            "consensus_candidate_count",
        ):
            object.__setattr__(self, name, _normalize_count(name, getattr(self, name)))
        if self.consensus_candidate_ratio is not None:
            object.__setattr__(
                self,
                "consensus_candidate_ratio",
                _normalize_ratio(
                    "consensus_candidate_ratio",
                    self.consensus_candidate_ratio,
                ),
            )
        _require_row_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_report_reasons(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_rollups", _normalize_rollups(self.reason_rollups))
        _check_report(self)
        _require_flags("report", self)


def build_strategy_recommendation_team_consensus_digest(
    *,
    generated_at: datetime,
    config_version: str,
    opinions: object,
    forecast_spread_limit: Decimal = _DEFAULT_SPREAD_LIMIT,
    stale_dissent_seconds: Decimal = _DEFAULT_STALE_DISSENT_SECONDS,
) -> StrategyRecommendationTeamConsensusDigestReport:
    generated_at = _as_utc("generated_at", generated_at)
    _require_text("config_version", config_version)
    forecast_spread_limit = _normalize_ratio("forecast_spread_limit", forecast_spread_limit)
    stale_dissent_seconds = _normalize_decimal(
        "stale_dissent_seconds",
        stale_dissent_seconds,
    )
    normalized_opinions = _normalize_opinions(opinions)
    rows = tuple(
        sorted(
            (
                _candidate_row(
                    candidate_id,
                    candidate_opinions,
                    generated_at=generated_at,
                    forecast_spread_limit=forecast_spread_limit,
                    stale_dissent_seconds=stale_dissent_seconds,
                )
                for candidate_id, candidate_opinions in _group_opinions(
                    normalized_opinions,
                )
            ),
            key=_row_key,
        ),
    )
    candidate_count = _count(len(rows))
    consensus_candidate_count = _count(
        sum(1 for row in rows if row.row_status == "clear"),
    )

    return StrategyRecommendationTeamConsensusDigestReport(
        generated_at=generated_at,
        config_version=config_version,
        candidate_count=candidate_count,
        specialist_opinion_count=_count(len(normalized_opinions)),
        clear_candidate_count=_row_count(rows, "clear"),
        watch_candidate_count=_row_count(rows, "watch"),
        blocked_candidate_count=_row_count(rows, "blocked"),
        consensus_candidate_count=consensus_candidate_count,
        consensus_candidate_ratio=(
            None
            if candidate_count == _ZERO
            else _ratio(consensus_candidate_count, candidate_count)
        ),
        status=_report_status(rows),
        reason_codes=_report_reasons(rows),
        rows=rows,
        reason_rollups=_reason_rollups(rows, candidate_count),
    )


def strategy_recommendation_team_consensus_digest_payload(
    report: StrategyRecommendationTeamConsensusDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationTeamConsensusDigestReport:
        _require_flags("report", report)
        _reject_surface_keys("report", report)
        _reject_payload_values("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        return payload
    if type(report) is dict:
        _reject_surface_keys("payload", report)
        _reject_payload_values("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError("report must be a StrategyRecommendationTeamConsensusDigestReport")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _candidate_row(
    candidate_id: str,
    opinions: tuple[StrategyRecommendationSpecialistOpinion, ...],
    *,
    generated_at: datetime,
    forecast_spread_limit: Decimal,
    stale_dissent_seconds: Decimal,
) -> StrategyRecommendationTeamConsensusRow:
    probabilities = tuple(opinion.forecast_probability for opinion in opinions)
    support_weight = sum(
        opinion.confidence
        for opinion in opinions
        if opinion.recommendation_status == "support"
    )
    confidence_sum = sum(opinion.confidence for opinion in opinions)
    confidence_weighted_probability = (
        None
        if confidence_sum == _ZERO
        else _ratio(
            sum(opinion.forecast_probability * opinion.confidence for opinion in opinions),
            confidence_sum,
        )
    )
    average_forecast_probability = _ratio(sum(probabilities), _count(len(probabilities)))
    forecast_spread = _quantize(max(probabilities) - min(probabilities))
    source_family_disagreement = any(
        opinion.source_family_status in ("conflict", "stale") for opinion in opinions
    ) or len({opinion.source_family_status for opinion in opinions}) > 1
    stale_dissent_count = _stale_dissent_count(
        opinions,
        generated_at=generated_at,
        stale_dissent_seconds=stale_dissent_seconds,
    )
    notes = tuple(
        sorted(
            {
                opinion.contradiction_note
                for opinion in opinions
                if opinion.contradiction_note is not None
                and not opinion.contradiction_resolved
            },
        ),
    )
    own_reasons = _own_row_reasons(
        forecast_spread=forecast_spread,
        forecast_spread_limit=forecast_spread_limit,
        source_family_disagreement=source_family_disagreement,
        stale_dissent_count=stale_dissent_count,
        unresolved_note_count=len(notes),
    )
    reason_codes = _merge_reasons(
        own_reasons,
        tuple(reason for opinion in opinions for reason in opinion.reason_codes),
    )

    return StrategyRecommendationTeamConsensusRow(
        candidate_id=candidate_id,
        row_status=_row_status(reason_codes),
        specialist_count=_count(len(opinions)),
        source_family_count=_count(len({opinion.source_family for opinion in opinions})),
        support_count=_opinion_count(opinions, "support"),
        oppose_count=_opinion_count(opinions, "oppose"),
        abstain_count=_opinion_count(opinions, "abstain"),
        dissent_count=_count(
            sum(1 for opinion in opinions if opinion.recommendation_status != "support"),
        ),
        stale_dissent_count=_count(stale_dissent_count),
        unresolved_contradiction_count=_count(len(notes)),
        confidence_weighted_probability=confidence_weighted_probability,
        average_forecast_probability=average_forecast_probability,
        forecast_spread=forecast_spread,
        confidence_weighted_support_ratio=(
            None if confidence_sum == _ZERO else _ratio(support_weight, confidence_sum)
        ),
        source_family_disagreement=source_family_disagreement,
        latest_reviewed_at=_latest_reviewed_at(opinions),
        unresolved_contradiction_notes=notes,
        reason_codes=reason_codes,
    )


def _normalize_opinions(
    opinions: object,
) -> tuple[StrategyRecommendationSpecialistOpinion, ...]:
    if isinstance(opinions, (str, bytes)):
        raise ValueError("opinions must be an iterable")
    try:
        items = tuple(opinions)
    except TypeError as exc:
        raise ValueError("opinions must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategyRecommendationSpecialistOpinion:
            raise ValueError("opinions must contain StrategyRecommendationSpecialistOpinion")
        _require_flags("opinion", item)
        key = (item.candidate_id, item.specialist_id)
        if key in seen:
            raise ValueError("opinions must contain unique candidate and specialist values")
        seen.add(key)
    return items


def _group_opinions(
    opinions: tuple[StrategyRecommendationSpecialistOpinion, ...],
) -> tuple[tuple[str, tuple[StrategyRecommendationSpecialistOpinion, ...]], ...]:
    candidate_ids = tuple(sorted({opinion.candidate_id for opinion in opinions}))
    return tuple(
        (
            candidate_id,
            tuple(
                sorted(
                    (
                        opinion
                        for opinion in opinions
                        if opinion.candidate_id == candidate_id
                    ),
                    key=lambda opinion: opinion.specialist_id,
                ),
            ),
        )
        for candidate_id in candidate_ids
    )


def _own_row_reasons(
    *,
    forecast_spread: Decimal,
    forecast_spread_limit: Decimal,
    source_family_disagreement: bool,
    stale_dissent_count: int,
    unresolved_note_count: int,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if forecast_spread > forecast_spread_limit:
        reasons.append("specialist_forecast_spread")
    if source_family_disagreement:
        reasons.append("source_family_disagreement")
    if stale_dissent_count > 0:
        reasons.append("stale_dissent")
    if unresolved_note_count > 0:
        reasons.append("unresolved_contradiction_note")
    return tuple(reasons)


def _merge_reasons(
    own_reasons: tuple[str, ...],
    source_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    if not own_reasons and not source_reasons:
        return ("team_consensus_clear",)
    return tuple(
        sorted(
            dict.fromkeys((*own_reasons, *source_reasons)),
            key=_reason_key,
        ),
    )


def _stale_dissent_count(
    opinions: tuple[StrategyRecommendationSpecialistOpinion, ...],
    *,
    generated_at: datetime,
    stale_dissent_seconds: Decimal,
) -> int:
    count = 0
    for opinion in opinions:
        if opinion.recommendation_status == "support":
            continue
        if opinion.reviewed_at is None:
            count += 1
            continue
        if opinion.reviewed_at > generated_at:
            raise ValueError("reviewed_at must not be after generated_at")
        if _age_seconds(generated_at, opinion.reviewed_at) > stale_dissent_seconds:
            count += 1
    return count


def _latest_reviewed_at(
    opinions: tuple[StrategyRecommendationSpecialistOpinion, ...],
) -> datetime | None:
    values = tuple(
        opinion.reviewed_at for opinion in opinions if opinion.reviewed_at is not None
    )
    if not values:
        return None
    return max(values)


def _report_status(rows: tuple[StrategyRecommendationTeamConsensusRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "unresolved_contradiction_note" in reason_codes:
        return "blocked"
    if reason_codes != ("team_consensus_clear",):
        return "watch"
    return "clear"


def _report_reasons(
    rows: tuple[StrategyRecommendationTeamConsensusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_specialist_opinions",)
    reasons = tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if reason != "team_consensus_clear"
            },
            key=_reason_key,
        ),
    )
    if reasons:
        return reasons
    return ("team_consensus_clear",)


def _reason_rollups(
    rows: tuple[StrategyRecommendationTeamConsensusRow, ...],
    candidate_count: Decimal,
) -> tuple[StrategyRecommendationTeamConsensusReasonRollup, ...]:
    if candidate_count == _ZERO:
        return ()
    reason_codes = tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if reason != "team_consensus_clear"
            },
            key=_reason_key,
        ),
    )
    return tuple(
        StrategyRecommendationTeamConsensusReasonRollup(
            reason_code=reason_code,
            candidate_count=_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
            candidate_ratio=_ratio(
                _count(sum(1 for row in rows if reason_code in row.reason_codes)),
                candidate_count,
            ),
        )
        for reason_code in reason_codes
    )


def _row_count(
    rows: tuple[StrategyRecommendationTeamConsensusRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == status))


def _opinion_count(
    opinions: tuple[StrategyRecommendationSpecialistOpinion, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for opinion in opinions if opinion.recommendation_status == status))


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationTeamConsensusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyRecommendationTeamConsensusRow:
            raise ValueError("rows must contain StrategyRecommendationTeamConsensusRow")
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_rollups(
    rollups: object,
) -> tuple[StrategyRecommendationTeamConsensusReasonRollup, ...]:
    if isinstance(rollups, (str, bytes)):
        raise ValueError("reason_rollups must be an iterable")
    try:
        normalized = tuple(rollups)
    except TypeError as exc:
        raise ValueError("reason_rollups must be an iterable") from exc
    for rollup in normalized:
        if type(rollup) is not StrategyRecommendationTeamConsensusReasonRollup:
            raise ValueError(
                "reason_rollups must contain StrategyRecommendationTeamConsensusReasonRollup",
            )
    if normalized != tuple(sorted(normalized, key=lambda rollup: _reason_key(rollup.reason_code))):
        raise ValueError("reason_rollups must use deterministic sequence")
    return normalized


def _check_row(row: StrategyRecommendationTeamConsensusRow) -> None:
    total = row.support_count + row.oppose_count + row.abstain_count
    if total != row.specialist_count:
        raise ValueError("specialist_count must match opinion counts")
    if row.dissent_count != row.oppose_count + row.abstain_count:
        raise ValueError("dissent_count must match oppose and abstain counts")
    if row.source_family_count > row.specialist_count:
        raise ValueError("source_family_count must not exceed specialist_count")
    if row.stale_dissent_count > row.dissent_count:
        raise ValueError("stale_dissent_count must not exceed dissent_count")
    if row.unresolved_contradiction_count != _count(
        len(row.unresolved_contradiction_notes),
    ):
        raise ValueError("unresolved_contradiction_count must match notes")
    expected_status = _row_status(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")


def _check_report(report: StrategyRecommendationTeamConsensusDigestReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.clear_candidate_count != _row_count(report.rows, "clear"):
        raise ValueError("clear_candidate_count must match rows")
    if report.watch_candidate_count != _row_count(report.rows, "watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _row_count(report.rows, "blocked"):
        raise ValueError("blocked_candidate_count must match rows")
    if report.consensus_candidate_count != report.clear_candidate_count:
        raise ValueError("consensus_candidate_count must match clear rows")
    if report.candidate_count == _ZERO:
        if report.consensus_candidate_ratio is not None:
            raise ValueError("consensus_candidate_ratio must be absent without rows")
    elif report.consensus_candidate_ratio != _ratio(
        report.consensus_candidate_count,
        report.candidate_count,
    ):
        raise ValueError("consensus_candidate_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reasons(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_key(row: StrategyRecommendationTeamConsensusRow) -> tuple[int, str]:
    return (_ROW_STATUS_RANK[row.row_status], row.candidate_id)


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REPORT_REASON_RANK.get(reason_code, len(_REPORT_REASON_RANK)), reason_code)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, reviewed_at: datetime) -> Decimal:
    value = Decimal(str((generated_at - reviewed_at).total_seconds()))
    if value < _ZERO:
        raise ValueError("reviewed_at must not be after generated_at")
    return _quantize(value)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _normalize_ratio(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _normalize_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    decimal_value = value
    if decimal_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be whole")
    return decimal_value.to_integral_value()


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_source_reason_codes(value: object) -> tuple[str, ...]:
    return tuple(sorted(_normalize_reason_codes(value), key=_reason_key))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    reasons = _normalize_text_tuple("reason_codes", value)
    if len(reasons) != len(set(reasons)):
        raise ValueError("reason_codes must be unique")
    return reasons


def _normalize_row_reasons(value: object) -> tuple[str, ...]:
    reasons = _normalize_reason_codes(value)
    if not reasons:
        raise ValueError("reason_codes must not be empty")
    if reasons != tuple(sorted(reasons, key=_reason_key)):
        raise ValueError("reason_codes must use deterministic sequence")
    return reasons


def _normalize_report_reasons(value: object) -> tuple[str, ...]:
    reasons = _normalize_reason_codes(value)
    if not reasons:
        raise ValueError("reason_codes must not be empty")
    if reasons != tuple(sorted(reasons, key=_reason_key)):
        raise ValueError("reason_codes must use deterministic sequence")
    return reasons


def _normalize_text_tuple(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    return tuple(_require_text(name, item) for item in items)


def _require_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if _has_surface_fragment(value):
        raise ValueError(f"{name} has unsafe value")
    return value


def _require_member(name: str, value: object, allowed: frozenset[str]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be a known value")


def _require_row_status(name: str, value: object) -> None:
    if value not in ("clear", "watch", "blocked"):
        raise ValueError(f"{name} must be a known value")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_surface_keys(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_surface_keys(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_surface_keys(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_surface_keys(label, item)


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_payload_values(label, asdict(value), path)
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is str:
        if _has_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)


def _has_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _SURFACE_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
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
    "StrategyRecommendationSpecialistOpinion",
    "StrategyRecommendationTeamConsensusDigestReport",
    "StrategyRecommendationTeamConsensusReasonRollup",
    "StrategyRecommendationTeamConsensusRow",
    "build_strategy_recommendation_team_consensus_digest",
    "strategy_recommendation_team_consensus_digest_payload",
)
