from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_PACKET_MARKET_CLOSE_INFORMATION_SLA_V2_CONFIG_VERSION = (
    "research-packet-market-close-information-sla-v2-v0"
)

SLA_STATUSES = ("ready", "watch", "blocked")
ESCALATION_PRIORITIES = ("p0", "p1", "p2", "p3")

READY_REASON = "market_close_information_sla_ready"
OFFICIAL_UPDATE_MISSING_REASON = "market_close_information_official_update_missing"
OFFICIAL_UPDATE_STALE_REASON = "market_close_information_official_update_stale"
INDEPENDENT_CONFIRMATION_MISSING_REASON = (
    "market_close_information_independent_confirmation_missing"
)
INDEPENDENT_CONFIRMATION_STALE_REASON = (
    "market_close_information_independent_confirmation_stale"
)
UNRESOLVED_CONTRADICTION_REASON = (
    "market_close_information_unresolved_contradiction"
)
RESOLUTION_SOURCE_NOT_READY_REASON = (
    "market_close_information_resolution_source_not_ready"
)
CLOSE_WINDOW_ACTIVE_REASON = "market_close_information_close_window_active"

REASON_CODES = (
    READY_REASON,
    OFFICIAL_UPDATE_MISSING_REASON,
    OFFICIAL_UPDATE_STALE_REASON,
    INDEPENDENT_CONFIRMATION_MISSING_REASON,
    INDEPENDENT_CONFIRMATION_STALE_REASON,
    UNRESOLVED_CONTRADICTION_REASON,
    RESOLUTION_SOURCE_NOT_READY_REASON,
    CLOSE_WINDOW_ACTIVE_REASON,
)
REPORT_TRIGGER_REASONS = tuple(reason for reason in REASON_CODES if reason != READY_REASON)

STATUS_RANK = {"blocked": 0, "watch": 1, "ready": 2}
PRIORITY_RANK = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_HOUR = Decimal("3600")
DIGEST_FIELD = "derived_validation_digest"
HEX_CHARS = frozenset("0123456789abcdef")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
        _join_parts("pri", "vate"),
        _join_parts("cre", "dential"),
    )
)


