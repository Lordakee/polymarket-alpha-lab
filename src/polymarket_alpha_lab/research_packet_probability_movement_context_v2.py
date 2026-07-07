"""Pure in-memory Phase 1 probability movement context report."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVEMENT_CONTEXT_V2_CONFIG_VERSION = (
    "research-packet-probability-movement-context-v2"
)

Q = Decimal("0.000001")
COUNT_Q = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")
COUNT_ONE = Decimal("1")

CONTEXT_BANDS = frozenset(("high", "medium", "low"))
RESEARCH_ACTIONS = frozenset(("explain_now", "monitor_context", "defer_context"))
REASON_PRIORITY = {
    "source_freshness_high": 0,
    "source_freshness_watch": 1,
    "source_freshness_stale": 2,
    "event_velocity_high": 3,
    "event_velocity_normal": 4,
    "event_velocity_low": 5,
    "official_source_update_high": 6,
    "official_source_update_normal": 7,
    "official_source_update_none": 8,
    "contradiction_change_high": 9,
    "contradiction_change_normal": 10,
    "contradiction_change_low": 11,
    "liquidity_depth_thin": 12,
    "liquidity_depth_watch": 13,
    "liquidity_depth_deep": 14,
    "specialist_uncertainty_elevated": 15,
    "specialist_uncertainty_normal": 16,
    "specialist_uncertainty_low": 17,
    "resolution_horizon_near": 18,
    "resolution_horizon_watch": 19,
    "resolution_horizon_distant": 20,
    "context_high": 21,
    "context_medium": 22,
    "context_low": 23,
}
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "high_context_count",
        "medium_context_count",
        "low_context_count",
        "average_movement_context_score",
        "max_movement_context_score",
        "max_probability_delta",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "rank",
        "packet_id",
        "event_title",
        "previous_probability",
        "current_probability",
        "probability_delta",
        "source_freshness_hours",
        "source_freshness_score",
        "event_velocity",
        "official_source_update_intensity",
        "contradiction_change_score",
        "liquidity_depth_usd",
        "liquidity_depth_score",
        "specialist_uncertainty",
        "hours_to_resolution",
        "resolution_horizon_score",
        "movement_context_score",
        "context_band",
        "research_action",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sign" + "ing",
        "muta" + "tion",
        "b" + "uy",
        "se" + "ll",
        "tra" + "de",
    ),
)


@dataclass(frozen=True)
class ResearchPacketProbabilityMovementContextV2Config:
    config_version: str
    stale_source_hours: Decimal
    resolution_horizon_hours: Decimal
    thin_liquidity_depth_usd: Decimal
    high_context_threshold: Decimal
    medium_context_threshold: Decimal
    source_freshness_weight: Decimal
    event_velocity_weight: Decimal
    official_source_update_weight: Decimal
    contradiction_change_weight: Decimal
    liquidity_depth_weight: Decimal
    specialist_uncertainty_weight: Decimal
    resolution_horizon_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _config_version(self.config_version)
        for name in (
            "stale_source_hours",
            "resolution_horizon_hours",
            "thin_liquidity_depth_usd",
        ):
            object.__setattr__(self, name, _dec_positive(name, getattr(self, name)))
        for name in ("high_context_threshold", "medium_context_threshold"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if self.medium_context_threshold > self.high_context_threshold:
            raise ValueError("medium_context_threshold must not exceed high_context_threshold")
        for name in (
            "source_freshness_weight",
            "event_velocity_weight",
            "official_source_update_weight",
            "contradiction_change_weight",
            "liquidity_depth_weight",
            "specialist_uncertainty_weight",
            "resolution_horizon_weight",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if _weight_total(self) != ONE:
            raise ValueError("context weights must total 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMovementContextV2Candidate:
    packet_id: str
    event_title: str
    previous_probability: Decimal
    current_probability: Decimal
    source_freshness_hours: Decimal
    event_velocity: Decimal
    official_source_update_intensity: Decimal
    contradiction_change_score: Decimal
    liquidity_depth_usd: Decimal
    specialist_uncertainty: Decimal
    hours_to_resolution: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _safe_text("packet_id", self.packet_id)
        _safe_text("event_title", self.event_title)
        for name in ("previous_probability", "current_probability"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        for name in (
            "source_freshness_hours",
            "liquidity_depth_usd",
            "hours_to_resolution",
        ):
            object.__setattr__(self, name, _dec_nonnegative(name, getattr(self, name)))
        for name in (
            "event_velocity",
            "official_source_update_intensity",
            "contradiction_change_score",
            "specialist_uncertainty",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMovementContextV2Row:
    rank: Decimal
    packet_id: str
    event_title: str
    previous_probability: Decimal
    current_probability: Decimal
    probability_delta: Decimal
    source_freshness_hours: Decimal
    source_freshness_score: Decimal
    event_velocity: Decimal
    official_source_update_intensity: Decimal
    contradiction_change_score: Decimal
    liquidity_depth_usd: Decimal
    liquidity_depth_score: Decimal
    specialist_uncertainty: Decimal
    hours_to_resolution: Decimal
    resolution_horizon_score: Decimal
    movement_context_score: Decimal
    context_band: str
    research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _count_positive("rank", self.rank))
        _safe_text("packet_id", self.packet_id)
        _safe_text("event_title", self.event_title)
        for name in ("previous_probability", "current_probability"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "probability_delta",
            _dec_nonnegative("probability_delta", self.probability_delta),
        )
        for name in (
            "source_freshness_hours",
            "liquidity_depth_usd",
            "hours_to_resolution",
        ):
            object.__setattr__(self, name, _dec_nonnegative(name, getattr(self, name)))
        for name in (
            "source_freshness_score",
            "event_velocity",
            "official_source_update_intensity",
            "contradiction_change_score",
            "liquidity_depth_score",
            "specialist_uncertainty",
            "resolution_horizon_score",
            "movement_context_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _member("context_band", self.context_band, CONTEXT_BANDS)
        _member("research_action", self.research_action, RESEARCH_ACTIONS)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMovementContextV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    high_context_count: Decimal
    medium_context_count: Decimal
    low_context_count: Decimal
    average_movement_context_score: Decimal
    max_movement_context_score: Decimal
    max_probability_delta: Decimal
    rows: tuple[ResearchPacketProbabilityMovementContextV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        for name in (
            "candidate_count",
            "high_context_count",
            "medium_context_count",
            "low_context_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in (
            "average_movement_context_score",
            "max_movement_context_score",
            "max_probability_delta",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_digest(self)
        _report_matches(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_probability_movement_context_v2_payload(self)


def build_research_packet_probability_movement_context_v2(
    candidates: Iterable[ResearchPacketProbabilityMovementContextV2Candidate],
    *,
    config: ResearchPacketProbabilityMovementContextV2Config,
    generated_at: datetime,
) -> ResearchPacketProbabilityMovementContextV2Report:
    if type(config) is not ResearchPacketProbabilityMovementContextV2Config:
        raise ValueError("config must be a probability movement context config")
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    source_rows = _normalize_candidates(candidates)
    built_rows = _ranked_rows(tuple(_row(candidate, config) for candidate in source_rows))
    report_values = {
        "generated_at": stamp,
        "config_version": config.config_version,
        "candidate_count": Decimal(len(built_rows)),
        "high_context_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.context_band == "high"),
        ),
        "medium_context_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.context_band == "medium"),
        ),
        "low_context_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.context_band == "low"),
        ),
        "average_movement_context_score": _average(
            tuple(row.movement_context_score for row in built_rows),
        ),
        "max_movement_context_score": max(
            (row.movement_context_score for row in built_rows),
            default=ZERO,
        ),
        "max_probability_delta": max(
            (row.probability_delta for row in built_rows),
            default=ZERO,
        ),
        "rows": built_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _derive_digest_from_public_payload(_payload(report_values))
    return ResearchPacketProbabilityMovementContextV2Report(
        **report_values,
        derived_validation_digest=digest,
    )


def research_packet_probability_movement_context_v2_payload(
    report: ResearchPacketProbabilityMovementContextV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketProbabilityMovementContextV2Report:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability movement context report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    return payload


def derive_research_packet_probability_movement_context_v2_digest(
    report: ResearchPacketProbabilityMovementContextV2Report | dict[str, Any],
) -> str:
    if type(report) is ResearchPacketProbabilityMovementContextV2Report:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability movement context report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload, digest_required=False)
    _require_hard_flags("payload", _DictFlags(payload))
    return _derive_digest_from_public_payload(payload)


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


def _row(
    candidate: ResearchPacketProbabilityMovementContextV2Candidate,
    config: ResearchPacketProbabilityMovementContextV2Config,
) -> ResearchPacketProbabilityMovementContextV2Row:
    source_freshness_score = _clamp_unit(
        ONE - _q(candidate.source_freshness_hours / config.stale_source_hours),
    )
    liquidity_depth_score = _clamp_unit(
        ONE - _q(candidate.liquidity_depth_usd / config.thin_liquidity_depth_usd),
    )
    resolution_horizon_score = _clamp_unit(
        ONE - _q(candidate.hours_to_resolution / config.resolution_horizon_hours),
    )
    context_score = _movement_context_score(
        config,
        source_freshness_score=source_freshness_score,
        event_velocity=candidate.event_velocity,
        official_source_update_intensity=candidate.official_source_update_intensity,
        contradiction_change_score=candidate.contradiction_change_score,
        liquidity_depth_score=liquidity_depth_score,
        specialist_uncertainty=candidate.specialist_uncertainty,
        resolution_horizon_score=resolution_horizon_score,
    )
    band = _context_band(context_score, config)
    return ResearchPacketProbabilityMovementContextV2Row(
        rank=COUNT_ONE,
        packet_id=candidate.packet_id,
        event_title=candidate.event_title,
        previous_probability=candidate.previous_probability,
        current_probability=candidate.current_probability,
        probability_delta=_probability_delta(
            candidate.previous_probability,
            candidate.current_probability,
        ),
        source_freshness_hours=candidate.source_freshness_hours,
        source_freshness_score=source_freshness_score,
        event_velocity=candidate.event_velocity,
        official_source_update_intensity=candidate.official_source_update_intensity,
        contradiction_change_score=candidate.contradiction_change_score,
        liquidity_depth_usd=candidate.liquidity_depth_usd,
        liquidity_depth_score=liquidity_depth_score,
        specialist_uncertainty=candidate.specialist_uncertainty,
        hours_to_resolution=candidate.hours_to_resolution,
        resolution_horizon_score=resolution_horizon_score,
        movement_context_score=context_score,
        context_band=band,
        research_action=_research_action_for_band(band),
        reason_codes=_dedupe(
            (
                _source_freshness_reason(source_freshness_score),
                _unit_reason("event_velocity", candidate.event_velocity),
                _official_update_reason(candidate.official_source_update_intensity),
                _unit_reason(
                    "contradiction_change",
                    candidate.contradiction_change_score,
                ),
                _liquidity_reason(liquidity_depth_score),
                _specialist_uncertainty_reason(candidate.specialist_uncertainty),
                _resolution_reason(resolution_horizon_score),
                f"context_{band}",
            ),
        ),
    )


def _ranked_rows(
    rows: tuple[ResearchPacketProbabilityMovementContextV2Row, ...],
) -> tuple[ResearchPacketProbabilityMovementContextV2Row, ...]:
    ranked = []
    for index, row in enumerate(sorted(rows, key=_row_key), start=1):
        ranked.append(
            ResearchPacketProbabilityMovementContextV2Row(
                rank=Decimal(index),
                packet_id=row.packet_id,
                event_title=row.event_title,
                previous_probability=row.previous_probability,
                current_probability=row.current_probability,
                probability_delta=row.probability_delta,
                source_freshness_hours=row.source_freshness_hours,
                source_freshness_score=row.source_freshness_score,
                event_velocity=row.event_velocity,
                official_source_update_intensity=row.official_source_update_intensity,
                contradiction_change_score=row.contradiction_change_score,
                liquidity_depth_usd=row.liquidity_depth_usd,
                liquidity_depth_score=row.liquidity_depth_score,
                specialist_uncertainty=row.specialist_uncertainty,
                hours_to_resolution=row.hours_to_resolution,
                resolution_horizon_score=row.resolution_horizon_score,
                movement_context_score=row.movement_context_score,
                context_band=row.context_band,
                research_action=row.research_action,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_key(row: ResearchPacketProbabilityMovementContextV2Row) -> tuple[Decimal, Decimal, str]:
    return (-row.movement_context_score, -row.probability_delta, row.packet_id)


def _movement_context_score(
    config: ResearchPacketProbabilityMovementContextV2Config,
    *,
    source_freshness_score: Decimal,
    event_velocity: Decimal,
    official_source_update_intensity: Decimal,
    contradiction_change_score: Decimal,
    liquidity_depth_score: Decimal,
    specialist_uncertainty: Decimal,
    resolution_horizon_score: Decimal,
) -> Decimal:
    return _q(
        source_freshness_score * config.source_freshness_weight
        + event_velocity * config.event_velocity_weight
        + official_source_update_intensity * config.official_source_update_weight
        + contradiction_change_score * config.contradiction_change_weight
        + liquidity_depth_score * config.liquidity_depth_weight
        + specialist_uncertainty * config.specialist_uncertainty_weight
        + resolution_horizon_score * config.resolution_horizon_weight,
    )


def _context_band(
    context_score: Decimal,
    config: ResearchPacketProbabilityMovementContextV2Config,
) -> str:
    if context_score >= config.high_context_threshold:
        return "high"
    if context_score >= config.medium_context_threshold:
        return "medium"
    return "low"


def _research_action_for_band(context_band: str) -> str:
    if context_band == "high":
        return "explain_now"
    if context_band == "medium":
        return "monitor_context"
    return "defer_context"


def _source_freshness_reason(source_freshness_score: Decimal) -> str:
    if source_freshness_score >= Decimal("0.750000"):
        return "source_freshness_high"
    if source_freshness_score >= Decimal("0.250000"):
        return "source_freshness_watch"
    return "source_freshness_stale"


def _unit_reason(prefix: str, value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return f"{prefix}_high"
    if value >= Decimal("0.250000"):
        return f"{prefix}_normal"
    return f"{prefix}_low"


def _official_update_reason(value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return "official_source_update_high"
    if value > ZERO:
        return "official_source_update_normal"
    return "official_source_update_none"


def _liquidity_reason(value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return "liquidity_depth_thin"
    if value >= Decimal("0.250000"):
        return "liquidity_depth_watch"
    return "liquidity_depth_deep"


def _specialist_uncertainty_reason(value: Decimal) -> str:
    if value >= Decimal("0.500000"):
        return "specialist_uncertainty_elevated"
    if value >= Decimal("0.250000"):
        return "specialist_uncertainty_normal"
    return "specialist_uncertainty_low"


def _resolution_reason(value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return "resolution_horizon_near"
    if value >= Decimal("0.250000"):
        return "resolution_horizon_watch"
    return "resolution_horizon_distant"


def _validate_row(row: ResearchPacketProbabilityMovementContextV2Row) -> None:
    if row.probability_delta != _probability_delta(
        row.previous_probability,
        row.current_probability,
    ):
        raise ValueError("probability_delta must match probability inputs")
    if row.research_action != _research_action_for_band(row.context_band):
        raise ValueError("research_action must match context_band")


def _report_matches(report: ResearchPacketProbabilityMovementContextV2Report) -> None:
    rows = report.rows
    expected_count = Decimal(len(rows))
    if report.candidate_count != expected_count:
        raise ValueError("candidate_count must match rows")
    if report.high_context_count != Decimal(
        sum(COUNT_ONE for row in rows if row.context_band == "high"),
    ):
        raise ValueError("high_context_count must match rows")
    if report.medium_context_count != Decimal(
        sum(COUNT_ONE for row in rows if row.context_band == "medium"),
    ):
        raise ValueError("medium_context_count must match rows")
    if report.low_context_count != Decimal(
        sum(COUNT_ONE for row in rows if row.context_band == "low"),
    ):
        raise ValueError("low_context_count must match rows")
    if report.average_movement_context_score != _average(
        tuple(row.movement_context_score for row in rows),
    ):
        raise ValueError("average_movement_context_score must match rows")
    if report.max_movement_context_score != max(
        (row.movement_context_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_movement_context_score must match rows")
    if report.max_probability_delta != max(
        (row.probability_delta for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_probability_delta must match rows")
    expected_ranks = tuple(Decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")


def _validate_digest(report: ResearchPacketProbabilityMovementContextV2Report) -> None:
    if report.derived_validation_digest != _derive_digest_from_public_payload(
        _payload(report),
    ):
        raise ValueError("derived_validation_digest must match report payload")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _hex_digest("derived_validation_digest", digest)
    if digest != _derive_digest_from_public_payload(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _derive_digest_from_public_payload(payload: dict[str, Any]) -> str:
    core = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, Decimal):
        if field_name in {
            "rank",
            "candidate_count",
            "high_context_count",
            "medium_context_count",
            "low_context_count",
        } and value == value.to_integral_value():
            return str(value.quantize(COUNT_Q))
        return str(value)
    if type(value) is datetime:
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return text[:-6] + "Z"
        return text
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload(getattr(value, field.name), field_name=field.name)
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload(item) for item in value]
    if isinstance(value, list):
        return [_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _payload(item, field_name=key)
            for key, item in value.items()
        }
    return value


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_payload(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is bool or type(value) is str or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _unsafe_text(key):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool = True,
) -> None:
    for key in payload:
        if key not in REPORT_PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")
    if digest_required and "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest must be present")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        for key in row:
            if key not in ROW_PAYLOAD_FIELDS:
                raise ValueError("payload field is not supported")
        _require_hard_flags("row payload", _DictFlags(row))


def _normalize_candidates(
    candidates: Iterable[ResearchPacketProbabilityMovementContextV2Candidate],
) -> tuple[ResearchPacketProbabilityMovementContextV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidate rows must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidate rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchPacketProbabilityMovementContextV2Candidate:
            raise ValueError("candidate rows must contain movement context candidates")
        _require_hard_flags("candidate", row)
    return rows


def _normalize_rows(
    rows: tuple[ResearchPacketProbabilityMovementContextV2Row, ...],
) -> tuple[ResearchPacketProbabilityMovementContextV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPacketProbabilityMovementContextV2Row:
            raise ValueError("rows must contain movement context row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_checked_reason(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _checked_reason(value: str) -> str:
    if type(value) is not str or value not in REASON_PRIORITY:
        raise ValueError("reason_codes must be supported")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")
    return value


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        _checked_reason(value)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(sorted(result, key=lambda item: REASON_PRIORITY[item]))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _q(sum(values, ZERO) / Decimal(len(values)))


def _weight_total(config: ResearchPacketProbabilityMovementContextV2Config) -> Decimal:
    return _q(
        config.source_freshness_weight
        + config.event_velocity_weight
        + config.official_source_update_weight
        + config.contradiction_change_weight
        + config.liquidity_depth_weight
        + config.specialist_uncertainty_weight
        + config.resolution_horizon_weight,
    )


def _probability_delta(previous_probability: Decimal, current_probability: Decimal) -> Decimal:
    return _q(abs(current_probability - previous_probability))


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_text(name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{name} must not have outer whitespace")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _config_version(value: str) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVEMENT_CONTEXT_V2_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _hex_digest(name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _member(name: str, value: str, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} is not supported")


def _dec(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _q(value)


def _dec_nonnegative(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _dec_positive(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result <= ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _ratio(name: str, value: Decimal) -> Decimal:
    result = _dec_nonnegative(name, value)
    if result > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return result


def _count(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < COUNT_ZERO or result != result.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    return result


def _count_positive(name: str, value: Decimal) -> Decimal:
    result = _count(name, value)
    if result <= COUNT_ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} must be readonly")


def _q(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


__all__ = (
    "DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVEMENT_CONTEXT_V2_CONFIG_VERSION",
    "ResearchPacketProbabilityMovementContextV2Candidate",
    "ResearchPacketProbabilityMovementContextV2Config",
    "ResearchPacketProbabilityMovementContextV2Report",
    "ResearchPacketProbabilityMovementContextV2Row",
    "build_research_packet_probability_movement_context_v2",
    "derive_research_packet_probability_movement_context_v2_digest",
    "research_packet_probability_movement_context_v2_payload",
)
