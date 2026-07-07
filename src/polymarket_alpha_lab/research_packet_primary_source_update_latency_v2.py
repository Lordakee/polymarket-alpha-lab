"""Phase 1 primary-source update latency report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any, Iterable, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    require_team_category_pair,
    require_team_id,
)


DEFAULT_RESEARCH_PACKET_PRIMARY_SOURCE_UPDATE_LATENCY_V2_CONFIG_VERSION = (
    "research-packet-primary-source-update-latency-v2"
)

SOURCE_FAMILIES = ("official", "primary", "proxy")
SOURCE_FAMILY_ROLLUP_SEQUENCE = ("none", "official", "primary", "proxy")
URGENCIES = ("routine", "elevated", "critical")
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("empty", "clear", "watch", "blocked")
STALE_SOURCE_REASONS = (
    "no_primary_source_update",
    "source_update_before_movement_only",
    "collection_sla_miss",
    "missing_official_source",
)
ROW_REASON_CODES = (
    "primary_source_update_latency_clear",
    "primary_source_update_missing",
    "primary_source_update_before_movement_only",
    "primary_source_update_sla_miss",
    "primary_source_update_missing_official_source",
)
REPORT_REASON_CODES = (
    "primary_source_update_latency_empty",
    "primary_source_update_latency_clear",
    "primary_source_update_missing",
    "primary_source_update_before_movement_only",
    "primary_source_update_sla_miss",
    "primary_source_update_missing_official_source",
)
STALE_REASON_TO_ROW_REASON = {
    "no_primary_source_update": "primary_source_update_missing",
    "source_update_before_movement_only": (
        "primary_source_update_before_movement_only"
    ),
    "collection_sla_miss": "primary_source_update_sla_miss",
    "missing_official_source": "primary_source_update_missing_official_source",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_QUANTIZED = Decimal("0.000000")
ONE_QUANTIZED = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
URGENCY_RANK = {"critical": 0, "elevated": 1, "routine": 2}
SOURCE_FAMILY_RANK = {"official": 0, "primary": 1, "proxy": 2}


@dataclass(frozen=True)
class ResearchPacketPrimarySourceUpdateLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_PRIMARY_SOURCE_UPDATE_LATENCY_V2_CONFIG_VERSION
    )
    routine_sla_seconds: Decimal = Decimal("3600.000000")
    elevated_sla_seconds: Decimal = Decimal("1800.000000")
    critical_sla_seconds: Decimal = Decimal("600.000000")
    elevated_probability_delta: Decimal = Decimal("0.050000")
    critical_probability_delta: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_supported_config_version(self.config_version)
        for field_name in (
            "routine_sla_seconds",
            "elevated_sla_seconds",
            "critical_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "elevated_probability_delta",
            "critical_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.critical_probability_delta <= self.elevated_probability_delta:
            raise ValueError(
                "critical_probability_delta must exceed elevated_probability_delta",
            )
        require_paper_only_flags("latency config", self)
        reject_unsafe_surface_fields("latency config", self)


@dataclass(frozen=True)
class ResearchPacketMarketProbabilityMovement:
    movement_id: str
    market_id: str
    team_id: str
    category_id: str
    detected_at: datetime
    probability_before: Decimal
    probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("movement_id", self.movement_id)
        _require_public_string("market_id", self.market_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        object.__setattr__(
            self,
            "probability_before",
            _require_ratio_decimal("probability_before", self.probability_before),
        )
        object.__setattr__(
            self,
            "probability_after",
            _require_ratio_decimal("probability_after", self.probability_after),
        )
        if self.probability_before == self.probability_after:
            raise ValueError("probability movement must have a nonzero delta")
        require_paper_only_flags("probability movement", self)
        reject_unsafe_surface_fields("probability movement", self)


@dataclass(frozen=True)
class ResearchPacketPrimarySourceUpdate:
    update_id: str
    market_id: str
    source_id: str
    source_family: str
    collected_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("update_id", "market_id", "source_id"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_source_family("source_family", self.source_family)
        object.__setattr__(
            self,
            "collected_at",
            _as_utc("collected_at", self.collected_at),
        )
        require_paper_only_flags("primary source update", self)
        reject_unsafe_surface_fields("primary source update", self)


@dataclass(frozen=True)
class ResearchPacketPrimarySourceUpdateLatencyRow:
    movement_id: str
    market_id: str
    team_id: str
    category_id: str
    status: str
    urgency: str
    sla_tier: str
    detected_at: datetime
    probability_before: Decimal
    probability_after: Decimal
    probability_delta_abs: Decimal
    sla_seconds: Decimal
    collected_update_id: str | None
    collected_source_id: str | None
    collected_update_at: datetime | None
    collected_source_family: str
    collection_latency_seconds: Decimal | None
    official_source_present: bool
    stale_source_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("movement_id", self.movement_id)
        _require_public_string("market_id", self.market_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_row_status("status", self.status)
        _require_urgency("urgency", self.urgency)
        _require_urgency("sla_tier", self.sla_tier)
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        for field_name in (
            "probability_before",
            "probability_after",
            "probability_delta_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sla_seconds",
            _require_positive_seconds_decimal("sla_seconds", self.sla_seconds),
        )
        object.__setattr__(
            self,
            "collected_update_id",
            _normalize_optional_public_string(
                "collected_update_id",
                self.collected_update_id,
            ),
        )
        object.__setattr__(
            self,
            "collected_source_id",
            _normalize_optional_public_string(
                "collected_source_id",
                self.collected_source_id,
            ),
        )
        object.__setattr__(
            self,
            "collected_update_at",
            _as_optional_utc("collected_update_at", self.collected_update_at),
        )
        _require_rollup_source_family(
            "collected_source_family",
            self.collected_source_family,
        )
        object.__setattr__(
            self,
            "collection_latency_seconds",
            _normalize_optional_seconds_decimal(
                "collection_latency_seconds",
                self.collection_latency_seconds,
            ),
        )
        _require_bool("official_source_present", self.official_source_present)
        object.__setattr__(
            self,
            "stale_source_reasons",
            _normalize_stale_source_reasons(self.stale_source_reasons),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("latency row", self)
        reject_unsafe_surface_fields("latency row", self)
        _validate_latency_row(self)


@dataclass(frozen=True)
class ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup:
    source_family: str
    movement_count: Decimal
    stale_source_count: Decimal
    official_source_present_count: Decimal
    max_collection_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_rollup_source_family("source_family", self.source_family)
        for field_name in (
            "movement_count",
            "stale_source_count",
            "official_source_present_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_collection_latency_seconds",
            _require_nonnegative_seconds_decimal(
                "max_collection_latency_seconds",
                self.max_collection_latency_seconds,
            ),
        )
        require_paper_only_flags("source family rollup", self)
        reject_unsafe_surface_fields("source family rollup", self)
        _validate_source_family_rollup(self)


@dataclass(frozen=True)
class ResearchPacketPrimarySourceUpdateLatencyReasonRollup:
    stale_source_reason: str
    movement_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_stale_source_reason("stale_source_reason", self.stale_source_reason)
        object.__setattr__(
            self,
            "movement_count",
            _require_positive_count_decimal("movement_count", self.movement_count),
        )
        require_paper_only_flags("stale source reason rollup", self)
        reject_unsafe_surface_fields("stale source reason rollup", self)


@dataclass(frozen=True)
class ResearchPacketPrimarySourceUpdateLatencyReport:
    generated_at: datetime
    config_version: str
    status: str
    movement_count: Decimal
    update_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    routine_count: Decimal
    elevated_count: Decimal
    critical_count: Decimal
    official_source_present_count: Decimal
    missing_official_source_count: Decimal
    sla_miss_count: Decimal
    no_update_count: Decimal
    before_movement_only_count: Decimal
    max_collection_latency_seconds: Decimal
    average_collection_latency_seconds: Decimal
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...]
    source_family_rollups: tuple[
        ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup,
        ...,
    ]
    stale_source_reason_rollups: tuple[
        ResearchPacketPrimarySourceUpdateLatencyReasonRollup,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_supported_config_version(self.config_version)
        _require_report_status("status", self.status)
        for field_name in (
            "movement_count",
            "update_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "routine_count",
            "elevated_count",
            "critical_count",
            "official_source_present_count",
            "missing_official_source_count",
            "sla_miss_count",
            "no_update_count",
            "before_movement_only_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_collection_latency_seconds",
            "average_collection_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_latency_rows(self.rows))
        object.__setattr__(
            self,
            "source_family_rollups",
            _normalize_source_family_rollups(self.source_family_rollups),
        )
        object.__setattr__(
            self,
            "stale_source_reason_rollups",
            _normalize_reason_rollups(self.stale_source_reason_rollups),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        reject_unsafe_surface_fields("latency report", self)
        require_paper_only_flags("latency report", self)
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_primary_source_update_latency_v2_report_to_payload(self)


def build_research_packet_primary_source_update_latency_v2_report(
    movements: Iterable[ResearchPacketMarketProbabilityMovement],
    updates: Iterable[ResearchPacketPrimarySourceUpdate],
    *,
    config: ResearchPacketPrimarySourceUpdateLatencyConfig | None = None,
    generated_at: datetime,
) -> ResearchPacketPrimarySourceUpdateLatencyReport:
    if config is None:
        config = ResearchPacketPrimarySourceUpdateLatencyConfig()
    if type(config) is not ResearchPacketPrimarySourceUpdateLatencyConfig:
        raise ValueError(
            "config must be a ResearchPacketPrimarySourceUpdateLatencyConfig",
        )
    require_paper_only_flags("latency config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_movements = _normalize_movements(movements)
    normalized_updates = _normalize_updates(updates)
    _validate_input_times(normalized_movements, normalized_updates, generated_at_utc)

    rows = _sort_latency_rows(
        tuple(
            _latency_row(
                movement,
                updates=_updates_for_market(movement.market_id, normalized_updates),
                config=config,
            )
            for movement in normalized_movements
        ),
    )
    reason_codes = _report_reason_codes(rows)
    source_family_rollups = _source_family_rollups(rows)
    reason_rollups = _reason_rollups(rows)
    latency_values = tuple(
        row.collection_latency_seconds
        for row in rows
        if row.collection_latency_seconds is not None
    )

    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "movement_count": _count(len(rows)),
        "update_count": _count(len(normalized_updates)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "routine_count": _urgency_count(rows, "routine"),
        "elevated_count": _urgency_count(rows, "elevated"),
        "critical_count": _urgency_count(rows, "critical"),
        "official_source_present_count": _count(
            sum(1 for row in rows if row.official_source_present),
        ),
        "missing_official_source_count": _stale_reason_count(
            rows,
            "missing_official_source",
        ),
        "sla_miss_count": _stale_reason_count(rows, "collection_sla_miss"),
        "no_update_count": _stale_reason_count(rows, "no_primary_source_update"),
        "before_movement_only_count": _stale_reason_count(
            rows,
            "source_update_before_movement_only",
        ),
        "max_collection_latency_seconds": max(
            latency_values,
            default=ZERO_QUANTIZED,
        ),
        "average_collection_latency_seconds": _average_seconds(latency_values),
        "rows": rows,
        "source_family_rollups": source_family_rollups,
        "stale_source_reason_rollups": reason_rollups,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketPrimarySourceUpdateLatencyReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_packet_primary_source_update_latency_v2_report_to_payload(
    report: ResearchPacketPrimarySourceUpdateLatencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketPrimarySourceUpdateLatencyReport:
        raise ValueError(
            "report must be a ResearchPacketPrimarySourceUpdateLatencyReport",
        )
    reject_unsafe_surface_fields("latency report", report)
    require_paper_only_flags("latency report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("latency report payload must be a JSON object")
    return payload


def _latency_row(
    movement: ResearchPacketMarketProbabilityMovement,
    *,
    updates: tuple[ResearchPacketPrimarySourceUpdate, ...],
    config: ResearchPacketPrimarySourceUpdateLatencyConfig,
) -> ResearchPacketPrimarySourceUpdateLatencyRow:
    later_updates = tuple(
        update for update in updates if update.collected_at >= movement.detected_at
    )
    prior_updates = tuple(
        update for update in updates if update.collected_at < movement.detected_at
    )
    collected_update = later_updates[0] if later_updates else None
    official_source_present = any(
        update.source_family == "official" for update in later_updates
    )
    probability_delta_abs = _probability_delta_abs(movement)
    urgency = _urgency(probability_delta_abs, config)
    sla_seconds = _sla_seconds(urgency, config)
    latency_seconds = (
        None
        if collected_update is None
        else _duration_seconds(movement.detected_at, collected_update.collected_at)
    )
    stale_source_reasons = _row_stale_source_reasons(
        has_collected_update=collected_update is not None,
        has_prior_update=bool(prior_updates),
        official_source_present=official_source_present,
        collection_latency_seconds=latency_seconds,
        sla_seconds=sla_seconds,
    )
    reason_codes = _row_reason_codes(stale_source_reasons)
    return ResearchPacketPrimarySourceUpdateLatencyRow(
        movement_id=movement.movement_id,
        market_id=movement.market_id,
        team_id=movement.team_id,
        category_id=movement.category_id,
        status=_row_status(urgency, stale_source_reasons),
        urgency=urgency,
        sla_tier=urgency,
        detected_at=movement.detected_at,
        probability_before=movement.probability_before,
        probability_after=movement.probability_after,
        probability_delta_abs=probability_delta_abs,
        sla_seconds=sla_seconds,
        collected_update_id=None if collected_update is None else collected_update.update_id,
        collected_source_id=None if collected_update is None else collected_update.source_id,
        collected_update_at=None if collected_update is None else collected_update.collected_at,
        collected_source_family=(
            "none" if collected_update is None else collected_update.source_family
        ),
        collection_latency_seconds=latency_seconds,
        official_source_present=official_source_present,
        stale_source_reasons=stale_source_reasons,
        reason_codes=reason_codes,
    )


def _row_stale_source_reasons(
    *,
    has_collected_update: bool,
    has_prior_update: bool,
    official_source_present: bool,
    collection_latency_seconds: Decimal | None,
    sla_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not has_collected_update:
        reasons.append("no_primary_source_update")
    if not has_collected_update and has_prior_update:
        reasons.append("source_update_before_movement_only")
    if (
        collection_latency_seconds is not None
        and collection_latency_seconds > sla_seconds
    ):
        reasons.append("collection_sla_miss")
    if not official_source_present:
        reasons.append("missing_official_source")
    return _normalize_stale_source_reasons(tuple(reasons))


def _row_reason_codes(stale_source_reasons: tuple[str, ...]) -> tuple[str, ...]:
    if not stale_source_reasons:
        return ("primary_source_update_latency_clear",)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(STALE_REASON_TO_ROW_REASON[reason] for reason in stale_source_reasons),
        allowed=ROW_REASON_CODES,
        allow_empty=False,
    )


def _row_status(urgency: str, stale_source_reasons: tuple[str, ...]) -> str:
    if "no_primary_source_update" in stale_source_reasons:
        return "blocked"
    if urgency == "critical" and "collection_sla_miss" in stale_source_reasons:
        return "blocked"
    if stale_source_reasons:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("primary_source_update_latency_empty",)
    issue_codes = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODES
        if reason_code not in (
            "primary_source_update_latency_empty",
            "primary_source_update_latency_clear",
        )
        and any(reason_code in row.reason_codes for row in rows)
    )
    if issue_codes:
        return issue_codes
    return ("primary_source_update_latency_clear",)


def _source_family_rollups(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
) -> tuple[ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup, ...]:
    rollups: list[ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup] = []
    for source_family in SOURCE_FAMILY_ROLLUP_SEQUENCE:
        family_rows = tuple(
            row for row in rows if row.collected_source_family == source_family
        )
        if not family_rows:
            continue
        latency_values = tuple(
            row.collection_latency_seconds
            for row in family_rows
            if row.collection_latency_seconds is not None
        )
        rollups.append(
            ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup(
                source_family=source_family,
                movement_count=_count(len(family_rows)),
                stale_source_count=_count(
                    sum(1 for row in family_rows if row.stale_source_reasons),
                ),
                official_source_present_count=_count(
                    sum(1 for row in family_rows if row.official_source_present),
                ),
                max_collection_latency_seconds=max(
                    latency_values,
                    default=ZERO_QUANTIZED,
                ),
            ),
        )
    return tuple(rollups)


def _reason_rollups(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
) -> tuple[ResearchPacketPrimarySourceUpdateLatencyReasonRollup, ...]:
    rollups: list[ResearchPacketPrimarySourceUpdateLatencyReasonRollup] = []
    for stale_source_reason in STALE_SOURCE_REASONS:
        movement_count = sum(
            1 for row in rows if stale_source_reason in row.stale_source_reasons
        )
        if movement_count:
            rollups.append(
                ResearchPacketPrimarySourceUpdateLatencyReasonRollup(
                    stale_source_reason=stale_source_reason,
                    movement_count=_count(movement_count),
                ),
            )
    return tuple(rollups)


def _normalize_movements(
    movements: Iterable[ResearchPacketMarketProbabilityMovement],
) -> tuple[ResearchPacketMarketProbabilityMovement, ...]:
    if isinstance(movements, str | bytes):
        raise ValueError("movements must be an iterable")
    try:
        normalized = tuple(movements)
    except TypeError as exc:
        raise ValueError("movements must be an iterable") from exc
    seen: set[str] = set()
    for movement in normalized:
        if type(movement) is not ResearchPacketMarketProbabilityMovement:
            raise ValueError("movements must contain exact movement values")
        require_paper_only_flags("probability movement", movement)
        if movement.movement_id in seen:
            raise ValueError("movement_id values must be unique")
        seen.add(movement.movement_id)
    return tuple(
        sorted(
            normalized,
            key=lambda movement: (
                movement.team_id,
                movement.category_id,
                movement.detected_at,
                movement.market_id,
                movement.movement_id,
            ),
        ),
    )


def _normalize_updates(
    updates: Iterable[ResearchPacketPrimarySourceUpdate],
) -> tuple[ResearchPacketPrimarySourceUpdate, ...]:
    if isinstance(updates, str | bytes):
        raise ValueError("updates must be an iterable")
    try:
        normalized = tuple(updates)
    except TypeError as exc:
        raise ValueError("updates must be an iterable") from exc
    seen: set[str] = set()
    for update in normalized:
        if type(update) is not ResearchPacketPrimarySourceUpdate:
            raise ValueError("updates must contain exact update values")
        require_paper_only_flags("primary source update", update)
        if update.update_id in seen:
            raise ValueError("update_id values must be unique")
        seen.add(update.update_id)
    return tuple(
        sorted(
            normalized,
            key=lambda update: (
                update.market_id,
                update.collected_at,
                SOURCE_FAMILY_RANK[update.source_family],
                update.update_id,
            ),
        ),
    )


def _updates_for_market(
    market_id: str,
    updates: tuple[ResearchPacketPrimarySourceUpdate, ...],
) -> tuple[ResearchPacketPrimarySourceUpdate, ...]:
    return tuple(update for update in updates if update.market_id == market_id)


def _validate_input_times(
    movements: tuple[ResearchPacketMarketProbabilityMovement, ...],
    updates: tuple[ResearchPacketPrimarySourceUpdate, ...],
    generated_at: datetime,
) -> None:
    for movement in movements:
        if movement.detected_at > generated_at:
            raise ValueError("detected_at must be <= generated_at")
    for update in updates:
        if update.collected_at > generated_at:
            raise ValueError("collected_at must be <= generated_at")


def _sort_latency_rows(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
) -> tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...]:
    return tuple(sorted(rows, key=_latency_row_rank))


def _latency_row_rank(
    row: ResearchPacketPrimarySourceUpdateLatencyRow,
) -> tuple[int, int, Decimal, str, datetime, str]:
    return (
        STATUS_RANK[row.status],
        URGENCY_RANK[row.urgency],
        row.collection_latency_seconds
        if row.collection_latency_seconds is not None
        else ZERO_QUANTIZED,
        row.market_id,
        row.detected_at,
        row.movement_id,
    )


def _normalize_latency_rows(
    rows: Iterable[ResearchPacketPrimarySourceUpdateLatencyRow],
) -> tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketPrimarySourceUpdateLatencyRow:
            raise ValueError("rows must contain exact latency rows")
        require_paper_only_flags("latency row", row)
        if row.movement_id in seen:
            raise ValueError("rows movement_id values must be unique")
        seen.add(row.movement_id)
    expected = _sort_latency_rows(normalized)
    if normalized != expected:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_source_family_rollups(
    rollups: Iterable[ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup],
) -> tuple[ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup, ...]:
    if isinstance(rollups, str | bytes):
        raise ValueError("source_family_rollups must be an iterable")
    try:
        normalized = tuple(rollups)
    except TypeError as exc:
        raise ValueError("source_family_rollups must be an iterable") from exc
    seen: set[str] = set()
    for rollup in normalized:
        if type(rollup) is not ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup:
            raise ValueError(
                "source_family_rollups must contain exact source family rollups",
            )
        require_paper_only_flags("source family rollup", rollup)
        if rollup.source_family in seen:
            raise ValueError("source_family_rollups values must be unique")
        seen.add(rollup.source_family)
    expected = tuple(
        sorted(
            normalized,
            key=lambda rollup: SOURCE_FAMILY_ROLLUP_SEQUENCE.index(
                rollup.source_family,
            ),
        ),
    )
    if normalized != expected:
        raise ValueError("source_family_rollups must use deterministic sorting")
    return normalized


def _normalize_reason_rollups(
    rollups: Iterable[ResearchPacketPrimarySourceUpdateLatencyReasonRollup],
) -> tuple[ResearchPacketPrimarySourceUpdateLatencyReasonRollup, ...]:
    if isinstance(rollups, str | bytes):
        raise ValueError("stale_source_reason_rollups must be an iterable")
    try:
        normalized = tuple(rollups)
    except TypeError as exc:
        raise ValueError("stale_source_reason_rollups must be an iterable") from exc
    seen: set[str] = set()
    for rollup in normalized:
        if type(rollup) is not ResearchPacketPrimarySourceUpdateLatencyReasonRollup:
            raise ValueError(
                "stale_source_reason_rollups must contain exact reason rollups",
            )
        require_paper_only_flags("stale source reason rollup", rollup)
        if rollup.stale_source_reason in seen:
            raise ValueError("stale_source_reason_rollups values must be unique")
        seen.add(rollup.stale_source_reason)
    expected = tuple(
        sorted(
            normalized,
            key=lambda rollup: STALE_SOURCE_REASONS.index(rollup.stale_source_reason),
        ),
    )
    if normalized != expected:
        raise ValueError("stale_source_reason_rollups must use deterministic sorting")
    return normalized


def _validate_latency_row(
    row: ResearchPacketPrimarySourceUpdateLatencyRow,
) -> None:
    if row.sla_tier != row.urgency:
        raise ValueError("sla_tier must match urgency")
    expected_delta = _quantize_ratio(
        (row.probability_after - row.probability_before).copy_abs(),
    )
    if row.probability_delta_abs != expected_delta:
        raise ValueError("probability_delta_abs must match probability movement")
    if row.collected_update_id is None:
        if (
            row.collected_source_id is not None
            or row.collected_update_at is not None
            or row.collection_latency_seconds is not None
            or row.collected_source_family != "none"
        ):
            raise ValueError("collected update fields must be absent together")
    else:
        if (
            row.collected_source_id is None
            or row.collected_update_at is None
            or row.collection_latency_seconds is None
            or row.collected_source_family == "none"
        ):
            raise ValueError("collected update fields must be present together")
        if row.collected_update_at < row.detected_at:
            raise ValueError("collected_update_at must be >= detected_at")
        expected_latency = _duration_seconds(row.detected_at, row.collected_update_at)
        if row.collection_latency_seconds != expected_latency:
            raise ValueError("collection_latency_seconds must match timestamps")
    if row.official_source_present and "missing_official_source" in row.stale_source_reasons:
        raise ValueError("official rows cannot include missing official reason")
    if row.status != _row_status(row.urgency, row.stale_source_reasons):
        raise ValueError("status must match stale_source_reasons")
    if row.reason_codes != _row_reason_codes(row.stale_source_reasons):
        raise ValueError("reason_codes must match stale_source_reasons")


def _validate_source_family_rollup(
    rollup: ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup,
) -> None:
    if rollup.stale_source_count > rollup.movement_count:
        raise ValueError("stale_source_count must not exceed movement_count")
    if rollup.official_source_present_count > rollup.movement_count:
        raise ValueError(
            "official_source_present_count must not exceed movement_count",
        )


def _validate_report(
    report: ResearchPacketPrimarySourceUpdateLatencyReport,
) -> None:
    if report.movement_count != _count(len(report.rows)):
        raise ValueError("movement_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    for urgency in URGENCIES:
        field_name = f"{urgency}_count"
        if getattr(report, field_name) != _urgency_count(report.rows, urgency):
            raise ValueError(f"{field_name} must match rows")
    if report.official_source_present_count != _count(
        sum(1 for row in report.rows if row.official_source_present),
    ):
        raise ValueError("official_source_present_count must match rows")
    expected_reason_counts = {
        "missing_official_source_count": "missing_official_source",
        "sla_miss_count": "collection_sla_miss",
        "no_update_count": "no_primary_source_update",
        "before_movement_only_count": "source_update_before_movement_only",
    }
    for field_name, stale_source_reason in expected_reason_counts.items():
        if getattr(report, field_name) != _stale_reason_count(
            report.rows,
            stale_source_reason,
        ):
            raise ValueError(f"{field_name} must match rows")
    latency_values = tuple(
        row.collection_latency_seconds
        for row in report.rows
        if row.collection_latency_seconds is not None
    )
    if report.max_collection_latency_seconds != max(
        latency_values,
        default=ZERO_QUANTIZED,
    ):
        raise ValueError("max_collection_latency_seconds must match rows")
    if report.average_collection_latency_seconds != _average_seconds(latency_values):
        raise ValueError("average_collection_latency_seconds must match rows")
    if report.source_family_rollups != _source_family_rollups(report.rows):
        raise ValueError("source_family_rollups must match rows")
    if report.stale_source_reason_rollups != _reason_rollups(report.rows):
        raise ValueError("stale_source_reason_rollups must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _urgency_count(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
    urgency: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.urgency == urgency))


def _stale_reason_count(
    rows: tuple[ResearchPacketPrimarySourceUpdateLatencyRow, ...],
    stale_source_reason: str,
) -> Decimal:
    return _count(
        sum(1 for row in rows if stale_source_reason in row.stale_source_reasons),
    )


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_QUANTIZED
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_QUANTIZED) / Decimal(len(values))).quantize(QUANTUM)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO_COUNT:
        raise ValueError("duration seconds must be nonnegative")
    return seconds.quantize(QUANTUM)


def _probability_delta_abs(
    movement: ResearchPacketMarketProbabilityMovement,
) -> Decimal:
    return _quantize_ratio(
        (movement.probability_after - movement.probability_before).copy_abs(),
    )


def _urgency(
    probability_delta_abs: Decimal,
    config: ResearchPacketPrimarySourceUpdateLatencyConfig,
) -> str:
    if probability_delta_abs >= config.critical_probability_delta:
        return "critical"
    if probability_delta_abs >= config.elevated_probability_delta:
        return "elevated"
    return "routine"


def _sla_seconds(
    urgency: str,
    config: ResearchPacketPrimarySourceUpdateLatencyConfig,
) -> Decimal:
    if urgency == "critical":
        return config.critical_sla_seconds
    if urgency == "elevated":
        return config.elevated_sla_seconds
    if urgency == "routine":
        return config.routine_sla_seconds
    raise ValueError("urgency must be known")


def _require_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_seconds_decimal(field_name, value)
    if decimal_value <= ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_optional_seconds_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_seconds_decimal(field_name, value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if decimal_value != quantized:
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return quantized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = _quantize_ratio(decimal_value)
    if quantized < ZERO_QUANTIZED or quantized > ONE_QUANTIZED:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_stale_source_reasons(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("stale_source_reasons must be an iterable")
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError("stale_source_reasons must be an iterable") from exc
    for reason in reasons:
        _require_stale_source_reason("stale_source_reason", reason)
    if len(set(reasons)) != len(reasons):
        raise ValueError("stale_source_reasons must be unique")
    expected = tuple(reason for reason in STALE_SOURCE_REASONS if reason in reasons)
    if reasons != expected:
        raise ValueError("stale_source_reasons must use deterministic sorting")
    return reasons


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(reason_code for reason_code in allowed if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return reason_codes


def _require_source_family(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_FAMILIES:
        raise ValueError(f"{field_name} must be official, primary, or proxy")


def _require_rollup_source_family(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_FAMILY_ROLLUP_SEQUENCE:
        raise ValueError(f"{field_name} must be a known source family")


def _require_stale_source_reason(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STALE_SOURCE_REASONS:
        raise ValueError(f"{field_name} must be a known stale source reason")


def _require_row_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be empty, clear, watch, or blocked")


def _require_urgency(field_name: str, value: object) -> None:
    if type(value) is not str or value not in URGENCIES:
        raise ValueError(f"{field_name} must be routine, elevated, or critical")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_supported_config_version(value: object) -> None:
    _require_canonical_string("config_version", value)
    if value != DEFAULT_RESEARCH_PACKET_PRIMARY_SOURCE_UPDATE_LATENCY_V2_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _report_values_without_digest(
    report: ResearchPacketPrimarySourceUpdateLatencyReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_PACKET_PRIMARY_SOURCE_UPDATE_LATENCY_V2_CONFIG_VERSION",
    "ResearchPacketMarketProbabilityMovement",
    "ResearchPacketPrimarySourceUpdate",
    "ResearchPacketPrimarySourceUpdateLatencyConfig",
    "ResearchPacketPrimarySourceUpdateLatencyReasonRollup",
    "ResearchPacketPrimarySourceUpdateLatencyReport",
    "ResearchPacketPrimarySourceUpdateLatencyRow",
    "ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup",
    "build_research_packet_primary_source_update_latency_v2_report",
    "research_packet_primary_source_update_latency_v2_report_to_payload",
)