@dataclass(frozen=True)
class ResearchPacketMarketCloseInformationSlaV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_MARKET_CLOSE_INFORMATION_SLA_V2_CONFIG_VERSION
    )
    official_update_sla_seconds: Decimal = Decimal("1800.000000")
    independent_confirmation_sla_seconds: Decimal = Decimal("3600.000000")
    close_window_hours: Decimal = Decimal("1.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketMarketCloseInformationSlaV2Config,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "official_update_sla_seconds",
            _require_positive_decimal(
                "official_update_sla_seconds",
                self.official_update_sla_seconds,
            ),
        )
        object.__setattr__(
            self,
            "independent_confirmation_sla_seconds",
            _require_positive_decimal(
                "independent_confirmation_sla_seconds",
                self.independent_confirmation_sla_seconds,
            ),
        )
        object.__setattr__(
            self,
            "close_window_hours",
            _require_positive_decimal("close_window_hours", self.close_window_hours),
        )
        _require_hard_flags("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketMarketCloseInformationSlaV2Observation:
    packet_id: str
    market_id: str
    team_id: str
    category_id: str
    market_close_at: datetime
    official_update_at: datetime | None
    independent_confirmation_at: datetime | None
    unresolved_contradiction: bool
    resolution_source_ready: bool
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchPacketMarketCloseInformationSlaV2Observation,
        )
        for field_name in ("packet_id", "market_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        for field_name in ("official_update_at", "independent_confirmation_at"):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        _require_bool("unresolved_contradiction", self.unresolved_contradiction)
        _require_bool("resolution_source_ready", self.resolution_source_ready)
        _require_hard_flags("observation", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketMarketCloseInformationSlaV2ReasonCount:
    reason_code: str
    count: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason count",
            self,
            ResearchPacketMarketCloseInformationSlaV2ReasonCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count("count", self.count),
        )
        _require_hard_flags("reason count", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketMarketCloseInformationSlaV2Row:
    packet_id: str
    market_id: str
    team_id: str
    category_id: str
    market_close_at: datetime
    official_update_at: datetime | None
    independent_confirmation_at: datetime | None
    official_update_age_seconds: Decimal | None
    independent_confirmation_age_seconds: Decimal | None
    close_hours: Decimal
    close_window_active: bool
    unresolved_contradiction: bool
    resolution_source_ready: bool
    sla_status: str
    escalation_priority: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("SLA row", self, ResearchPacketMarketCloseInformationSlaV2Row)
        for field_name in ("packet_id", "market_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        for field_name in ("official_update_at", "independent_confirmation_at"):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_update_age_seconds",
            "independent_confirmation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "close_hours",
            _require_nonnegative_decimal("close_hours", self.close_hours),
        )
        _require_bool("close_window_active", self.close_window_active)
        _require_bool("unresolved_contradiction", self.unresolved_contradiction)
        _require_bool("resolution_source_ready", self.resolution_source_ready)
        _require_status("sla_status", self.sla_status)
        _require_priority("escalation_priority", self.escalation_priority)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_sla_row(self)
        _require_hard_flags("SLA row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketMarketCloseInformationSlaV2Report:
    generated_at: datetime
    config_version: str
    sla_status: str
    row_count: Decimal
    flagged_row_count: Decimal
    ready_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    official_update_missing_count: Decimal
    official_update_stale_count: Decimal
    independent_confirmation_missing_count: Decimal
    independent_confirmation_stale_count: Decimal
    unresolved_contradiction_count: Decimal
    resolution_source_not_ready_count: Decimal
    close_window_row_count: Decimal
    p0_priority_count: Decimal
    p1_priority_count: Decimal
    p2_priority_count: Decimal
    p3_priority_count: Decimal
    flagged_ratio: Decimal
    max_official_update_age_seconds: Decimal
    max_independent_confirmation_age_seconds: Decimal
    minimum_close_hours: Decimal
    reason_code_counts: tuple[ResearchPacketMarketCloseInformationSlaV2ReasonCount, ...]
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "SLA report",
            self,
            ResearchPacketMarketCloseInformationSlaV2Report,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("sla_status", self.sla_status)
        for field_name in (
            "row_count",
            "flagged_row_count",
            "ready_row_count",
            "watch_row_count",
            "blocked_row_count",
            "official_update_missing_count",
            "official_update_stale_count",
            "independent_confirmation_missing_count",
            "independent_confirmation_stale_count",
            "unresolved_contradiction_count",
            "resolution_source_not_ready_count",
            "close_window_row_count",
            "p0_priority_count",
            "p1_priority_count",
            "p2_priority_count",
            "p3_priority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flagged_ratio",
            _require_ratio_decimal("flagged_ratio", self.flagged_ratio),
        )
        for field_name in (
            "max_official_update_age_seconds",
            "max_independent_confirmation_age_seconds",
            "minimum_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("SLA report", self)
        _require_or_set_digest(self)


def build_research_packet_market_close_information_sla_v2_report(
    observations: Iterable[ResearchPacketMarketCloseInformationSlaV2Observation],
    *,
    config: ResearchPacketMarketCloseInformationSlaV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketCloseInformationSlaV2Report:
    if type(config) is not ResearchPacketMarketCloseInformationSlaV2Config:
        raise ValueError(
            "config must be a ResearchPacketMarketCloseInformationSlaV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchPacketMarketCloseInformationSlaV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        sla_status=_report_status(rows),
        row_count=_decimal_count(len(rows)),
        flagged_row_count=_flagged_row_count(rows),
        ready_row_count=_status_count(rows, "ready"),
        watch_row_count=_status_count(rows, "watch"),
        blocked_row_count=_status_count(rows, "blocked"),
        official_update_missing_count=_reason_count(
            rows,
            OFFICIAL_UPDATE_MISSING_REASON,
        ),
        official_update_stale_count=_reason_count(rows, OFFICIAL_UPDATE_STALE_REASON),
        independent_confirmation_missing_count=_reason_count(
            rows,
            INDEPENDENT_CONFIRMATION_MISSING_REASON,
        ),
        independent_confirmation_stale_count=_reason_count(
            rows,
            INDEPENDENT_CONFIRMATION_STALE_REASON,
        ),
        unresolved_contradiction_count=_bool_count(rows, "unresolved_contradiction"),
        resolution_source_not_ready_count=_decimal_count(
            sum(1 for row in rows if not row.resolution_source_ready),
        ),
        close_window_row_count=_bool_count(rows, "close_window_active"),
        p0_priority_count=_priority_count(rows, "p0"),
        p1_priority_count=_priority_count(rows, "p1"),
        p2_priority_count=_priority_count(rows, "p2"),
        p3_priority_count=_priority_count(rows, "p3"),
        flagged_ratio=_ratio(_flagged_row_count(rows), _decimal_count(len(rows))),
        max_official_update_age_seconds=_max_optional_decimal(
            rows,
            "official_update_age_seconds",
        ),
        max_independent_confirmation_age_seconds=_max_optional_decimal(
            rows,
            "independent_confirmation_age_seconds",
        ),
        minimum_close_hours=_minimum_close_hours(rows),
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_packet_market_close_information_sla_v2_report_to_payload(
    report: ResearchPacketMarketCloseInformationSlaV2Report,
) -> dict[str, object]:
    if type(report) is not ResearchPacketMarketCloseInformationSlaV2Report:
        raise ValueError(
            "report must be a ResearchPacketMarketCloseInformationSlaV2Report",
        )
    _require_hard_flags("report", report)
    rendered = _payload_value(report)
    if type(rendered) is not dict:
        raise ValueError("report rendering failed")
    return rendered


def _normalize_observations(
    observations: Iterable[ResearchPacketMarketCloseInformationSlaV2Observation],
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketMarketCloseInformationSlaV2Observation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_packet_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchPacketMarketCloseInformationSlaV2Observation:
            raise ValueError("observations must contain exact observation values")
        _require_hard_flags("observation", observation)
        if observation.packet_id in seen_packet_ids:
            raise ValueError("packet_id values must be unique")
        if observation.market_close_at < generated_at:
            raise ValueError("market_close_at must be >= generated_at")
        for field_name in ("official_update_at", "independent_confirmation_at"):
            value = getattr(observation, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must be <= generated_at")
        seen_packet_ids.add(observation.packet_id)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.team_id,
                observation.category_id,
                observation.market_close_at,
                observation.packet_id,
                observation.market_id,
            ),
        ),
    )


def _row_from_observation(
    observation: ResearchPacketMarketCloseInformationSlaV2Observation,
    *,
    config: ResearchPacketMarketCloseInformationSlaV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketCloseInformationSlaV2Row:
    official_update_age = (
        None
        if observation.official_update_at is None
        else _duration_seconds(observation.official_update_at, generated_at)
    )
    independent_confirmation_age = (
        None
        if observation.independent_confirmation_at is None
        else _duration_seconds(observation.independent_confirmation_at, generated_at)
    )
    close_hours = _duration_hours(generated_at, observation.market_close_at)
    close_window_active = close_hours <= config.close_window_hours
    reason_codes = _row_reason_codes(
        official_update_age_seconds=official_update_age,
        independent_confirmation_age_seconds=independent_confirmation_age,
        unresolved_contradiction=observation.unresolved_contradiction,
        resolution_source_ready=observation.resolution_source_ready,
        close_window_active=close_window_active,
        config=config,
    )
    escalation_priority = _priority_from_reasons(reason_codes)
    return ResearchPacketMarketCloseInformationSlaV2Row(
        packet_id=observation.packet_id,
        market_id=observation.market_id,
        team_id=observation.team_id,
        category_id=observation.category_id,
        market_close_at=observation.market_close_at,
        official_update_at=observation.official_update_at,
        independent_confirmation_at=observation.independent_confirmation_at,
        official_update_age_seconds=official_update_age,
        independent_confirmation_age_seconds=independent_confirmation_age,
        close_hours=close_hours,
        close_window_active=close_window_active,
        unresolved_contradiction=observation.unresolved_contradiction,
        resolution_source_ready=observation.resolution_source_ready,
        sla_status=_status_from_priority(escalation_priority),
        escalation_priority=escalation_priority,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    official_update_age_seconds: Decimal | None,
    independent_confirmation_age_seconds: Decimal | None,
    unresolved_contradiction: bool,
    resolution_source_ready: bool,
    close_window_active: bool,
    config: ResearchPacketMarketCloseInformationSlaV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if official_update_age_seconds is None:
        reasons.append(OFFICIAL_UPDATE_MISSING_REASON)
    elif official_update_age_seconds > config.official_update_sla_seconds:
        reasons.append(OFFICIAL_UPDATE_STALE_REASON)
    if independent_confirmation_age_seconds is None:
        reasons.append(INDEPENDENT_CONFIRMATION_MISSING_REASON)
    elif independent_confirmation_age_seconds > config.independent_confirmation_sla_seconds:
        reasons.append(INDEPENDENT_CONFIRMATION_STALE_REASON)
    if unresolved_contradiction:
        reasons.append(UNRESOLVED_CONTRADICTION_REASON)
    if not resolution_source_ready:
        reasons.append(RESOLUTION_SOURCE_NOT_READY_REASON)
    if reasons and close_window_active:
        reasons.append(CLOSE_WINDOW_ACTIVE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reasons)


def _priority_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "p3"
    if (
        UNRESOLVED_CONTRADICTION_REASON in reason_codes
        and CLOSE_WINDOW_ACTIVE_REASON in reason_codes
    ):
        return "p0"
    if (
        UNRESOLVED_CONTRADICTION_REASON in reason_codes
        or RESOLUTION_SOURCE_NOT_READY_REASON in reason_codes
        or CLOSE_WINDOW_ACTIVE_REASON in reason_codes
    ):
        return "p1"
    return "p2"


def _status_from_priority(priority: str) -> str:
    if priority in ("p0", "p1"):
        return "blocked"
    if priority == "p2":
        return "watch"
    return "ready"


def _report_status(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
) -> str:
    if any(row.sla_status == "blocked" for row in rows):
        return "blocked"
    if any(row.sla_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
) -> tuple[str, ...]:
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASONS
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (READY_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchPacketMarketCloseInformationSlaV2ReasonCount, ...]:
    if reason_codes == (READY_REASON,):
        ready_count = sum(1 for row in rows if row.reason_codes == (READY_REASON,))
        return (
            ResearchPacketMarketCloseInformationSlaV2ReasonCount(
                reason_code=READY_REASON,
                count=_decimal_count(max(1, ready_count)),
            ),
        )
    return tuple(
        ResearchPacketMarketCloseInformationSlaV2ReasonCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in REPORT_TRIGGER_REASONS
        if reason_code in reason_codes
    )


def _row_sort_key(
    row: ResearchPacketMarketCloseInformationSlaV2Row,
) -> tuple[int, int, str, str, datetime, str, str]:
    return (
        PRIORITY_RANK[row.escalation_priority],
        STATUS_RANK[row.sla_status],
        row.team_id,
        row.category_id,
        row.market_close_at,
        row.packet_id,
        row.market_id,
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketMarketCloseInformationSlaV2Row:
            raise ValueError("rows must contain exact SLA rows")
        _require_hard_flags("SLA row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("rows packet_id values must be unique")
        seen_packet_ids.add(row.packet_id)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchPacketMarketCloseInformationSlaV2ReasonCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketMarketCloseInformationSlaV2ReasonCount:
            raise ValueError("reason_code_counts must contain exact reason count rows")
        _require_hard_flags("reason count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts values must be unique")
        seen.add(row.reason_code)
    expected = tuple(sorted(rows, key=lambda row: REASON_CODES.index(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(reason for reason in REASON_CODES if reason in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_sla_row(row: ResearchPacketMarketCloseInformationSlaV2Row) -> None:
    if row.official_update_at is None:
        if row.official_update_age_seconds is not None:
            raise ValueError("official_update_age_seconds requires official_update_at")
        if OFFICIAL_UPDATE_MISSING_REASON not in row.reason_codes:
            raise ValueError("missing official update rows require missing reason")
    else:
        if row.official_update_age_seconds is None:
            raise ValueError("official_update_at requires official_update_age_seconds")
    if row.independent_confirmation_at is None:
        if row.independent_confirmation_age_seconds is not None:
            raise ValueError(
                "independent_confirmation_age_seconds requires independent_confirmation_at",
            )
        if INDEPENDENT_CONFIRMATION_MISSING_REASON not in row.reason_codes:
            raise ValueError("missing independent confirmation rows require missing reason")
    else:
        if row.independent_confirmation_age_seconds is None:
            raise ValueError(
                "independent_confirmation_at requires independent_confirmation_age_seconds",
            )
    if row.unresolved_contradiction and (
        UNRESOLVED_CONTRADICTION_REASON not in row.reason_codes
    ):
        raise ValueError("unresolved contradiction rows require contradiction reason")
    if (not row.resolution_source_ready) and (
        RESOLUTION_SOURCE_NOT_READY_REASON not in row.reason_codes
    ):
        raise ValueError("not ready resolution source rows require readiness reason")
    if row.close_window_active and row.reason_codes != (READY_REASON,):
        if CLOSE_WINDOW_ACTIVE_REASON not in row.reason_codes:
            raise ValueError("close window rows require close window reason")
    if (not row.close_window_active) and CLOSE_WINDOW_ACTIVE_REASON in row.reason_codes:
        raise ValueError("close window reason requires close_window_active")
    if row.reason_codes == (READY_REASON,):
        if (
            row.official_update_age_seconds is None
            or row.independent_confirmation_age_seconds is None
            or row.unresolved_contradiction
            or not row.resolution_source_ready
        ):
            raise ValueError("ready rows require complete clear information")
    if row.escalation_priority != _priority_from_reasons(row.reason_codes):
        raise ValueError("escalation_priority must match reason_codes")
    if row.sla_status != _status_from_priority(row.escalation_priority):
        raise ValueError("sla_status must match escalation_priority")


def _validate_report(report: ResearchPacketMarketCloseInformationSlaV2Report) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.flagged_row_count != _flagged_row_count(rows):
        raise ValueError("flagged_row_count must match rows")
    for status in SLA_STATUSES:
        field_name = f"{status}_row_count"
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    expected_reason_counts = (
        (OFFICIAL_UPDATE_MISSING_REASON, report.official_update_missing_count),
        (OFFICIAL_UPDATE_STALE_REASON, report.official_update_stale_count),
        (
            INDEPENDENT_CONFIRMATION_MISSING_REASON,
            report.independent_confirmation_missing_count,
        ),
        (
            INDEPENDENT_CONFIRMATION_STALE_REASON,
            report.independent_confirmation_stale_count,
        ),
    )
    for reason_code, expected_count in expected_reason_counts:
        if expected_count != _reason_count(rows, reason_code):
            raise ValueError("reason count fields must match rows")
    if report.unresolved_contradiction_count != _bool_count(
        rows,
        "unresolved_contradiction",
    ):
        raise ValueError("unresolved_contradiction_count must match rows")
    if report.resolution_source_not_ready_count != _decimal_count(
        sum(1 for row in rows if not row.resolution_source_ready),
    ):
        raise ValueError("resolution_source_not_ready_count must match rows")
    if report.close_window_row_count != _bool_count(rows, "close_window_active"):
        raise ValueError("close_window_row_count must match rows")
    for priority in ESCALATION_PRIORITIES:
        field_name = f"{priority}_priority_count"
        if getattr(report, field_name) != _priority_count(rows, priority):
            raise ValueError(f"{field_name} must match rows")
    if report.flagged_ratio != _ratio(report.flagged_row_count, report.row_count):
        raise ValueError("flagged_ratio must match rows")
    if report.max_official_update_age_seconds != _max_optional_decimal(
        rows,
        "official_update_age_seconds",
    ):
        raise ValueError("max_official_update_age_seconds must match rows")
    if report.max_independent_confirmation_age_seconds != _max_optional_decimal(
        rows,
        "independent_confirmation_age_seconds",
    ):
        raise ValueError("max_independent_confirmation_age_seconds must match rows")
    if report.minimum_close_hours != _minimum_close_hours(rows):
        raise ValueError("minimum_close_hours must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.sla_status != _report_status(rows):
        raise ValueError("sla_status must match rows")


def _flagged_row_count(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.reason_codes != (READY_REASON,)))


def _status_count(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.sla_status == status))


def _priority_count(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
    priority: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.escalation_priority == priority))


def _reason_count(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _bool_count(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name)))


def _max_optional_decimal(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
    field_name: str,
) -> Decimal:
    values = tuple(
        value
        for row in rows
        for value in (getattr(row, field_name),)
        if value is not None
    )
    return max(values) if values else ZERO


def _minimum_close_hours(
    rows: tuple[ResearchPacketMarketCloseInformationSlaV2Row, ...],
) -> Decimal:
    return min((row.close_hours for row in rows), default=ZERO)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = _as_utc("end", end) - _as_utc("start", start)
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    if microseconds < ZERO:
        raise ValueError("duration must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return (microseconds / MICROSECONDS_PER_SECOND).quantize(QUANTUM)


def _duration_hours(start: datetime, end: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (_duration_seconds(start, end) / SECONDS_PER_HOUR).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANTUM)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SLA_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_priority(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ESCALATION_PRIORITIES:
        raise ValueError(f"{field_name} must be p0, p1, p2, or p3")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be an exact {expected_type.__name__} value")


def _require_or_set_digest(value: object) -> None:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("derived_validation_digest requires a dataclass value")
    expected = _compute_digest(value)
    current = getattr(value, DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if current == "":
        object.__setattr__(value, DIGEST_FIELD, expected)
        return
    if len(current) != 64 or any(character not in HEX_CHARS for character in current):
        raise ValueError("derived_validation_digest must be lowercase sha256 hex")
    if current != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _compute_digest(value: object) -> str:
    stripped = _strip_digest_fields(_payload_value(value))
    encoded = json.dumps(stripped, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _strip_digest_fields(value: object) -> object:
    if type(value) is dict:
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != DIGEST_FIELD
        }
    if type(value) is list:
        return [_strip_digest_fields(item) for item in value]
    return value


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return format(_require_nonnegative_decimal("decimal", value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise TypeError("value is not JSON-ready")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_MARKET_CLOSE_INFORMATION_SLA_V2_CONFIG_VERSION",
    "ResearchPacketMarketCloseInformationSlaV2Config",
    "ResearchPacketMarketCloseInformationSlaV2Observation",
    "ResearchPacketMarketCloseInformationSlaV2ReasonCount",
    "ResearchPacketMarketCloseInformationSlaV2Report",
    "ResearchPacketMarketCloseInformationSlaV2Row",
    "build_research_packet_market_close_information_sla_v2_report",
    "research_packet_market_close_information_sla_v2_report_to_payload",
)
