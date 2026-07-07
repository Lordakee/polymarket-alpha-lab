"""Pure Phase 1 probability move source-gap detector."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_GAP_V2_CONFIG_VERSION = (
    "research-packet-probability-move-source-gap-v2"
)

Q = Decimal("0.000001")
COUNT_Q = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")

REPORT_STATUSES = ("pass", "watch", "blocked")
MOVE_BANDS = ("small", "medium", "large")
MOVE_DIRECTIONS = ("down", "flat", "up")
SOURCE_RECENCY_STATUSES = ("fresh", "watch", "stale", "missing")
CONTRADICTION_STATUSES = ("none", "elevated", "severe")
LIQUIDITY_CONTEXTS = ("thin", "normal", "deep")

ROW_REASON_CODES = (
    "move_large",
    "move_medium",
    "move_small",
    "source_count_missing",
    "source_count_low",
    "source_count_sufficient",
    "official_source_missing",
    "official_source_present",
    "source_recency_missing",
    "source_recency_stale",
    "source_recency_watch",
    "source_recency_fresh",
    "contradiction_severe",
    "contradiction_elevated",
    "contradiction_none",
    "liquidity_thin",
    "liquidity_normal",
    "liquidity_deep",
)
ROW_REASON_SET = frozenset(ROW_REASON_CODES)

PASS_REPORT_REASON = "probability_move_source_gap_v2_passed"
WATCH_REPORT_REASON = "probability_move_source_gap_v2_watch"
BLOCKED_REPORT_REASON = "probability_move_source_gap_v2_blocked"
REPORT_REASON_BY_ROW_REASON = {
    "move_large": "move_large_present",
    "move_medium": "move_medium_present",
    "source_count_missing": "source_count_missing_present",
    "source_count_low": "source_count_low_present",
    "official_source_missing": "official_source_missing_present",
    "source_recency_missing": "source_recency_missing_present",
    "source_recency_stale": "source_recency_stale_present",
    "source_recency_watch": "source_recency_watch_present",
    "contradiction_elevated": "contradiction_elevated_present",
    "contradiction_severe": "contradiction_severe_present",
    "liquidity_thin": "liquidity_thin_present",
}
REPORT_REASON_CODES = (
    BLOCKED_REPORT_REASON,
    WATCH_REPORT_REASON,
    PASS_REPORT_REASON,
    "move_large_present",
    "move_medium_present",
    "source_count_missing_present",
    "source_count_low_present",
    "official_source_missing_present",
    "source_recency_missing_present",
    "source_recency_stale_present",
    "source_recency_watch_present",
    "contradiction_elevated_present",
    "contradiction_severe_present",
    "liquidity_thin_present",
)
REPORT_REASON_SET = frozenset(REPORT_REASON_CODES)

REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_candidate_count",
        "watch_candidate_count",
        "blocked_candidate_count",
        "unsupported_move_count",
        "unsupported_move_ratio",
        "large_move_count",
        "insufficient_source_count",
        "official_source_missing_count",
        "source_recency_gap_count",
        "severe_contradiction_count",
        "thin_liquidity_count",
        "max_move_magnitude",
        "max_contradiction_severity",
        "min_liquidity_depth_usd",
        "required_source_count",
        "medium_move_threshold",
        "large_move_threshold",
        "fresh_source_max_age_seconds",
        "stale_source_age_seconds",
        "elevated_contradiction_threshold",
        "severe_contradiction_threshold",
        "thin_liquidity_depth_usd",
        "deep_liquidity_depth_usd",
        "report_status",
        "reason_codes",
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
        "market_id",
        "event_title",
        "previous_probability",
        "current_probability",
        "move_magnitude",
        "move_direction",
        "move_band",
        "source_count",
        "required_source_count",
        "source_gap_count",
        "official_source_count",
        "official_source_present",
        "latest_source_age_seconds",
        "source_recency_status",
        "contradiction_severity",
        "contradiction_status",
        "liquidity_depth_usd",
        "liquidity_context",
        "gap_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
COUNT_FIELD_NAMES = frozenset(
    (
        "rank",
        "candidate_count",
        "pass_candidate_count",
        "watch_candidate_count",
        "blocked_candidate_count",
        "unsupported_move_count",
        "large_move_count",
        "insufficient_source_count",
        "official_source_missing_count",
        "source_recency_gap_count",
        "severe_contradiction_count",
        "thin_liquidity_count",
        "source_count",
        "required_source_count",
        "source_gap_count",
        "official_source_count",
    ),
)
STATUS_WEIGHT = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("li", "ve"),
        _join("au", "th"),
        _join("wal", "let"),
        _join("or", "der"),
        _join("net", "work"),
        _join("data", "base"),
        _join("per", "sist"),
        _join("sign", "ing"),
        _join("muta", "tion"),
        _join("b", "uy"),
        _join("se", "ll"),
        _join("tra", "de"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketProbabilityMoveSourceGapV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_GAP_V2_CONFIG_VERSION
    )
    medium_move_threshold: Decimal = Decimal("0.050000")
    large_move_threshold: Decimal = Decimal("0.100000")
    required_source_count: Decimal = Decimal("2")
    fresh_source_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_source_age_seconds: Decimal = Decimal("7200.000000")
    elevated_contradiction_threshold: Decimal = Decimal("0.250000")
    severe_contradiction_threshold: Decimal = Decimal("0.750000")
    thin_liquidity_depth_usd: Decimal = Decimal("100.000000")
    deep_liquidity_depth_usd: Decimal = Decimal("1000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketProbabilityMoveSourceGapV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _config_version(self.config_version)
        for name in ("medium_move_threshold", "large_move_threshold"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if self.medium_move_threshold > self.large_move_threshold:
            raise ValueError(
                "medium_move_threshold must not exceed large_move_threshold",
            )
        object.__setattr__(
            self,
            "required_source_count",
            _count_positive("required_source_count", self.required_source_count),
        )
        for name in ("fresh_source_max_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(self, name, _dec_positive(name, getattr(self, name)))
        if self.fresh_source_max_age_seconds > self.stale_source_age_seconds:
            raise ValueError(
                "fresh_source_max_age_seconds must not exceed stale_source_age_seconds",
            )
        for name in (
            "elevated_contradiction_threshold",
            "severe_contradiction_threshold",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if self.elevated_contradiction_threshold > self.severe_contradiction_threshold:
            raise ValueError(
                "elevated_contradiction_threshold must not exceed "
                "severe_contradiction_threshold",
            )
        for name in ("thin_liquidity_depth_usd", "deep_liquidity_depth_usd"):
            object.__setattr__(self, name, _dec_positive(name, getattr(self, name)))
        if self.thin_liquidity_depth_usd > self.deep_liquidity_depth_usd:
            raise ValueError(
                "thin_liquidity_depth_usd must not exceed deep_liquidity_depth_usd",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMoveSourceGapV2Candidate:
    packet_id: str
    market_id: str
    event_title: str
    previous_probability: Decimal
    current_probability: Decimal
    source_count: Decimal
    official_source_count: Decimal
    latest_source_age_seconds: Decimal | None
    contradiction_severity: Decimal
    liquidity_depth_usd: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketProbabilityMoveSourceGapV2Candidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        for name in ("packet_id", "market_id", "event_title"):
            _safe_text(name, getattr(self, name))
        for name in ("previous_probability", "current_probability"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        for name in ("source_count", "official_source_count"):
            object.__setattr__(self, name, _count_nonnegative(name, getattr(self, name)))
        if self.official_source_count > self.source_count:
            raise ValueError("official_source_count must not exceed source_count")
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _dec_optional_nonnegative(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        if self.source_count == COUNT_ZERO and self.latest_source_age_seconds is not None:
            raise ValueError("latest_source_age_seconds must be absent without sources")
        object.__setattr__(
            self,
            "contradiction_severity",
            _ratio("contradiction_severity", self.contradiction_severity),
        )
        object.__setattr__(
            self,
            "liquidity_depth_usd",
            _dec_nonnegative("liquidity_depth_usd", self.liquidity_depth_usd),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMoveSourceGapV2Row:
    rank: Decimal
    packet_id: str
    market_id: str
    event_title: str
    previous_probability: Decimal
    current_probability: Decimal
    move_magnitude: Decimal
    move_direction: str
    move_band: str
    source_count: Decimal
    required_source_count: Decimal
    source_gap_count: Decimal
    official_source_count: Decimal
    official_source_present: bool
    latest_source_age_seconds: Decimal | None
    source_recency_status: str
    contradiction_severity: Decimal
    contradiction_status: str
    liquidity_depth_usd: Decimal
    liquidity_context: str
    gap_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketProbabilityMoveSourceGapV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _count_positive("rank", self.rank))
        for name in ("packet_id", "market_id", "event_title"):
            _safe_text(name, getattr(self, name))
        for name in ("previous_probability", "current_probability", "move_magnitude"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _member("move_direction", self.move_direction, MOVE_DIRECTIONS)
        _member("move_band", self.move_band, MOVE_BANDS)
        for name in ("source_count", "required_source_count", "source_gap_count"):
            object.__setattr__(self, name, _count_nonnegative(name, getattr(self, name)))
        if self.required_source_count <= COUNT_ZERO:
            raise ValueError("required_source_count must be positive")
        object.__setattr__(
            self,
            "official_source_count",
            _count_nonnegative("official_source_count", self.official_source_count),
        )
        if type(self.official_source_present) is not bool:
            raise ValueError("official_source_present must be a bool")
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _dec_optional_nonnegative(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        _member(
            "source_recency_status",
            self.source_recency_status,
            SOURCE_RECENCY_STATUSES,
        )
        object.__setattr__(
            self,
            "contradiction_severity",
            _ratio("contradiction_severity", self.contradiction_severity),
        )
        _member(
            "contradiction_status",
            self.contradiction_status,
            CONTRADICTION_STATUSES,
        )
        object.__setattr__(
            self,
            "liquidity_depth_usd",
            _dec_nonnegative("liquidity_depth_usd", self.liquidity_depth_usd),
        )
        _member("liquidity_context", self.liquidity_context, LIQUIDITY_CONTEXTS)
        _member("gap_status", self.gap_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketProbabilityMoveSourceGapV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    unsupported_move_count: Decimal
    unsupported_move_ratio: Decimal
    large_move_count: Decimal
    insufficient_source_count: Decimal
    official_source_missing_count: Decimal
    source_recency_gap_count: Decimal
    severe_contradiction_count: Decimal
    thin_liquidity_count: Decimal
    max_move_magnitude: Decimal
    max_contradiction_severity: Decimal
    min_liquidity_depth_usd: Decimal
    required_source_count: Decimal
    medium_move_threshold: Decimal
    large_move_threshold: Decimal
    fresh_source_max_age_seconds: Decimal
    stale_source_age_seconds: Decimal
    elevated_contradiction_threshold: Decimal
    severe_contradiction_threshold: Decimal
    thin_liquidity_depth_usd: Decimal
    deep_liquidity_depth_usd: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketProbabilityMoveSourceGapV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketProbabilityMoveSourceGapV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        for name in (
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
            "unsupported_move_count",
            "large_move_count",
            "insufficient_source_count",
            "official_source_missing_count",
            "source_recency_gap_count",
            "severe_contradiction_count",
            "thin_liquidity_count",
            "required_source_count",
        ):
            object.__setattr__(self, name, _count_nonnegative(name, getattr(self, name)))
        if self.required_source_count <= COUNT_ZERO:
            raise ValueError("required_source_count must be positive")
        for name in (
            "unsupported_move_ratio",
            "max_move_magnitude",
            "max_contradiction_severity",
            "medium_move_threshold",
            "large_move_threshold",
            "elevated_contradiction_threshold",
            "severe_contradiction_threshold",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        for name in (
            "min_liquidity_depth_usd",
            "fresh_source_max_age_seconds",
            "stale_source_age_seconds",
            "thin_liquidity_depth_usd",
            "deep_liquidity_depth_usd",
        ):
            object.__setattr__(self, name, _dec_nonnegative(name, getattr(self, name)))
        _member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_digest(self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_probability_move_source_gap_v2_payload(self)


def build_research_packet_probability_move_source_gap_v2(
    candidates: Iterable[ResearchPacketProbabilityMoveSourceGapV2Candidate],
    *,
    config: ResearchPacketProbabilityMoveSourceGapV2Config,
    generated_at: datetime,
) -> ResearchPacketProbabilityMoveSourceGapV2Report:
    if type(config) is not ResearchPacketProbabilityMoveSourceGapV2Config:
        raise ValueError("config must be a probability move source gap config")
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    source_rows = _normalize_candidates(candidates)
    rows = _ranked_rows(tuple(_row(candidate, config) for candidate in source_rows))
    count = _count_from_int(len(rows))
    unsupported_count = _count_from_int(sum(1 for row in rows if row.gap_status != "pass"))
    report_values = {
        "generated_at": stamp,
        "config_version": config.config_version,
        "candidate_count": count,
        "pass_candidate_count": _status_count(rows, "pass"),
        "watch_candidate_count": _status_count(rows, "watch"),
        "blocked_candidate_count": _status_count(rows, "blocked"),
        "unsupported_move_count": unsupported_count,
        "unsupported_move_ratio": _ratio_decimal(unsupported_count, count),
        "large_move_count": _count_from_int(
            sum(1 for row in rows if row.move_band == "large"),
        ),
        "insufficient_source_count": _count_from_int(
            sum(1 for row in rows if row.source_gap_count > COUNT_ZERO),
        ),
        "official_source_missing_count": _count_from_int(
            sum(1 for row in rows if not row.official_source_present),
        ),
        "source_recency_gap_count": _count_from_int(
            sum(1 for row in rows if row.source_recency_status != "fresh"),
        ),
        "severe_contradiction_count": _count_from_int(
            sum(1 for row in rows if row.contradiction_status == "severe"),
        ),
        "thin_liquidity_count": _count_from_int(
            sum(1 for row in rows if row.liquidity_context == "thin"),
        ),
        "max_move_magnitude": max((row.move_magnitude for row in rows), default=ZERO),
        "max_contradiction_severity": max(
            (row.contradiction_severity for row in rows),
            default=ZERO,
        ),
        "min_liquidity_depth_usd": min(
            (row.liquidity_depth_usd for row in rows),
            default=ZERO,
        ),
        "required_source_count": config.required_source_count,
        "medium_move_threshold": config.medium_move_threshold,
        "large_move_threshold": config.large_move_threshold,
        "fresh_source_max_age_seconds": config.fresh_source_max_age_seconds,
        "stale_source_age_seconds": config.stale_source_age_seconds,
        "elevated_contradiction_threshold": config.elevated_contradiction_threshold,
        "severe_contradiction_threshold": config.severe_contradiction_threshold,
        "thin_liquidity_depth_usd": config.thin_liquidity_depth_usd,
        "deep_liquidity_depth_usd": config.deep_liquidity_depth_usd,
        "report_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _derive_digest_from_public_payload(_payload(report_values))
    return ResearchPacketProbabilityMoveSourceGapV2Report(
        **report_values,
        derived_validation_digest=digest,
    )


def research_packet_probability_move_source_gap_v2_payload(
    report: ResearchPacketProbabilityMoveSourceGapV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketProbabilityMoveSourceGapV2Report:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability move source gap report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    return payload


def derive_research_packet_probability_move_source_gap_v2_digest(
    report: ResearchPacketProbabilityMoveSourceGapV2Report | dict[str, Any],
) -> str:
    if type(report) is ResearchPacketProbabilityMoveSourceGapV2Report:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability move source gap report")
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
    candidate: ResearchPacketProbabilityMoveSourceGapV2Candidate,
    config: ResearchPacketProbabilityMoveSourceGapV2Config,
) -> ResearchPacketProbabilityMoveSourceGapV2Row:
    move_magnitude = _q(abs(candidate.current_probability - candidate.previous_probability))
    move_band = _move_band(move_magnitude, config)
    source_gap_count = max(config.required_source_count - candidate.source_count, COUNT_ZERO)
    official_present = candidate.official_source_count > COUNT_ZERO
    source_recency_status = _source_recency_status(
        candidate.latest_source_age_seconds,
        config,
    )
    contradiction_status = _contradiction_status(candidate.contradiction_severity, config)
    liquidity_context = _liquidity_context(candidate.liquidity_depth_usd, config)
    reason_codes = _row_reason_codes(
        move_band=move_band,
        source_count=candidate.source_count,
        source_gap_count=source_gap_count,
        official_present=official_present,
        source_recency_status=source_recency_status,
        contradiction_status=contradiction_status,
        liquidity_context=liquidity_context,
    )
    return ResearchPacketProbabilityMoveSourceGapV2Row(
        rank=Decimal("1"),
        packet_id=candidate.packet_id,
        market_id=candidate.market_id,
        event_title=candidate.event_title,
        previous_probability=candidate.previous_probability,
        current_probability=candidate.current_probability,
        move_magnitude=move_magnitude,
        move_direction=_move_direction(
            candidate.previous_probability,
            candidate.current_probability,
        ),
        move_band=move_band,
        source_count=candidate.source_count,
        required_source_count=config.required_source_count,
        source_gap_count=source_gap_count,
        official_source_count=candidate.official_source_count,
        official_source_present=official_present,
        latest_source_age_seconds=candidate.latest_source_age_seconds,
        source_recency_status=source_recency_status,
        contradiction_severity=candidate.contradiction_severity,
        contradiction_status=contradiction_status,
        liquidity_depth_usd=candidate.liquidity_depth_usd,
        liquidity_context=liquidity_context,
        gap_status=_row_status(
            move_band=move_band,
            source_count=candidate.source_count,
            source_gap_count=source_gap_count,
            official_present=official_present,
            source_recency_status=source_recency_status,
            contradiction_status=contradiction_status,
            liquidity_context=liquidity_context,
        ),
        reason_codes=reason_codes,
    )


def _ranked_rows(
    rows: tuple[ResearchPacketProbabilityMoveSourceGapV2Row, ...],
) -> tuple[ResearchPacketProbabilityMoveSourceGapV2Row, ...]:
    ranked: list[ResearchPacketProbabilityMoveSourceGapV2Row] = []
    for index, row in enumerate(sorted(rows, key=_row_key), start=1):
        ranked.append(
            ResearchPacketProbabilityMoveSourceGapV2Row(
                rank=Decimal(index),
                packet_id=row.packet_id,
                market_id=row.market_id,
                event_title=row.event_title,
                previous_probability=row.previous_probability,
                current_probability=row.current_probability,
                move_magnitude=row.move_magnitude,
                move_direction=row.move_direction,
                move_band=row.move_band,
                source_count=row.source_count,
                required_source_count=row.required_source_count,
                source_gap_count=row.source_gap_count,
                official_source_count=row.official_source_count,
                official_source_present=row.official_source_present,
                latest_source_age_seconds=row.latest_source_age_seconds,
                source_recency_status=row.source_recency_status,
                contradiction_severity=row.contradiction_severity,
                contradiction_status=row.contradiction_status,
                liquidity_depth_usd=row.liquidity_depth_usd,
                liquidity_context=row.liquidity_context,
                gap_status=row.gap_status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_key(row: ResearchPacketProbabilityMoveSourceGapV2Row) -> tuple[Decimal, ...] | tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    str,
]:
    return (
        STATUS_WEIGHT[row.gap_status],
        -row.move_magnitude,
        -row.source_gap_count,
        -row.contradiction_severity,
        row.liquidity_depth_usd,
        row.packet_id,
        row.market_id,
    )


def _move_direction(previous: Decimal, current: Decimal) -> str:
    if current > previous:
        return "up"
    if current < previous:
        return "down"
    return "flat"


def _move_band(
    move_magnitude: Decimal,
    config: ResearchPacketProbabilityMoveSourceGapV2Config,
) -> str:
    if move_magnitude >= config.large_move_threshold:
        return "large"
    if move_magnitude >= config.medium_move_threshold:
        return "medium"
    return "small"


def _source_recency_status(
    latest_source_age_seconds: Decimal | None,
    config: ResearchPacketProbabilityMoveSourceGapV2Config,
) -> str:
    if latest_source_age_seconds is None:
        return "missing"
    if latest_source_age_seconds <= config.fresh_source_max_age_seconds:
        return "fresh"
    if latest_source_age_seconds <= config.stale_source_age_seconds:
        return "watch"
    return "stale"


def _contradiction_status(
    contradiction_severity: Decimal,
    config: ResearchPacketProbabilityMoveSourceGapV2Config,
) -> str:
    if contradiction_severity >= config.severe_contradiction_threshold:
        return "severe"
    if contradiction_severity >= config.elevated_contradiction_threshold:
        return "elevated"
    return "none"


def _liquidity_context(
    liquidity_depth_usd: Decimal,
    config: ResearchPacketProbabilityMoveSourceGapV2Config,
) -> str:
    if liquidity_depth_usd <= config.thin_liquidity_depth_usd:
        return "thin"
    if liquidity_depth_usd >= config.deep_liquidity_depth_usd:
        return "deep"
    return "normal"


def _row_reason_codes(
    *,
    move_band: str,
    source_count: Decimal,
    source_gap_count: Decimal,
    official_present: bool,
    source_recency_status: str,
    contradiction_status: str,
    liquidity_context: str,
) -> tuple[str, ...]:
    if source_count == COUNT_ZERO:
        source_reason = "source_count_missing"
    elif source_gap_count > COUNT_ZERO:
        source_reason = "source_count_low"
    else:
        source_reason = "source_count_sufficient"
    return (
        f"move_{move_band}",
        source_reason,
        "official_source_present" if official_present else "official_source_missing",
        f"source_recency_{source_recency_status}",
        f"contradiction_{contradiction_status}",
        f"liquidity_{liquidity_context}",
    )


def _row_status(
    *,
    move_band: str,
    source_count: Decimal,
    source_gap_count: Decimal,
    official_present: bool,
    source_recency_status: str,
    contradiction_status: str,
    liquidity_context: str,
) -> str:
    if source_count == COUNT_ZERO or contradiction_status == "severe":
        return "blocked"
    if move_band == "large" and (
        source_gap_count > COUNT_ZERO
        or not official_present
        or source_recency_status in ("missing", "stale")
        or contradiction_status == "elevated"
        or liquidity_context == "thin"
    ):
        return "blocked"
    if move_band == "medium" and source_gap_count > COUNT_ZERO and not official_present:
        return "blocked"
    if (
        source_gap_count > COUNT_ZERO
        or not official_present
        or source_recency_status != "fresh"
        or contradiction_status == "elevated"
        or (move_band != "small" and liquidity_context == "thin")
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchPacketProbabilityMoveSourceGapV2Row, ...]) -> str:
    if any(row.gap_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketProbabilityMoveSourceGapV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "blocked":
        codes = [BLOCKED_REPORT_REASON]
    elif status == "watch":
        codes = [WATCH_REPORT_REASON]
    else:
        codes = [PASS_REPORT_REASON]
    present = frozenset(reason for row in rows for reason in row.reason_codes)
    present_report_reasons = frozenset(
        report_reason
        for row_reason, report_reason in REPORT_REASON_BY_ROW_REASON.items()
        if row_reason in present
    )
    for report_reason in REPORT_REASON_CODES:
        if report_reason in present_report_reasons:
            codes.append(report_reason)
    return tuple(codes)


def _status_count(
    rows: tuple[ResearchPacketProbabilityMoveSourceGapV2Row, ...],
    status: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if row.gap_status == status))


def _normalize_candidates(
    candidates: Iterable[ResearchPacketProbabilityMoveSourceGapV2Candidate],
) -> tuple[ResearchPacketProbabilityMoveSourceGapV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidate rows must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidate rows must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketProbabilityMoveSourceGapV2Candidate:
            raise ValueError("candidate rows must contain source gap candidates")
        _require_hard_flags("candidate", row)
        key = (row.packet_id, row.market_id)
        if key in seen_keys:
            raise ValueError("candidate rows must be unique by packet_id and market_id")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketProbabilityMoveSourceGapV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    expected_ranks = tuple(Decimal(index) for index in range(1, len(normalized) + 1))
    actual_ranks: list[Decimal] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketProbabilityMoveSourceGapV2Row:
            raise ValueError("rows must contain source gap row values")
        _require_hard_flags("row", row)
        key = (row.packet_id, row.market_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by packet_id and market_id")
        seen_keys.add(key)
        actual_ranks.append(row.rank)
    if tuple(actual_ranks) != expected_ranks:
        raise ValueError("row ranks must be sequential")
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _validate_row(row: ResearchPacketProbabilityMoveSourceGapV2Row) -> None:
    if row.move_magnitude != _q(abs(row.current_probability - row.previous_probability)):
        raise ValueError("move_magnitude must match probability values")
    expected_direction = _move_direction(row.previous_probability, row.current_probability)
    if row.move_direction != expected_direction:
        raise ValueError("move_direction must match probability values")
    if row.official_source_count > row.source_count:
        raise ValueError("official_source_count must not exceed source_count")
    if row.official_source_present != (row.official_source_count > COUNT_ZERO):
        raise ValueError("official_source_present must match official_source_count")
    expected_gap = max(row.required_source_count - row.source_count, COUNT_ZERO)
    if row.source_gap_count != expected_gap:
        raise ValueError("source_gap_count must match source counts")
    if row.source_count == COUNT_ZERO and row.latest_source_age_seconds is not None:
        raise ValueError("latest_source_age_seconds must be absent without sources")
    expected_status = _row_status(
        move_band=row.move_band,
        source_count=row.source_count,
        source_gap_count=row.source_gap_count,
        official_present=row.official_source_present,
        source_recency_status=row.source_recency_status,
        contradiction_status=row.contradiction_status,
        liquidity_context=row.liquidity_context,
    )
    if row.gap_status != expected_status:
        raise ValueError("gap_status must match source gap factors")


def _validate_report(report: ResearchPacketProbabilityMoveSourceGapV2Report) -> None:
    rows = report.rows
    count = _count_from_int(len(rows))
    if report.candidate_count != count:
        raise ValueError("candidate_count must match rows")
    for field_name, status in (
        ("pass_candidate_count", "pass"),
        ("watch_candidate_count", "watch"),
        ("blocked_candidate_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    unsupported_count = _count_from_int(sum(1 for row in rows if row.gap_status != "pass"))
    if report.unsupported_move_count != unsupported_count:
        raise ValueError("unsupported_move_count must match rows")
    if report.unsupported_move_ratio != _ratio_decimal(unsupported_count, count):
        raise ValueError("unsupported_move_ratio must match rows")
    if report.large_move_count != _count_from_int(
        sum(1 for row in rows if row.move_band == "large"),
    ):
        raise ValueError("large_move_count must match rows")
    if report.insufficient_source_count != _count_from_int(
        sum(1 for row in rows if row.source_gap_count > COUNT_ZERO),
    ):
        raise ValueError("insufficient_source_count must match rows")
    if report.official_source_missing_count != _count_from_int(
        sum(1 for row in rows if not row.official_source_present),
    ):
        raise ValueError("official_source_missing_count must match rows")
    if report.source_recency_gap_count != _count_from_int(
        sum(1 for row in rows if row.source_recency_status != "fresh"),
    ):
        raise ValueError("source_recency_gap_count must match rows")
    if report.severe_contradiction_count != _count_from_int(
        sum(1 for row in rows if row.contradiction_status == "severe"),
    ):
        raise ValueError("severe_contradiction_count must match rows")
    if report.thin_liquidity_count != _count_from_int(
        sum(1 for row in rows if row.liquidity_context == "thin"),
    ):
        raise ValueError("thin_liquidity_count must match rows")
    if report.max_move_magnitude != max((row.move_magnitude for row in rows), default=ZERO):
        raise ValueError("max_move_magnitude must match rows")
    if report.max_contradiction_severity != max(
        (row.contradiction_severity for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_severity must match rows")
    if report.min_liquidity_depth_usd != min(
        (row.liquidity_depth_usd for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_liquidity_depth_usd must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_digest(report: ResearchPacketProbabilityMoveSourceGapV2Report) -> None:
    if report.derived_validation_digest != _derive_digest_from_public_payload(
        _payload(report),
    ):
        raise ValueError("derived_validation_digest must match report payload")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _hex_digest("derived_validation_digest", digest)
    if digest != _derive_digest_from_public_payload(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _derive_digest_from_public_payload(payload: dict[str, Any]) -> str:
    core = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload(value: Any, *, field_name: str | None = None) -> Any:
    if type(value) is Decimal:
        if field_name in COUNT_FIELD_NAMES and value == value.to_integral_value():
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
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_payload(value))
    if type(value) is float:
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


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool = True,
) -> None:
    for key in payload:
        if key not in REPORT_PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")
    required = (
        REPORT_PAYLOAD_FIELDS
        if digest_required
        else REPORT_PAYLOAD_FIELDS - {"derived_validation_digest"}
    )
    if not required.issubset(payload.keys()):
        raise ValueError("payload field is missing")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        for key in row:
            if key not in ROW_PAYLOAD_FIELDS:
                raise ValueError("payload field is not supported")
        if not ROW_PAYLOAD_FIELDS.issubset(row.keys()):
            raise ValueError("payload field is missing")
        _require_hard_flags("row payload", _DictFlags(row))


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


def _safe_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be text")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be canonical nonblank text")
    if _unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe text")


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _config_version(value: object) -> None:
    _safe_text("config_version", value)
    if value != DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_GAP_V2_CONFIG_VERSION:
        raise ValueError("config_version must be the supported value")


def _member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain text")
        if reason_code not in ROW_REASON_SET and reason_code not in REPORT_REASON_SET:
            raise ValueError(f"{field_name} must be supported")
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must be supported")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed if reason_code in seen)
    if value != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _q(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


def _ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _q(_require_decimal(field_name, value))
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _dec_nonnegative(field_name: str, value: object) -> Decimal:
    decimal_value = _q(_require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _dec_optional_nonnegative(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _dec_nonnegative(field_name, value)


def _dec_positive(field_name: str, value: object) -> Decimal:
    decimal_value = _dec_nonnegative(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _count_nonnegative(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    normalized = decimal_value.quantize(COUNT_Q)
    if normalized < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count_positive(field_name: str, value: object) -> Decimal:
    normalized = _count_nonnegative(field_name, value)
    if normalized <= COUNT_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_from_int(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_Q)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_ZERO:
        return ZERO
    return _ratio("ratio", numerator / denominator)


def _hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc


__all__ = (
    "DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_GAP_V2_CONFIG_VERSION",
    "ResearchPacketProbabilityMoveSourceGapV2Candidate",
    "ResearchPacketProbabilityMoveSourceGapV2Config",
    "ResearchPacketProbabilityMoveSourceGapV2Report",
    "ResearchPacketProbabilityMoveSourceGapV2Row",
    "build_research_packet_probability_move_source_gap_v2",
    "derive_research_packet_probability_move_source_gap_v2_digest",
    "research_packet_probability_move_source_gap_v2_payload",
)
