"""Phase 1 paper-only strategy candidate attention queue report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Iterable


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
READY_REASON_CODE = "candidate_attention_queue_v2_ready"
EMPTY_REASON_CODE = "no_candidates_for_attention_review"
WATCH_REASON_CODE = "candidate_attention_queue_v2_watch"
UNSAFE_PUBLIC_FRAGMENT_RE = re.compile(
    r"(?<![a-z])(live|auth|wallet|order|network|database|persist|signing|"
    r"mutation|buy|sell|trade)(?![a-z])",
    re.IGNORECASE,
)
SENSITIVE_PUBLIC_FRAGMENT_RE = re.compile(
    r"(api[_-]?key|secret|token=|password|passwd|private[_-]?key|postgres://)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class StrategyCandidateAttentionQueueV2Config:
    config_version: str
    min_source_verified_edge: Decimal = Decimal("0.010000")
    min_research_readiness: Decimal = Decimal("0.500000")
    min_attention_score: Decimal = Decimal("0.500000")
    max_liquidity_exit_risk: Decimal = Decimal("0.750000")
    max_resolution_ambiguity: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyCandidateAttentionQueueV2Config is final")

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_source_verified_edge",
            _quantize_edge("min_source_verified_edge", self.min_source_verified_edge),
        )
        for field_name in (
            "min_research_readiness",
            "min_attention_score",
            "max_liquidity_exit_risk",
            "max_resolution_ambiguity",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateAttentionQueueV2Candidate:
    candidate_id: str
    market_slug: str
    question: str
    outcome_name: str
    side: str
    source_reference: str
    source_verified_edge: Decimal
    market_probability_movement: Decimal
    research_readiness: Decimal
    uncertainty_band_width: Decimal
    liquidity_exit_risk: Decimal
    resolution_ambiguity: Decimal
    portfolio_impact: Decimal
    specialist_confidence: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyCandidateAttentionQueueV2Candidate is final")

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "question",
            "outcome_name",
            "source_reference",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_side(self.side)
        object.__setattr__(
            self,
            "source_verified_edge",
            _quantize_edge("source_verified_edge", self.source_verified_edge),
        )
        for field_name in (
            "market_probability_movement",
            "research_readiness",
            "uncertainty_band_width",
            "liquidity_exit_risk",
            "resolution_ambiguity",
            "portfolio_impact",
            "specialist_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyCandidateAttentionQueueV2Row:
    attention_rank: Decimal
    candidate_id: str
    market_slug: str
    question: str
    outcome_name: str
    side: str
    source_reference: str
    source_verified_edge: Decimal
    market_probability_movement: Decimal
    research_readiness: Decimal
    uncertainty_band_width: Decimal
    liquidity_exit_risk: Decimal
    resolution_ambiguity: Decimal
    portfolio_impact: Decimal
    specialist_confidence: Decimal
    attention_score: Decimal
    attention_status: str
    observed_at: datetime
    primary_reason_code: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyCandidateAttentionQueueV2Row is final")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attention_rank",
            _require_positive_count_decimal("attention_rank", self.attention_rank),
        )
        for field_name in (
            "candidate_id",
            "market_slug",
            "question",
            "outcome_name",
            "source_reference",
            "primary_reason_code",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_side(self.side)
        object.__setattr__(
            self,
            "source_verified_edge",
            _quantize_edge("source_verified_edge", self.source_verified_edge),
        )
        for field_name in (
            "market_probability_movement",
            "research_readiness",
            "uncertainty_band_width",
            "liquidity_exit_risk",
            "resolution_ambiguity",
            "portfolio_impact",
            "specialist_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "attention_score",
            _quantize_decimal("attention_score", self.attention_score),
        )
        if self.attention_status not in {"ready", "watch"}:
            raise ValueError("attention_status must be ready or watch")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.attention_status == "ready" and self.primary_reason_code != "attention_review_ready":
            raise ValueError("ready rows must use attention_review_ready")
        if self.attention_status == "watch" and self.primary_reason_code == "attention_review_ready":
            raise ValueError("watch rows must not use attention_review_ready")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateAttentionQueueV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    candidate_count: Decimal
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    top_candidate_id: str | None
    average_attention_score: Decimal
    max_uncertainty_band_width: Decimal
    max_liquidity_exit_risk: Decimal
    max_resolution_ambiguity: Decimal
    rows: tuple[StrategyCandidateAttentionQueueV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyCandidateAttentionQueueV2Report is final")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.report_status not in {"ready", "watch", "empty"}:
            raise ValueError("report_status must be ready, watch, or empty")
        for field_name in ("candidate_count", "row_count", "ready_count", "watch_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.top_candidate_id is not None:
            _require_public_string("top_candidate_id", self.top_candidate_id)
        for field_name in (
            "average_attention_score",
            "max_uncertainty_band_width",
            "max_liquidity_exit_risk",
            "max_resolution_ambiguity",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_validation_digest(_report_payload(self, include_digest=False))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report contents")
        _require_public_string("derived_validation_digest", self.derived_validation_digest)


def build_strategy_candidate_attention_queue_v2_report(
    candidates: Iterable[StrategyCandidateAttentionQueueV2Candidate],
    *,
    config: StrategyCandidateAttentionQueueV2Config,
    generated_at: datetime,
) -> StrategyCandidateAttentionQueueV2Report:
    """Build a readonly paper report ranking strategy candidates for review."""

    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of attention candidates")
    if type(config) is not StrategyCandidateAttentionQueueV2Config:
        raise ValueError("config must be a StrategyCandidateAttentionQueueV2Config")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)

    normalized_candidates = tuple(candidates)
    seen_candidate_ids: set[str] = set()
    unranked_rows: list[StrategyCandidateAttentionQueueV2Row] = []
    for item in normalized_candidates:
        if type(item) is not StrategyCandidateAttentionQueueV2Candidate:
            raise ValueError(
                "candidates must contain StrategyCandidateAttentionQueueV2Candidate values",
            )
        _require_hard_flags("candidate", item)
        if item.candidate_id in seen_candidate_ids:
            raise ValueError("duplicate candidate_id in attention candidates")
        seen_candidate_ids.add(item.candidate_id)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        unranked_rows.append(_unranked_row(item, config=config))

    ordered_rows = sorted(unranked_rows, key=_sort_key)
    rows = tuple(_rank_row(index, row) for index, row in enumerate(ordered_rows, start=1))
    ready_count = sum(row.attention_status == "ready" for row in rows)
    watch_count = sum(row.attention_status == "watch" for row in rows)
    if not rows:
        report_status = "empty"
        reason_codes = (EMPTY_REASON_CODE,)
    elif ready_count:
        report_status = "ready"
        reason_codes = (READY_REASON_CODE,)
    else:
        report_status = "watch"
        reason_codes = (WATCH_REASON_CODE,)

    return StrategyCandidateAttentionQueueV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        report_status=report_status,
        candidate_count=_count_decimal(len(normalized_candidates)),
        row_count=_count_decimal(len(rows)),
        ready_count=_count_decimal(ready_count),
        watch_count=_count_decimal(watch_count),
        top_candidate_id=rows[0].candidate_id if rows else None,
        average_attention_score=_average_attention_score(rows),
        max_uncertainty_band_width=_max_row_decimal(rows, "uncertainty_band_width"),
        max_liquidity_exit_risk=_max_row_decimal(rows, "liquidity_exit_risk"),
        max_resolution_ambiguity=_max_row_decimal(rows, "resolution_ambiguity"),
        rows=rows,
        reason_codes=reason_codes,
    )


def strategy_candidate_attention_queue_v2_payload(
    report: StrategyCandidateAttentionQueueV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateAttentionQueueV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("attention queue report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        _reject_unsafe_public_payload("attention queue payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
    else:
        raise ValueError("report must be a StrategyCandidateAttentionQueueV2Report")

    _reject_unsafe_public_payload("attention queue payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
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


def _unranked_row(
    candidate: StrategyCandidateAttentionQueueV2Candidate,
    *,
    config: StrategyCandidateAttentionQueueV2Config,
) -> StrategyCandidateAttentionQueueV2Row:
    attention_score = _attention_score(candidate)
    primary_reason_code = _primary_reason_code(
        candidate,
        attention_score=attention_score,
        config=config,
    )
    return StrategyCandidateAttentionQueueV2Row(
        attention_rank=ONE.quantize(QUANTUM),
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        question=candidate.question,
        outcome_name=candidate.outcome_name,
        side=candidate.side,
        source_reference=candidate.source_reference,
        source_verified_edge=candidate.source_verified_edge,
        market_probability_movement=candidate.market_probability_movement,
        research_readiness=candidate.research_readiness,
        uncertainty_band_width=candidate.uncertainty_band_width,
        liquidity_exit_risk=candidate.liquidity_exit_risk,
        resolution_ambiguity=candidate.resolution_ambiguity,
        portfolio_impact=candidate.portfolio_impact,
        specialist_confidence=candidate.specialist_confidence,
        attention_score=attention_score,
        attention_status=(
            "ready" if primary_reason_code == "attention_review_ready" else "watch"
        ),
        observed_at=candidate.observed_at,
        primary_reason_code=primary_reason_code,
        reason_codes=_reason_codes(candidate),
    )


def _attention_score(candidate: StrategyCandidateAttentionQueueV2Candidate) -> Decimal:
    score = (
        (candidate.source_verified_edge * Decimal("3.000000"))
        + (candidate.market_probability_movement * Decimal("2.000000"))
        + (candidate.research_readiness * Decimal("0.500000"))
        + (candidate.uncertainty_band_width * Decimal("0.750000"))
        - (candidate.liquidity_exit_risk * Decimal("0.200000"))
        - (candidate.resolution_ambiguity * Decimal("0.250000"))
        + (candidate.portfolio_impact * Decimal("0.250000"))
        + (candidate.specialist_confidence * Decimal("0.300000"))
    )
    return _quantize_decimal("attention_score", score)


def _primary_reason_code(
    candidate: StrategyCandidateAttentionQueueV2Candidate,
    *,
    attention_score: Decimal,
    config: StrategyCandidateAttentionQueueV2Config,
) -> str:
    if candidate.source_verified_edge < config.min_source_verified_edge:
        return "watch_low_source_verified_edge"
    if candidate.research_readiness < config.min_research_readiness:
        return "watch_research_not_ready"
    if candidate.liquidity_exit_risk > config.max_liquidity_exit_risk:
        return "watch_liquidity_exit_risk"
    if candidate.resolution_ambiguity > config.max_resolution_ambiguity:
        return "watch_resolution_ambiguity"
    if attention_score < config.min_attention_score:
        return "watch_low_attention_score"
    return "attention_review_ready"


def _reason_codes(candidate: StrategyCandidateAttentionQueueV2Candidate) -> tuple[str, ...]:
    return (
        _threshold_code(
            "source_verified_edge",
            candidate.source_verified_edge,
            high=Decimal("0.050000"),
            moderate=Decimal("0.010000"),
        ),
        _threshold_code(
            "market_probability_movement",
            candidate.market_probability_movement,
            high=Decimal("0.030000"),
            moderate=Decimal("0.010000"),
        ),
        _threshold_code(
            "research_readiness",
            candidate.research_readiness,
            high=Decimal("0.750000"),
            moderate=Decimal("0.500000"),
        ),
        _threshold_code(
            "uncertainty_band",
            candidate.uncertainty_band_width,
            high=Decimal("0.250000"),
            moderate=Decimal("0.150000"),
            high_label="wide",
            moderate_label="moderate",
            low_label="narrow",
        ),
        _risk_code("liquidity_exit_risk", candidate.liquidity_exit_risk),
        _risk_code("resolution_ambiguity", candidate.resolution_ambiguity),
        _threshold_code(
            "portfolio_impact",
            candidate.portfolio_impact,
            high=Decimal("0.300000"),
            moderate=Decimal("0.150000"),
        ),
        _threshold_code(
            "specialist_confidence",
            candidate.specialist_confidence,
            high=Decimal("0.750000"),
            moderate=Decimal("0.500000"),
        ),
    )


def _threshold_code(
    prefix: str,
    value: Decimal,
    *,
    high: Decimal,
    moderate: Decimal,
    high_label: str = "high",
    moderate_label: str = "moderate",
    low_label: str = "low",
) -> str:
    if value >= high:
        return f"{prefix}_{high_label}"
    if value >= moderate:
        return f"{prefix}_{moderate_label}"
    return f"{prefix}_{low_label}"


def _risk_code(prefix: str, value: Decimal) -> str:
    if value >= Decimal("0.500000"):
        return f"{prefix}_high"
    if value > Decimal("0.250000"):
        return f"{prefix}_moderate"
    return f"{prefix}_low"


def _sort_key(row: StrategyCandidateAttentionQueueV2Row) -> tuple[object, ...]:
    status_rank = 0 if row.attention_status == "ready" else 1
    return (
        status_rank,
        -row.attention_score,
        -row.source_verified_edge,
        -row.market_probability_movement,
        -row.research_readiness,
        -row.uncertainty_band_width,
        row.liquidity_exit_risk,
        row.resolution_ambiguity,
        -row.portfolio_impact,
        -row.specialist_confidence,
        row.observed_at,
        row.candidate_id,
    )


def _rank_row(
    rank: int,
    row: StrategyCandidateAttentionQueueV2Row,
) -> StrategyCandidateAttentionQueueV2Row:
    return StrategyCandidateAttentionQueueV2Row(
        attention_rank=_count_decimal(rank),
        candidate_id=row.candidate_id,
        market_slug=row.market_slug,
        question=row.question,
        outcome_name=row.outcome_name,
        side=row.side,
        source_reference=row.source_reference,
        source_verified_edge=row.source_verified_edge,
        market_probability_movement=row.market_probability_movement,
        research_readiness=row.research_readiness,
        uncertainty_band_width=row.uncertainty_band_width,
        liquidity_exit_risk=row.liquidity_exit_risk,
        resolution_ambiguity=row.resolution_ambiguity,
        portfolio_impact=row.portfolio_impact,
        specialist_confidence=row.specialist_confidence,
        attention_score=row.attention_score,
        attention_status=row.attention_status,
        observed_at=row.observed_at,
        primary_reason_code=row.primary_reason_code,
        reason_codes=row.reason_codes,
    )


def _average_attention_score(rows: tuple[StrategyCandidateAttentionQueueV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    total = sum((row.attention_score for row in rows), ZERO)
    return _quantize_nonnegative_decimal("average_attention_score", total / Decimal(len(rows)))


def _max_row_decimal(
    rows: tuple[StrategyCandidateAttentionQueueV2Row, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    return max(getattr(row, field_name) for row in rows).quantize(
        QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _validate_report_consistency(report: StrategyCandidateAttentionQueueV2Report) -> None:
    row_count = _count_decimal(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    if report.candidate_count < report.row_count:
        raise ValueError("candidate_count must be at least row_count")
    if report.ready_count != _count_decimal(
        sum(row.attention_status == "ready" for row in report.rows),
    ):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _count_decimal(
        sum(row.attention_status == "watch" for row in report.rows),
    ):
        raise ValueError("watch_count must match rows")
    if report.rows:
        if report.top_candidate_id != report.rows[0].candidate_id:
            raise ValueError("top_candidate_id must match first row")
        expected_ranks = tuple(_count_decimal(index) for index in range(1, len(report.rows) + 1))
        if tuple(row.attention_rank for row in report.rows) != expected_ranks:
            raise ValueError("attention ranks must be consecutive")
        if report.report_status == "empty":
            raise ValueError("report_status must not be empty with rows")
    elif report.top_candidate_id is not None:
        raise ValueError("top_candidate_id must be absent without rows")
    if report.report_status == "ready" and report.ready_count == ZERO:
        raise ValueError("ready report_status requires ready rows")
    if report.report_status == "watch" and (
        report.ready_count != ZERO or report.watch_count == ZERO
    ):
        raise ValueError("watch report_status requires only watch rows")
    if report.report_status == "empty" and report.row_count != ZERO:
        raise ValueError("empty report_status requires no rows")
    if report.average_attention_score != _average_attention_score(report.rows):
        raise ValueError("average_attention_score must match rows")
    if report.max_uncertainty_band_width != _max_row_decimal(report.rows, "uncertainty_band_width"):
        raise ValueError("max_uncertainty_band_width must match rows")
    if report.max_liquidity_exit_risk != _max_row_decimal(report.rows, "liquidity_exit_risk"):
        raise ValueError("max_liquidity_exit_risk must match rows")
    if report.max_resolution_ambiguity != _max_row_decimal(report.rows, "resolution_ambiguity"):
        raise ValueError("max_resolution_ambiguity must match rows")


def _report_payload(
    report: StrategyCandidateAttentionQueueV2Report,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.astimezone(UTC).isoformat(),
        "config_version": report.config_version,
        "report_status": report.report_status,
        "candidate_count": _decimal_payload(report.candidate_count),
        "row_count": _decimal_payload(report.row_count),
        "ready_count": _decimal_payload(report.ready_count),
        "watch_count": _decimal_payload(report.watch_count),
        "top_candidate_id": report.top_candidate_id,
        "average_attention_score": _decimal_payload(report.average_attention_score),
        "max_uncertainty_band_width": _decimal_payload(report.max_uncertainty_band_width),
        "max_liquidity_exit_risk": _decimal_payload(report.max_liquidity_exit_risk),
        "max_resolution_ambiguity": _decimal_payload(report.max_resolution_ambiguity),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: StrategyCandidateAttentionQueueV2Row) -> dict[str, Any]:
    return {
        "attention_rank": _decimal_payload(row.attention_rank),
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "question": row.question,
        "outcome_name": row.outcome_name,
        "side": row.side,
        "source_reference": row.source_reference,
        "source_verified_edge": _decimal_payload(row.source_verified_edge),
        "market_probability_movement": _decimal_payload(row.market_probability_movement),
        "research_readiness": _decimal_payload(row.research_readiness),
        "uncertainty_band_width": _decimal_payload(row.uncertainty_band_width),
        "liquidity_exit_risk": _decimal_payload(row.liquidity_exit_risk),
        "resolution_ambiguity": _decimal_payload(row.resolution_ambiguity),
        "portfolio_impact": _decimal_payload(row.portfolio_impact),
        "specialist_confidence": _decimal_payload(row.specialist_confidence),
        "attention_score": _decimal_payload(row.attention_score),
        "attention_status": row.attention_status,
        "observed_at": row.observed_at.astimezone(UTC).isoformat(),
        "primary_reason_code": row.primary_reason_code,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _derived_validation_digest(payload_without_digest: dict[str, Any]) -> str:
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or digest == "":
        raise ValueError("derived_validation_digest must be present")
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    expected_digest = _derived_validation_digest(payload_without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload contents")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _is_unsafe_public_text(value) or SENSITIVE_PUBLIC_FRAGMENT_RE.search(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{path or label} must be a finite Decimal")
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("public payload must not contain floats")
    if type(value) is int:
        raise ValueError("public payload numeric values must use Decimal strings")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _is_unsafe_public_text(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            nested_path = key if path == "" else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("public payload value is not JSON serializable")


def _is_unsafe_public_text(value: str) -> bool:
    return UNSAFE_PUBLIC_FRAGMENT_RE.search(value) is not None


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload value must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload Decimal must be finite")
    return str(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _quantize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    quantized = _quantize_decimal(field_name, value)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _quantize_probability(field_name: str, value: Decimal) -> Decimal:
    quantized = _quantize_nonnegative_decimal(field_name, value)
    if quantized > ONE:
        raise ValueError(f"{field_name} probability must be between 0 and 1")
    return quantized


def _quantize_edge(field_name: str, value: Decimal) -> Decimal:
    quantized = _quantize_decimal(field_name, value)
    if quantized < -ONE or quantized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return quantized


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    quantized = _require_nonnegative_count_decimal(field_name, value)
    if quantized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    quantized = _quantize_nonnegative_decimal(field_name, value)
    if quantized != quantized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return quantized


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must not contain control whitespace")
    if _is_unsafe_public_text(value) or SENSITIVE_PUBLIC_FRAGMENT_RE.search(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_side(value: str) -> None:
    _require_public_string("side", value)
    if value not in {"yes", "no"}:
        raise ValueError("side must be yes or no")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _normalize_reason_codes(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_public_string(field_name, value)
    return values


def _normalize_rows(
    values: tuple[StrategyCandidateAttentionQueueV2Row, ...],
) -> tuple[StrategyCandidateAttentionQueueV2Row, ...]:
    if not isinstance(values, tuple):
        raise ValueError("rows must be a tuple")
    for value in values:
        if type(value) is not StrategyCandidateAttentionQueueV2Row:
            raise ValueError("rows must contain StrategyCandidateAttentionQueueV2Row values")
    return values
