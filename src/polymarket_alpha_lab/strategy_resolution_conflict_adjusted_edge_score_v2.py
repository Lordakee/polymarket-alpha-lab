"""Phase 1 paper-only resolution-conflict adjusted edge score report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_STRATEGY_RESOLUTION_CONFLICT_ADJUSTED_EDGE_SCORE_V2_CONFIG_VERSION = (
    "strategy-resolution-conflict-adjusted-edge-score-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_SIDES = frozenset(("yes", "no"))
_STATUSES = frozenset(("blocked", "watch", "qualified"))
_STATUS_RANK = {"qualified": 0, "watch": 1, "blocked": 2}
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
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
_EMPTY_REASON = "empty_resolution_conflict_adjusted_edge"
_OWNED_REASON_CODES = frozenset(
    (
        "conflict_adjusted_edge_qualified",
        "conflict_adjusted_edge_watch",
        "conflict_adjusted_edge_blocked",
        "positive_raw_edge",
        "nonpositive_raw_edge",
        "unresolved_resolution_conflict_penalty",
        "no_unresolved_resolution_conflict_penalty",
        "official_resolution_source_boost",
        "no_official_resolution_source_boost",
        _EMPTY_REASON,
    ),
)
_REASON_RANK = {
    "conflict_adjusted_edge_blocked": 0,
    "conflict_adjusted_edge_qualified": 1,
    "conflict_adjusted_edge_watch": 2,
    "nonpositive_raw_edge": 3,
    "positive_raw_edge": 4,
    "unresolved_resolution_conflict_penalty": 5,
    "no_unresolved_resolution_conflict_penalty": 6,
    "official_resolution_source_boost": 7,
    "no_official_resolution_source_boost": 8,
    _EMPTY_REASON: 9,
}
_ROW_PAYLOAD_KEYS = (
    "candidate_id",
    "market_slug",
    "recommendation_side",
    "forecast_probability",
    "implied_probability",
    "confidence_score",
    "resolution_conflict_count",
    "unresolved_resolution_conflict_count",
    "official_resolution_source_count",
    "observed_at",
    "raw_edge",
    "confidence_weighted_edge",
    "unresolved_resolution_conflict_penalty",
    "official_resolution_source_boost",
    "conflict_adjusted_edge_score",
    "edge_status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "qualified_count",
    "watch_count",
    "blocked_count",
    "average_conflict_adjusted_edge_score",
    "max_unresolved_resolution_conflict_penalty",
    "status",
    "reason_codes",
    "rows",
    "public_payload",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_STRATEGY_RESOLUTION_CONFLICT_ADJUSTED_EDGE_SCORE_V2_CONFIG_VERSION",
    "StrategyResolutionConflictAdjustedEdgeScoreV2Candidate",
    "StrategyResolutionConflictAdjustedEdgeScoreV2Config",
    "StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem",
    "StrategyResolutionConflictAdjustedEdgeScoreV2Report",
    "StrategyResolutionConflictAdjustedEdgeScoreV2Row",
    "build_strategy_resolution_conflict_adjusted_edge_score_v2_report",
    "strategy_resolution_conflict_adjusted_edge_score_v2_payload",
)


@dataclass(frozen=True)
class StrategyResolutionConflictAdjustedEdgeScoreV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RESOLUTION_CONFLICT_ADJUSTED_EDGE_SCORE_V2_CONFIG_VERSION
    )
    min_qualified_edge_score: Decimal = Decimal("0.050000")
    min_watch_edge_score: Decimal = Decimal("0.010000")
    unresolved_conflict_penalty_per_conflict: Decimal = Decimal("0.040000")
    official_source_boost_per_source: Decimal = Decimal("0.020000")
    max_official_source_boost: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyResolutionConflictAdjustedEdgeScoreV2Config:
            raise TypeError(
                "StrategyResolutionConflictAdjustedEdgeScoreV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionConflictAdjustedEdgeScoreV2Config:
            raise ValueError(
                "config must be exactly StrategyResolutionConflictAdjustedEdgeScoreV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RESOLUTION_CONFLICT_ADJUSTED_EDGE_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_qualified_edge_score",
            "min_watch_edge_score",
            "unresolved_conflict_penalty_per_conflict",
            "official_source_boost_per_source",
            "max_official_source_boost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_edge_score > self.min_qualified_edge_score:
            raise ValueError("min_watch_edge_score must not exceed min_qualified_edge_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyResolutionConflictAdjustedEdgeScoreV2Candidate:
    candidate_id: str
    market_slug: str
    recommendation_side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence_score: Decimal
    resolution_conflict_count: Decimal
    unresolved_resolution_conflict_count: Decimal
    official_resolution_source_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyResolutionConflictAdjustedEdgeScoreV2Candidate:
            raise TypeError(
                "StrategyResolutionConflictAdjustedEdgeScoreV2Candidate does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionConflictAdjustedEdgeScoreV2Candidate:
            raise ValueError(
                "candidate must be exactly StrategyResolutionConflictAdjustedEdgeScoreV2Candidate",
            )
        for field_name in ("candidate_id", "market_slug"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_public_identifier("recommendation_side", self.recommendation_side)
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "forecast_probability",
            "implied_probability",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_conflict_count",
            "unresolved_resolution_conflict_count",
            "official_resolution_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.unresolved_resolution_conflict_count > self.resolution_conflict_count:
            raise ValueError(
                "unresolved_resolution_conflict_count must not exceed resolution_conflict_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload("candidate", self)


@dataclass(frozen=True)
class StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem:
            raise TypeError(
                "StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        _require_public_text("value", self.value)
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class StrategyResolutionConflictAdjustedEdgeScoreV2Row:
    candidate_id: str
    market_slug: str
    recommendation_side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence_score: Decimal
    resolution_conflict_count: Decimal
    unresolved_resolution_conflict_count: Decimal
    official_resolution_source_count: Decimal
    observed_at: datetime
    raw_edge: Decimal
    confidence_weighted_edge: Decimal
    unresolved_resolution_conflict_penalty: Decimal
    official_resolution_source_boost: Decimal
    conflict_adjusted_edge_score: Decimal
    edge_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyResolutionConflictAdjustedEdgeScoreV2Row:
            raise TypeError(
                "StrategyResolutionConflictAdjustedEdgeScoreV2Row does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionConflictAdjustedEdgeScoreV2Row:
            raise ValueError("row must be exactly StrategyResolutionConflictAdjustedEdgeScoreV2Row")
        for field_name in ("candidate_id", "market_slug", "recommendation_side"):
            _require_public_identifier(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "forecast_probability",
            "implied_probability",
            "confidence_score",
            "official_resolution_source_boost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_conflict_count",
            "unresolved_resolution_conflict_count",
            "official_resolution_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "raw_edge",
            "confidence_weighted_edge",
            "unresolved_resolution_conflict_penalty",
            "conflict_adjusted_edge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("edge_status", self.edge_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategyResolutionConflictAdjustedEdgeScoreV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    qualified_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_conflict_adjusted_edge_score: Decimal
    max_unresolved_resolution_conflict_penalty: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyResolutionConflictAdjustedEdgeScoreV2Row, ...]
    public_payload: tuple[StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyResolutionConflictAdjustedEdgeScoreV2Report:
            raise TypeError(
                "StrategyResolutionConflictAdjustedEdgeScoreV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionConflictAdjustedEdgeScoreV2Report:
            raise ValueError(
                "report must be exactly StrategyResolutionConflictAdjustedEdgeScoreV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RESOLUTION_CONFLICT_ADJUSTED_EDGE_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "candidate_count",
            "qualified_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_conflict_adjusted_edge_score",
            "max_unresolved_resolution_conflict_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        for row in self.rows:
            _require_row_digest(row)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_resolution_conflict_adjusted_edge_score_v2_payload(self)


def build_strategy_resolution_conflict_adjusted_edge_score_v2_report(
    candidates: object,
    *,
    generated_at: datetime,
    config: StrategyResolutionConflictAdjustedEdgeScoreV2Config | None = None,
    public_payload: object = (),
) -> StrategyResolutionConflictAdjustedEdgeScoreV2Report:
    if config is None:
        config = StrategyResolutionConflictAdjustedEdgeScoreV2Config()
    if type(config) is not StrategyResolutionConflictAdjustedEdgeScoreV2Config:
        raise ValueError(
            "config must be a StrategyResolutionConflictAdjustedEdgeScoreV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_candidates(candidates)
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("generated_at must not precede observed_at")
    rows = tuple(sorted((_candidate_row(item, config=config) for item in items), key=_row_key))
    return StrategyResolutionConflictAdjustedEdgeScoreV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        qualified_count=_status_count(rows, "qualified"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        average_conflict_adjusted_edge_score=_average(
            tuple(row.conflict_adjusted_edge_score for row in rows),
        ),
        max_unresolved_resolution_conflict_penalty=max(
            (row.unresolved_resolution_conflict_penalty for row in rows),
            default=_ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        public_payload=_normalize_public_payload(public_payload),
    )


def strategy_resolution_conflict_adjusted_edge_score_v2_payload(
    report: StrategyResolutionConflictAdjustedEdgeScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyResolutionConflictAdjustedEdgeScoreV2Report:
        _require_hard_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _reject_raw_public_numbers("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload
    raise ValueError(
        "report must be a StrategyResolutionConflictAdjustedEdgeScoreV2Report",
    )


def _candidate_row(
    item: StrategyResolutionConflictAdjustedEdgeScoreV2Candidate,
    *,
    config: StrategyResolutionConflictAdjustedEdgeScoreV2Config,
) -> StrategyResolutionConflictAdjustedEdgeScoreV2Row:
    raw_edge = _normalize_decimal(
        "raw_edge",
        item.forecast_probability - item.implied_probability,
    )
    confidence_weighted_edge = _normalize_decimal(
        "confidence_weighted_edge",
        raw_edge * item.confidence_score,
    )
    conflict_penalty = _normalize_decimal(
        "unresolved_resolution_conflict_penalty",
        item.unresolved_resolution_conflict_count
        * config.unresolved_conflict_penalty_per_conflict,
    )
    official_boost = min(
        _normalize_decimal(
            "official_resolution_source_boost",
            item.official_resolution_source_count * config.official_source_boost_per_source,
        ),
        config.max_official_source_boost,
    )
    adjusted_score = _normalize_decimal(
        "conflict_adjusted_edge_score",
        confidence_weighted_edge - conflict_penalty + official_boost,
    )
    edge_status = _status_from_score(adjusted_score, config)
    return StrategyResolutionConflictAdjustedEdgeScoreV2Row(
        candidate_id=item.candidate_id,
        market_slug=item.market_slug,
        recommendation_side=item.recommendation_side,
        forecast_probability=item.forecast_probability,
        implied_probability=item.implied_probability,
        confidence_score=item.confidence_score,
        resolution_conflict_count=item.resolution_conflict_count,
        unresolved_resolution_conflict_count=item.unresolved_resolution_conflict_count,
        official_resolution_source_count=item.official_resolution_source_count,
        observed_at=item.observed_at,
        raw_edge=raw_edge,
        confidence_weighted_edge=confidence_weighted_edge,
        unresolved_resolution_conflict_penalty=conflict_penalty,
        official_resolution_source_boost=official_boost,
        conflict_adjusted_edge_score=adjusted_score,
        edge_status=edge_status,
        reason_codes=_row_reason_codes(
            edge_status=edge_status,
            raw_edge=raw_edge,
            unresolved_resolution_conflict_penalty=conflict_penalty,
            official_resolution_source_boost=official_boost,
        ),
    )


def _status_from_score(
    adjusted_score: Decimal,
    config: StrategyResolutionConflictAdjustedEdgeScoreV2Config,
) -> str:
    if adjusted_score >= config.min_qualified_edge_score:
        return "qualified"
    if adjusted_score >= config.min_watch_edge_score:
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    edge_status: str,
    raw_edge: Decimal,
    unresolved_resolution_conflict_penalty: Decimal,
    official_resolution_source_boost: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"conflict_adjusted_edge_{edge_status}"]
    if raw_edge > _ZERO:
        reason_codes.append("positive_raw_edge")
    else:
        reason_codes.append("nonpositive_raw_edge")
    if unresolved_resolution_conflict_penalty > _ZERO:
        reason_codes.append("unresolved_resolution_conflict_penalty")
    else:
        reason_codes.append("no_unresolved_resolution_conflict_penalty")
    if official_resolution_source_boost > _ZERO:
        reason_codes.append("official_resolution_source_boost")
    else:
        reason_codes.append("no_official_resolution_source_boost")
    return tuple(reason_codes)


def _normalize_candidates(
    candidates: object,
) -> tuple[StrategyResolutionConflictAdjustedEdgeScoreV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of candidate rows")
    try:
        items = tuple(candidates)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of candidate rows") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyResolutionConflictAdjustedEdgeScoreV2Candidate:
            raise ValueError(
                "candidates must contain StrategyResolutionConflictAdjustedEdgeScoreV2Candidate",
            )
        _require_hard_flags("candidate", item)
        if item.candidate_id in seen:
            raise ValueError("candidate_id values must be unique")
        seen.add(item.candidate_id)
    return items


def _normalize_rows(rows: object) -> tuple[StrategyResolutionConflictAdjustedEdgeScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of report rows")
    try:
        items = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable of report rows") from exc
    seen: set[str] = set()
    for row in items:
        if type(row) is not StrategyResolutionConflictAdjustedEdgeScoreV2Row:
            raise ValueError("rows must contain StrategyResolutionConflictAdjustedEdgeScoreV2Row")
        _require_hard_flags("row", row)
        _require_row_digest(row)
        if row.candidate_id in seen:
            raise ValueError("rows must have unique candidate_id values")
        seen.add(row.candidate_id)
    return tuple(sorted(items, key=_row_key))


def _normalize_public_payload(
    public_payload: object,
) -> tuple[StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)):
        raise ValueError("public_payload must be an iterable")
    try:
        items = tuple(public_payload)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("public_payload must be an iterable") from exc
    normalized: list[StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _row_key(row: StrategyResolutionConflictAdjustedEdgeScoreV2Row) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.edge_status], -row.conflict_adjusted_edge_score, row.candidate_id)


def _status_count(
    rows: tuple[StrategyResolutionConflictAdjustedEdgeScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.edge_status == status))


def _report_status(rows: tuple[StrategyResolutionConflictAdjustedEdgeScoreV2Row, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.edge_status == "blocked" for row in rows):
        return "blocked"
    if any(row.edge_status == "watch" for row in rows):
        return "watch"
    return "qualified"


def _report_reason_codes(
    rows: tuple[StrategyResolutionConflictAdjustedEdgeScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    status_codes = {f"conflict_adjusted_edge_{row.edge_status}" for row in rows}
    return tuple(sorted(status_codes, key=lambda value: _REASON_RANK[value]))


def _validate_row(row: StrategyResolutionConflictAdjustedEdgeScoreV2Row) -> None:
    expected_raw_edge = _normalize_decimal(
        "raw_edge",
        row.forecast_probability - row.implied_probability,
    )
    if row.raw_edge != expected_raw_edge:
        raise ValueError("raw_edge must match probabilities")
    expected_weighted = _normalize_decimal(
        "confidence_weighted_edge",
        row.raw_edge * row.confidence_score,
    )
    if row.confidence_weighted_edge != expected_weighted:
        raise ValueError("confidence_weighted_edge must match raw_edge and confidence_score")
    if row.unresolved_resolution_conflict_count > row.resolution_conflict_count:
        raise ValueError(
            "unresolved_resolution_conflict_count must not exceed resolution_conflict_count",
        )
    expected_score = _normalize_decimal(
        "conflict_adjusted_edge_score",
        row.confidence_weighted_edge
        - row.unresolved_resolution_conflict_penalty
        + row.official_resolution_source_boost,
    )
    if row.conflict_adjusted_edge_score != expected_score:
        raise ValueError("conflict_adjusted_edge_score must match adjusted components")
    if row.reason_codes[0] != f"conflict_adjusted_edge_{row.edge_status}":
        raise ValueError("reason_codes must match edge_status")


def _validate_report(report: StrategyResolutionConflictAdjustedEdgeScoreV2Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.qualified_count != _status_count(report.rows, "qualified"):
        raise ValueError("qualified_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.candidate_count != report.qualified_count + report.watch_count + report.blocked_count:
        raise ValueError("candidate_count must reconcile with status counts")
    if report.average_conflict_adjusted_edge_score != _average(
        tuple(row.conflict_adjusted_edge_score for row in report.rows),
    ):
        raise ValueError("average_conflict_adjusted_edge_score must match rows")
    expected_max_penalty = max(
        (row.unresolved_resolution_conflict_penalty for row in report.rows),
        default=_ZERO,
    )
    if report.max_unresolved_resolution_conflict_penalty != expected_max_penalty:
        raise ValueError("max_unresolved_resolution_conflict_penalty must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_digest(row: StrategyResolutionConflictAdjustedEdgeScoreV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategyResolutionConflictAdjustedEdgeScoreV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _require_row_digest(row: StrategyResolutionConflictAdjustedEdgeScoreV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: StrategyResolutionConflictAdjustedEdgeScoreV2Report) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_payload_flags("payload", payload)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a JSON list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_row_payload(f"payload.rows[{index}]", row)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _verify_row_payload(label: str, payload: dict[str, Any]) -> None:
    _require_exact_keys(label, payload, _ROW_PAYLOAD_KEYS)
    _require_payload_flags(label, payload)
    for field_name in (
        "forecast_probability",
        "implied_probability",
        "confidence_score",
        "resolution_conflict_count",
        "unresolved_resolution_conflict_count",
        "official_resolution_source_count",
        "raw_edge",
        "confidence_weighted_edge",
        "unresolved_resolution_conflict_penalty",
        "official_resolution_source_boost",
        "conflict_adjusted_edge_score",
    ):
        _require_decimal_string(f"{label}.{field_name}", payload[field_name])
    _require_status(f"{label}.edge_status", payload["edge_status"])
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _require_exact_keys(label: str, payload: dict[str, Any], expected: tuple[str, ...]) -> None:
    if set(payload) != set(expected):
        raise ValueError(f"{label} must contain exactly the expected public fields")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must be Decimal strings")
    if isinstance(value, float):
        raise ValueError("JSON values must not be floats")
    if type(value) is str:
        _require_public_text("JSON string", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_identifier("JSON object key", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            StrategyResolutionConflictAdjustedEdgeScoreV2Config,
            StrategyResolutionConflictAdjustedEdgeScoreV2Candidate,
            StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem,
            StrategyResolutionConflictAdjustedEdgeScoreV2Row,
            StrategyResolutionConflictAdjustedEdgeScoreV2Report,
        ):
            raise ValueError(f"{label} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError(f"{label} JSON Decimal values must be strings")
    if isinstance(value, float):
        raise ValueError(f"{label} JSON values must not be floats")
    if type(value) is int:
        raise ValueError(f"{label} JSON numeric values must be Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_public_numbers(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _has_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or "?" in lowered or "@" in lowered or any(
        term in lowered for term in _UNSAFE_PUBLIC_TERMS
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be blocked, watch, or qualified")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicate values")
    for item in items:
        _require_public_identifier(field_name, item)
    owned = [item for item in items if item in _OWNED_REASON_CODES]
    if owned != sorted(owned, key=lambda item: _REASON_RANK[item]):
        raise ValueError(f"{field_name} owned reason codes must match report semantics")
    return items


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _normalize_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a six-place Decimal string")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _normalize_decimal("average", sum(values, _ZERO) / Decimal(len(values)))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
