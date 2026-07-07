"""Pure Phase 1 market-close specialist handoff gate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_TEAM_SPECIALIST_MARKET_CLOSE_HANDOFF_GATE_V2_CONFIG_VERSION = (
    "team-specialist-market-close-handoff-gate-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

GATE_STATUSES = ("blocked", "watch", "pass")
EMPTY_REASON_CODE = "team_specialist_market_close_handoff_gate_v2_empty"

REPORT_REASON_PRIORITY = (
    "team_specialist_market_close_handoff_gate_blocked",
    "team_specialist_market_close_handoff_gate_watch",
    "team_specialist_market_close_handoff_gate_pass",
    "source_freshness_blocked",
    "source_freshness_watch",
    "source_freshness_pass",
    "official_source_coverage_blocked",
    "official_source_coverage_watch",
    "official_source_coverage_pass",
    "unresolved_contradictions_blocked",
    "unresolved_contradictions_watch",
    "unresolved_contradictions_pass",
    "queue_age_blocked",
    "queue_age_watch",
    "queue_age_pass",
    "handoff_completeness_blocked",
    "handoff_completeness_watch",
    "handoff_completeness_pass",
    "reviewer_availability_blocked",
    "reviewer_availability_watch",
    "reviewer_availability_pass",
    EMPTY_REASON_CODE,
)


@dataclass(frozen=True)
class TeamSpecialistMarketCloseHandoffGateV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_MARKET_CLOSE_HANDOFF_GATE_V2_CONFIG_VERSION
    )
    max_pass_source_freshness_minutes: Decimal = Decimal("15.000000")
    max_watch_source_freshness_minutes: Decimal = Decimal("45.000000")
    min_pass_official_source_coverage_ratio: Decimal = Decimal("1.000000")
    min_watch_official_source_coverage_ratio: Decimal = Decimal("0.750000")
    max_pass_unresolved_contradiction_count: Decimal = Decimal("0")
    max_watch_unresolved_contradiction_count: Decimal = Decimal("1")
    max_pass_queue_age_minutes: Decimal = Decimal("10.000000")
    max_watch_queue_age_minutes: Decimal = Decimal("30.000000")
    min_pass_handoff_completeness_ratio: Decimal = Decimal("1.000000")
    min_watch_handoff_completeness_ratio: Decimal = Decimal("0.800000")
    min_pass_available_reviewer_count: Decimal = Decimal("2")
    min_watch_available_reviewer_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_pass_source_freshness_minutes",
            "max_watch_source_freshness_minutes",
            "max_pass_queue_age_minutes",
            "max_watch_queue_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_official_source_coverage_ratio",
            "min_watch_official_source_coverage_ratio",
            "min_pass_handoff_completeness_ratio",
            "min_watch_handoff_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_unresolved_contradiction_count",
            "max_watch_unresolved_contradiction_count",
            "min_pass_available_reviewer_count",
            "min_watch_available_reviewer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamSpecialistMarketCloseHandoffGateV2Input:
    handoff_reference: str
    market_slug: str
    specialist_team: str
    observed_at: datetime
    source_freshness_minutes: Decimal
    official_source_coverage_ratio: Decimal
    unresolved_contradiction_count: Decimal
    queue_age_minutes: Decimal
    handoff_completeness_ratio: Decimal
    available_reviewer_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("handoff_reference", self.handoff_reference)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("specialist_team", self.specialist_team)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in ("source_freshness_minutes", "queue_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_coverage_ratio",
            "handoff_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_contradiction_count",
            "available_reviewer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class TeamSpecialistMarketCloseHandoffGateV2Row:
    redacted_handoff_reference: str
    market_slug: str
    specialist_team: str
    observed_at: datetime
    source_freshness_minutes: Decimal
    official_source_coverage_ratio: Decimal
    unresolved_contradiction_count: Decimal
    queue_age_minutes: Decimal
    handoff_completeness_ratio: Decimal
    available_reviewer_count: Decimal
    gate_status: str
    handoff_permitted: bool
    handoff_digest: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_handoff_reference(self.redacted_handoff_reference)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("specialist_team", self.specialist_team)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in ("source_freshness_minutes", "queue_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_coverage_ratio",
            "handoff_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_contradiction_count",
            "available_reviewer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_bool("handoff_permitted", self.handoff_permitted)
        _require_row_digest("handoff_digest", self.handoff_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class TeamSpecialistMarketCloseHandoffGateV2Report:
    generated_at: datetime
    config_version: str
    handoff_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_source_freshness_minutes: Decimal
    min_official_source_coverage_ratio: Decimal
    max_unresolved_contradiction_count: Decimal
    max_queue_age_minutes: Decimal
    min_handoff_completeness_ratio: Decimal
    min_available_reviewer_count: Decimal
    gate_status: str
    gate_digest: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...]
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
        for field_name in (
            "handoff_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_unresolved_contradiction_count",
            "min_available_reviewer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_source_freshness_minutes",
            "min_official_source_coverage_ratio",
            "max_queue_age_minutes",
            "min_handoff_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_report_digest("gate_digest", self.gate_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_team_specialist_market_close_handoff_gate_v2(
    handoffs: Iterable[object],
    *,
    config: TeamSpecialistMarketCloseHandoffGateV2Config,
    generated_at: datetime,
) -> TeamSpecialistMarketCloseHandoffGateV2Report:
    if type(config) is not TeamSpecialistMarketCloseHandoffGateV2Config:
        raise ValueError("config must be a TeamSpecialistMarketCloseHandoffGateV2Config")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_handoffs = _normalize_handoffs(handoffs)
    rows = tuple(
        sorted(
            (
                _row_from_handoff(
                    handoff,
                    config=config,
                    generated_at=generated_at,
                )
                for handoff in source_handoffs
            ),
            key=_row_sort_key,
        ),
    )
    handoff_count = _count_decimal(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    gate_status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    gate_digest = _report_digest(
        generated_at=generated_at,
        config_version=config.config_version,
        handoff_count=handoff_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        gate_status=gate_status,
        reason_codes=reason_codes,
        rows=rows,
    )
    return TeamSpecialistMarketCloseHandoffGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        handoff_count=handoff_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        max_source_freshness_minutes=_max_row_decimal(rows, "source_freshness_minutes"),
        min_official_source_coverage_ratio=_min_row_decimal(
            rows,
            "official_source_coverage_ratio",
        ),
        max_unresolved_contradiction_count=_max_row_decimal(
            rows,
            "unresolved_contradiction_count",
        ),
        max_queue_age_minutes=_max_row_decimal(rows, "queue_age_minutes"),
        min_handoff_completeness_ratio=_min_row_decimal(
            rows,
            "handoff_completeness_ratio",
        ),
        min_available_reviewer_count=_min_row_decimal(
            rows,
            "available_reviewer_count",
        ),
        gate_status=gate_status,
        gate_digest=gate_digest,
        reason_codes=reason_codes,
        rows=rows,
    )


def team_specialist_market_close_handoff_gate_v2_payload(
    report: TeamSpecialistMarketCloseHandoffGateV2Report,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistMarketCloseHandoffGateV2Report:
        raise ValueError("report must be a TeamSpecialistMarketCloseHandoffGateV2Report")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dictionary")
    return payload


def _row_from_handoff(
    handoff: TeamSpecialistMarketCloseHandoffGateV2Input,
    *,
    config: TeamSpecialistMarketCloseHandoffGateV2Config,
    generated_at: datetime,
) -> TeamSpecialistMarketCloseHandoffGateV2Row:
    if handoff.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gate_status = _handoff_gate_status(handoff, config)
    reason_codes = _row_reason_codes(handoff, config, gate_status)
    redacted_handoff_reference = _redacted_handoff_reference(handoff.handoff_reference)
    handoff_permitted = _handoff_permitted(gate_status)
    handoff_digest = _row_digest(
        redacted_handoff_reference=redacted_handoff_reference,
        market_slug=handoff.market_slug,
        specialist_team=handoff.specialist_team,
        observed_at=handoff.observed_at,
        source_freshness_minutes=handoff.source_freshness_minutes,
        official_source_coverage_ratio=handoff.official_source_coverage_ratio,
        unresolved_contradiction_count=handoff.unresolved_contradiction_count,
        queue_age_minutes=handoff.queue_age_minutes,
        handoff_completeness_ratio=handoff.handoff_completeness_ratio,
        available_reviewer_count=handoff.available_reviewer_count,
        gate_status=gate_status,
        handoff_permitted=handoff_permitted,
        reason_codes=reason_codes,
    )
    return TeamSpecialistMarketCloseHandoffGateV2Row(
        redacted_handoff_reference=redacted_handoff_reference,
        market_slug=handoff.market_slug,
        specialist_team=handoff.specialist_team,
        observed_at=handoff.observed_at,
        source_freshness_minutes=handoff.source_freshness_minutes,
        official_source_coverage_ratio=handoff.official_source_coverage_ratio,
        unresolved_contradiction_count=handoff.unresolved_contradiction_count,
        queue_age_minutes=handoff.queue_age_minutes,
        handoff_completeness_ratio=handoff.handoff_completeness_ratio,
        available_reviewer_count=handoff.available_reviewer_count,
        gate_status=gate_status,
        handoff_permitted=handoff_permitted,
        handoff_digest=handoff_digest,
        reason_codes=reason_codes,
    )


def _handoff_gate_status(
    handoff: TeamSpecialistMarketCloseHandoffGateV2Input,
    config: TeamSpecialistMarketCloseHandoffGateV2Config,
) -> str:
    states = (
        _ceiling_state(
            handoff.source_freshness_minutes,
            passing=config.max_pass_source_freshness_minutes,
            watching=config.max_watch_source_freshness_minutes,
        ),
        _floor_state(
            handoff.official_source_coverage_ratio,
            passing=config.min_pass_official_source_coverage_ratio,
            watching=config.min_watch_official_source_coverage_ratio,
        ),
        _ceiling_state(
            handoff.unresolved_contradiction_count,
            passing=config.max_pass_unresolved_contradiction_count,
            watching=config.max_watch_unresolved_contradiction_count,
        ),
        _ceiling_state(
            handoff.queue_age_minutes,
            passing=config.max_pass_queue_age_minutes,
            watching=config.max_watch_queue_age_minutes,
        ),
        _floor_state(
            handoff.handoff_completeness_ratio,
            passing=config.min_pass_handoff_completeness_ratio,
            watching=config.min_watch_handoff_completeness_ratio,
        ),
        _floor_state(
            handoff.available_reviewer_count,
            passing=config.min_pass_available_reviewer_count,
            watching=config.min_watch_available_reviewer_count,
        ),
    )
    if "blocked" in states:
        return "blocked"
    if "watch" in states:
        return "watch"
    return "pass"


def _row_reason_codes(
    handoff: TeamSpecialistMarketCloseHandoffGateV2Input,
    config: TeamSpecialistMarketCloseHandoffGateV2Config,
    gate_status: str,
) -> tuple[str, ...]:
    reason_codes = [
        *handoff.reason_codes,
        f"team_specialist_market_close_handoff_gate_{gate_status}",
        _dimension_reason_code(
            "source_freshness",
            _ceiling_state(
                handoff.source_freshness_minutes,
                passing=config.max_pass_source_freshness_minutes,
                watching=config.max_watch_source_freshness_minutes,
            ),
        ),
        _dimension_reason_code(
            "official_source_coverage",
            _floor_state(
                handoff.official_source_coverage_ratio,
                passing=config.min_pass_official_source_coverage_ratio,
                watching=config.min_watch_official_source_coverage_ratio,
            ),
        ),
        _dimension_reason_code(
            "unresolved_contradictions",
            _ceiling_state(
                handoff.unresolved_contradiction_count,
                passing=config.max_pass_unresolved_contradiction_count,
                watching=config.max_watch_unresolved_contradiction_count,
            ),
        ),
        _dimension_reason_code(
            "queue_age",
            _ceiling_state(
                handoff.queue_age_minutes,
                passing=config.max_pass_queue_age_minutes,
                watching=config.max_watch_queue_age_minutes,
            ),
        ),
        _dimension_reason_code(
            "handoff_completeness",
            _floor_state(
                handoff.handoff_completeness_ratio,
                passing=config.min_pass_handoff_completeness_ratio,
                watching=config.min_watch_handoff_completeness_ratio,
            ),
        ),
        _dimension_reason_code(
            "reviewer_availability",
            _floor_state(
                handoff.available_reviewer_count,
                passing=config.min_pass_available_reviewer_count,
                watching=config.min_watch_available_reviewer_count,
            ),
        ),
    ]
    return _unique_reason_codes(tuple(reason_codes))


def _dimension_reason_code(prefix: str, state: str) -> str:
    return f"{prefix}_{state}"


def _ceiling_state(value: Decimal, *, passing: Decimal, watching: Decimal) -> str:
    if value <= passing:
        return "pass"
    if value <= watching:
        return "watch"
    return "blocked"


def _floor_state(value: Decimal, *, passing: Decimal, watching: Decimal) -> str:
    if value >= passing:
        return "pass"
    if value >= watching:
        return "watch"
    return "blocked"


def _handoff_permitted(gate_status: str) -> bool:
    return gate_status == "pass"


def _normalize_handoffs(
    handoffs: Iterable[object],
) -> tuple[TeamSpecialistMarketCloseHandoffGateV2Input, ...]:
    if isinstance(handoffs, (str, bytes)):
        raise ValueError("handoffs must be an iterable")
    try:
        rows = tuple(handoffs)
    except TypeError as exc:
        raise ValueError("handoffs must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[TeamSpecialistMarketCloseHandoffGateV2Input] = []
    for row in rows:
        if type(row) is not TeamSpecialistMarketCloseHandoffGateV2Input:
            raise ValueError(
                "handoffs must contain TeamSpecialistMarketCloseHandoffGateV2Input",
            )
        _require_hard_flags("input", row)
        if row.handoff_reference in seen:
            raise ValueError("duplicate handoff_reference")
        seen.add(row.handoff_reference)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamSpecialistMarketCloseHandoffGateV2Row:
            raise ValueError("rows must contain TeamSpecialistMarketCloseHandoffGateV2Row")
        _require_hard_flags("row", row)
    return rows


def _row_sort_key(row: TeamSpecialistMarketCloseHandoffGateV2Row) -> tuple[str, str]:
    return (row.market_slug, row.redacted_handoff_reference)


def _status_count(
    rows: tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.gate_status == status))


def _max_row_decimal(
    rows: tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _report_status(
    rows: tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...],
) -> str:
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    prioritized = tuple(code for code in REPORT_REASON_PRIORITY if code in observed)
    extras = tuple(sorted(code for code in observed if code not in prioritized))
    return (*prioritized, *extras)


def _validate_config(config: TeamSpecialistMarketCloseHandoffGateV2Config) -> None:
    if config.max_pass_source_freshness_minutes > config.max_watch_source_freshness_minutes:
        raise ValueError(
            "max_pass_source_freshness_minutes must not exceed "
            "max_watch_source_freshness_minutes",
        )
    if config.max_pass_queue_age_minutes > config.max_watch_queue_age_minutes:
        raise ValueError(
            "max_pass_queue_age_minutes must not exceed max_watch_queue_age_minutes",
        )
    if (
        config.max_pass_unresolved_contradiction_count
        > config.max_watch_unresolved_contradiction_count
    ):
        raise ValueError(
            "max_pass_unresolved_contradiction_count must not exceed "
            "max_watch_unresolved_contradiction_count",
        )
    if (
        config.min_watch_official_source_coverage_ratio
        > config.min_pass_official_source_coverage_ratio
    ):
        raise ValueError(
            "min_watch_official_source_coverage_ratio must not exceed "
            "min_pass_official_source_coverage_ratio",
        )
    if (
        config.min_watch_handoff_completeness_ratio
        > config.min_pass_handoff_completeness_ratio
    ):
        raise ValueError(
            "min_watch_handoff_completeness_ratio must not exceed "
            "min_pass_handoff_completeness_ratio",
        )
    if config.min_watch_available_reviewer_count > config.min_pass_available_reviewer_count:
        raise ValueError(
            "min_watch_available_reviewer_count must not exceed "
            "min_pass_available_reviewer_count",
        )


def _validate_row(row: TeamSpecialistMarketCloseHandoffGateV2Row) -> None:
    expected_status = _row_status_from_reason_codes(row.reason_codes)
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    if row.handoff_permitted is not _handoff_permitted(row.gate_status):
        raise ValueError("handoff_permitted must match gate_status")
    if row.handoff_digest != _row_digest_from_row(row):
        raise ValueError("handoff_digest must match row inputs")


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "team_specialist_market_close_handoff_gate_blocked" in reason_codes:
        return "blocked"
    if "team_specialist_market_close_handoff_gate_watch" in reason_codes:
        return "watch"
    if "team_specialist_market_close_handoff_gate_pass" in reason_codes:
        return "pass"
    raise ValueError("reason_codes must include handoff gate status")


def _validate_report(report: TeamSpecialistMarketCloseHandoffGateV2Report) -> None:
    if report.handoff_count != _count_decimal(len(report.rows)):
        raise ValueError("handoff_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.max_source_freshness_minutes != _max_row_decimal(
        report.rows,
        "source_freshness_minutes",
    ):
        raise ValueError("max_source_freshness_minutes must match rows")
    if report.min_official_source_coverage_ratio != _min_row_decimal(
        report.rows,
        "official_source_coverage_ratio",
    ):
        raise ValueError("min_official_source_coverage_ratio must match rows")
    if report.max_unresolved_contradiction_count != _max_row_decimal(
        report.rows,
        "unresolved_contradiction_count",
    ):
        raise ValueError("max_unresolved_contradiction_count must match rows")
    if report.max_queue_age_minutes != _max_row_decimal(report.rows, "queue_age_minutes"):
        raise ValueError("max_queue_age_minutes must match rows")
    if report.min_handoff_completeness_ratio != _min_row_decimal(
        report.rows,
        "handoff_completeness_ratio",
    ):
        raise ValueError("min_handoff_completeness_ratio must match rows")
    if report.min_available_reviewer_count != _min_row_decimal(
        report.rows,
        "available_reviewer_count",
    ):
        raise ValueError("min_available_reviewer_count must match rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.gate_digest != _report_digest_from_report(report):
        raise ValueError("gate_digest must match report inputs")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in values:
        raise ValueError(f"{field_name} must be one of {values}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _unique_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return _normalize_reason_codes(tuple(unique), require_nonempty=True)


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _redacted_handoff_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"handoff_ref_{digest}"


def _require_redacted_handoff_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("redacted_handoff_reference must be a string")
    prefix = "handoff_ref_"
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 16
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError("redacted_handoff_reference must be redacted")


def _require_row_digest(field_name: str, value: object) -> None:
    _require_prefixed_digest(field_name, value, "market_close_handoff_row_digest_")


def _require_report_digest(field_name: str, value: object) -> None:
    _require_prefixed_digest(field_name, value, "market_close_handoff_report_digest_")


def _require_prefixed_digest(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest")
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 16
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError(f"{field_name} must be a digest")


def _row_digest_from_row(row: TeamSpecialistMarketCloseHandoffGateV2Row) -> str:
    return _row_digest(
        redacted_handoff_reference=row.redacted_handoff_reference,
        market_slug=row.market_slug,
        specialist_team=row.specialist_team,
        observed_at=row.observed_at,
        source_freshness_minutes=row.source_freshness_minutes,
        official_source_coverage_ratio=row.official_source_coverage_ratio,
        unresolved_contradiction_count=row.unresolved_contradiction_count,
        queue_age_minutes=row.queue_age_minutes,
        handoff_completeness_ratio=row.handoff_completeness_ratio,
        available_reviewer_count=row.available_reviewer_count,
        gate_status=row.gate_status,
        handoff_permitted=row.handoff_permitted,
        reason_codes=row.reason_codes,
    )


def _row_digest(
    *,
    redacted_handoff_reference: str,
    market_slug: str,
    specialist_team: str,
    observed_at: datetime,
    source_freshness_minutes: Decimal,
    official_source_coverage_ratio: Decimal,
    unresolved_contradiction_count: Decimal,
    queue_age_minutes: Decimal,
    handoff_completeness_ratio: Decimal,
    available_reviewer_count: Decimal,
    gate_status: str,
    handoff_permitted: bool,
    reason_codes: tuple[str, ...],
) -> str:
    parts = (
        redacted_handoff_reference,
        market_slug,
        specialist_team,
        _as_utc("observed_at", observed_at).isoformat(),
        str(source_freshness_minutes),
        str(official_source_coverage_ratio),
        str(unresolved_contradiction_count),
        str(queue_age_minutes),
        str(handoff_completeness_ratio),
        str(available_reviewer_count),
        gate_status,
        str(handoff_permitted),
        ",".join(reason_codes),
    )
    return f"market_close_handoff_row_digest_{_digest(parts)}"


def _report_digest_from_report(report: TeamSpecialistMarketCloseHandoffGateV2Report) -> str:
    return _report_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        handoff_count=report.handoff_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        gate_status=report.gate_status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _report_digest(
    *,
    generated_at: datetime,
    config_version: str,
    handoff_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    gate_status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[TeamSpecialistMarketCloseHandoffGateV2Row, ...],
) -> str:
    parts = (
        _as_utc("generated_at", generated_at).isoformat(),
        config_version,
        str(handoff_count),
        str(pass_count),
        str(watch_count),
        str(blocked_count),
        gate_status,
        ",".join(reason_codes),
        ",".join(row.handoff_digest for row in rows),
    )
    return f"market_close_handoff_report_digest_{_digest(parts)}"


def _digest(parts: tuple[str, ...]) -> str:
    payload = "\x1f".join(parts)
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(type(value).__name__, value)
        return _payload_mapping(vars(value))
    if type(value) is dict:
        return _payload_mapping(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not serializable")


def _payload_mapping(value: dict[Any, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
        if key.startswith("_"):
            continue
        payload[key] = _payload_value(item)
    return payload


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_MARKET_CLOSE_HANDOFF_GATE_V2_CONFIG_VERSION",
    "TeamSpecialistMarketCloseHandoffGateV2Config",
    "TeamSpecialistMarketCloseHandoffGateV2Input",
    "TeamSpecialistMarketCloseHandoffGateV2Report",
    "TeamSpecialistMarketCloseHandoffGateV2Row",
    "build_team_specialist_market_close_handoff_gate_v2",
    "team_specialist_market_close_handoff_gate_v2_payload",
)
