"""Pure in-memory source ack recheck SLA report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    require_team_category_pair,
    require_team_id,
)


DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_SLA_CONFIG_VERSION = (
    "research-packet-source-ack-recheck-sla-v0"
)

SOURCE_KINDS = ("official", "proxy")
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("empty", "clear", "watch", "blocked")
ROW_REASON_CODES = (
    "source_ack_recheck_sla_clear",
    "source_ack_recheck_overdue",
    "source_ack_missing_owner",
    "source_ack_contradiction_after_ack",
    "source_ack_repeated_team_category_miss",
)
REPORT_REASON_CODES = (
    "source_ack_recheck_sla_empty",
    "source_ack_recheck_sla_clear",
    "source_ack_recheck_overdue",
    "source_ack_missing_owner",
    "source_ack_contradiction_after_ack",
    "source_ack_repeated_team_category_miss",
)
REPORT_TRIGGER_REASON_CODES = tuple(
    code
    for code in REPORT_REASON_CODES
    if code not in ("source_ack_recheck_sla_empty", "source_ack_recheck_sla_clear")
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_QUANTIZED = Decimal("0.000000")
ONE_QUANTIZED = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("cre", "den", "tial"),
        _join_parts("pri", "vate_key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
        _join_parts("au", "th"),
        _join_parts("li", "ve"),
        _join_parts("fa", "st"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckSlaConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_SLA_CONFIG_VERSION
    overdue_recheck_seconds: Decimal = Decimal("86400.000000")
    repeated_miss_threshold_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "overdue_recheck_seconds",
            _require_positive_seconds_decimal(
                "overdue_recheck_seconds",
                self.overdue_recheck_seconds,
            ),
        )
        object.__setattr__(
            self,
            "repeated_miss_threshold_count",
            _require_positive_count_decimal(
                "repeated_miss_threshold_count",
                self.repeated_miss_threshold_count,
            ),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckSlaAcknowledgement:
    acknowledgement_id: str
    packet_id: str
    source_id: str
    team_id: str
    category_id: str
    owner_id: str | None
    acknowledged_at: datetime
    acknowledged_value: str
    rechecked_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("acknowledgement_id", "packet_id", "source_id"):
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
            "owner_id",
            _normalize_optional_public_string("owner_id", self.owner_id),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        _require_public_string("acknowledged_value", self.acknowledged_value)
        object.__setattr__(
            self,
            "rechecked_at",
            _as_optional_utc("rechecked_at", self.rechecked_at),
        )
        if self.rechecked_at is not None and self.rechecked_at < self.acknowledged_at:
            raise ValueError("rechecked_at must be >= acknowledged_at")
        require_paper_only_flags("acknowledgement", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckSlaUpdate:
    update_id: str
    packet_id: str
    source_id: str
    source_kind: str
    updated_at: datetime
    updated_value: str | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("update_id", "packet_id", "source_id"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_source_kind("source_kind", self.source_kind)
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        object.__setattr__(
            self,
            "updated_value",
            _normalize_optional_public_string("updated_value", self.updated_value),
        )
        require_paper_only_flags("update", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckSlaRow:
    acknowledgement_id: str
    packet_id: str
    source_id: str
    team_id: str
    category_id: str
    owner_id: str | None
    status: str
    acknowledged_at: datetime
    latest_update_id: str | None
    latest_update_source_kind: str | None
    latest_update_at: datetime | None
    acknowledgement_age_seconds: Decimal
    recheck_lag_seconds: Decimal
    later_update_count: Decimal
    overdue_recheck: bool
    missing_owner: bool
    contradiction_after_ack: bool
    repeated_team_category_miss: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("acknowledgement_id", "packet_id", "source_id"):
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
            "owner_id",
            _normalize_optional_public_string("owner_id", self.owner_id),
        )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "latest_update_id",
            _normalize_optional_public_string(
                "latest_update_id",
                self.latest_update_id,
            ),
        )
        if self.latest_update_source_kind is not None:
            _require_source_kind("latest_update_source_kind", self.latest_update_source_kind)
        object.__setattr__(
            self,
            "latest_update_at",
            _as_optional_utc("latest_update_at", self.latest_update_at),
        )
        for field_name in ("acknowledgement_age_seconds", "recheck_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "later_update_count",
            _require_nonnegative_count_decimal(
                "later_update_count",
                self.later_update_count,
            ),
        )
        _require_bool("overdue_recheck", self.overdue_recheck)
        _require_bool("missing_owner", self.missing_owner)
        _require_bool("contradiction_after_ack", self.contradiction_after_ack)
        _require_bool(
            "repeated_team_category_miss",
            self.repeated_team_category_miss,
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
        require_paper_only_flags("sla row", self)
        _validate_sla_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckSlaTeamCategoryRow:
    team_id: str
    category_id: str
    missed_acknowledgement_count: Decimal
    total_acknowledgement_count: Decimal
    miss_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "missed_acknowledgement_count",
            _require_nonnegative_count_decimal(
                "missed_acknowledgement_count",
                self.missed_acknowledgement_count,
            ),
        )
        object.__setattr__(
            self,
            "total_acknowledgement_count",
            _require_nonnegative_count_decimal(
                "total_acknowledgement_count",
                self.total_acknowledgement_count,
            ),
        )
        object.__setattr__(
            self,
            "miss_ratio",
            _require_ratio("miss_ratio", self.miss_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=("source_ack_repeated_team_category_miss",),
                allow_empty=False,
            ),
        )
        require_paper_only_flags("team category row", self)
        _validate_team_category_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckSlaReport:
    generated_at: datetime
    config_version: str
    status: str
    acknowledgement_count: Decimal
    update_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    overdue_recheck_count: Decimal
    missing_owner_count: Decimal
    contradiction_after_ack_count: Decimal
    repeated_team_category_miss_count: Decimal
    issue_ratio: Decimal
    max_acknowledgement_age_seconds: Decimal
    rows: tuple[ResearchPacketSourceAckRecheckSlaRow, ...]
    team_category_rows: tuple[ResearchPacketSourceAckRecheckSlaTeamCategoryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("status", self.status)
        for field_name in (
            "acknowledgement_count",
            "update_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "overdue_recheck_count",
            "missing_owner_count",
            "contradiction_after_ack_count",
            "repeated_team_category_miss_count",
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
            "issue_ratio",
            _require_ratio("issue_ratio", self.issue_ratio),
        )
        object.__setattr__(
            self,
            "max_acknowledgement_age_seconds",
            _require_nonnegative_seconds_decimal(
                "max_acknowledgement_age_seconds",
                self.max_acknowledgement_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_sla_rows(self.rows))
        object.__setattr__(
            self,
            "team_category_rows",
            _normalize_team_category_rows(self.team_category_rows),
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
        reject_unsafe_surface_fields("ack recheck sla report", self)
        require_paper_only_flags("sla report", self)
        _validate_report(self)


def build_research_packet_source_ack_recheck_sla_report(
    acknowledgements: Iterable[ResearchPacketSourceAckRecheckSlaAcknowledgement],
    updates: Iterable[ResearchPacketSourceAckRecheckSlaUpdate],
    *,
    config: ResearchPacketSourceAckRecheckSlaConfig,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckSlaReport:
    if type(config) is not ResearchPacketSourceAckRecheckSlaConfig:
        raise ValueError("config must be a ResearchPacketSourceAckRecheckSlaConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_acks = _normalize_acknowledgements(acknowledgements)
    normalized_updates = _normalize_updates(updates)
    _validate_input_times(normalized_acks, normalized_updates, generated_at_utc)

    base_rows = tuple(
        _sla_row(
            acknowledgement,
            updates=_pending_later_updates(acknowledgement, normalized_updates),
            config=config,
            generated_at=generated_at_utc,
        )
        for acknowledgement in normalized_acks
    )
    team_rows = _team_category_rows(
        base_rows,
        threshold=config.repeated_miss_threshold_count,
    )
    repeated_keys = {(row.team_id, row.category_id) for row in team_rows}
    rows = _sort_sla_rows(
        tuple(
            _with_repeated_team_category_miss(row)
            if (row.team_id, row.category_id) in repeated_keys
            and row.reason_codes != ("source_ack_recheck_sla_clear",)
            else row
            for row in base_rows
        ),
    )
    reason_codes = _report_reason_codes(rows)

    return ResearchPacketSourceAckRecheckSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        acknowledgement_count=_count(len(rows)),
        update_count=_count(len(normalized_updates)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        overdue_recheck_count=_count(sum(1 for row in rows if row.overdue_recheck)),
        missing_owner_count=_count(sum(1 for row in rows if row.missing_owner)),
        contradiction_after_ack_count=_count(
            sum(1 for row in rows if row.contradiction_after_ack),
        ),
        repeated_team_category_miss_count=_count(len(team_rows)),
        issue_ratio=_ratio(
            _count(sum(1 for row in rows if row.status != "pass")),
            _count(len(rows)),
        ),
        max_acknowledgement_age_seconds=max(
            (row.acknowledgement_age_seconds for row in rows),
            default=ZERO_QUANTIZED,
        ),
        rows=rows,
        team_category_rows=team_rows,
        reason_codes=reason_codes,
    )


def research_packet_source_ack_recheck_sla_report_to_payload(
    report: ResearchPacketSourceAckRecheckSlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketSourceAckRecheckSlaReport:
        raise ValueError("report must be a ResearchPacketSourceAckRecheckSlaReport")
    reject_unsafe_surface_fields("ack recheck sla report", report)
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _sla_row(
    acknowledgement: ResearchPacketSourceAckRecheckSlaAcknowledgement,
    *,
    updates: tuple[ResearchPacketSourceAckRecheckSlaUpdate, ...],
    config: ResearchPacketSourceAckRecheckSlaConfig,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckSlaRow:
    latest_update = updates[-1] if updates else None
    recheck_lag_seconds = (
        ZERO_QUANTIZED
        if latest_update is None
        else _duration_seconds(acknowledgement.acknowledged_at, latest_update.updated_at)
    )
    overdue_recheck = recheck_lag_seconds > config.overdue_recheck_seconds
    missing_owner = acknowledgement.owner_id is None
    contradiction_after_ack = any(
        _contradicts_acknowledgement(acknowledgement, update) for update in updates
    )
    reason_codes = _row_reason_codes(
        overdue_recheck=overdue_recheck,
        missing_owner=missing_owner,
        contradiction_after_ack=contradiction_after_ack,
        repeated_team_category_miss=False,
    )
    return ResearchPacketSourceAckRecheckSlaRow(
        acknowledgement_id=acknowledgement.acknowledgement_id,
        packet_id=acknowledgement.packet_id,
        source_id=acknowledgement.source_id,
        team_id=acknowledgement.team_id,
        category_id=acknowledgement.category_id,
        owner_id=acknowledgement.owner_id,
        status=_row_status(reason_codes),
        acknowledged_at=acknowledgement.acknowledged_at,
        latest_update_id=None if latest_update is None else latest_update.update_id,
        latest_update_source_kind=(
            None if latest_update is None else latest_update.source_kind
        ),
        latest_update_at=None if latest_update is None else latest_update.updated_at,
        acknowledgement_age_seconds=_duration_seconds(
            acknowledgement.acknowledged_at,
            generated_at,
        ),
        recheck_lag_seconds=recheck_lag_seconds,
        later_update_count=_count(len(updates)),
        overdue_recheck=overdue_recheck,
        missing_owner=missing_owner,
        contradiction_after_ack=contradiction_after_ack,
        repeated_team_category_miss=False,
        reason_codes=reason_codes,
    )


def _pending_later_updates(
    acknowledgement: ResearchPacketSourceAckRecheckSlaAcknowledgement,
    updates: tuple[ResearchPacketSourceAckRecheckSlaUpdate, ...],
) -> tuple[ResearchPacketSourceAckRecheckSlaUpdate, ...]:
    return tuple(
        sorted(
            (
                update
                for update in updates
                if update.packet_id == acknowledgement.packet_id
                and update.source_id == acknowledgement.source_id
                and update.updated_at > acknowledgement.acknowledged_at
                and not _rechecked_after(acknowledgement, update)
            ),
            key=lambda update: (update.updated_at, update.update_id),
        ),
    )


def _rechecked_after(
    acknowledgement: ResearchPacketSourceAckRecheckSlaAcknowledgement,
    update: ResearchPacketSourceAckRecheckSlaUpdate,
) -> bool:
    return (
        acknowledgement.rechecked_at is not None
        and acknowledgement.rechecked_at >= update.updated_at
    )


def _contradicts_acknowledgement(
    acknowledgement: ResearchPacketSourceAckRecheckSlaAcknowledgement,
    update: ResearchPacketSourceAckRecheckSlaUpdate,
) -> bool:
    if update.updated_value is None:
        return False
    if acknowledgement.acknowledged_value in ("unknown", "unresolved"):
        return False
    if update.updated_value in ("unknown", "unresolved"):
        return False
    return acknowledgement.acknowledged_value != update.updated_value


def _team_category_rows(
    rows: tuple[ResearchPacketSourceAckRecheckSlaRow, ...],
    *,
    threshold: Decimal,
) -> tuple[ResearchPacketSourceAckRecheckSlaTeamCategoryRow, ...]:
    total_counts: dict[tuple[str, str], int] = {}
    miss_counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row.team_id, row.category_id)
        total_counts[key] = total_counts.get(key, 0) + 1
        if row.reason_codes != ("source_ack_recheck_sla_clear",):
            miss_counts[key] = miss_counts.get(key, 0) + 1

    team_rows: list[ResearchPacketSourceAckRecheckSlaTeamCategoryRow] = []
    for key in sorted(total_counts):
        missed_count = _count(miss_counts.get(key, 0))
        total_count = _count(total_counts[key])
        if missed_count >= threshold and missed_count > ZERO_COUNT:
            team_rows.append(
                ResearchPacketSourceAckRecheckSlaTeamCategoryRow(
                    team_id=key[0],
                    category_id=key[1],
                    missed_acknowledgement_count=missed_count,
                    total_acknowledgement_count=total_count,
                    miss_ratio=_ratio(missed_count, total_count),
                    reason_codes=("source_ack_repeated_team_category_miss",),
                ),
            )
    return tuple(team_rows)


def _with_repeated_team_category_miss(
    row: ResearchPacketSourceAckRecheckSlaRow,
) -> ResearchPacketSourceAckRecheckSlaRow:
    reason_codes = _row_reason_codes(
        overdue_recheck=row.overdue_recheck,
        missing_owner=row.missing_owner,
        contradiction_after_ack=row.contradiction_after_ack,
        repeated_team_category_miss=True,
    )
    return ResearchPacketSourceAckRecheckSlaRow(
        acknowledgement_id=row.acknowledgement_id,
        packet_id=row.packet_id,
        source_id=row.source_id,
        team_id=row.team_id,
        category_id=row.category_id,
        owner_id=row.owner_id,
        status=_row_status(reason_codes),
        acknowledged_at=row.acknowledged_at,
        latest_update_id=row.latest_update_id,
        latest_update_source_kind=row.latest_update_source_kind,
        latest_update_at=row.latest_update_at,
        acknowledgement_age_seconds=row.acknowledgement_age_seconds,
        recheck_lag_seconds=row.recheck_lag_seconds,
        later_update_count=row.later_update_count,
        overdue_recheck=row.overdue_recheck,
        missing_owner=row.missing_owner,
        contradiction_after_ack=row.contradiction_after_ack,
        repeated_team_category_miss=True,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    overdue_recheck: bool,
    missing_owner: bool,
    contradiction_after_ack: bool,
    repeated_team_category_miss: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if overdue_recheck:
        reason_codes.append("source_ack_recheck_overdue")
    if missing_owner:
        reason_codes.append("source_ack_missing_owner")
    if contradiction_after_ack:
        reason_codes.append("source_ack_contradiction_after_ack")
    if repeated_team_category_miss:
        reason_codes.append("source_ack_repeated_team_category_miss")
    if not reason_codes:
        reason_codes.append("source_ack_recheck_sla_clear")
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("source_ack_recheck_sla_clear",):
        return "pass"
    if (
        "source_ack_missing_owner" in reason_codes
        or "source_ack_contradiction_after_ack" in reason_codes
        or "source_ack_repeated_team_category_miss" in reason_codes
    ):
        return "blocked"
    return "watch"


def _report_status(rows: tuple[ResearchPacketSourceAckRecheckSlaRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceAckRecheckSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_ack_recheck_sla_empty",)
    reason_codes = tuple(
        reason_code
        for reason_code in REPORT_TRIGGER_REASON_CODES
        if any(reason_code in row.reason_codes for row in rows)
    )
    if reason_codes:
        return reason_codes
    return ("source_ack_recheck_sla_clear",)


def _normalize_acknowledgements(
    acknowledgements: Iterable[ResearchPacketSourceAckRecheckSlaAcknowledgement],
) -> tuple[ResearchPacketSourceAckRecheckSlaAcknowledgement, ...]:
    if isinstance(acknowledgements, str | bytes):
        raise ValueError("acknowledgements must be an iterable")
    try:
        normalized = tuple(acknowledgements)
    except TypeError as exc:
        raise ValueError("acknowledgements must be an iterable") from exc
    seen: set[str] = set()
    for acknowledgement in normalized:
        if type(acknowledgement) is not ResearchPacketSourceAckRecheckSlaAcknowledgement:
            raise ValueError(
                "acknowledgements must contain exact acknowledgement values",
            )
        require_paper_only_flags("acknowledgement", acknowledgement)
        if acknowledgement.acknowledgement_id in seen:
            raise ValueError("acknowledgement_id values must be unique")
        seen.add(acknowledgement.acknowledgement_id)
    return tuple(
        sorted(
            normalized,
            key=lambda acknowledgement: (
                acknowledgement.team_id,
                acknowledgement.category_id,
                acknowledgement.packet_id,
                acknowledgement.source_id,
                acknowledgement.acknowledged_at,
                acknowledgement.acknowledgement_id,
            ),
        ),
    )


def _normalize_updates(
    updates: Iterable[ResearchPacketSourceAckRecheckSlaUpdate],
) -> tuple[ResearchPacketSourceAckRecheckSlaUpdate, ...]:
    if isinstance(updates, str | bytes):
        raise ValueError("updates must be an iterable")
    try:
        normalized = tuple(updates)
    except TypeError as exc:
        raise ValueError("updates must be an iterable") from exc
    seen: set[str] = set()
    for update in normalized:
        if type(update) is not ResearchPacketSourceAckRecheckSlaUpdate:
            raise ValueError("updates must contain exact update values")
        require_paper_only_flags("update", update)
        if update.update_id in seen:
            raise ValueError("update_id values must be unique")
        seen.add(update.update_id)
    return tuple(sorted(normalized, key=lambda update: (update.updated_at, update.update_id)))


def _validate_input_times(
    acknowledgements: tuple[ResearchPacketSourceAckRecheckSlaAcknowledgement, ...],
    updates: tuple[ResearchPacketSourceAckRecheckSlaUpdate, ...],
    generated_at: datetime,
) -> None:
    for acknowledgement in acknowledgements:
        if acknowledgement.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at must be <= generated_at")
        if acknowledgement.rechecked_at is not None and acknowledgement.rechecked_at > generated_at:
            raise ValueError("rechecked_at must be <= generated_at")
    for update in updates:
        if update.updated_at > generated_at:
            raise ValueError("updated_at must be <= generated_at")


def _sort_sla_rows(
    rows: tuple[ResearchPacketSourceAckRecheckSlaRow, ...],
) -> tuple[ResearchPacketSourceAckRecheckSlaRow, ...]:
    return tuple(sorted(rows, key=_sla_row_rank))


def _sla_row_rank(
    row: ResearchPacketSourceAckRecheckSlaRow,
) -> tuple[int, Decimal, str, str, datetime, str]:
    return (
        STATUS_RANK[row.status],
        -_count(len(row.reason_codes)),
        row.team_id,
        row.category_id,
        row.acknowledged_at,
        row.acknowledgement_id,
    )


def _normalize_sla_rows(
    rows: Iterable[ResearchPacketSourceAckRecheckSlaRow],
) -> tuple[ResearchPacketSourceAckRecheckSlaRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketSourceAckRecheckSlaRow:
            raise ValueError("rows must contain exact SLA rows")
        require_paper_only_flags("sla row", row)
        if row.acknowledgement_id in seen:
            raise ValueError("rows acknowledgement_id values must be unique")
        seen.add(row.acknowledgement_id)
    expected = _sort_sla_rows(normalized)
    if normalized != expected:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_team_category_rows(
    rows: Iterable[ResearchPacketSourceAckRecheckSlaTeamCategoryRow],
) -> tuple[ResearchPacketSourceAckRecheckSlaTeamCategoryRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("team_category_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("team_category_rows must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketSourceAckRecheckSlaTeamCategoryRow:
            raise ValueError("team_category_rows must contain exact team category rows")
        require_paper_only_flags("team category row", row)
        key = (row.team_id, row.category_id)
        if key in seen:
            raise ValueError("team_category_rows values must be unique")
        seen.add(key)
    expected = tuple(sorted(normalized, key=lambda row: (row.team_id, row.category_id)))
    if normalized != expected:
        raise ValueError("team_category_rows must use deterministic sorting")
    return normalized


def _validate_sla_row(row: ResearchPacketSourceAckRecheckSlaRow) -> None:
    if row.latest_update_id is None:
        if row.latest_update_source_kind is not None or row.latest_update_at is not None:
            raise ValueError("latest update fields must be absent together")
        if row.later_update_count != ZERO_COUNT:
            raise ValueError("later_update_count must be zero without latest update")
        if row.recheck_lag_seconds != ZERO_QUANTIZED:
            raise ValueError("recheck_lag_seconds must be zero without latest update")
    else:
        if row.latest_update_source_kind is None or row.latest_update_at is None:
            raise ValueError("latest update fields must be present together")
        if row.latest_update_at <= row.acknowledged_at:
            raise ValueError("latest_update_at must be later than acknowledged_at")
        if row.later_update_count <= ZERO_COUNT:
            raise ValueError("later_update_count must be positive with latest update")
    if row.overdue_recheck and "source_ack_recheck_overdue" not in row.reason_codes:
        raise ValueError("overdue rows require overdue reason")
    if row.missing_owner and "source_ack_missing_owner" not in row.reason_codes:
        raise ValueError("missing owner rows require missing owner reason")
    if (
        row.contradiction_after_ack
        and "source_ack_contradiction_after_ack" not in row.reason_codes
    ):
        raise ValueError("contradiction rows require contradiction reason")
    if (
        row.repeated_team_category_miss
        and "source_ack_repeated_team_category_miss" not in row.reason_codes
    ):
        raise ValueError("repeated team category rows require repeated miss reason")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_team_category_row(
    row: ResearchPacketSourceAckRecheckSlaTeamCategoryRow,
) -> None:
    if row.missed_acknowledgement_count <= ZERO_COUNT:
        raise ValueError("missed_acknowledgement_count must be positive")
    if row.missed_acknowledgement_count > row.total_acknowledgement_count:
        raise ValueError(
            "missed_acknowledgement_count must not exceed total_acknowledgement_count",
        )
    if row.miss_ratio != _ratio(
        row.missed_acknowledgement_count,
        row.total_acknowledgement_count,
    ):
        raise ValueError("miss_ratio must match miss counts")


def _validate_report(report: ResearchPacketSourceAckRecheckSlaReport) -> None:
    if report.acknowledgement_count != _count(len(report.rows)):
        raise ValueError("acknowledgement_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.overdue_recheck_count != _count(
        sum(1 for row in report.rows if row.overdue_recheck),
    ):
        raise ValueError("overdue_recheck_count must match rows")
    if report.missing_owner_count != _count(
        sum(1 for row in report.rows if row.missing_owner),
    ):
        raise ValueError("missing_owner_count must match rows")
    if report.contradiction_after_ack_count != _count(
        sum(1 for row in report.rows if row.contradiction_after_ack),
    ):
        raise ValueError("contradiction_after_ack_count must match rows")
    if report.repeated_team_category_miss_count != _count(
        len(report.team_category_rows),
    ):
        raise ValueError("repeated_team_category_miss_count must match rows")
    if report.issue_ratio != _ratio(
        _count(sum(1 for row in report.rows if row.status != "pass")),
        report.acknowledgement_count,
    ):
        raise ValueError("issue_ratio must match counts")
    expected_max_age = max(
        (row.acknowledgement_age_seconds for row in report.rows),
        default=ZERO_QUANTIZED,
    )
    if report.max_acknowledgement_age_seconds != expected_max_age:
        raise ValueError("max_acknowledgement_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchPacketSourceAckRecheckSlaRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    _require_nonnegative_count_decimal("numerator", numerator)
    _require_nonnegative_count_decimal("denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_QUANTIZED
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


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


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO_QUANTIZED or quantized > ONE_QUANTIZED:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


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
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(reason_code for reason_code in allowed if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return reason_codes


def _require_source_kind(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_KINDS:
        raise ValueError(f"{field_name} must be official or proxy")


def _require_row_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be empty, clear, watch, or blocked")


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


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_SLA_CONFIG_VERSION",
    "ResearchPacketSourceAckRecheckSlaAcknowledgement",
    "ResearchPacketSourceAckRecheckSlaConfig",
    "ResearchPacketSourceAckRecheckSlaReport",
    "ResearchPacketSourceAckRecheckSlaRow",
    "ResearchPacketSourceAckRecheckSlaTeamCategoryRow",
    "ResearchPacketSourceAckRecheckSlaUpdate",
    "build_research_packet_source_ack_recheck_sla_report",
    "research_packet_source_ack_recheck_sla_report_to_payload",
)
