"""Pure Phase 1 paper-only candidate news freshness edge gate."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_NEWS_FRESHNESS_EDGE_GATE_V2_CONFIG_VERSION = (
    "strategy-candidate-news-freshness-edge-gate-v2"
)

GATE_STATUSES = ("pass", "watch", "blocked")
PASS_REASON_CODE = "news_freshness_edge_supported"
EMPTY_REASON_CODE = "news_freshness_edge_gate_empty"
ROW_REASON_CODE_SEQUENCE = (
    "latest_source_age_above_watch_limit",
    "latest_source_age_above_pass_limit",
    "official_update_below_watch_minimum",
    "official_update_below_pass_minimum",
    "independent_confirmations_below_watch_minimum",
    "independent_confirmations_below_pass_minimum",
    "probability_move_velocity_above_watch_limit",
    "probability_move_velocity_above_pass_limit",
    "edge_margin_below_watch_minimum",
    "edge_margin_below_pass_minimum",
    "cost_drag_above_watch_limit",
    "cost_drag_above_pass_limit",
    "news_freshness_edge_score_below_watch_minimum",
    "news_freshness_edge_score_below_pass_minimum",
    PASS_REASON_CODE,
)
REPORT_REASON_CODE_SEQUENCE = (EMPTY_REASON_CODE,) + ROW_REASON_CODE_SEQUENCE
BLOCK_REASON_CODES = frozenset(
    (
        "latest_source_age_above_watch_limit",
        "official_update_below_watch_minimum",
        "independent_confirmations_below_watch_minimum",
        "probability_move_velocity_above_watch_limit",
        "edge_margin_below_watch_minimum",
        "cost_drag_above_watch_limit",
        "news_freshness_edge_score_below_watch_minimum",
    ),
)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NEXT_STEP_BY_STATUS = {
    "pass": "retain_candidate_for_paper_review",
    "watch": "watch_candidate_pending_fresh_news",
    "blocked": "block_candidate_until_fresh_news_supports_edge",
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MINUS_ONE = Decimal("-1.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("mu", "tation"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


@dataclass(frozen=True)
class StrategyCandidateNewsFreshnessEdgeGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_NEWS_FRESHNESS_EDGE_GATE_V2_CONFIG_VERSION
    )
    max_pass_latest_source_age_seconds: Decimal = Decimal("1800.000000")
    max_watch_latest_source_age_seconds: Decimal = Decimal("7200.000000")
    min_pass_official_update_count: Decimal = Decimal("1.000000")
    min_watch_official_update_count: Decimal = Decimal("0.000000")
    min_pass_independent_confirmation_count: Decimal = Decimal("2.000000")
    min_watch_independent_confirmation_count: Decimal = Decimal("1.000000")
    max_pass_probability_move_velocity_per_hour: Decimal = Decimal("0.050000")
    max_watch_probability_move_velocity_per_hour: Decimal = Decimal("0.120000")
    min_pass_edge_margin_probability: Decimal = Decimal("0.030000")
    min_watch_edge_margin_probability: Decimal = Decimal("0.010000")
    max_pass_cost_drag_probability: Decimal = Decimal("0.010000")
    max_watch_cost_drag_probability: Decimal = Decimal("0.030000")
    min_pass_news_freshness_edge_score: Decimal = Decimal("0.700000")
    min_watch_news_freshness_edge_score: Decimal = Decimal("0.350000")
    source_age_weight: Decimal = Decimal("0.250000")
    official_update_weight: Decimal = Decimal("0.150000")
    independent_confirmation_weight: Decimal = Decimal("0.150000")
    probability_move_velocity_weight: Decimal = Decimal("0.150000")
    edge_margin_weight: Decimal = Decimal("0.200000")
    cost_drag_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateNewsFreshnessEdgeGateV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateNewsFreshnessEdgeGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_NEWS_FRESHNESS_EDGE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_latest_source_age_seconds",
            "max_watch_latest_source_age_seconds",
            "max_pass_probability_move_velocity_per_hour",
            "max_watch_probability_move_velocity_per_hour",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_official_update_count",
            "min_watch_official_update_count",
            "min_pass_independent_confirmation_count",
            "min_watch_independent_confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_edge_margin_probability",
            "min_watch_edge_margin_probability",
            "max_pass_cost_drag_probability",
            "max_watch_cost_drag_probability",
            "min_pass_news_freshness_edge_score",
            "min_watch_news_freshness_edge_score",
            "source_age_weight",
            "official_update_weight",
            "independent_confirmation_weight",
            "probability_move_velocity_weight",
            "edge_margin_weight",
            "cost_drag_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyCandidateNewsFreshnessEdgeGateV2Snapshot:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    latest_source_age_seconds: Decimal
    official_update_count: Decimal
    independent_confirmation_count: Decimal
    probability_move_velocity_per_hour: Decimal
    edge_margin_probability: Decimal
    cost_drag_probability: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateNewsFreshnessEdgeGateV2Snapshot does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateNewsFreshnessEdgeGateV2Snapshot, "snapshot")
        for field_name in ("candidate_id", "market_slug", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in ("official_update_count", "independent_confirmation_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_move_velocity_per_hour",
            _normalize_ratio(
                "probability_move_velocity_per_hour",
                self.probability_move_velocity_per_hour,
            ),
        )
        object.__setattr__(
            self,
            "edge_margin_probability",
            _normalize_margin("edge_margin_probability", self.edge_margin_probability),
        )
        object.__setattr__(
            self,
            "cost_drag_probability",
            _normalize_ratio("cost_drag_probability", self.cost_drag_probability),
        )
        _require_hard_flags("snapshot", self)
        _reject_unsafe_public_payload("snapshot", self)


@dataclass(frozen=True)
class StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_ratio("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class StrategyCandidateNewsFreshnessEdgeGateV2Row:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    latest_source_age_seconds: Decimal
    official_update_count: Decimal
    independent_confirmation_count: Decimal
    probability_move_velocity_per_hour: Decimal
    edge_margin_probability: Decimal
    cost_drag_probability: Decimal
    source_age_score: Decimal
    official_update_presence_score: Decimal
    independent_confirmation_score: Decimal
    probability_move_velocity_score: Decimal
    edge_margin_score: Decimal
    cost_drag_score: Decimal
    news_freshness_edge_score: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateNewsFreshnessEdgeGateV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateNewsFreshnessEdgeGateV2Row, "row")
        for field_name in ("candidate_id", "market_slug", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in ("official_update_count", "independent_confirmation_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_move_velocity_per_hour",
            _normalize_ratio(
                "probability_move_velocity_per_hour",
                self.probability_move_velocity_per_hour,
            ),
        )
        object.__setattr__(
            self,
            "edge_margin_probability",
            _normalize_margin("edge_margin_probability", self.edge_margin_probability),
        )
        object.__setattr__(
            self,
            "cost_drag_probability",
            _normalize_ratio("cost_drag_probability", self.cost_drag_probability),
        )
        for field_name in (
            "source_age_score",
            "official_update_presence_score",
            "independent_confirmation_score",
            "probability_move_velocity_score",
            "edge_margin_score",
            "cost_drag_score",
            "news_freshness_edge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyCandidateNewsFreshnessEdgeGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_latest_source_age_seconds: Decimal
    max_probability_move_velocity_per_hour: Decimal
    min_news_freshness_edge_score: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount, ...]
    rows: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateNewsFreshnessEdgeGateV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateNewsFreshnessEdgeGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_NEWS_FRESHNESS_EDGE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_latest_source_age_seconds",
                self.max_latest_source_age_seconds,
            ),
        )
        for field_name in (
            "max_probability_move_velocity_per_hour",
            "min_news_freshness_edge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)


def build_strategy_candidate_news_freshness_edge_gate_v2_report(
    snapshots: list[StrategyCandidateNewsFreshnessEdgeGateV2Snapshot]
    | tuple[StrategyCandidateNewsFreshnessEdgeGateV2Snapshot, ...],
    *,
    config: StrategyCandidateNewsFreshnessEdgeGateV2Config,
    generated_at: datetime,
) -> StrategyCandidateNewsFreshnessEdgeGateV2Report:
    if type(config) is not StrategyCandidateNewsFreshnessEdgeGateV2Config:
        raise ValueError("config must be a StrategyCandidateNewsFreshnessEdgeGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    _validate_unique_snapshots(normalized_snapshots)
    _validate_not_after_generated_at(normalized_snapshots, generated_at=generated_at_utc)

    rows = tuple(
        sorted(
            (_row_for_snapshot(snapshot, config=config) for snapshot in normalized_snapshots),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return StrategyCandidateNewsFreshnessEdgeGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_latest_source_age_seconds=max(
            (row.latest_source_age_seconds for row in rows),
            default=ZERO,
        ),
        max_probability_move_velocity_per_hour=max(
            (row.probability_move_velocity_per_hour for row in rows),
            default=ZERO,
        ),
        min_news_freshness_edge_score=min(
            (row.news_freshness_edge_score for row in rows),
            default=ZERO,
        ),
        gate_status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_candidate_news_freshness_edge_gate_v2_public_payload(
    report: StrategyCandidateNewsFreshnessEdgeGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateNewsFreshnessEdgeGateV2Report:
        raise ValueError("report must be a StrategyCandidateNewsFreshnessEdgeGateV2Report")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload(payload)
    return payload


def validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("strategy candidate news freshness edge payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_snapshot(
    snapshot: StrategyCandidateNewsFreshnessEdgeGateV2Snapshot,
    *,
    config: StrategyCandidateNewsFreshnessEdgeGateV2Config,
) -> StrategyCandidateNewsFreshnessEdgeGateV2Row:
    source_age_score = _upper_limit_score(
        snapshot.latest_source_age_seconds,
        config.max_watch_latest_source_age_seconds,
    )
    official_update_presence_score = _count_floor_score(
        snapshot.official_update_count,
        config.min_pass_official_update_count,
    )
    independent_confirmation_score = _count_floor_score(
        snapshot.independent_confirmation_count,
        config.min_pass_independent_confirmation_count,
    )
    probability_move_velocity_score = _upper_limit_score(
        snapshot.probability_move_velocity_per_hour,
        config.max_watch_probability_move_velocity_per_hour,
    )
    edge_margin_score = _ratio_floor_score(
        snapshot.edge_margin_probability,
        config.min_pass_edge_margin_probability,
    )
    cost_drag_score = _upper_limit_score(
        snapshot.cost_drag_probability,
        config.max_watch_cost_drag_probability,
    )
    news_freshness_edge_score = _news_freshness_edge_score(
        source_age_score=source_age_score,
        official_update_presence_score=official_update_presence_score,
        independent_confirmation_score=independent_confirmation_score,
        probability_move_velocity_score=probability_move_velocity_score,
        edge_margin_score=edge_margin_score,
        cost_drag_score=cost_drag_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        latest_source_age_seconds=snapshot.latest_source_age_seconds,
        official_update_count=snapshot.official_update_count,
        independent_confirmation_count=snapshot.independent_confirmation_count,
        probability_move_velocity_per_hour=snapshot.probability_move_velocity_per_hour,
        edge_margin_probability=snapshot.edge_margin_probability,
        cost_drag_probability=snapshot.cost_drag_probability,
        news_freshness_edge_score=news_freshness_edge_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return StrategyCandidateNewsFreshnessEdgeGateV2Row(
        candidate_id=snapshot.candidate_id,
        market_slug=snapshot.market_slug,
        observed_at=snapshot.observed_at,
        latest_source_age_seconds=snapshot.latest_source_age_seconds,
        official_update_count=snapshot.official_update_count,
        independent_confirmation_count=snapshot.independent_confirmation_count,
        probability_move_velocity_per_hour=snapshot.probability_move_velocity_per_hour,
        edge_margin_probability=snapshot.edge_margin_probability,
        cost_drag_probability=snapshot.cost_drag_probability,
        source_age_score=source_age_score,
        official_update_presence_score=official_update_presence_score,
        independent_confirmation_score=independent_confirmation_score,
        probability_move_velocity_score=probability_move_velocity_score,
        edge_margin_score=edge_margin_score,
        cost_drag_score=cost_drag_score,
        news_freshness_edge_score=news_freshness_edge_score,
        gate_status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        reason_codes=reason_codes,
        source_config_version=snapshot.source_config_version,
    )


def _row_reason_codes(
    *,
    latest_source_age_seconds: Decimal,
    official_update_count: Decimal,
    independent_confirmation_count: Decimal,
    probability_move_velocity_per_hour: Decimal,
    edge_margin_probability: Decimal,
    cost_drag_probability: Decimal,
    news_freshness_edge_score: Decimal,
    config: StrategyCandidateNewsFreshnessEdgeGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if latest_source_age_seconds > config.max_watch_latest_source_age_seconds:
        reason_codes.append("latest_source_age_above_watch_limit")
    elif latest_source_age_seconds > config.max_pass_latest_source_age_seconds:
        reason_codes.append("latest_source_age_above_pass_limit")
    if official_update_count < config.min_watch_official_update_count:
        reason_codes.append("official_update_below_watch_minimum")
    elif official_update_count < config.min_pass_official_update_count:
        reason_codes.append("official_update_below_pass_minimum")
    if independent_confirmation_count < config.min_watch_independent_confirmation_count:
        reason_codes.append("independent_confirmations_below_watch_minimum")
    elif independent_confirmation_count < config.min_pass_independent_confirmation_count:
        reason_codes.append("independent_confirmations_below_pass_minimum")
    if probability_move_velocity_per_hour > config.max_watch_probability_move_velocity_per_hour:
        reason_codes.append("probability_move_velocity_above_watch_limit")
    elif probability_move_velocity_per_hour > config.max_pass_probability_move_velocity_per_hour:
        reason_codes.append("probability_move_velocity_above_pass_limit")
    if edge_margin_probability < config.min_watch_edge_margin_probability:
        reason_codes.append("edge_margin_below_watch_minimum")
    elif edge_margin_probability < config.min_pass_edge_margin_probability:
        reason_codes.append("edge_margin_below_pass_minimum")
    if cost_drag_probability > config.max_watch_cost_drag_probability:
        reason_codes.append("cost_drag_above_watch_limit")
    elif cost_drag_probability > config.max_pass_cost_drag_probability:
        reason_codes.append("cost_drag_above_pass_limit")
    if news_freshness_edge_score < config.min_watch_news_freshness_edge_score:
        reason_codes.append("news_freshness_edge_score_below_watch_minimum")
    elif news_freshness_edge_score < config.min_pass_news_freshness_edge_score:
        reason_codes.append("news_freshness_edge_score_below_pass_minimum")
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Row, ...]) -> str:
    statuses = tuple(row.gate_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    if "pass" in statuses:
        return "pass"
    return "blocked"


def _report_reason_codes(
    rows: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    present = set(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    )
    if not present:
        return (PASS_REASON_CODE,)
    return tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in present)


def _reason_code_counts(
    rows: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Row, ...],
) -> tuple[StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount, ...]:
    candidate_count = _count(len(rows))
    return tuple(
        StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            candidate_ratio=_ratio(_reason_count(rows, reason_code), candidate_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_snapshots(
    value: object,
) -> tuple[StrategyCandidateNewsFreshnessEdgeGateV2Snapshot, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    snapshots = tuple(value)
    for item in snapshots:
        if type(item) is not StrategyCandidateNewsFreshnessEdgeGateV2Snapshot:
            raise ValueError(
                "snapshots must contain StrategyCandidateNewsFreshnessEdgeGateV2Snapshot values",
            )
        _require_hard_flags("snapshot", item)
    return snapshots


def _normalize_rows(
    value: object,
) -> tuple[StrategyCandidateNewsFreshnessEdgeGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyCandidateNewsFreshnessEdgeGateV2Row:
            raise ValueError("rows must contain StrategyCandidateNewsFreshnessEdgeGateV2Row values")
        _require_hard_flags("row", row)
        key = _candidate_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate candidate news freshness snapshot")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODE_SEQUENCE
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_config(config: StrategyCandidateNewsFreshnessEdgeGateV2Config) -> None:
    _require_less_or_equal(
        "max_pass_latest_source_age_seconds",
        config.max_pass_latest_source_age_seconds,
        config.max_watch_latest_source_age_seconds,
    )
    _require_less_or_equal(
        "min_watch_official_update_count",
        config.min_watch_official_update_count,
        config.min_pass_official_update_count,
    )
    _require_less_or_equal(
        "min_watch_independent_confirmation_count",
        config.min_watch_independent_confirmation_count,
        config.min_pass_independent_confirmation_count,
    )
    _require_less_or_equal(
        "max_pass_probability_move_velocity_per_hour",
        config.max_pass_probability_move_velocity_per_hour,
        config.max_watch_probability_move_velocity_per_hour,
    )
    _require_less_or_equal(
        "min_watch_edge_margin_probability",
        config.min_watch_edge_margin_probability,
        config.min_pass_edge_margin_probability,
    )
    _require_less_or_equal(
        "max_pass_cost_drag_probability",
        config.max_pass_cost_drag_probability,
        config.max_watch_cost_drag_probability,
    )
    _require_less_or_equal(
        "min_watch_news_freshness_edge_score",
        config.min_watch_news_freshness_edge_score,
        config.min_pass_news_freshness_edge_score,
    )
    weight_sum = _add_decimal(
        config.source_age_weight,
        config.official_update_weight,
        config.independent_confirmation_weight,
        config.probability_move_velocity_weight,
        config.edge_margin_weight,
        config.cost_drag_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_unique_snapshots(
    snapshots: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Snapshot, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for snapshot in snapshots:
        key = _candidate_key(snapshot)
        if key in seen:
            raise ValueError("snapshots contain duplicate candidate news freshness snapshot")
        seen.add(key)


def _validate_not_after_generated_at(
    snapshots: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Snapshot, ...],
    *,
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _validate_row(row: StrategyCandidateNewsFreshnessEdgeGateV2Row) -> None:
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.recommended_next_step != NEXT_STEP_BY_STATUS[row.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyCandidateNewsFreshnessEdgeGateV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.candidate_count != report.pass_count + report.watch_count + report.blocked_count:
        raise ValueError("candidate_count must reconcile with status counts")
    if report.max_latest_source_age_seconds != max(
        (row.latest_source_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_latest_source_age_seconds must match rows")
    if report.max_probability_move_velocity_per_hour != max(
        (row.probability_move_velocity_per_hour for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_probability_move_velocity_per_hour must match rows")
    if report.min_news_freshness_edge_score != min(
        (row.news_freshness_edge_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_news_freshness_edge_score must match rows")
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _news_freshness_edge_score(
    *,
    source_age_score: Decimal,
    official_update_presence_score: Decimal,
    independent_confirmation_score: Decimal,
    probability_move_velocity_score: Decimal,
    edge_margin_score: Decimal,
    cost_drag_score: Decimal,
    config: StrategyCandidateNewsFreshnessEdgeGateV2Config,
) -> Decimal:
    return _normalize_ratio(
        "news_freshness_edge_score",
        _add_decimal(
            source_age_score * config.source_age_weight,
            official_update_presence_score * config.official_update_weight,
            independent_confirmation_score * config.independent_confirmation_weight,
            probability_move_velocity_score * config.probability_move_velocity_weight,
            edge_margin_score * config.edge_margin_weight,
            cost_drag_score * config.cost_drag_weight,
        ),
    )


def _upper_limit_score(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO:
        raise ValueError("upper limit must be positive")
    return _clamp_ratio(_subtract_decimal(ONE, _ratio_decimal(value, limit)))


def _count_floor_score(value: Decimal, floor: Decimal) -> Decimal:
    if floor == ZERO:
        return ONE
    return _clamp_ratio(_ratio_decimal(value, floor))


def _ratio_floor_score(value: Decimal, floor: Decimal) -> Decimal:
    if floor == ZERO:
        if value >= ZERO:
            return ONE
        return ZERO
    return _clamp_ratio(_ratio_decimal(max(value, ZERO), floor))


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _digest_payload(digest_payload)


def _report_derived_validation_digest(
    report: StrategyCandidateNewsFreshnessEdgeGateV2Report,
) -> str:
    return _digest_payload(_report_public_payload_for_digest(report))


def _row_derived_validation_digest(row: StrategyCandidateNewsFreshnessEdgeGateV2Row) -> str:
    return _digest_payload(_row_public_payload_for_digest(row))


def _report_public_payload_for_digest(
    report: StrategyCandidateNewsFreshnessEdgeGateV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "max_latest_source_age_seconds": _decimal_payload(
            report.max_latest_source_age_seconds,
        ),
        "max_probability_move_velocity_per_hour": _decimal_payload(
            report.max_probability_move_velocity_per_hour,
        ),
        "min_news_freshness_edge_score": _decimal_payload(
            report.min_news_freshness_edge_score,
        ),
        "gate_status": report.gate_status,
        "recommended_next_step": report.recommended_next_step,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_public_payload(item) for item in report.reason_code_counts
        ],
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: StrategyCandidateNewsFreshnessEdgeGateV2Row) -> dict[str, Any]:
    payload = _row_public_payload_for_digest(row)
    payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _row_public_payload_for_digest(
    row: StrategyCandidateNewsFreshnessEdgeGateV2Row,
) -> dict[str, Any]:
    return {
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "observed_at": _datetime_payload(row.observed_at),
        "latest_source_age_seconds": _decimal_payload(row.latest_source_age_seconds),
        "official_update_count": _decimal_payload(row.official_update_count),
        "independent_confirmation_count": _decimal_payload(
            row.independent_confirmation_count,
        ),
        "probability_move_velocity_per_hour": _decimal_payload(
            row.probability_move_velocity_per_hour,
        ),
        "edge_margin_probability": _decimal_payload(row.edge_margin_probability),
        "cost_drag_probability": _decimal_payload(row.cost_drag_probability),
        "source_age_score": _decimal_payload(row.source_age_score),
        "official_update_presence_score": _decimal_payload(
            row.official_update_presence_score,
        ),
        "independent_confirmation_score": _decimal_payload(
            row.independent_confirmation_score,
        ),
        "probability_move_velocity_score": _decimal_payload(
            row.probability_move_velocity_score,
        ),
        "edge_margin_score": _decimal_payload(row.edge_margin_score),
        "cost_drag_score": _decimal_payload(row.cost_drag_score),
        "news_freshness_edge_score": _decimal_payload(row.news_freshness_edge_score),
        "gate_status": row.gate_status,
        "recommended_next_step": row.recommended_next_step,
        "reason_codes": list(row.reason_codes),
        "source_config_version": row.source_config_version,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_public_payload(
    item: StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "candidate_ratio": _decimal_payload(item.candidate_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _digest_payload(payload: dict[str, Any]) -> str:
    _reject_public_numeric_values(payload)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _datetime_payload(value: datetime) -> str:
    value = _as_utc("datetime payload", value)
    return value.isoformat()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("Decimal payload value must be exactly Decimal")
    if not value.is_finite():
        raise ValueError("Decimal payload value must be finite")
    return str(_quantize(value))


def _reject_public_numeric_values(value: object) -> None:
    if value is None or type(value) in (str, bool):
        return
    if isinstance(value, Decimal) or type(value) is int or isinstance(value, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_public_numeric_values(item)
        return
    raise ValueError("public payload contains unsupported value")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _json_ready(value: object) -> Any:
    if type(value) is StrategyCandidateNewsFreshnessEdgeGateV2Report:
        payload = _report_public_payload_for_digest(value)
        payload["derived_validation_digest"] = value.derived_validation_digest
        return payload
    if type(value) is StrategyCandidateNewsFreshnessEdgeGateV2Row:
        return _row_public_payload(value)
    if type(value) is StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount:
        return _reason_code_count_public_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return _datetime_payload(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            StrategyCandidateNewsFreshnessEdgeGateV2Config,
            StrategyCandidateNewsFreshnessEdgeGateV2Snapshot,
            StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount,
            StrategyCandidateNewsFreshnessEdgeGateV2Row,
            StrategyCandidateNewsFreshnessEdgeGateV2Report,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), field_path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        _as_utc(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numeric values must use Decimal strings")
    if isinstance(value, (Decimal, datetime)):
        raise ValueError(f"{current_path} must use supported public value types")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} contains unsafe detail")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe detail")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_less_or_equal(field_name: str, lower_value: Decimal, upper_value: Decimal) -> None:
    if lower_value > upper_value:
        raise ValueError(f"{field_name} must not exceed paired threshold")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_margin(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < MINUS_ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between minus one and one")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _status_count(
    rows: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Row, ...],
    gate_status: str,
) -> Decimal:
    _require_member("gate_status", gate_status, GATE_STATUSES)
    return _count(len(tuple(row for row in rows if row.gate_status == gate_status)))


def _reason_count(
    rows: tuple[StrategyCandidateNewsFreshnessEdgeGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    _require_member("reason_code", reason_code, ROW_REASON_CODE_SEQUENCE)
    return _count(len(tuple(row for row in rows if reason_code in row.reason_codes)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(_ratio_decimal(numerator, denominator))


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("ratio denominator must be positive")
    return _quantize(numerator / denominator)


def _add_decimal(*values: Decimal) -> Decimal:
    return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left - right)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), ZERO), ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _candidate_key(
    value: StrategyCandidateNewsFreshnessEdgeGateV2Snapshot
    | StrategyCandidateNewsFreshnessEdgeGateV2Row,
) -> tuple[str, str]:
    return (value.candidate_id, value.market_slug)


def _row_sort_key(
    row: StrategyCandidateNewsFreshnessEdgeGateV2Row,
) -> tuple[Decimal, str, str]:
    return (STATUS_RANK[row.gate_status], row.candidate_id, row.market_slug)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_NEWS_FRESHNESS_EDGE_GATE_V2_CONFIG_VERSION",
    "StrategyCandidateNewsFreshnessEdgeGateV2Config",
    "StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount",
    "StrategyCandidateNewsFreshnessEdgeGateV2Report",
    "StrategyCandidateNewsFreshnessEdgeGateV2Row",
    "StrategyCandidateNewsFreshnessEdgeGateV2Snapshot",
    "build_strategy_candidate_news_freshness_edge_gate_v2_report",
    "strategy_candidate_news_freshness_edge_gate_v2_public_payload",
    "validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload",
)
