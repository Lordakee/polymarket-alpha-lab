"""Phase 1 research-to-recommendation scorecard reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_RESEARCH_TO_RECOMMENDATION_SCORECARD_V2_CONFIG_VERSION",
    "StrategyResearchToRecommendationScorecardV2Config",
    "StrategyResearchToRecommendationScorecardV2Input",
    "StrategyResearchToRecommendationScorecardV2ReasonCodeCount",
    "StrategyResearchToRecommendationScorecardV2Report",
    "StrategyResearchToRecommendationScorecardV2Row",
    "build_strategy_research_to_recommendation_scorecard_v2_report",
    "strategy_research_to_recommendation_scorecard_v2_payload",
)


DEFAULT_STRATEGY_RESEARCH_TO_RECOMMENDATION_SCORECARD_V2_CONFIG_VERSION = (
    "strategy-research-to-recommendation-scorecard-v2"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
POSTURES = ("promote", "watch", "block", "research-needed")
POSTURE_WEIGHT = {
    "block": Decimal("3.000000"),
    "research-needed": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "promote": Decimal("0.000000"),
}
SCORE_DIMENSION_COUNT = Decimal("7.000000")
DERIVED_DIGEST_FIELD = "derived_validation_digest"
UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
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
    ),
)


@dataclass(frozen=True)
class StrategyResearchToRecommendationScorecardV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RESEARCH_TO_RECOMMENDATION_SCORECARD_V2_CONFIG_VERSION
    )
    minimum_promote_score: Decimal = Decimal("0.800000")
    maximum_block_score: Decimal = Decimal("0.250000")
    minimum_research_packet_quality: Decimal = Decimal("0.600000")
    minimum_source_crosscheck_readiness: Decimal = Decimal("0.600000")
    minimum_rule_clarity: Decimal = Decimal("0.600000")
    minimum_information_freshness: Decimal = Decimal("0.600000")
    minimum_specialist_quorum: Decimal = Decimal("0.600000")
    minimum_cost_adjusted_edge: Decimal = Decimal("0.020000")
    block_cost_adjusted_edge: Decimal = Decimal("0.000000")
    target_promote_cost_adjusted_edge: Decimal = Decimal("0.050000")
    minimum_exit_feasibility: Decimal = Decimal("0.600000")
    block_exit_feasibility: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_promote_score",
            "maximum_block_score",
            "minimum_research_packet_quality",
            "minimum_source_crosscheck_readiness",
            "minimum_rule_clarity",
            "minimum_information_freshness",
            "minimum_specialist_quorum",
            "minimum_exit_feasibility",
            "block_exit_feasibility",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_cost_adjusted_edge",
            "block_cost_adjusted_edge",
            "target_promote_cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_block_score > self.minimum_promote_score:
            raise ValueError("maximum_block_score must not exceed minimum_promote_score")
        if self.block_cost_adjusted_edge > self.minimum_cost_adjusted_edge:
            raise ValueError(
                "block_cost_adjusted_edge must not exceed minimum_cost_adjusted_edge",
            )
        if self.minimum_cost_adjusted_edge > self.target_promote_cost_adjusted_edge:
            raise ValueError(
                "minimum_cost_adjusted_edge must not exceed target_promote_cost_adjusted_edge",
            )
        if self.block_exit_feasibility > self.minimum_exit_feasibility:
            raise ValueError(
                "block_exit_feasibility must not exceed minimum_exit_feasibility",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyResearchToRecommendationScorecardV2Input:
    candidate_id: str
    research_packet_quality: Decimal
    source_crosscheck_readiness: Decimal
    rule_clarity: Decimal
    information_freshness: Decimal
    specialist_quorum: Decimal
    cost_adjusted_edge: Decimal
    exit_feasibility: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "research_packet_quality",
            "source_crosscheck_readiness",
            "rule_clarity",
            "information_freshness",
            "specialist_quorum",
            "exit_feasibility",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_signed_unit_decimal(
                "cost_adjusted_edge",
                self.cost_adjusted_edge,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_order(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyResearchToRecommendationScorecardV2Row:
    candidate_id: str
    posture: str
    score: Decimal
    research_packet_quality: Decimal
    source_crosscheck_readiness: Decimal
    rule_clarity: Decimal
    information_freshness: Decimal
    specialist_quorum: Decimal
    cost_adjusted_edge: Decimal
    cost_adjusted_edge_score: Decimal
    exit_feasibility: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_posture("posture", self.posture)
        for field_name in (
            "score",
            "research_packet_quality",
            "source_crosscheck_readiness",
            "rule_clarity",
            "information_freshness",
            "specialist_quorum",
            "cost_adjusted_edge_score",
            "exit_feasibility",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_signed_unit_decimal(
                "cost_adjusted_edge",
                self.cost_adjusted_edge,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_order(self.reason_codes),
        )
        _require_hard_flags("scorecard row", self)
        if self.derived_validation_digest:
            _validate_derived_digest("row", _row_digest_payload(self))
            return
        _validate_row_consistency(self)
        object.__setattr__(
            self,
            DERIVED_DIGEST_FIELD,
            _derived_digest(_row_digest_payload(self)),
        )


@dataclass(frozen=True)
class StrategyResearchToRecommendationScorecardV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class StrategyResearchToRecommendationScorecardV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    promote_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    research_needed_count: Decimal
    average_score: Decimal
    max_score: Decimal
    min_score: Decimal
    overall_posture: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyResearchToRecommendationScorecardV2ReasonCodeCount, ...]
    scorecard_rows: tuple[StrategyResearchToRecommendationScorecardV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "promote_count",
            "watch_count",
            "block_count",
            "research_needed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_score", "max_score", "min_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_posture("overall_posture", self.overall_posture)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "scorecard_rows",
            _normalize_rows(self.scorecard_rows),
        )
        _require_hard_flags("scorecard report", self)
        _validate_report_consistency(self)
        if self.derived_validation_digest:
            _validate_derived_digest("report", _report_digest_payload(self))
        else:
            object.__setattr__(
                self,
                DERIVED_DIGEST_FIELD,
                _derived_digest(_report_digest_payload(self)),
            )


def build_strategy_research_to_recommendation_scorecard_v2_report(
    candidates: Iterable[StrategyResearchToRecommendationScorecardV2Input],
    *,
    config: StrategyResearchToRecommendationScorecardV2Config,
    generated_at: datetime,
) -> StrategyResearchToRecommendationScorecardV2Report:
    if type(config) is not StrategyResearchToRecommendationScorecardV2Config:
        raise ValueError(
            "config must be a StrategyResearchToRecommendationScorecardV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (_scorecard_row(candidate, config=config) for candidate in input_rows),
            key=_row_sort_key,
        ),
    )
    return StrategyResearchToRecommendationScorecardV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        promote_count=_posture_count(rows, "promote"),
        watch_count=_posture_count(rows, "watch"),
        block_count=_posture_count(rows, "block"),
        research_needed_count=_posture_count(rows, "research-needed"),
        average_score=_average_score(rows),
        max_score=_max_score(rows),
        min_score=_min_score(rows),
        overall_posture=_rollup_posture(tuple(row.posture for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        scorecard_rows=rows,
    )


def strategy_research_to_recommendation_scorecard_v2_payload(
    report: StrategyResearchToRecommendationScorecardV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyResearchToRecommendationScorecardV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("scorecard report", report)
        _validate_derived_digest("report", _report_digest_payload(report))
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("scorecard payload", report)
        _reject_flag_downgrades("payload", report)
        payload = _json_ready(report)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_public_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a StrategyResearchToRecommendationScorecardV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("scorecard payload", payload)
    return payload


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


def _scorecard_row(
    candidate: StrategyResearchToRecommendationScorecardV2Input,
    *,
    config: StrategyResearchToRecommendationScorecardV2Config,
) -> StrategyResearchToRecommendationScorecardV2Row:
    edge_score = _edge_score(
        candidate.cost_adjusted_edge,
        block_edge=config.block_cost_adjusted_edge,
        target_edge=config.target_promote_cost_adjusted_edge,
    )
    score = _score(
        (
            candidate.research_packet_quality,
            candidate.source_crosscheck_readiness,
            candidate.rule_clarity,
            candidate.information_freshness,
            candidate.specialist_quorum,
            edge_score,
            candidate.exit_feasibility,
        ),
    )
    reason_codes = _row_reason_codes(
        candidate,
        score=score,
        config=config,
    )
    return StrategyResearchToRecommendationScorecardV2Row(
        candidate_id=candidate.candidate_id,
        posture=_row_posture(reason_codes),
        score=score,
        research_packet_quality=candidate.research_packet_quality,
        source_crosscheck_readiness=candidate.source_crosscheck_readiness,
        rule_clarity=candidate.rule_clarity,
        information_freshness=candidate.information_freshness,
        specialist_quorum=candidate.specialist_quorum,
        cost_adjusted_edge=candidate.cost_adjusted_edge,
        cost_adjusted_edge_score=edge_score,
        exit_feasibility=candidate.exit_feasibility,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    candidate: StrategyResearchToRecommendationScorecardV2Input,
    *,
    score: Decimal,
    config: StrategyResearchToRecommendationScorecardV2Config,
) -> tuple[str, ...]:
    reason_codes = list(candidate.reason_codes)
    research_needed_codes: list[str] = []
    for field_name, threshold in (
        ("research_packet_quality", config.minimum_research_packet_quality),
        ("source_crosscheck_readiness", config.minimum_source_crosscheck_readiness),
        ("rule_clarity", config.minimum_rule_clarity),
        ("information_freshness", config.minimum_information_freshness),
        ("specialist_quorum", config.minimum_specialist_quorum),
    ):
        if getattr(candidate, field_name) < threshold:
            research_needed_codes.append(f"scorecard_{field_name}_research_needed")
    research_needed_codes.sort()

    block_codes: list[str] = []
    if candidate.cost_adjusted_edge <= config.block_cost_adjusted_edge:
        block_codes.append("scorecard_cost_adjusted_edge_block")
    if candidate.exit_feasibility <= config.block_exit_feasibility:
        block_codes.append("scorecard_exit_feasibility_block")

    watch_codes: list[str] = []
    if (
        candidate.cost_adjusted_edge < config.minimum_cost_adjusted_edge
        and "scorecard_cost_adjusted_edge_block" not in block_codes
    ):
        watch_codes.append("scorecard_cost_adjusted_edge_watch")
    if not block_codes and not research_needed_codes and score < config.minimum_promote_score:
        watch_codes.append("scorecard_composite_watch")
    if (
        candidate.exit_feasibility < config.minimum_exit_feasibility
        and "scorecard_exit_feasibility_block" not in block_codes
    ):
        watch_codes.append("scorecard_exit_feasibility_watch")

    reason_codes.extend(research_needed_codes)
    reason_codes.extend(block_codes)
    reason_codes.extend(watch_codes)
    if not research_needed_codes and not block_codes and not watch_codes:
        reason_codes.append("scorecard_promote_ready")
    return _normalize_reason_codes_preserving_order(tuple(reason_codes))


def _row_posture(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_research_needed") for reason_code in reason_codes):
        return "research-needed"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "promote"


def _rollup_posture(postures: tuple[str, ...]) -> str:
    if any(posture == "block" for posture in postures):
        return "block"
    if not postures or any(posture == "research-needed" for posture in postures):
        return "research-needed"
    if any(posture == "watch" for posture in postures):
        return "watch"
    return "promote"


def _rollup_reason_codes(
    rows: tuple[StrategyResearchToRecommendationScorecardV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("scorecard_no_candidates_research_needed",)
    posture = _rollup_posture(tuple(row.posture for row in rows))
    reason_codes = [f"scorecard_{'promote_ready' if posture == 'promote' else posture}"]
    row_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code.startswith("scorecard_")
        and reason_code not in {"scorecard_promote_ready", "scorecard_composite_watch"}
    }
    reason_codes.extend(sorted(row_codes))
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[StrategyResearchToRecommendationScorecardV2Row, ...],
) -> tuple[StrategyResearchToRecommendationScorecardV2ReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _edge_score(
    edge: Decimal,
    *,
    block_edge: Decimal,
    target_edge: Decimal,
) -> Decimal:
    if target_edge == block_edge:
        return ONE if edge > target_edge else ZERO
    ratio = _quantize((edge - block_edge) / (target_edge - block_edge))
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return ratio


def _score(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return _quantize(total / SCORE_DIMENSION_COUNT)


def _average_score(
    rows: tuple[StrategyResearchToRecommendationScorecardV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    total = ZERO
    for row in rows:
        total = _quantize(total + row.score)
    return _quantize(total / Decimal(len(rows)).quantize(COUNT_QUANTUM))


def _max_score(rows: tuple[StrategyResearchToRecommendationScorecardV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_ratio("max_score", max(row.score for row in rows))


def _min_score(rows: tuple[StrategyResearchToRecommendationScorecardV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_ratio("min_score", min(row.score for row in rows))


def _posture_count(
    rows: tuple[StrategyResearchToRecommendationScorecardV2Row, ...],
    posture: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.posture == posture))


def _validate_row_consistency(
    row: StrategyResearchToRecommendationScorecardV2Row,
) -> None:
    if row.posture != _row_posture(row.reason_codes):
        raise ValueError("posture must match reason_codes")
    expected_score = _score(
        (
            row.research_packet_quality,
            row.source_crosscheck_readiness,
            row.rule_clarity,
            row.information_freshness,
            row.specialist_quorum,
            row.cost_adjusted_edge_score,
            row.exit_feasibility,
        ),
    )
    if row.score != expected_score:
        raise ValueError("score must match scorecard inputs")


def _validate_report_consistency(
    report: StrategyResearchToRecommendationScorecardV2Report,
) -> None:
    rows = report.scorecard_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match scorecard_rows")
    for field_name, posture in (
        ("promote_count", "promote"),
        ("watch_count", "watch"),
        ("block_count", "block"),
        ("research_needed_count", "research-needed"),
    ):
        if getattr(report, field_name) != _posture_count(rows, posture):
            raise ValueError(f"{field_name} must match scorecard_rows")
    if report.average_score != _average_score(rows):
        raise ValueError("average_score must match scorecard_rows")
    if report.max_score != _max_score(rows):
        raise ValueError("max_score must match scorecard_rows")
    if report.min_score != _min_score(rows):
        raise ValueError("min_score must match scorecard_rows")
    if report.overall_posture != _rollup_posture(tuple(row.posture for row in rows)):
        raise ValueError("overall_posture must match scorecard_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match scorecard_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match scorecard_rows")


def _normalize_inputs(
    candidates: Iterable[StrategyResearchToRecommendationScorecardV2Input],
) -> tuple[StrategyResearchToRecommendationScorecardV2Input, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyResearchToRecommendationScorecardV2Input:
            raise ValueError(
                "candidates must contain StrategyResearchToRecommendationScorecardV2Input values",
            )
        _require_hard_flags("candidate", row)
        if row.candidate_id in seen_ids:
            raise ValueError("candidates must not contain duplicate ids")
        seen_ids.add(row.candidate_id)
    return rows


def _normalize_rows(
    rows: Iterable[StrategyResearchToRecommendationScorecardV2Row],
) -> tuple[StrategyResearchToRecommendationScorecardV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("scorecard_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("scorecard_rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in values:
        if type(row) is not StrategyResearchToRecommendationScorecardV2Row:
            raise ValueError(
                "scorecard_rows must contain StrategyResearchToRecommendationScorecardV2Row values",
            )
        _require_hard_flags("scorecard row", row)
        _validate_derived_digest("row", _row_digest_payload(row))
        _validate_row_consistency(row)
        if row.candidate_id in seen_ids:
            raise ValueError("scorecard_rows must not contain duplicate ids")
        seen_ids.add(row.candidate_id)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("scorecard_rows must use stable sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[StrategyResearchToRecommendationScorecardV2ReasonCodeCount],
) -> tuple[StrategyResearchToRecommendationScorecardV2ReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in values:
        if type(row) is not StrategyResearchToRecommendationScorecardV2ReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use stable sequence")
        previous_key = key
        seen_codes.add(row.reason_code)
    return values


def _row_sort_key(
    row: StrategyResearchToRecommendationScorecardV2Row,
) -> tuple[Decimal, Decimal, str]:
    return (
        -POSTURE_WEIGHT[row.posture],
        -_row_severity(row),
        row.candidate_id,
    )


def _row_severity(row: StrategyResearchToRecommendationScorecardV2Row) -> Decimal:
    return _count(
        sum(
            1
            for reason_code in row.reason_codes
            if reason_code.startswith("scorecard_")
            and reason_code not in {"scorecard_promote_ready", "scorecard_composite_watch"}
        ),
    )


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    rows = payload.get("scorecard_rows")
    if rows is None:
        raise ValueError("scorecard_rows must be present")
    if type(rows) is not list:
        raise ValueError("scorecard_rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("scorecard_rows must contain JSON objects")
        _validate_derived_digest("row", row)
    _validate_derived_digest("report", payload)


def _row_digest_payload(row: StrategyResearchToRecommendationScorecardV2Row) -> dict[str, Any]:
    payload = asdict(row)
    return payload


def _report_digest_payload(
    report: StrategyResearchToRecommendationScorecardV2Report,
) -> dict[str, Any]:
    payload = asdict(report)
    return payload


def _validate_derived_digest(label: str, payload: dict[str, Any]) -> None:
    observed = payload.get(DERIVED_DIGEST_FIELD)
    if type(observed) is not str or len(observed) != 64:
        raise ValueError(f"{label} derived_validation_digest must be a sha256 hex digest")
    expected = _derived_digest(payload)
    if observed != expected:
        raise ValueError(f"{label} derived_validation_digest mismatch")


def _derived_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        key: value for key, value in payload.items() if key != DERIVED_DIGEST_FIELD
    }
    canonical = json.dumps(
        _json_ready(digest_payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_payload_value(label, payload)


def _reject_unsafe_payload_value(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload_value(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {path or label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_payload_value(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload_value(label, item, nested_path)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_posture(field_name: str, value: object) -> None:
    if type(value) is not str or value not in POSTURES:
        raise ValueError(f"{field_name} must be promote, watch, block, or research-needed")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return tuple(sorted(reason_codes))


def _normalize_reason_codes_preserving_order(value: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicate values")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_signed_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
