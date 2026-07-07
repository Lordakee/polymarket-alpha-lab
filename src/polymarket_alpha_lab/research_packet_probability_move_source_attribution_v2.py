"""Pure in-memory Phase 1 probability move source attribution report."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_ATTRIBUTION_V2_CONFIG_VERSION = (
    "research-packet-probability-move-source-attribution-v2"
)

Q = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")
COUNT_ONE = Decimal("1")

ATTRIBUTION_BANDS = frozenset(("high", "medium", "low"))
PRIMARY_ATTRIBUTIONS = frozenset(
    (
        "source_update",
        "official_source_event",
        "contradiction_change",
        "liquidity_movement",
        "event_velocity",
        "specialist_uncertainty",
    ),
)
RESEARCH_ACTIONS = frozenset(
    (
        "explain_source_move",
        "monitor_source_move",
        "defer_source_move",
    ),
)
REASON_PRIORITY = {
    "source_update_primary": 0,
    "source_update_high": 1,
    "source_update_watch": 2,
    "source_update_low": 3,
    "official_source_event_primary": 4,
    "official_source_event_high": 5,
    "official_source_event_normal": 6,
    "official_source_event_none": 7,
    "contradiction_change_primary": 8,
    "contradiction_change_elevated": 9,
    "contradiction_change_normal": 10,
    "contradiction_change_low": 11,
    "liquidity_movement_primary": 12,
    "liquidity_movement_high": 13,
    "liquidity_movement_watch": 14,
    "liquidity_movement_low": 15,
    "event_velocity_primary": 16,
    "event_velocity_high": 17,
    "event_velocity_normal": 18,
    "event_velocity_low": 19,
    "specialist_uncertainty_primary": 20,
    "specialist_uncertainty_elevated": 21,
    "specialist_uncertainty_normal": 22,
    "specialist_uncertainty_low": 23,
    "attribution_high": 24,
    "attribution_medium": 25,
    "attribution_low": 26,
}
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "high_attribution_count",
        "medium_attribution_count",
        "low_attribution_count",
        "average_probability_move",
        "max_probability_move",
        "average_total_attribution_score",
        "max_total_attribution_score",
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
        "source_id",
        "previous_probability",
        "current_probability",
        "probability_move",
        "source_update_score",
        "official_source_event_score",
        "contradiction_change_score",
        "liquidity_movement_score",
        "event_velocity_score",
        "specialist_uncertainty_score",
        "source_update_contribution",
        "official_source_event_contribution",
        "contradiction_change_contribution",
        "liquidity_movement_contribution",
        "event_velocity_contribution",
        "specialist_uncertainty_contribution",
        "total_attribution_score",
        "primary_attribution",
        "attribution_band",
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
class ResearchPacketProbabilityMoveSourceAttributionV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_ATTRIBUTION_V2_CONFIG_VERSION
    )
    high_attribution_threshold: Decimal = Decimal("0.700000")
    medium_attribution_threshold: Decimal = Decimal("0.400000")
    source_update_weight: Decimal = Decimal("0.200000")
    official_source_event_weight: Decimal = Decimal("0.200000")
    contradiction_change_weight: Decimal = Decimal("0.200000")
    liquidity_movement_weight: Decimal = Decimal("0.150000")
    event_velocity_weight: Decimal = Decimal("0.150000")
    specialist_uncertainty_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _config_version(self.config_version)
        for name in ("high_attribution_threshold", "medium_attribution_threshold"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if self.medium_attribution_threshold > self.high_attribution_threshold:
            raise ValueError(
                "medium_attribution_threshold must not exceed "
                "high_attribution_threshold",
            )
        for name in (
            "source_update_weight",
            "official_source_event_weight",
            "contradiction_change_weight",
            "liquidity_movement_weight",
            "event_velocity_weight",
            "specialist_uncertainty_weight",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if _weight_total(self) != ONE:
            raise ValueError("attribution weights must total 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMoveSourceAttributionV2Candidate:
    packet_id: str
    event_title: str
    source_id: str
    previous_probability: Decimal
    current_probability: Decimal
    source_update_score: Decimal
    official_source_event_score: Decimal
    contradiction_change_score: Decimal
    liquidity_movement_score: Decimal
    event_velocity_score: Decimal
    specialist_uncertainty_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("packet_id", "event_title", "source_id"):
            _safe_text(name, getattr(self, name))
        for name in ("previous_probability", "current_probability"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        for name in (
            "source_update_score",
            "official_source_event_score",
            "contradiction_change_score",
            "liquidity_movement_score",
            "event_velocity_score",
            "specialist_uncertainty_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMoveSourceAttributionV2Row:
    rank: Decimal
    packet_id: str
    event_title: str
    source_id: str
    previous_probability: Decimal
    current_probability: Decimal
    probability_move: Decimal
    source_update_score: Decimal
    official_source_event_score: Decimal
    contradiction_change_score: Decimal
    liquidity_movement_score: Decimal
    event_velocity_score: Decimal
    specialist_uncertainty_score: Decimal
    source_update_contribution: Decimal
    official_source_event_contribution: Decimal
    contradiction_change_contribution: Decimal
    liquidity_movement_contribution: Decimal
    event_velocity_contribution: Decimal
    specialist_uncertainty_contribution: Decimal
    total_attribution_score: Decimal
    primary_attribution: str
    attribution_band: str
    research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _count_positive("rank", self.rank))
        for name in ("packet_id", "event_title", "source_id"):
            _safe_text(name, getattr(self, name))
        for name in ("previous_probability", "current_probability"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "probability_move",
            _ratio("probability_move", self.probability_move),
        )
        for name in (
            "source_update_score",
            "official_source_event_score",
            "contradiction_change_score",
            "liquidity_movement_score",
            "event_velocity_score",
            "specialist_uncertainty_score",
            "source_update_contribution",
            "official_source_event_contribution",
            "contradiction_change_contribution",
            "liquidity_movement_contribution",
            "event_velocity_contribution",
            "specialist_uncertainty_contribution",
            "total_attribution_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _member("primary_attribution", self.primary_attribution, PRIMARY_ATTRIBUTIONS)
        _member("attribution_band", self.attribution_band, ATTRIBUTION_BANDS)
        _member("research_action", self.research_action, RESEARCH_ACTIONS)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMoveSourceAttributionV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    high_attribution_count: Decimal
    medium_attribution_count: Decimal
    low_attribution_count: Decimal
    average_probability_move: Decimal
    max_probability_move: Decimal
    average_total_attribution_score: Decimal
    max_total_attribution_score: Decimal
    rows: tuple[ResearchPacketProbabilityMoveSourceAttributionV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        for name in (
            "candidate_count",
            "high_attribution_count",
            "medium_attribution_count",
            "low_attribution_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in (
            "average_probability_move",
            "max_probability_move",
            "average_total_attribution_score",
            "max_total_attribution_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_digest(self)
        _report_matches(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_probability_move_source_attribution_v2_payload(self)


def build_research_packet_probability_move_source_attribution_v2(
    candidates: Iterable[ResearchPacketProbabilityMoveSourceAttributionV2Candidate],
    *,
    config: ResearchPacketProbabilityMoveSourceAttributionV2Config,
    generated_at: datetime,
) -> ResearchPacketProbabilityMoveSourceAttributionV2Report:
    if type(config) is not ResearchPacketProbabilityMoveSourceAttributionV2Config:
        raise ValueError("config must be a probability move source attribution config")
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    source_rows = _normalize_candidates(candidates)
    built_rows = _ranked_rows(tuple(_row(candidate, config) for candidate in source_rows))
    report_values = {
        "generated_at": stamp,
        "config_version": config.config_version,
        "candidate_count": Decimal(len(built_rows)),
        "high_attribution_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.attribution_band == "high"),
        ),
        "medium_attribution_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.attribution_band == "medium"),
        ),
        "low_attribution_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.attribution_band == "low"),
        ),
        "average_probability_move": _average(
            tuple(row.probability_move for row in built_rows),
        ),
        "max_probability_move": max(
            (row.probability_move for row in built_rows),
            default=ZERO,
        ),
        "average_total_attribution_score": _average(
            tuple(row.total_attribution_score for row in built_rows),
        ),
        "max_total_attribution_score": max(
            (row.total_attribution_score for row in built_rows),
            default=ZERO,
        ),
        "rows": built_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _derive_digest_from_public_payload(_payload(report_values))
    return ResearchPacketProbabilityMoveSourceAttributionV2Report(
        **report_values,
        derived_validation_digest=digest,
    )


def research_packet_probability_move_source_attribution_v2_payload(
    report: ResearchPacketProbabilityMoveSourceAttributionV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketProbabilityMoveSourceAttributionV2Report:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability move source attribution report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    return payload


def derive_research_packet_probability_move_source_attribution_v2_digest(
    report: ResearchPacketProbabilityMoveSourceAttributionV2Report | dict[str, Any],
) -> str:
    if type(report) is ResearchPacketProbabilityMoveSourceAttributionV2Report:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability move source attribution report")
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
    candidate: ResearchPacketProbabilityMoveSourceAttributionV2Candidate,
    config: ResearchPacketProbabilityMoveSourceAttributionV2Config,
) -> ResearchPacketProbabilityMoveSourceAttributionV2Row:
    contributions = {
        "source_update": _q(candidate.source_update_score * config.source_update_weight),
        "official_source_event": _q(
            candidate.official_source_event_score * config.official_source_event_weight,
        ),
        "contradiction_change": _q(
            candidate.contradiction_change_score * config.contradiction_change_weight,
        ),
        "liquidity_movement": _q(
            candidate.liquidity_movement_score * config.liquidity_movement_weight,
        ),
        "event_velocity": _q(candidate.event_velocity_score * config.event_velocity_weight),
        "specialist_uncertainty": _q(
            candidate.specialist_uncertainty_score
            * config.specialist_uncertainty_weight,
        ),
    }
    primary = _primary_attribution(contributions)
    score = _q(sum(contributions.values(), ZERO))
    band = _attribution_band(score, config)
    return ResearchPacketProbabilityMoveSourceAttributionV2Row(
        rank=COUNT_ONE,
        packet_id=candidate.packet_id,
        event_title=candidate.event_title,
        source_id=candidate.source_id,
        previous_probability=candidate.previous_probability,
        current_probability=candidate.current_probability,
        probability_move=_probability_move(
            candidate.previous_probability,
            candidate.current_probability,
        ),
        source_update_score=candidate.source_update_score,
        official_source_event_score=candidate.official_source_event_score,
        contradiction_change_score=candidate.contradiction_change_score,
        liquidity_movement_score=candidate.liquidity_movement_score,
        event_velocity_score=candidate.event_velocity_score,
        specialist_uncertainty_score=candidate.specialist_uncertainty_score,
        source_update_contribution=contributions["source_update"],
        official_source_event_contribution=contributions["official_source_event"],
        contradiction_change_contribution=contributions["contradiction_change"],
        liquidity_movement_contribution=contributions["liquidity_movement"],
        event_velocity_contribution=contributions["event_velocity"],
        specialist_uncertainty_contribution=contributions["specialist_uncertainty"],
        total_attribution_score=score,
        primary_attribution=primary,
        attribution_band=band,
        research_action=_research_action_for_band(band),
        reason_codes=_dedupe(
            (
                _primary_or_unit_reason(
                    "source_update",
                    candidate.source_update_score,
                    primary,
                ),
                _primary_or_official_reason(candidate.official_source_event_score, primary),
                _primary_or_contradiction_reason(
                    candidate.contradiction_change_score,
                    primary,
                ),
                _primary_or_liquidity_reason(candidate.liquidity_movement_score, primary),
                _primary_or_event_velocity_reason(candidate.event_velocity_score, primary),
                _primary_or_specialist_reason(
                    candidate.specialist_uncertainty_score,
                    primary,
                ),
                f"attribution_{band}",
            ),
        ),
    )


def _ranked_rows(
    rows: tuple[ResearchPacketProbabilityMoveSourceAttributionV2Row, ...],
) -> tuple[ResearchPacketProbabilityMoveSourceAttributionV2Row, ...]:
    ranked = []
    for index, row in enumerate(sorted(rows, key=_row_key), start=1):
        ranked.append(
            ResearchPacketProbabilityMoveSourceAttributionV2Row(
                rank=Decimal(index),
                packet_id=row.packet_id,
                event_title=row.event_title,
                source_id=row.source_id,
                previous_probability=row.previous_probability,
                current_probability=row.current_probability,
                probability_move=row.probability_move,
                source_update_score=row.source_update_score,
                official_source_event_score=row.official_source_event_score,
                contradiction_change_score=row.contradiction_change_score,
                liquidity_movement_score=row.liquidity_movement_score,
                event_velocity_score=row.event_velocity_score,
                specialist_uncertainty_score=row.specialist_uncertainty_score,
                source_update_contribution=row.source_update_contribution,
                official_source_event_contribution=row.official_source_event_contribution,
                contradiction_change_contribution=row.contradiction_change_contribution,
                liquidity_movement_contribution=row.liquidity_movement_contribution,
                event_velocity_contribution=row.event_velocity_contribution,
                specialist_uncertainty_contribution=(
                    row.specialist_uncertainty_contribution
                ),
                total_attribution_score=row.total_attribution_score,
                primary_attribution=row.primary_attribution,
                attribution_band=row.attribution_band,
                research_action=row.research_action,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_key(row: ResearchPacketProbabilityMoveSourceAttributionV2Row) -> tuple[object, ...]:
    return (
        -row.total_attribution_score,
        -row.probability_move,
        row.packet_id,
        row.source_id,
    )


def _primary_attribution(contributions: dict[str, Decimal]) -> str:
    priority = {
        "source_update": 0,
        "official_source_event": 1,
        "contradiction_change": 2,
        "liquidity_movement": 3,
        "event_velocity": 4,
        "specialist_uncertainty": 5,
    }
    return min(
        contributions,
        key=lambda name: (-contributions[name], priority[name]),
    )


def _probability_move(previous: Decimal, current: Decimal) -> Decimal:
    return _q(abs(current - previous))


def _attribution_band(
    score: Decimal,
    config: ResearchPacketProbabilityMoveSourceAttributionV2Config,
) -> str:
    if score >= config.high_attribution_threshold:
        return "high"
    if score >= config.medium_attribution_threshold:
        return "medium"
    return "low"


def _research_action_for_band(band: str) -> str:
    if band == "high":
        return "explain_source_move"
    if band == "medium":
        return "monitor_source_move"
    return "defer_source_move"


def _primary_or_unit_reason(prefix: str, score: Decimal, primary: str) -> str:
    if primary == prefix:
        return f"{prefix}_primary"
    if score >= Decimal("0.750000"):
        return f"{prefix}_high"
    if score >= Decimal("0.250000"):
        return f"{prefix}_watch"
    return f"{prefix}_low"


def _primary_or_official_reason(score: Decimal, primary: str) -> str:
    if primary == "official_source_event":
        return "official_source_event_primary"
    if score >= Decimal("0.750000"):
        return "official_source_event_high"
    if score > ZERO:
        return "official_source_event_normal"
    return "official_source_event_none"


def _primary_or_contradiction_reason(score: Decimal, primary: str) -> str:
    if primary == "contradiction_change":
        return "contradiction_change_primary"
    if score >= Decimal("0.650000"):
        return "contradiction_change_elevated"
    if score >= Decimal("0.250000"):
        return "contradiction_change_normal"
    return "contradiction_change_low"


def _primary_or_liquidity_reason(score: Decimal, primary: str) -> str:
    if primary == "liquidity_movement":
        return "liquidity_movement_primary"
    if score >= Decimal("0.750000"):
        return "liquidity_movement_high"
    if score >= Decimal("0.250000"):
        return "liquidity_movement_watch"
    return "liquidity_movement_low"


def _primary_or_event_velocity_reason(score: Decimal, primary: str) -> str:
    if primary == "event_velocity":
        return "event_velocity_primary"
    if score >= Decimal("0.750000"):
        return "event_velocity_high"
    if score >= Decimal("0.250000"):
        return "event_velocity_normal"
    return "event_velocity_low"


def _primary_or_specialist_reason(score: Decimal, primary: str) -> str:
    if primary == "specialist_uncertainty":
        return "specialist_uncertainty_primary"
    if score >= Decimal("0.750000"):
        return "specialist_uncertainty_elevated"
    if score >= Decimal("0.250000"):
        return "specialist_uncertainty_normal"
    return "specialist_uncertainty_low"


def _normalize_candidates(
    candidates: Iterable[ResearchPacketProbabilityMoveSourceAttributionV2Candidate],
) -> tuple[ResearchPacketProbabilityMoveSourceAttributionV2Candidate, ...]:
    rows = tuple(candidates)
    seen_keys: set[tuple[str, str]] = set()
    for candidate in rows:
        if type(candidate) is not ResearchPacketProbabilityMoveSourceAttributionV2Candidate:
            raise ValueError("candidate rows must be probability move attribution candidates")
        _require_hard_flags("candidate", candidate)
        key = (candidate.packet_id, candidate.source_id)
        if key in seen_keys:
            raise ValueError("packet_id and source_id rows must be unique")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    rows: tuple[ResearchPacketProbabilityMoveSourceAttributionV2Row, ...],
) -> tuple[ResearchPacketProbabilityMoveSourceAttributionV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPacketProbabilityMoveSourceAttributionV2Row:
            raise ValueError("rows must be probability move source attribution rows")
        _require_hard_flags("row", row)
    return rows


def _validate_row(row: ResearchPacketProbabilityMoveSourceAttributionV2Row) -> None:
    expected_move = _probability_move(row.previous_probability, row.current_probability)
    if row.probability_move != expected_move:
        raise ValueError("probability_move must match probability values")
    expected_total = _q(
        row.source_update_contribution
        + row.official_source_event_contribution
        + row.contradiction_change_contribution
        + row.liquidity_movement_contribution
        + row.event_velocity_contribution
        + row.specialist_uncertainty_contribution,
    )
    if row.total_attribution_score != expected_total:
        raise ValueError("total_attribution_score must match component contributions")


def _report_matches(report: ResearchPacketProbabilityMoveSourceAttributionV2Report) -> None:
    rows = report.rows
    if report.candidate_count != Decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    high_count = Decimal(sum(COUNT_ONE for row in rows if row.attribution_band == "high"))
    medium_count = Decimal(
        sum(COUNT_ONE for row in rows if row.attribution_band == "medium"),
    )
    low_count = Decimal(sum(COUNT_ONE for row in rows if row.attribution_band == "low"))
    if report.high_attribution_count != high_count:
        raise ValueError("high_attribution_count must match rows")
    if report.medium_attribution_count != medium_count:
        raise ValueError("medium_attribution_count must match rows")
    if report.low_attribution_count != low_count:
        raise ValueError("low_attribution_count must match rows")
    if report.average_probability_move != _average(tuple(row.probability_move for row in rows)):
        raise ValueError("average_probability_move must match rows")
    if report.max_probability_move != max(
        (row.probability_move for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_probability_move must match rows")
    if report.average_total_attribution_score != _average(
        tuple(row.total_attribution_score for row in rows),
    ):
        raise ValueError("average_total_attribution_score must match rows")
    if report.max_total_attribution_score != max(
        (row.total_attribution_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_total_attribution_score must match rows")


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _q(sum(values, ZERO) / Decimal(len(values)))


def _weight_total(
    config: ResearchPacketProbabilityMoveSourceAttributionV2Config,
) -> Decimal:
    return _q(
        config.source_update_weight
        + config.official_source_event_weight
        + config.contradiction_change_weight
        + config.liquidity_movement_weight
        + config.event_velocity_weight
        + config.specialist_uncertainty_weight,
    )


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _hex_digest("derived_validation_digest", digest)
    if digest != _derive_digest_from_public_payload(payload):
        raise ValueError("derived_validation_digest must match")


def _validate_digest(report: ResearchPacketProbabilityMoveSourceAttributionV2Report) -> None:
    if report.derived_validation_digest != _derive_digest_from_public_payload(
        _payload(report),
    ):
        raise ValueError("derived_validation_digest must match")


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
        if field_name in _count_field_names() and value == value.to_integral_value():
            return format(value.quantize(COUNT_ONE), "f")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload(getattr(value, field.name), field_name=field.name)
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload(item) for item in value]
    if type(value) is list:
        return [_payload(item) for item in value]
    if type(value) is dict:
        return {
            key: _payload(item, field_name=key if type(key) is str else None)
            for key, item in value.items()
        }
    return value


def _json_ready(value: Any) -> Any:
    return _payload(value)


def _count_field_names() -> frozenset[str]:
    return frozenset(
        (
            "rank",
            "candidate_count",
            "high_attribution_count",
            "medium_attribution_count",
            "low_attribution_count",
        ),
    )


def _reject_unsafe_public_payload(value: object, path: str = "") -> None:
    if type(value) is str:
        if _has_unsafe_text(value):
            raise ValueError("unsafe public payload value")
        return
    if type(value) is bool or value is None:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_text(key):
                raise ValueError("unsafe public payload key")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"[{index}]"
            _reject_unsafe_public_payload(item, item_path)
        return
    raise ValueError(f"{path or 'payload'} is not JSON serializable")


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool = True,
) -> None:
    for key in payload:
        if key not in REPORT_PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")
    required_report_fields = set(REPORT_PAYLOAD_FIELDS)
    if not digest_required:
        required_report_fields.remove("derived_validation_digest")
    missing_report_fields = required_report_fields - payload.keys()
    if missing_report_fields:
        raise ValueError("payload missing required field")
    if type(payload.get("rows")) is not list:
        raise ValueError("payload rows must be a list")
    for row in payload["rows"]:
        if type(row) is not dict:
            raise ValueError("payload rows must contain objects")
        for key in row:
            if key not in ROW_PAYLOAD_FIELDS:
                raise ValueError("payload row field is not supported")
        if ROW_PAYLOAD_FIELDS - row.keys():
            raise ValueError("payload row missing required field")


def _config_version(value: object) -> None:
    _safe_text("config_version", value)
    if value != DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_ATTRIBUTION_V2_CONFIG_VERSION:
        raise ValueError("config_version must be supported")


def _reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized = []
    for item in value:
        _safe_text("reason_codes", item)
        if item not in REASON_PRIORITY:
            raise ValueError("reason_codes contains unsupported code")
        if item not in seen:
            seen.add(item)
            normalized.append(item)
    return tuple(sorted(normalized, key=lambda code: REASON_PRIORITY[code]))


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _member(field_name: str, value: object, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _count(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(COUNT_ONE)


def _count_positive(field_name: str, value: object) -> Decimal:
    decimal_value = _count(field_name, value)
    if decimal_value <= COUNT_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _safe_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe text")
    return value


def _has_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_ATTRIBUTION_V2_CONFIG_VERSION",
    "ResearchPacketProbabilityMoveSourceAttributionV2Candidate",
    "ResearchPacketProbabilityMoveSourceAttributionV2Config",
    "ResearchPacketProbabilityMoveSourceAttributionV2Report",
    "ResearchPacketProbabilityMoveSourceAttributionV2Row",
    "build_research_packet_probability_move_source_attribution_v2",
    "derive_research_packet_probability_move_source_attribution_v2_digest",
    "research_packet_probability_move_source_attribution_v2_payload",
)
