"""Pure report-only prioritization for team/domain market watchlists."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_TEAM_DOMAIN_WATCHLIST_PRIORITIZATION_REPORT_CONFIG_VERSION = (
    "team-domain-watchlist-prioritization-report-v1"
)
TEAM_DOMAIN_WATCHLIST_PRIORITY_BANDS = ("ready", "watch", "defer")
TEAM_DOMAIN_WATCHLIST_DOMAINS = (
    "politics",
    "crypto",
    "equities",
    "gold",
    "soccer",
    "basketball",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_DOMAIN_INDEX = {domain: index for index, domain in enumerate(TEAM_DOMAIN_WATCHLIST_DOMAINS)}
_BAND_INDEX = {band: index for index, band in enumerate(TEAM_DOMAIN_WATCHLIST_PRIORITY_BANDS)}
_DIGEST_LENGTH = 64
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "@",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "access_token",
    "bearer ",
    "ord" + "er",
    "tra" + "de",
    "exec" + "ution",
    "event_" + "id",
    "market_" + "id",
    "market_" + "slug",
    "source_" + "id",
    "source_" + "url",
    "source_" + "name",
    "source_" + "text",
    "raw_" + "source",
    "net" + "work",
    "req" + "uests",
    "url" + "lib",
    "sock" + "et",
    "sql" + "ite",
    "reco" + "mmend",
    "siz" + "ing",
)
_CANDIDATE_SCORE_FIELDS = (
    "information_freshness",
    "source_quorum",
    "edge_to_threshold",
    "liquidity",
    "cost_burden",
    "settlement_timing",
    "team_memory_calibration_readiness",
)
_ROW_REASON_CODES = frozenset(
    (
        "watchlist_candidate_ready",
        "information_freshness_watch",
        "information_freshness_block",
        "source_quorum_watch",
        "source_quorum_block",
        "edge_to_threshold_watch",
        "edge_to_threshold_block",
        "liquidity_watch",
        "liquidity_block",
        "cost_burden_watch",
        "cost_burden_block",
        "settlement_timing_watch",
        "settlement_timing_block",
        "team_memory_calibration_readiness_watch",
        "team_memory_calibration_readiness_block",
    ),
)
_REPORT_REASON_CODES = frozenset(
    (
        "team_domain_watchlist_prioritization_clear",
        "team_domain_watchlist_prioritization_watch",
        "team_domain_watchlist_prioritization_block",
        "candidate_watch_present",
        "candidate_defer_present",
    ),
)
_ALL_REASON_CODES = _ROW_REASON_CODES | _REPORT_REASON_CODES


@dataclass(frozen=True)
class TeamDomainWatchlistPrioritizationConfig:
    config_version: str = DEFAULT_TEAM_DOMAIN_WATCHLIST_PRIORITIZATION_REPORT_CONFIG_VERSION
    ready_priority_score: Decimal = Decimal("0.800000")
    watch_priority_score: Decimal = Decimal("0.550000")
    freshness_block_floor: Decimal = Decimal("0.500000")
    source_quorum_block_floor: Decimal = Decimal("0.500000")
    edge_to_threshold_block_floor: Decimal = Decimal("0.500000")
    liquidity_block_floor: Decimal = Decimal("0.500000")
    cost_burden_block_ceiling: Decimal = Decimal("0.800000")
    settlement_timing_block_floor: Decimal = Decimal("0.500000")
    team_memory_calibration_readiness_block_floor: Decimal = Decimal("0.500000")
    freshness_watch_floor: Decimal = Decimal("0.750000")
    source_quorum_watch_floor: Decimal = Decimal("0.750000")
    edge_to_threshold_watch_floor: Decimal = Decimal("0.700000")
    liquidity_watch_floor: Decimal = Decimal("0.700000")
    cost_burden_watch_ceiling: Decimal = Decimal("0.350000")
    settlement_timing_watch_floor: Decimal = Decimal("0.700000")
    team_memory_calibration_readiness_watch_floor: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamDomainWatchlistPrioritizationConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "ready_priority_score",
            "watch_priority_score",
            "freshness_block_floor",
            "source_quorum_block_floor",
            "edge_to_threshold_block_floor",
            "liquidity_block_floor",
            "cost_burden_block_ceiling",
            "settlement_timing_block_floor",
            "team_memory_calibration_readiness_block_floor",
            "freshness_watch_floor",
            "source_quorum_watch_floor",
            "edge_to_threshold_watch_floor",
            "liquidity_watch_floor",
            "cost_burden_watch_ceiling",
            "settlement_timing_watch_floor",
            "team_memory_calibration_readiness_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_priority_score > self.ready_priority_score:
            raise ValueError("watch_priority_score must not exceed ready_priority_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamDomainWatchlistPrioritizationCandidate:
    candidate_ref: str
    team_code: str
    domain: str
    information_freshness: Decimal
    source_quorum: Decimal
    edge_to_threshold: Decimal
    liquidity: Decimal
    cost_burden: Decimal
    settlement_timing: Decimal
    team_memory_calibration_readiness: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamDomainWatchlistPrioritizationCandidate, "candidate")
        _require_public_code("candidate_ref", self.candidate_ref)
        _require_public_code("team_code", self.team_code)
        _require_domain(self.domain)
        for field_name in _CANDIDATE_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class TeamDomainWatchlistPrioritizationRow:
    priority_rank: Decimal
    candidate_ref: str
    team_code: str
    domain: str
    information_freshness: Decimal
    source_quorum: Decimal
    edge_to_threshold: Decimal
    liquidity: Decimal
    cost_burden: Decimal
    settlement_timing: Decimal
    team_memory_calibration_readiness: Decimal
    priority_score: Decimal
    priority_band: str
    top_blockers: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamDomainWatchlistPrioritizationRow, "row")
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        _require_public_code("candidate_ref", self.candidate_ref)
        _require_public_code("team_code", self.team_code)
        _require_domain(self.domain)
        for field_name in _CANDIDATE_SCORE_FIELDS + ("priority_score",):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_priority_band("priority_band", self.priority_band)
        object.__setattr__(
            self,
            "top_blockers",
            _normalize_reason_codes("top_blockers", self.top_blockers, _ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class TeamDomainWatchlistPrioritizationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamDomainWatchlistPrioritizationReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, _ALL_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class TeamDomainWatchlistPrioritizationReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    defer_count: Decimal
    average_priority_score: Decimal
    max_priority_score: Decimal
    min_priority_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamDomainWatchlistPrioritizationRow, ...]
    reason_code_counts: tuple[TeamDomainWatchlistPrioritizationReasonCodeCount, ...]
    input_candidates: tuple[TeamDomainWatchlistPrioritizationCandidate, ...]
    validation_digest: str
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamDomainWatchlistPrioritizationReport, "report")
        object.__setattr__(self, "generated_at", _normalize_datetime(self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "defer_count",
            "average_priority_score",
            "max_priority_score",
            "min_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "rows",
            _normalize_tuple_of_exact_type(
                "rows",
                self.rows,
                TeamDomainWatchlistPrioritizationRow,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_tuple_of_exact_type(
                "reason_code_counts",
                self.reason_code_counts,
                TeamDomainWatchlistPrioritizationReasonCodeCount,
            ),
        )
        object.__setattr__(
            self,
            "input_candidates",
            _normalize_tuple_of_exact_type(
                "input_candidates",
                self.input_candidates,
                TeamDomainWatchlistPrioritizationCandidate,
            ),
        )
        _require_sha256_digest("validation_digest", self.validation_digest)
        if type(self.payload) is not dict:
            raise ValueError("payload must be a plain dict")
        _require_hard_flags("report", self)


def build_team_domain_watchlist_prioritization_report(
    candidates: tuple[TeamDomainWatchlistPrioritizationCandidate, ...] | list[Any] | Any,
    *,
    config: TeamDomainWatchlistPrioritizationConfig | None = None,
    generated_at: datetime | None = None,
) -> TeamDomainWatchlistPrioritizationReport:
    selected_config = config if config is not None else TeamDomainWatchlistPrioritizationConfig()
    _require_exact_type(selected_config, TeamDomainWatchlistPrioritizationConfig, "config")
    normalized_candidates = _normalize_tuple_of_exact_type(
        "candidates",
        candidates,
        TeamDomainWatchlistPrioritizationCandidate,
    )
    rows = _build_rows(normalized_candidates, selected_config)
    report_values = _report_values_for_rows(
        rows,
        normalized_candidates,
        selected_config,
        _normalize_datetime(generated_at if generated_at is not None else datetime.now(UTC)),
    )
    digest = _validation_digest(report_values)
    payload = _payload_from_report_values(report_values, digest)
    return TeamDomainWatchlistPrioritizationReport(
        **report_values,
        validation_digest=digest,
        payload=payload,
    )


def team_domain_watchlist_prioritization_report_payload(
    report: TeamDomainWatchlistPrioritizationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_nested_payload_objects(report)
        _validate_payload_schema(report)
        expected_digest = _validation_digest(_report_values_from_payload(report))
        if report["validation_digest"] != expected_digest:
            raise ValueError("validation_digest mismatch for candidate_count or payload fields")
        _require_hard_flags("payload", report)
        return dict(report)
    _require_exact_type(report, TeamDomainWatchlistPrioritizationReport, "report")
    expected_digest = _validation_digest(_report_values_from_report(report))
    if report.validation_digest != expected_digest:
        raise ValueError("validation_digest mismatch for report")
    expected_payload = _payload_from_report_values(
        _report_values_from_report(report),
        report.validation_digest,
    )
    if report.payload != expected_payload:
        raise ValueError("payload mismatch for report")
    _require_hard_flags("report", report)
    return dict(expected_payload)


def validate_team_domain_watchlist_prioritization_report_payload(
    payload: dict[str, Any],
) -> bool:
    team_domain_watchlist_prioritization_report_payload(payload)
    return True


def _build_rows(
    candidates: tuple[TeamDomainWatchlistPrioritizationCandidate, ...],
    config: TeamDomainWatchlistPrioritizationConfig,
) -> tuple[TeamDomainWatchlistPrioritizationRow, ...]:
    scored = tuple(_row_value_for_candidate(candidate, config) for candidate in candidates)
    sorted_rows = sorted(
        scored,
        key=lambda item: (
            _BAND_INDEX[item["priority_band"]],
            -item["priority_score"],
            item["team_code"],
            _DOMAIN_INDEX[item["domain"]],
            item["candidate_ref"],
        ),
    )
    return tuple(
        TeamDomainWatchlistPrioritizationRow(
            **dict(values, priority_rank=_decimal_count(index)),
        )
        for index, values in enumerate(sorted_rows, start=1)
    )


def _row_value_for_candidate(
    candidate: TeamDomainWatchlistPrioritizationCandidate,
    config: TeamDomainWatchlistPrioritizationConfig,
) -> dict[str, Any]:
    priority_score = _priority_score(candidate)
    top_blockers = _top_blockers(candidate, config)
    if priority_score >= config.ready_priority_score and top_blockers == (
        "watchlist_candidate_ready",
    ):
        priority_band = "ready"
    elif priority_score >= config.watch_priority_score and not any(
        reason.endswith("_block") for reason in top_blockers
    ):
        priority_band = "watch"
    else:
        priority_band = "defer"
    return {
        "candidate_ref": candidate.candidate_ref,
        "team_code": candidate.team_code,
        "domain": candidate.domain,
        "information_freshness": candidate.information_freshness,
        "source_quorum": candidate.source_quorum,
        "edge_to_threshold": candidate.edge_to_threshold,
        "liquidity": candidate.liquidity,
        "cost_burden": candidate.cost_burden,
        "settlement_timing": candidate.settlement_timing,
        "team_memory_calibration_readiness": (
            candidate.team_memory_calibration_readiness
        ),
        "priority_score": priority_score,
        "priority_band": priority_band,
        "top_blockers": top_blockers,
    }


def _priority_score(candidate: TeamDomainWatchlistPrioritizationCandidate) -> Decimal:
    cost_readiness = ONE - candidate.cost_burden
    weighted_total = (
        candidate.information_freshness * Decimal("0.180000")
        + candidate.source_quorum * Decimal("0.170000")
        + candidate.edge_to_threshold * Decimal("0.170000")
        + candidate.liquidity * Decimal("0.160000")
        + cost_readiness * Decimal("0.120000")
        + candidate.settlement_timing * Decimal("0.090000")
        + candidate.team_memory_calibration_readiness * Decimal("0.110000")
    )
    return _quantize(weighted_total)


def _top_blockers(
    candidate: TeamDomainWatchlistPrioritizationCandidate,
    config: TeamDomainWatchlistPrioritizationConfig,
) -> tuple[str, ...]:
    blocker_candidates = (
        _blocker_for_floor(
            "information_freshness",
            candidate.information_freshness,
            config.freshness_block_floor,
            config.freshness_watch_floor,
        ),
        _blocker_for_floor(
            "source_quorum",
            candidate.source_quorum,
            config.source_quorum_block_floor,
            config.source_quorum_watch_floor,
        ),
        _blocker_for_floor(
            "edge_to_threshold",
            candidate.edge_to_threshold,
            config.edge_to_threshold_block_floor,
            config.edge_to_threshold_watch_floor,
        ),
        _blocker_for_floor(
            "liquidity",
            candidate.liquidity,
            config.liquidity_block_floor,
            config.liquidity_watch_floor,
        ),
        _blocker_for_ceiling(
            "cost_burden",
            candidate.cost_burden,
            config.cost_burden_block_ceiling,
            config.cost_burden_watch_ceiling,
        ),
        _blocker_for_floor(
            "settlement_timing",
            candidate.settlement_timing,
            config.settlement_timing_block_floor,
            config.settlement_timing_watch_floor,
        ),
        _blocker_for_floor(
            "team_memory_calibration_readiness",
            candidate.team_memory_calibration_readiness,
            config.team_memory_calibration_readiness_block_floor,
            config.team_memory_calibration_readiness_watch_floor,
        ),
    )
    blockers = tuple(sorted(
        (item for item in blocker_candidates if item is not None),
        key=lambda item: (-item[1], -item[2], item[0]),
    ))
    if not blockers:
        return ("watchlist_candidate_ready",)
    return tuple(reason for reason, _, _ in blockers[:3])


def _blocker_for_floor(
    prefix: str,
    value: Decimal,
    block_floor: Decimal,
    watch_floor: Decimal,
) -> tuple[str, Decimal, Decimal] | None:
    if value < block_floor:
        return (f"{prefix}_block", Decimal("1.000000"), block_floor - value)
    if value < watch_floor:
        return (f"{prefix}_watch", ZERO, watch_floor - value)
    return None


def _blocker_for_ceiling(
    prefix: str,
    value: Decimal,
    block_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> tuple[str, Decimal, Decimal] | None:
    if value >= block_ceiling:
        return (f"{prefix}_block", Decimal("1.000000"), value - block_ceiling)
    if value > watch_ceiling:
        return (f"{prefix}_watch", ZERO, value - watch_ceiling)
    return None


def _report_values_for_rows(
    rows: tuple[TeamDomainWatchlistPrioritizationRow, ...],
    candidates: tuple[TeamDomainWatchlistPrioritizationCandidate, ...],
    config: TeamDomainWatchlistPrioritizationConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    ready_count = _decimal_count(
        sum(1 for row in rows if row.priority_band == "ready"),
    )
    watch_count = _decimal_count(
        sum(1 for row in rows if row.priority_band == "watch"),
    )
    defer_count = _decimal_count(
        sum(1 for row in rows if row.priority_band == "defer"),
    )
    candidate_count = _decimal_count(len(rows))
    priority_scores = tuple(row.priority_score for row in rows)
    reason_codes = _report_reason_codes(watch_count, defer_count)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    return {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "candidate_count": candidate_count,
        "ready_count": ready_count,
        "watch_count": watch_count,
        "defer_count": defer_count,
        "average_priority_score": _average(priority_scores),
        "max_priority_score": max(priority_scores) if priority_scores else ZERO,
        "min_priority_score": min(priority_scores) if priority_scores else ZERO,
        "report_status": _report_status(watch_count, defer_count),
        "reason_codes": reason_codes,
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "input_candidates": tuple(
            sorted(
                candidates,
                key=lambda item: (
                    item.team_code,
                    _DOMAIN_INDEX[item.domain],
                    item.candidate_ref,
                ),
            ),
        ),
    }


def _report_reason_codes(watch_count: Decimal, defer_count: Decimal) -> tuple[str, ...]:
    if defer_count > ZERO:
        return (
            "team_domain_watchlist_prioritization_block",
            "candidate_defer_present",
        )
    if watch_count > ZERO:
        return (
            "team_domain_watchlist_prioritization_watch",
            "candidate_watch_present",
        )
    return ("team_domain_watchlist_prioritization_clear",)


def _report_status(watch_count: Decimal, defer_count: Decimal) -> str:
    if defer_count > ZERO:
        return "block"
    if watch_count > ZERO:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[TeamDomainWatchlistPrioritizationRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[TeamDomainWatchlistPrioritizationReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in report_reason_codes:
        counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    for row in rows:
        for reason_code in row.top_blockers:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        TeamDomainWatchlistPrioritizationReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in sorted(counts)
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _payload_from_report_values(
    values: dict[str, Any],
    validation_digest: str,
) -> dict[str, Any]:
    return {
        "generated_at": values["generated_at"].isoformat(),
        "config_version": values["config_version"],
        "candidate_count": _decimal_to_str(values["candidate_count"]),
        "ready_count": _decimal_to_str(values["ready_count"]),
        "watch_count": _decimal_to_str(values["watch_count"]),
        "defer_count": _decimal_to_str(values["defer_count"]),
        "average_priority_score": _decimal_to_str(values["average_priority_score"]),
        "max_priority_score": _decimal_to_str(values["max_priority_score"]),
        "min_priority_score": _decimal_to_str(values["min_priority_score"]),
        "report_status": values["report_status"],
        "reason_codes": list(values["reason_codes"]),
        "rows": [_payload_from_row(row) for row in values["rows"]],
        "reason_code_counts": [
            _payload_from_reason_count(item) for item in values["reason_code_counts"]
        ],
        "validation_digest": validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_from_row(row: TeamDomainWatchlistPrioritizationRow) -> dict[str, Any]:
    return {
        "priority_rank": _decimal_to_str(row.priority_rank),
        "candidate_ref": row.candidate_ref,
        "team_code": row.team_code,
        "domain": row.domain,
        "information_freshness": _decimal_to_str(row.information_freshness),
        "source_quorum": _decimal_to_str(row.source_quorum),
        "edge_to_threshold": _decimal_to_str(row.edge_to_threshold),
        "liquidity": _decimal_to_str(row.liquidity),
        "cost_burden": _decimal_to_str(row.cost_burden),
        "settlement_timing": _decimal_to_str(row.settlement_timing),
        "team_memory_calibration_readiness": _decimal_to_str(
            row.team_memory_calibration_readiness,
        ),
        "priority_score": _decimal_to_str(row.priority_score),
        "priority_band": row.priority_band,
        "top_blockers": list(row.top_blockers),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_from_reason_count(
    item: TeamDomainWatchlistPrioritizationReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_to_str(item.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_values_from_report(
    report: TeamDomainWatchlistPrioritizationReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "ready_count": report.ready_count,
        "watch_count": report.watch_count,
        "defer_count": report.defer_count,
        "average_priority_score": report.average_priority_score,
        "max_priority_score": report.max_priority_score,
        "min_priority_score": report.min_priority_score,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "input_candidates": report.input_candidates,
    }


def _report_values_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": _parse_datetime(payload["generated_at"]),
        "config_version": payload["config_version"],
        "candidate_count": _parse_decimal_payload("candidate_count", payload),
        "ready_count": _parse_decimal_payload("ready_count", payload),
        "watch_count": _parse_decimal_payload("watch_count", payload),
        "defer_count": _parse_decimal_payload("defer_count", payload),
        "average_priority_score": _parse_decimal_payload("average_priority_score", payload),
        "max_priority_score": _parse_decimal_payload("max_priority_score", payload),
        "min_priority_score": _parse_decimal_payload("min_priority_score", payload),
        "report_status": payload["report_status"],
        "reason_codes": tuple(payload["reason_codes"]),
        "rows": tuple(_row_from_payload(item) for item in payload["rows"]),
        "reason_code_counts": tuple(
            _reason_count_from_payload(item) for item in payload["reason_code_counts"]
        ),
        "input_candidates": (),
    }


def _row_from_payload(payload: dict[str, Any]) -> TeamDomainWatchlistPrioritizationRow:
    if type(payload) is not dict:
        raise ValueError("row payload must be a plain dict")
    return TeamDomainWatchlistPrioritizationRow(
        priority_rank=_parse_decimal_payload("priority_rank", payload),
        candidate_ref=payload["candidate_ref"],
        team_code=payload["team_code"],
        domain=payload["domain"],
        information_freshness=_parse_decimal_payload("information_freshness", payload),
        source_quorum=_parse_decimal_payload("source_quorum", payload),
        edge_to_threshold=_parse_decimal_payload("edge_to_threshold", payload),
        liquidity=_parse_decimal_payload("liquidity", payload),
        cost_burden=_parse_decimal_payload("cost_burden", payload),
        settlement_timing=_parse_decimal_payload("settlement_timing", payload),
        team_memory_calibration_readiness=_parse_decimal_payload(
            "team_memory_calibration_readiness",
            payload,
        ),
        priority_score=_parse_decimal_payload("priority_score", payload),
        priority_band=payload["priority_band"],
        top_blockers=tuple(payload["top_blockers"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _reason_count_from_payload(
    payload: dict[str, Any],
) -> TeamDomainWatchlistPrioritizationReasonCodeCount:
    if type(payload) is not dict:
        raise ValueError("reason_code_count payload must be a plain dict")
    return TeamDomainWatchlistPrioritizationReasonCodeCount(
        reason_code=payload["reason_code"],
        count=_parse_decimal_payload("count", payload),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _validation_digest(values: dict[str, Any]) -> str:
    canonical = {
        "generated_at": values["generated_at"].isoformat(),
        "config_version": values["config_version"],
        "candidate_count": _decimal_to_str(values["candidate_count"]),
        "ready_count": _decimal_to_str(values["ready_count"]),
        "watch_count": _decimal_to_str(values["watch_count"]),
        "defer_count": _decimal_to_str(values["defer_count"]),
        "average_priority_score": _decimal_to_str(values["average_priority_score"]),
        "max_priority_score": _decimal_to_str(values["max_priority_score"]),
        "min_priority_score": _decimal_to_str(values["min_priority_score"]),
        "report_status": values["report_status"],
        "reason_codes": list(values["reason_codes"]),
        "rows": [_payload_from_row(row) for row in values["rows"]],
        "reason_code_counts": [
            _payload_from_reason_count(item) for item in values["reason_code_counts"]
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    required_keys = {
        "generated_at",
        "config_version",
        "candidate_count",
        "ready_count",
        "watch_count",
        "defer_count",
        "average_priority_score",
        "max_priority_score",
        "min_priority_score",
        "report_status",
        "reason_codes",
        "rows",
        "reason_code_counts",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != required_keys:
        raise ValueError("payload schema keys are required")
    if type(payload["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    if type(payload["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    _require_sha256_digest("validation_digest", payload["validation_digest"])


def _reject_nested_payload_objects(value: Any) -> None:
    if type(value) in (dict, list, tuple, str, bool) or value is None:
        children: tuple[Any, ...]
        if type(value) is dict:
            children = tuple(value.values())
        elif type(value) in (list, tuple):
            children = tuple(value)
        else:
            children = ()
        for child in children:
            _reject_nested_payload_objects(child)
        return
    raise ValueError("payload must contain plain JSON-ready values and Decimal strings")


def _require_exact_type(value: object, expected_type: type[Any], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if value != DEFAULT_TEAM_DOMAIN_WATCHLIST_PRIORITIZATION_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_text(field_name, value)
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    return value


def _require_domain(value: object) -> str:
    if type(value) is not str or value not in _DOMAIN_INDEX:
        raise ValueError("domain must be supported")
    return value


def _require_priority_band(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _BAND_INDEX:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_report_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in ("pass", "watch", "block"):
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_reason_codes: frozenset[str],
) -> str:
    if type(value) is not str or value not in allowed_reason_codes:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: frozenset[str],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    return tuple(
        _require_reason_code(field_name, reason_code, allowed_reason_codes)
        for reason_code in value
    )


def _normalize_tuple_of_exact_type(
    field_name: str,
    value: Any,
    expected_type: type[Any],
) -> tuple[Any, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    result = tuple(value)
    for item in result:
        _require_exact_type(item, expected_type, field_name)
    return result


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_to_str(value: Decimal) -> str:
    return f"{_quantize(value):.6f}"


def _parse_decimal_payload(field_name: str, payload: dict[str, Any]) -> Decimal:
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return _require_decimal(field_name, Decimal(value))
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _normalize_datetime(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _parse_datetime(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError("generated_at must be an ISO datetime string")
    return _normalize_datetime(datetime.fromisoformat(value))


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != _DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if _flag_value(value, flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _flag_value(value: object, flag_name: str) -> object:
    if type(value) is dict:
        return value.get(flag_name)
    return getattr(value, flag_name)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} must be public-safe")


__all__ = (
    "DEFAULT_TEAM_DOMAIN_WATCHLIST_PRIORITIZATION_REPORT_CONFIG_VERSION",
    "TEAM_DOMAIN_WATCHLIST_DOMAINS",
    "TEAM_DOMAIN_WATCHLIST_PRIORITY_BANDS",
    "TeamDomainWatchlistPrioritizationCandidate",
    "TeamDomainWatchlistPrioritizationConfig",
    "TeamDomainWatchlistPrioritizationReasonCodeCount",
    "TeamDomainWatchlistPrioritizationReport",
    "TeamDomainWatchlistPrioritizationRow",
    "build_team_domain_watchlist_prioritization_report",
    "team_domain_watchlist_prioritization_report_payload",
    "validate_team_domain_watchlist_prioritization_report_payload",
)
